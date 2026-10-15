import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.domain.chat import ChatHistory, ChatMessage
from app.rag.pipeline import ask
from eval.run_retrieval_eval import load

NO_ANSWER = ("не знайшов", "не знаю", "немає інформації")


def check(q: dict, result: dict) -> bool:
    text = result["answer"].lower()
    if not q["answerable"]:
        return any(marker in text for marker in NO_ANSWER)
    return all(fact.lower() in text for fact in q["must_contain"])


def main() -> None:
    items = load("eval/golden_set_v1.jsonl")
    rows = []
    for q in items:
        history = ChatHistory(messages=[ChatMessage(**m) for m in q["history"]]) if q["history"] else None
        result = ask(q["question"], history=history)
        ok = check(q, result)
        rows.append({"id": q["id"], "category": q["category"], "ok": ok, "answer": result["answer"]})
        print(f"{q['id']} {q['category']:16} ok={int(ok)}")
    Path("eval/results/answers_v1.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved {len(rows)} rows to eval/results/answers_v1.json")


if __name__ == "__main__":
    main()
