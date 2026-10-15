import anthropic
from anthropic.types import TextBlock

from app.core.clients import get_anthropic
from app.core.config import settings
from app.core.logs import logger
from app.domain.chat import ChatHistory
from app.prompts.query_rewriter import SYSTEM_QUERY_REWRITER


def rewrite_query(question: str, history: ChatHistory | None = None) -> str:
    if history is None or not history.messages:
        return question

    try:
        response = get_anthropic().messages.create(
            model=settings.rewriter_model,
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": f"<history>\n{history.to_text(last=4)}\n</history>\n\n<question>\n{question}\n</question>",
                }
            ],
            system=SYSTEM_QUERY_REWRITER,
        )
        if not response.content or not isinstance(response.content[0], TextBlock):
            raise ValueError("Failed to process PDF text with the API.")
        return response.content[0].text
    except anthropic.APIError:
        logger.warning("rewrite failed, using original question", exc_info=True)
        raise
