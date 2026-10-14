"""
Calibration script for min_rerank_score threshold.
"""

import statistics

from app.core.logs import get_logger
from app.rag.retriever import retrieve

logger = get_logger(__name__)

answerable = [
    "Яка рада уповноважена щодо сіл Довгий Ліс та Великі Кліщі?",
    "Які громади охоплює постанова 1174?",
    "Від якої дати постанова № 1187 про внесення змін?",
    "Які зміни внесено до постанови Кабінету Міністрів України?",
    "Коли набирає чинності постанова про внесення змін?",
    "Ким затверджено зміни щодо надання державної субсидії?",
    "Що доповнено в пункті 11 переліку заходів у сфері культури?",
    "Який порядок використання коштів затверджено постановою № 638?",
    "Які доповнення внесено до пункту 4 порядку використання коштів?",
    "В якій постанові йдеться про Довгий Ліс та Великі Кліщі?",
]

unanswerable = [
    "Який курс долара сьогодні?",
    "Яка погода завтра в Києві?",
    "Хто виграв вчорашній футбольний матч?",
    "Як приготувати борщ?",
    "Яка ціна біткоїна зараз?",
]


def top_score(q: str) -> float | None:
    chunks = retrieve(q, search_limit=15, rerank_limit=3)
    if not chunks:
        return None
    return chunks[0].rerank_score


def main() -> None:
    a_raw = [(q, top_score(q)) for q in answerable]
    u_raw = [(q, top_score(q)) for q in unanswerable]

    for q, s in a_raw:
        print(f"  [A] {s} | {q}")
    for q, s in u_raw:
        print(f"  [U] {s} | {q}")

    a = sorted(s for _, s in a_raw if s is not None)
    u = sorted(s for _, s in u_raw if s is not None)

    if not a:
        print("No scores for answerable — check Qdrant/collection.")
        return
    if not u:
        print("No scores for unanswerable — check Qdrant/collection.")
        return

    print(f"answerable: min {a[0]:+.3f} median {statistics.median(a):+.3f} max {a[-1]:+.3f} (n={len(a)})")
    print(f"unanswerable: min {u[0]:+.3f} max {u[-1]:+.3f} (n={len(u)})")

    if u[-1] < a[0]:
        mid = (u[-1] + a[0]) / 2
        print(f"Pick a threshold between {u[-1]:+.3f} and {a[0]:+.3f}, e.g. {mid:+.3f} -> MIN_RERANK_SCORE")
    else:
        print("Ranges overlap — the threshold cannot be trusted, an LLM gate is needed.")

    none_a = sum(1 for _, s in a_raw if s is None)
    none_u = sum(1 for _, s in u_raw if s is None)
    if none_a or none_u:
        logger.warning("Empty results / None scores: answerable=%d unanswerable=%d", none_a, none_u)


if __name__ == "__main__":
    main()

#   [A] 0.943545937538147 | Яка рада уповноважена щодо сіл Довгий Ліс та Великі Кліщі?
#   [A] 0.43225008249282837 | Які громади охоплює постанова 1174?
#   [A] 0.8548252582550049 | Від якої дати постанова № 1187 про внесення змін?
#   [A] 1.2190173864364624 | Які зміни внесено до постанови Кабінету Міністрів України?
#   [A] 0.5682789087295532 | Коли набирає чинності постанова про внесення змін?
#   [A] 0.7227606177330017 | Ким затверджено зміни щодо надання державної субсидії?
#   [A] 0.5777747631072998 | Що доповнено в пункті 11 переліку заходів у сфері культури?
#   [A] 0.41328561305999756 | Який порядок використання коштів затверджено постановою № 638?
#   [A] 0.5208566784858704 | Які доповнення внесено до пункту 4 порядку використання коштів?
#   [A] 0.5017598271369934 | В якій постанові йдеться про Довгий Ліс та Великі Кліщі?
#   [U] -3.049144744873047 | Який курс долара сьогодні?
#   [U] -2.7340638637542725 | Яка погода завтра в Києві?
#   [U] -3.5169596672058105 | Хто виграв вчорашній футбольний матч?
#   [U] -3.074880361557007 | Як приготувати борщ?
#   [U] -2.9137063026428223 | Яка ціна біткоїна зараз?
# With a response: min +0.413, median +0.573, max +1.219 (n=10)
# Without a response: min -3.517, max -2.734 (n=5)
# Choose a threshold between -2.734 and +0.413; for example, -1.160 -> MIN_RERANK_SCORE