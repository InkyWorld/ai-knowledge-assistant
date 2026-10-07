from google import genai

from app.core.config import settings

client = genai.Client(
    api_key=settings.google_api_key,
)


def get_embedding(
    model: str,
    text: str,
) -> list[float]:
    response = client.models.embed_content(
        model=model,
        contents=text,
        config={
            "output_dimensionality": 1536,
        },
    )
    if not response.embeddings or not response.embeddings[0].values:
        raise ValueError("Failed to generate embedding from the API.")

    return response.embeddings[0].values


if __name__ == "__main__":
    # Example usage
    text = "Hello, world!"
    embedding = get_embedding(model=settings.google_embedding_model, text=text)
    print(f"Embedding for text: {len(embedding)} dimensions")
