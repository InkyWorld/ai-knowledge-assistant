from anthropic.types import TextBlock

from app.core.clients import get_anthropic
from app.core.config import settings
from app.core.logs import get_logger
from app.domain.chat import ChatHistory
from app.domain.retrieval import RetrievedChunk
from app.prompts.rag_system import RAG_SYSTEM_PROMPT
from app.rag.prompt_builder import build_rag_user_prompt
from app.rag.query_rewriter import rewrite_query
from app.rag.relevance import is_relevant
from app.rag.retriever import retrieve

logger = get_logger(__name__)

NO_ANSWER = {"answer": "Я не знайшов релевантної інформації в базі знань.", "sources": []}


def ask(
    question: str,
    history: ChatHistory | None = None,
    document_type: str | None = None,
    search_limit: int = 15,
    rerank_limit: int | None = 3,
) -> dict:
    standalone = rewrite_query(question, history)
    chunks = retrieve(
        standalone,
        document_type=document_type,
        search_limit=search_limit,
        rerank_limit=rerank_limit,
    )
    if not chunks or not is_relevant(chunks[0]):
        top = chunks[0].rerank_score if chunks else None
        logger.info("no relevant chunks: standalone=%r top_rerank=%s", standalone, top)
        return NO_ANSWER

    user_prompt = build_rag_user_prompt(question, chunks)

    response = get_anthropic().messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=RAG_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    if response.content is None or not isinstance(response.content[0], TextBlock):
        raise ValueError("Failed to get a valid response from the API.")

    return {
        "answer": response.content[0].text,
        "sources": [
            {
                "source": c.source,
                "score": c.rerank_score if c.rerank_score is not None else c.rrf_score,
                "index": c.index,
            }
            for c in chunks
        ],
    }


if __name__ == "__main__":
    from app.domain.chat import ChatHistory

    history = ChatHistory(messages=[])
    question1 = "Яка рада уповноважена щодо сел Довгий Ліс та Великі Кліщі?"
    result1 = ask(question1, history=history)
    history.append(role="user", content=question1)
    history.append(role="assistant", content=result1["answer"])
    print("Відповідь:", result1["answer"])
    print("\nДжерела:")
    for s in result1["sources"]:
        print(f"  {s['source']} | (score={s['score']:.3f}) | (index={s['index']})")

    question2 = "В якій постанові про це йдеться?"
    result2 = ask(question2, history=history)
    history.append(role="user", content=question2)
    history.append(role="assistant", content=result2["answer"])
    print("Відповідь:", result2["answer"])
    print("\nДжерела:")
    for s in result2["sources"]:
        print(f"  {s['source']} | (score={s['score']:.3f}) | (index={s['index']})")
