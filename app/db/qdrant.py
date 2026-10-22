from qdrant_client.http import models

from app.core.clients import get_qdrant
from app.core.config import settings

PAYLOAD_INDEXES = {
    "file_source": models.PayloadSchemaType.KEYWORD,
    "ingest_id": models.PayloadSchemaType.INTEGER,
    # Хэш всего текста документа для дедупликации по содержимому.
    # KEYWORD-индекс должен существовать ДО загрузки (иначе фильтр по doc_hash — fullscan).
    "doc_hash": models.PayloadSchemaType.KEYWORD,
}


def source_filter(file_source: str) -> models.Filter:
    return models.Filter(must=[models.FieldCondition(key="file_source", match=models.MatchValue(value=file_source))])


def get_points(ids: list):
    qdrant = get_qdrant()
    return qdrant.retrieve(
        collection_name=settings.qdrant_collection,
        ids=ids,
        with_payload=True,
        with_vectors=False,
    )


def delete_by_source(file_source: str) -> int:
    qdrant = get_qdrant()
    flt = source_filter(file_source)
    name = settings.qdrant_collection
    before = qdrant.count(collection_name=name, count_filter=flt, exact=True).count
    if before == 0:
        raise ValueError(f"No points with file_source={file_source!r}: check the key and source name")
    qdrant.delete(collection_name=name, points_selector=models.FilterSelector(filter=flt), wait=True)
    after = qdrant.count(collection_name=name, count_filter=flt, exact=True).count
    if after != 0:
        raise RuntimeError(f"Delete incomplete: {after} points remain")
    return before


def drop_knowledge_base_collection(collection_name: str):
    qdrant = get_qdrant()
    if qdrant.collection_exists(collection_name):
        qdrant.delete_collection(collection_name=collection_name)
        print("Collection dropped")
    else:
        print("Collection does not exist")


def create_payload_indexes(collection_name: str) -> None:
    qdrant = get_qdrant()
    for field_name, field_schema in PAYLOAD_INDEXES.items():
        qdrant.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=field_schema,
        )


def create_knowledge_base_collection(collection_name: str):
    qdrant = get_qdrant()
    if not qdrant.collection_exists(collection_name):
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": models.VectorParams(
                    size=1536,
                    distance=models.Distance.COSINE,
                )
            },
            quantization_config=models.ScalarQuantization(
                scalar=models.ScalarQuantizationConfig(
                    type=models.ScalarType.INT8,
                    always_ram=True,
                )
            ),
            sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )

        create_payload_indexes(collection_name)

        print("Collection created")

    else:
        print("Collection already exists")


if __name__ == "__main__":
    drop_knowledge_base_collection(settings.qdrant_collection)
    create_knowledge_base_collection(settings.qdrant_collection)
