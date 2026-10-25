from functools import lru_cache

from anthropic import Anthropic
from google import genai
from qdrant_client import QdrantClient
from sqlalchemy import Engine, create_engine

from app.core.config import settings


@lru_cache(maxsize=1)
def get_anthropic() -> Anthropic:
    return Anthropic(api_key=settings.anthropic_api_key)


@lru_cache(maxsize=1)
def get_google() -> genai.Client:
    return genai.Client(api_key=settings.google_api_key)


@lru_cache(maxsize=1)
def get_qdrant() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True)

@lru_cache(maxsize=1)
def get_readonly_engine() -> Engine:
    return create_engine(
        settings.database_url_readonly,
        connect_args={"options": "-c statement_timeout=5000 -c default_transaction_read_only=on"},
    )
