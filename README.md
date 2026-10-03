# AI Knowledge Assistant

> Day 7 — embeddings
## Local run

```bash
cp .env.example .env  # fill in ANTHROPIC_API_KEY
uv sync
uv run uvicorn app.main:app --reload
```

Health check: http://127.0.0.1:8000/health

## Structure

- `app/api/` — FastAPI routers
- `app/core/` — settings, constants, client singletons
- `app/db/` — DB connections
- `app/ingestion/` — document processing
- `app/rag/` — vector search, reranker
- `app/agent/tools/` — LangGraph and tools
- `app/evaluation/` — RAGAS
- `app/main.py` — entrypoint
- `tests/` — tests
