import uuid
from collections.abc import Iterator

from qdrant_client.http import models
from qdrant_client.http.models import PointStruct

from app.core.config import settings
from app.db.qdrant_client import client
from app.embeddings.client import get_embeddings
from app.embeddings.sparse import get_sparse_vector
from app.ingestion.chunker import Chunk

EMBED_BATCH_SIZE = 100


def make_point_id(file_source: str, chunk_index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{file_source}#{chunk_index}"))


def _batched_dense(chunks: list[Chunk]) -> Iterator[tuple[Chunk, list[float]]]:
    for i in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[i : i + EMBED_BATCH_SIZE]
        vectors = get_embeddings(settings.google_embedding_model, [c.content for c in batch])
        yield from zip(batch, vectors)


def load_chunks_to_qdrant(chunks: list[Chunk], ingest_id: str | None = None) -> None:
    points = []
    for chunk, dense in _batched_dense(chunks):
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
    client.upsert(collection_name="knowledge_base", points=points)


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
    client.upload_points(
        collection_name=settings.qdrant_collection, points=_points(chunks, ingest_id), batch_size=256, wait=True
    )
    # the new version is already in the DB; delete only leftovers of the old one
    client.delete(
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
