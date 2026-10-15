from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    text: str
    source: str
    rrf_score: float
    index: int
    rerank_score: float | None = None
