from functools import lru_cache

from langfuse import Langfuse, get_client

from app.core.config import settings


@lru_cache(maxsize=1)
def init_tracing() -> None:
    from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

    Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    AnthropicInstrumentor().instrument()


def flush_tracing() -> None:
    get_client().flush()