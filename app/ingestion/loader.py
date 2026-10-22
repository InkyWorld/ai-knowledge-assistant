import hashlib
import uuid
from collections.abc import Iterator

from qdrant_client.http import models
from qdrant_client.http.models import PointStruct

from app.core.clients import get_qdrant
from app.core.config import settings
from app.domain.documents import Chunk
from app.embeddings.dense import get_embeddings
from app.embeddings.sparse import get_sparse_vector

EMBED_BATCH_SIZE = 100


def compute_doc_hash(text: str) -> str:
    """SHA-256 всего текста документа (дедупликация по содержимому).

    Нормализация минимальная (strip + CRLF->LF), чтобы один и тот же текст
    под разными именами файлов давал одинаковый хэш, а правки текста — другой.
    """
    normalized = text.replace("\r\n", "\n").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def ensure_doc_hash_index() -> None:
    """Создать KEYWORD-индекс doc_hash ДО загрузки (иначе фильтр — fullscan)."""
    get_qdrant().create_payload_index(
        collection_name=settings.qdrant_collection,
        field_name="doc_hash",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )


def doc_hash_exists(doc_hash: str, exclude_file_source: str | None = None) -> bool:
    """True, если документ с таким хэшем уже загружен (дубль по содержимому)."""
    if not doc_hash:
        return False
    must = [models.FieldCondition(key="doc_hash", match=models.MatchValue(value=doc_hash))]
    must_not = None
    if exclude_file_source:
        must_not = [models.FieldCondition(key="file_source", match=models.MatchValue(value=exclude_file_source))]
    flt = models.Filter(must=must, must_not=must_not)  # type: ignore[arg-type]
    return get_qdrant().count(collection_name=settings.qdrant_collection, count_filter=flt, exact=True).count > 0


def make_point_id(file_source: str, chunk_index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{file_source}#{chunk_index}"))


def _batched_dense(chunks: list[Chunk]) -> Iterator[tuple[Chunk, list[float]]]:
    for i in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[i : i + EMBED_BATCH_SIZE]
        vectors = get_embeddings(settings.google_embedding_model, [c.content for c in batch])
        yield from zip(batch, vectors)


def load_chunks_to_qdrant(chunks: list[Chunk], ingest_id: str | None = None) -> dict:
    """Загрузить чанки, пропустив документы-дубли по doc_hash.

    Returns: {"loaded": N, "skipped": M, "skipped_sources": [...]}.
    Дедупликация — предпосылка всех замеров: дубль съедает места в топ-k
    и искажает Recall@k для списков, поэтому пропуск — до эмбеддингов.
    """
    by_doc: dict[str, list[Chunk]] = {}
    for c in chunks:
        by_doc.setdefault(c.file_source, []).append(c)

    fresh: list[Chunk] = []
    skipped_sources: list[str] = []
    for file_source, doc_chunks in by_doc.items():
        doc_hash = doc_chunks[0].doc_hash if doc_chunks and doc_chunks[0].doc_hash else ""
        if doc_hash and doc_hash_exists(doc_hash):
            skipped_sources.append(file_source)
            continue
        fresh.extend(doc_chunks)

    points = []
    for chunk, dense in _batched_dense(fresh):
        bm25 = get_sparse_vector(chunk.content)
        vector = {"dense": dense, "bm25": bm25}
        points.append(
            PointStruct(
                id=make_point_id(chunk.file_source, chunk.chunk_index),
                vector=vector,
                payload={
                    **chunk.__dict__,
                    "ingest_id": ingest_id,
                },
            )
        )
    get_qdrant().upsert(collection_name=settings.qdrant_collection, points=points)
    return {"loaded": len(fresh), "skipped": len(chunks) - len(fresh), "skipped_sources": skipped_sources}


def _points(chunks: list[Chunk], ingest_id: str):
    all_chunks = list(chunks)
    for c, dense in _batched_dense(all_chunks):
        yield PointStruct(
            id=make_point_id(c.file_source, c.chunk_index),
            vector={
                "dense": dense,
                "bm25": get_sparse_vector(c.content),
            },
            payload={**c.__dict__, "ingest_id": ingest_id},
        )


def replace_document(file_source: str, chunks: list[Chunk]) -> None:
    ingest_id = uuid.uuid4().hex
    get_qdrant().upload_points(
        collection_name=settings.qdrant_collection, points=_points(chunks, ingest_id), batch_size=256, wait=True
    )
    # the new version is already in the DB; delete only leftovers of the old one
    get_qdrant().delete(
        collection_name=settings.qdrant_collection,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[models.FieldCondition(key="file_source", match=models.MatchValue(value=file_source))],
                must_not=[models.FieldCondition(key="ingest_id", match=models.MatchValue(value=ingest_id))],
            )
        ),
        wait=True,
    )


if __name__ == "__main__":
    import json
    from pathlib import Path

    test_pdf_folder_output_path = Path("data\\chunks\\Про внесення змін до постанови КМУ")
    all_chunks = []
    for input_path in test_pdf_folder_output_path.glob("*.json"):
        with open(input_path, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)
        chunks = [Chunk(**chunk_data) for chunk_data in chunks_data]
        all_chunks.extend(chunks)

    load_chunks_to_qdrant(all_chunks, ingest_id="1")
