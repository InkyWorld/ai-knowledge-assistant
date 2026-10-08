from dataclasses import dataclass

from qdrant_client.http import models

from app.core.config import settings
from app.db.qdrant_client import client
from app.embeddings.client import get_embedding
from app.embeddings.sparse import get_sparse_vector


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float
    index: int
    

def retrieve(query: str, document_type: str | None = None, limit: int = 3) -> list[RetrievedChunk]:
    query_dense = get_embedding(settings.google_embedding_model, query)
    query_bm25 = get_sparse_vector(query)
    query_filter = None
    if document_type:
        query_filter = models.Filter(
            must=[models.FieldCondition(key="document_type", match=models.MatchValue(value=document_type))]
        )

    results = client.query_points(
        collection_name="knowledge_base",
        prefetch=[
            models.Prefetch(query=query_dense, using="", limit=10),
            models.Prefetch(query=query_bm25, using="bm25", limit=10),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        query_filter=query_filter,
        limit=limit,
    )
    if not results.points:
        return []
    
    return [
        RetrievedChunk(
            text=hit.payload["content"], 
            source=hit.payload["file_source"], 
            index=hit.payload["chunk_index"],
            score=hit.score
        )
        for hit in results.points 
        if hit.payload is not None and "content" in hit.payload
    ]

if __name__ == "__main__":
    result = retrieve("До якої дати продовжено термін реалізації публічного інвестиційного проекту \"Створення ветеранських просторів\"?")
    print(result)