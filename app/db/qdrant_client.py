from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient(url="http://localhost:6333")

COLLECTION_NAME = "knowledge_base"

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
            sparse_vectors_config={
                "bm25": models.SparseVectorParams(
                    modifier=models.Modifier.IDF
                )
            }
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
    drop_knowledge_base_collection(COLLECTION_NAME)
    create_knowledge_base_collection(COLLECTION_NAME)