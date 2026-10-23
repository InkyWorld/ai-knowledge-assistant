import anthropic

from app.core.clients import get_anthropic
from app.core.config import settings
from app.core.logs import logger
from app.domain.retrieval import RetrievedChunk
from app.prompts.crag import SYSTEM_GRADER, SYSTEM_SEARCH_REWRITER

GRADE_TOOL = {
    "name": "submit_grade",
    "description": "Повідомляє, чи містить контекст відповідь на запитання.",
    "input_schema": {
        "type": "object",
        "properties": {"answers_question": {"type": "boolean"}, "reason": {"type": "string"}},
        "required": ["answers_question", "reason"],
    },
}


def llm_grade(question: str, chunks: list[RetrievedChunk]) -> bool:
    context = "\n\n".join(f"<fragment index='{i}'>{c.text[:1200]}</fragment>" for i, c in enumerate(chunks[:3], 1))
    try:
        response = get_anthropic().messages.create(
            model=settings.rewriter_model, max_tokens=150, system=SYSTEM_GRADER,
            tools=[GRADE_TOOL], tool_choice={"type": "tool", "name": "submit_grade"},
            messages=[{"role": "user", "content": f"<context>\n{context}\n</context>\n\n<question>{question}</question>"}],
        )
        block = next(b for b in response.content if b.type == "tool_use")
        return bool(block.input["answers_question"])
    except (anthropic.APIError, StopIteration, KeyError):
        logger.warning("grader failed, treating as not answered", exc_info=True)
        return False   # закрытое решение: сомнительное не пропускаем


def rewrite_for_search(question: str, previous_query: str) -> str:
    try:
        response = get_anthropic().messages.create(
            model=settings.rewriter_model, max_tokens=100, system=SYSTEM_SEARCH_REWRITER,
            messages=[{"role": "user", "content": f"<question>{question}</question>\n<previous_query>{previous_query}</previous_query>"}],
        )
        block = response.content[0] if response.content else None
        text = getattr(block, "text", "").strip()
        return text or previous_query
    except anthropic.APIError:
        logger.warning("search rewrite failed, keeping previous query", exc_info=True)
        return previous_query