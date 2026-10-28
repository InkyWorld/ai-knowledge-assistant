from dataclasses import replace
from functools import lru_cache

from langfuse import observe

from app.core.config import settings
from app.domain.retrieval import RetrievedChunk


@lru_cache(maxsize=1)
def get_reranker():  # type: ignore[no-untyped-def]
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    return TextCrossEncoder(model_name=settings.reranker_model, cache_dir=".cache/fastembed")


@observe(name="rerank")
def rerank(query: str, chunks: list[RetrievedChunk], top_n: int = 3) -> list[RetrievedChunk]:
    if len(chunks) <= 1:
        return chunks
    scores = list(get_reranker().rerank(query, [c.text for c in chunks]))
    ranked = sorted(zip(chunks, scores), key=lambda pair: pair[1], reverse=True)[:top_n]
    return [replace(chunk, rerank_score=float(score)) for chunk, score in ranked]
