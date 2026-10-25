from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5"

    google_api_key: str = ""
    google_embedding_model: str = "gemini-embedding-2"

    qdrant_collection: str = "knowledge_base"
    qdrant_url: str = "http://localhost:6333"

    reranker_model: str = "jinaai/jina-reranker-v2-base-multilingual"

    rewriter_model: str = "claude-haiku-4-5"

    # Retrieval defaults
    search_limit: int = 15
    rerank_limit: int = 3
    min_rerank_score: float = -1.16

    crag_pass_score: float = -0.5
    crag_reject_score: float = -2.0
    crag_max_attempts: int = 2

    database_url: str = "postgresql+psycopg://app:app@localhost:5432/assistant"
    database_url_readonly: str = "postgresql+psycopg://assistant_ro:change-me@localhost:5432/assistant"


settings = Settings()
