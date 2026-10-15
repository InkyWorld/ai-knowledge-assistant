import json
from pathlib import Path

from app.domain.chat import ChatHistory, ChatMessage
from app.evaluation.metrics import report, score
from app.rag.query_rewriter import rewrite_query
from app.rag.retriever import retrieve

CONFIGS = {
    "hybrid": dict(search_limit=15, rerank_limit=None),
    "hybrid+rerank": dict(search_limit=15, rerank_limit=3),
}
K = 3

GOLDEN_PATH = "eval/golden_set_v1.jsonl"
RESULTS_PATH = "eval/results/retrieval_v1.json"


def load(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def standalone(q: dict) -> str:
    if not q["history"]:
        return q["question"]
    history = ChatHistory(messages=[ChatMessage(**m) for m in q["history"]])
    return rewrite_query(q["question"], history)


def run(items: list[dict], cfg: dict) -> list[dict]:
    rows = []
    for q in items:
        if not q["answerable"]:
            continue
        gold = {(g["file_source"], g["chunk_index"]) for g in q["gold_chunks"]}
        chunks = retrieve(standalone(q), **cfg)
        rows.append({"id": q["id"], "category": q["category"], **score([(c.source, c.index) for c in chunks], gold, K)})
    return rows


def main() -> None:
    items = load(GOLDEN_PATH)
    all_rows: dict[str, list[dict]] = {}
    for name, cfg in CONFIGS.items():
        rows = run(items, cfg)
        report(name, rows, K)
        all_rows[name] = rows
    Path(RESULTS_PATH).write_text(json.dumps(all_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved per-question rows to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
