from app.core.config import settings
from app.domain.retrieval import RetrievedChunk


def is_relevant(chunk: RetrievedChunk) -> bool:
    if chunk.rerank_score is None:
        return True
    return chunk.rerank_score >= settings.min_rerank_score