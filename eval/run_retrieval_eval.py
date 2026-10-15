import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.domain.chat import ChatHistory, ChatMessage  # noqa: E402
from app.rag.query_rewriter import rewrite_query  # noqa: E402
from app.rag.retriever import retrieve  # noqa: E402

CONFIGS = {
    "hybrid": dict(search_limit=15, rerank_limit=None),
    "hybrid+rerank": dict(search_limit=15, rerank_limit=3),
}
K = 3


def load(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def standalone(q: dict) -> str:
    if not q["history"]:
        return q["question"]
    history = ChatHistory(messages=[ChatMessage(**m) for m in q["history"]])
    return rewrite_query(q["question"], history)


def score(retrieved: list[tuple], gold: set[tuple]) -> dict:
    top = retrieved[:K]
    return {
        "hit": any(r in gold for r in top),
        "rr": next((1 / i for i, r in enumerate(retrieved, 1) if r in gold), 0.0),
        "recall": len(gold & set(top)) / len(gold),
    }


def run(items: list[dict], cfg: dict) -> list[dict]:
    rows = []
    for q in items:
        if not q["answerable"]:
            continue
        gold = {(g["file_source"], g["chunk_index"]) for g in q["gold_chunks"]}
        chunks = retrieve(standalone(q), **cfg)
        rows.append({"id": q["id"], "category": q["category"], **score([(c.source, c.index) for c in chunks], gold)})
    return rows


def report(name: str, rows: list[dict]) -> None:
    print(f"\n== {name} (k={K}) ==")
    for cat in sorted({r["category"] for r in rows}) + ["ALL"]:
        sel = [r for r in rows if cat == "ALL" or r["category"] == cat]
        print(
            f"{cat:16} n={len(sel):2}  hit={sum(r['hit'] for r in sel)}/{len(sel)}  "
            f"MRR={statistics.mean(r['rr'] for r in sel):.2f}  "
            f"recall={statistics.mean(r['recall'] for r in sel):.2f}"
        )


if __name__ == "__main__":
    items = load("eval/golden_set_v1.jsonl")
    for name, cfg in CONFIGS.items():
        report(name, run(items, cfg))
