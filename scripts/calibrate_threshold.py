"""
Calibration script for min_rerank_score threshold.

- Answerable: собираются ПРОГРАММНО из dev-части golden set (не копируются вручную),
  чтобы калибровка не расходилась с замером.
- Unanswerable: минимум половина — «трудные отрицательные» (вопросы по теме,
  ответа на которые нет в базе). Оффтопик (курс доллара, погода) даёт
  завышенный зазор и ложную уверенность в пороге.
- Вместо одного значения печатается чувствительность порога: цена q07
  (ответ был, реранкер −1.75 отправил в отказ) видна сразу.
"""

import json
import statistics
from pathlib import Path

from app.core.logs import get_logger
from app.domain.chat import ChatHistory, ChatMessage
from app.rag.query_rewriter import rewrite_query
from app.rag.retriever import retrieve

logger = get_logger(__name__)

GOLDEN_PATH = "eval/golden_set_v1.jsonl"

# Трудные отрицательные: по теме корпуса, но ответа в базе нет.
# >= 50% неотвечаемых — такие (остальные — явный оффтопик для якоря).
HARD_NEGATIVES = [
    "Хто підписав постанову № 1189?",
    "Що змінює постанова № 9999?",
    "Який строк дії постанови № 1179 для підприємств Запоріжжя?",
    "Яку суму виділено на безбар'єрні маршрути у 2027 році?",
    "Які громади охоплює постанова № 9999?",
]

OFFTOPIC_NEGATIVES = [
    "Який курс долара сьогодні?",
    "Яка погода завтра в Києві?",
    "Хто виграв вчорашній футбольний матч?",
]

THRESHOLDS = [-2.5, -2.0, -1.5, -1.16, -0.5, 0.0, 0.4]


def standalone(question: str, history: list | None = None) -> str:
    if not history:
        return question
    h = ChatHistory(messages=[ChatMessage(**m) for m in history])
    return rewrite_query(question, h)


def top_score(q: str) -> float | None:
    chunks = retrieve(q, search_limit=15, rerank_limit=3)
    if not chunks:
        return None
    return chunks[0].rerank_score


def main() -> None:
    items = [json.loads(line) for line in Path(GOLDEN_PATH).read_text(encoding="utf-8").splitlines() if line.strip()]
    answerable = [(q["id"], standalone(q["question"], q["history"])) for q in items if q["answerable"] and q.get("split") == "dev"]
    unanswerable_dev = [q["question"] for q in items if not q["answerable"] and q.get("split") == "dev"]
    unanswerable = HARD_NEGATIVES + OFFTOPIC_NEGATIVES + unanswerable_dev
    hard_share = len(HARD_NEGATIVES) / len(unanswerable)
    print(f"answerable: {len(answerable)} (dev golden), unanswerable: {len(unanswerable)} (hard {len(HARD_NEGATIVES)}, share={hard_share:.0%})")
    assert hard_share >= 0.5, "трудных отрицательных должно быть >= 50% неотвечаемых"

    a_raw = [(qid, q, top_score(q)) for qid, q in answerable]
    u_raw = [(q, top_score(q)) for q in unanswerable]

    for qid, q, s in a_raw:
        mark = "  <-- РИСК ОТКАЗА (ср. q07=-1.75)" if s is not None and s < -1.16 else ""
        print(f"  [A] {qid} {s:+.3f}" if s is not None else f"  [A] {qid} None", f"| {q[:60]}" + mark)
    for q, s in u_raw:
        print(f"  [U] {s:+.3f}" if s is not None else "  [U] None", f"| {q[:60]}")

    a = sorted(s for _, _, s in a_raw if s is not None)
    u = sorted(s for _, s in u_raw if s is not None)

    if not a or not u:
        print("No scores — check Qdrant/collection.")
        return

    print(f"answerable: min {a[0]:+.3f} median {statistics.median(a):+.3f} max {a[-1]:+.3f} (n={len(a)})")
    print(f"unanswerable: min {u[0]:+.3f} max {u[-1]:+.3f} (n={len(u)})")

    if u[-1] < a[0]:
        mid = (u[-1] + a[0]) / 2
        print(f"Gap: threshold between {u[-1]:+.3f} and {a[0]:+.3f}, e.g. {mid:+.3f}")
    else:
        print("Ranges overlap — один порог не разделяет классы, нужен LLM-гейт поверх скора.")

    print("\nЧувствительность порога (верные отказы vs потерянные ответы):")
    for t in THRESHOLDS:
        denied_u = sum(s < t for s in u)
        lost_a = sum(s < t for s in a)
        print(f"t={t:+.2f}: верных отказов {denied_u}/{len(u)}, потеряно ответов {lost_a}/{len(a)}")

    none_a = sum(1 for _, _, s in a_raw if s is None)
    none_u = sum(1 for _, s in u_raw if s is None)
    if none_a or none_u:
        logger.warning("Empty results / None scores: answerable=%d unanswerable=%d", none_a, none_u)


if __name__ == "__main__":
    main()
