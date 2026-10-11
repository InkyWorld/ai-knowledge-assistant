from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings

client = QdrantClient(url="http://localhost:6333")


def source_filter(source: str) -> models.Filter:
    return models.Filter(must=[models.FieldCondition(key="source", match=models.MatchValue(value=source))])


def get_points(ids: list):
    return client.retrieve(
        collection_name=settings.qdrant_collection,
        ids=ids,
        with_payload=True,
        with_vectors=False,
    )


def delete_by_source(source: str) -> int:
    flt = source_filter(source)
    before = client.count(collection_name=settings.qdrant_collection, count_filter=flt, exact=True).count
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=models.FilterSelector(filter=flt),
        wait=True,
    )
    after = client.count(collection_name=settings.qdrant_collection, count_filter=flt, exact=True).count
    if after != 0:
        raise RuntimeError(f"Удаление не завершилось: осталось {after} точек")
    return before


def drop_knowledge_base_collection(collection_name: str):
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name=collection_name)
        print("Collection dropped")
    else:
        print("Collection does not exist")


def create_knowledge_base_collection(collection_name: str):
    if not client.collection_exists(collection_name):
        client.create_collection(
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

        client.create_payload_index(
            collection_name=collection_name,
            field_name="document_type",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

        print("Collection created")

    else:
        print("Collection already exists")


if __name__ == "__main__":
    drop_knowledge_base_collection(settings.qdrant_collection)
    create_knowledge_base_collection(settings.qdrant_collection)
