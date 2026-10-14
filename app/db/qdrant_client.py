from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings

client = QdrantClient(url="http://localhost:6333")


PAYLOAD_INDEXES = {
    "file_source": models.PayloadSchemaType.KEYWORD,
    "ingest_id": models.PayloadSchemaType.INTEGER,
}

def source_filter(file_source: str) -> models.Filter:
    return models.Filter(must=[models.FieldCondition(key="file_source", match=models.MatchValue(value=file_source))])


def get_points(ids: list):
    return client.retrieve(
        collection_name=settings.qdrant_collection,
        ids=ids,
        with_payload=True,
        with_vectors=False,
    )


def delete_by_source(file_source: str) -> int:
    flt = source_filter(file_source)
    name = settings.qdrant_collection
    before = client.count(collection_name=name, count_filter=flt, exact=True).count
    if before == 0:
        raise ValueError(f"No points with file_source={file_source!r}: check the key and source name")
    client.delete(collection_name=name, points_selector=models.FilterSelector(filter=flt), wait=True)
    after = client.count(collection_name=name, count_filter=flt, exact=True).count
    if after != 0:
        raise RuntimeError(f"Delete incomplete: {after} points remain")
    return before


def drop_knowledge_base_collection(collection_name: str):
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name=collection_name)
        print("Collection dropped")
    else:
        print("Collection does not exist")

def create_payload_indexes(
    client: QdrantClient,
    collection_name: str,
) -> None:
    for field_name, field_schema in PAYLOAD_INDEXES.items():
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=field_schema,
        )

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

        create_payload_indexes(client, collection_name)

        print("Collection created")

    else:
        print("Collection already exists")


if __name__ == "__main__":
    drop_knowledge_base_collection(settings.qdrant_collection)
    create_knowledge_base_collection(settings.qdrant_collection)
