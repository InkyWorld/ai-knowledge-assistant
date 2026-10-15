from functools import lru_cache

from fastembed import SparseTextEmbedding
from qdrant_client.http import models


@lru_cache(maxsize=1)
def get_sparse_model() -> SparseTextEmbedding:
    return SparseTextEmbedding(model_name="Qdrant/bm25")


def get_sparse_vector(text: str):
    embedding = next(iter(get_sparse_model().embed([text])))
    return models.SparseVector(
            indices=embedding.indices.tolist(), 
            values=embedding.values.tolist()
        )
