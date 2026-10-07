from uuid import uuid4

from qdrant_client.http.models import PointStruct

from app.core.config import settings
from app.db.qdrant_client import client
from app.embeddings.client import get_embedding
from app.ingestion.chunker import Chunk


def load_chunks_to_qdrant(chunks: list[Chunk]):
    points = []
    for chunk in chunks:
        vector = get_embedding(settings.google_embedding_model, chunk.content)
        points.append(
            PointStruct(
                id=uuid4(),
                vector=vector,
                payload={
                    **chunk.__dict__,
                },
            )
        )
    client.upsert(collection_name="knowledge_base", points=points)


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

    load_chunks_to_qdrant(all_chunks)
