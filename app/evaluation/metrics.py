import statistics


def score(retrieved: list[tuple], gold: set[tuple], k: int) -> dict:
    top = retrieved[:k]
    top_set = set(top)
    first_rank = next((i for i, r in enumerate(top, 1) if r in gold), None)
    return {
        "hit": any(r in gold for r in top),
        # MRR@k: ранг считается только внутри топ-k; находка за пределами k — 0.
        # Иначе hit=False при rr>0 (бывший баг: rr считался по всему списку выдачи).
        "rr": (1 / first_rank) if first_rank else 0.0,
        "recall": len(gold & top_set) / len(gold) if gold else 1.0,
    }


def report(name: str, rows: list[dict], k: int) -> None:
    print(f"\n== {name} (k={k}) ==")
    cats = sorted({r["category"] for r in rows})
    splits = sorted({r.get("split", "?") for r in rows})
    for cat in cats + ["ALL"]:
        sel = [r for r in rows if cat == "ALL" or r["category"] == cat]
        print(
            f"{cat:16} n={len(sel):2}  hit={sum(r['hit'] for r in sel)}/{len(sel)}  "
            f"MRR={statistics.mean(r['rr'] for r in sel):.2f}  "
            f"recall={statistics.mean(r['recall'] for r in sel):.2f}"
        )
    if len(splits) > 1 or (len(splits) == 1 and splits[0] in ("dev", "holdout")):
        for sp in splits + (["ALL"] if len(splits) > 1 else []):
            sel = [r for r in rows if sp == "ALL" or r.get("split") == sp]
            if not sel:
                continue
            print(
                f"  split={sp:8} n={len(sel):2}  hit={sum(r['hit'] for r in sel)}/{len(sel)}  "
                f"MRR={statistics.mean(r['rr'] for r in sel):.2f}  "
                f"recall={statistics.mean(r['recall'] for r in sel):.2f}"
            )
