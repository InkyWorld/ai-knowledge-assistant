from fastembed import SparseTextEmbedding
from qdrant_client.http import models

sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")


def get_sparse_vector(text: str):
    embedding = next(iter(sparse_model.embed([text])))
    return models.SparseVector(
            indices=embedding.indices.tolist(), 
            values=embedding.values.tolist()
        )
