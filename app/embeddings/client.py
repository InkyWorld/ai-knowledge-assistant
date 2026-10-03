from openai import OpenAI

from app.core.config import settings

openai_client = OpenAI(
    api_key=settings.google_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)


def get_embedding(text: str, model: str) -> list[float]:
    response = openai_client.embeddings.create(
        model=model,
        input=text,
        dimensions=768
    )
    return response.data[0].embedding


if __name__ == "__main__":
    # Example usage
    text = "Hello, world!"
    embedding = get_embedding(text, model=settings.google_embedding_model)
    print(f"Embedding for text: {len(embedding)} dimensions")
