from qdrant_client.http import models

from app.core.config import settings
from app.db.qdrant_client import client
from app.embeddings.client import get_embedding
from app.embeddings.sparse import get_sparse_vector
from app.rag.reranker import rerank
from app.domain.retrieval import RetrievedChunk


def _search(query: str, document_type: str | None, fetch_limit: int) -> list[RetrievedChunk]:
    query_dense = get_embedding(settings.google_embedding_model, query, kind="query")
    query_bm25 = get_sparse_vector(query)
    query_filter = None
    if document_type:
        query_filter = models.Filter(
            must=[models.FieldCondition(key="document_type", match=models.MatchValue(value=document_type))]
        )

    results = client.query_points(
        collection_name="knowledge_base",
        prefetch=[
            models.Prefetch(query=query_dense, using="dense", limit=20),
            models.Prefetch(query=query_bm25, using="bm25", limit=20),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        query_filter=query_filter,
        limit=fetch_limit,
    )
    if not results.points:
        return []

    return [
        RetrievedChunk(
            text=hit.payload["content"],
            source=hit.payload["file_source"],
            index=hit.payload["chunk_index"],
            rrf_score=hit.score,
        )
        for hit in results.points
        if hit.payload is not None and "content" in hit.payload
    ]


def retrieve(
    query: str,
    search_limit: int = 10,
    rerank_limit: int | None = None,
    document_type: str | None = None,
) -> list[RetrievedChunk]:
    chunks = _search(query, document_type, search_limit)
    if rerank_limit is not None:
        return rerank(query, chunks, top_n=rerank_limit)
    return chunks




if __name__ == "__main__":
    # ПЕРЕЛІК «село → рада» розбитий на чанки 8, 9 (+ хвіст 10). RRF топ-1 — процедурний чанк
    # (реєстр тергромади), а шматки списку лежать внизу видачі; реранк піднімає 9 і 8 у топ-2
    demo_query = "Які громади охоплює постанова 1174?"
    print(f"\n{'=' * 80}\nQUERY: {demo_query}")
    base = retrieve(demo_query, search_limit=15, rerank_limit=None)
    ranked = retrieve(demo_query, search_limit=15, rerank_limit=3)
    print("--- необхідні чанки (без reranking) ---")
    for i, chunk in enumerate(base):
        if chunk.index in (8, 9, 10):
            print(f" rank {i+1}: rrf={chunk.rrf_score:.3f} [index {chunk.index}]")
    print("--- необхідні чанки після reranking ---")
    for i, chunk in enumerate(ranked):
        if chunk.index in (8, 9, 10):
            print(
                f" rank {i+1}: rerank={chunk.rerank_score:+.3f}"
                f"[index {chunk.index}]"
            )
