import json
from pathlib import Path

from app.core.observability import flush_tracing, init_tracing
from app.domain.chat import ChatHistory, ChatMessage
from app.evaluation.run_retrieval import load
from app.rag.pipeline import ask

GOLDEN_PATH = "eval/golden_set_v1.jsonl"
RESULTS_PATH = "eval/results/answers_v1.json"

NO_ANSWER = ("не знайшов", "не знаю", "немає інформації")

# Маркеры спекуляции: must_contain их пропускает (пример q15 — «вірогідно, тисяч гривень»,
# хотя в контексте чанка 9 постанови № 1176 единицы измерения нет, только «16 050»).
# check() их не фейлит (чтобы не шуметь на детерминированности), но помечает warn для ручного разбора.
SPECULATION_MARKERS = ("вірогідно", "ймовірно", "скоріш за все", "тисяч гривень", "млн грн")


def speculation_warn(answer: str) -> list[str]:
    text = answer.lower()
    return [m for m in SPECULATION_MARKERS if m in text]


def check(q: dict, result: dict) -> bool:
    text = result["answer"].lower()
    if not q["answerable"]:
        return any(marker in text for marker in NO_ANSWER)
    return all(fact.lower() in text for fact in q["must_contain"])


def main() -> None:
    init_tracing()
    items = load(GOLDEN_PATH)
    rows = []
    for q in items:
        history = ChatHistory(messages=[ChatMessage(**m) for m in q["history"]]) if q["history"] else None
        result = ask(q["question"], history=history)
        ok = check(q, result)
        warn = speculation_warn(result["answer"])
        rows.append({"id": q["id"], "category": q["category"], "split": q.get("split", "?"), "ok": ok, "answer": result["answer"], "speculation_warn": warn})
        flag = f" SPEC?{warn}" if warn else ""
        print(f"{q['id']} {q['category']:16} ok={int(ok)}{flag}")
    Path(RESULTS_PATH).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved {len(rows)} rows to {RESULTS_PATH}")
    flush_tracing()


if __name__ == "__main__":
    main()
