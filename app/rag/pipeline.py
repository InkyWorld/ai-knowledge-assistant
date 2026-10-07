from anthropic import Anthropic
from anthropic.types import TextBlock

from app.core.config import settings
from app.prompts.rag_system import RAG_SYSTEM_PROMPT
from app.rag.prompt_builder import build_rag_user_prompt
from app.rag.retriever import retrieve

client = Anthropic(api_key=settings.anthropic_api_key)


def ask(question: str, document_type: str | None = None, limit: int = 3) -> dict:
    chunks = retrieve(question, document_type=document_type, limit=limit)

    if not chunks:
        return {"answer": "Я не знайшов релевантної інформації в базі знань.", "sources": []}

    user_prompt = build_rag_user_prompt(question, chunks)

    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=RAG_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    if response.content is None or not isinstance(response.content[0], TextBlock):
        raise ValueError("Failed to get a valid response from the API.")

    return {
        "answer": response.content[0].text,
        "sources": [{"source": c.source, "score": c.score, "index": c.index} for c in chunks],
    }


if __name__ == "__main__":
    result = ask("Яка рада уповноважена щодо сел Довгий Ліс та Великі Кліщі?")
    print("Відповідь:", result["answer"])
    print("\nДжерела:")
    for s in result["sources"]:
        print(f"  {s['source']} | (score={s['score']:.3f}) | (index={s['index']})")
