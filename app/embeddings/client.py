from typing import cast

from google import genai
from google.genai import types

from app.core.config import settings

client = genai.Client(
    api_key=settings.google_api_key,
)


def get_embedding(model: str, text: str, kind: str = "document", title: str | None = None) -> list[float]:
    prepared = (
        f"task: question answering | query: {text}" if kind == "query" else f"title: {title or 'none'} | text: {text}"
    )
    response = client.models.embed_content(
        model=model,
        contents=prepared,
        config={
            "output_dimensionality": 1536,
        },
    )
    if not response.embeddings or not response.embeddings[0].values:
        raise ValueError("Failed to generate embedding from the API.")

    return response.embeddings[0].values


def get_embeddings(model: str, texts: list[str], kind: str = "document", title: str | None = None) -> list[list[float]]:
    """Batch version. Each text is wrapped in its own Content,
    otherwise gemini-embedding returns a single aggregated vector."""
    if not texts:
        return []
    prepared = [
        f"task: question answering | query: {t}" if kind == "query" else f"title: {title or 'none'} | text: {t}"
        for t in texts
    ]
    contents = [types.Content(parts=[types.Part.from_text(text=t)]) for t in prepared]
    response = client.models.embed_content(
        model=model,
        contents=cast(types.ContentListUnion, contents),
        config={
            "output_dimensionality": 1536,
        },
    )
    if not response.embeddings or len(response.embeddings) != len(texts):
        raise ValueError("Failed to generate batch embeddings from the API.")
    vectors = []
    for embedding in response.embeddings:
        if not embedding.values:
            raise ValueError("Failed to generate batch embeddings from the API.")
        vectors.append(embedding.values)
    return vectors


if __name__ == "__main__":
    # Example usage
    text = "Hello, world!"
    embedding = get_embedding(model=settings.google_embedding_model, text=text)
    print(f"Embedding for text: {len(embedding)} dimensions")
