from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient(url="http://localhost:6333")

COLLECTION_NAME = "knowledge_base"


def create_knowledge_base_collection():
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=1536,
                distance=models.Distance.COSINE,
            ),
            quantization_config=models.ScalarQuantization(
                scalar=models.ScalarQuantizationConfig(
                    type=models.ScalarType.INT8,
                    always_ram=True,
                )
            ),
        )

        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="document_type",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

        print("Collection created")

    else:
        print("Collection already exists")


if __name__ == "__main__":
    create_knowledge_base_collection()