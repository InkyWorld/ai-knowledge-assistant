import statistics


def score(retrieved: list[tuple], gold: set[tuple], k: int) -> dict:
    top = retrieved[:k]
    return {
        "hit": any(r in gold for r in top),
        "rr": next((1 / i for i, r in enumerate(retrieved, 1) if r in gold), 0.0),
        "recall": len(gold & set(top)) / len(gold),
    }


def report(name: str, rows: list[dict], k: int) -> None:
    print(f"\n== {name} (k={k}) ==")
    for cat in sorted({r["category"] for r in rows}) + ["ALL"]:
        sel = [r for r in rows if cat == "ALL" or r["category"] == cat]
        print(
            f"{cat:16} n={len(sel):2}  hit={sum(r['hit'] for r in sel)}/{len(sel)}  "
            f"MRR={statistics.mean(r['rr'] for r in sel):.2f}  "
            f"recall={statistics.mean(r['recall'] for r in sel):.2f}"
        )
