# AI Knowledge Assistant

> Day 5 — multimodal ingestion (PDF/Vision): extract text, tables, and data from PDFs into Markdown via Claude.

Layered FastAPI + RAG skeleton with multimodal PDF ingestion.

## Local run

```bash
cp .env.example .env  # fill in ANTHROPIC_API_KEY
uv sync
uv run uvicorn app.main:app --reload
```

Health check: http://127.0.0.1:8000/health

## Ingestion (PDF/Vision)

Parse a PDF into Markdown with Claude (`app/ingestion/document_processor.py`):

```bash
# put your source PDF under data/ (gitignored), e.g. data/input.pdf
uv run python -m app.ingestion.document_processor
```

Output: Markdown written under `data/output/`.

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
