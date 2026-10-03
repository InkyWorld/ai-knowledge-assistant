import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x**2 for x in a))
    norm_b = math.sqrt(sum(x**2 for x in b))
    return dot_product / (norm_a * norm_b)


if __name__ == "__main__":
    sentences = [
        "The cat is sleeping on the sofa.",
        "A feline is resting on the couch.",
        "Python is a popular programming language.",
        "Python is widely used for software development.",
        "The car is parked near the house.",
        "A vehicle is standing beside the building.",
        "The company released a new smartphone.",
        "A new mobile phone was launched by the company.",
        "The bank approved my loan application.",
        "The bank rejected my loan application.",
    ]
    from app.core.config import settings
    from app.embeddings.client import get_embedding

    embeddings = [get_embedding(sentence, model=settings.google_embedding_model) for sentence in sentences]

    for i, (sentence, embedding) in enumerate(zip(sentences, embeddings)):
        for j, (other_sentence, other_embedding) in enumerate(zip(sentences[i + 1 :], embeddings[i + 1 :])):
            similarity = cosine_similarity(embedding, other_embedding)
            print(f"Similarity between '{sentence}' and '{other_sentence}': {similarity:.2f}")
