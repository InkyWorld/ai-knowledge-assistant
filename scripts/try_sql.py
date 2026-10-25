import sqlglot
from sqlalchemy import text

from app.agent.tools.sql_query import generate_sql
from app.core.clients import get_engine

QUESTIONS = [
    "Скільки постанов у каталозі?",
    "Скільки документів ухвалено у вересні 2026?",
    "Яка найновіша постанова? Дай номер і дату.",
    "Яка найстаріша постанова?",
    "Перелічи номери постанов, ухвалених 23 вересня 2026.",
    "Скільки фрагментів у найбільшому документі?",
    "Які документи ухвалено після 25 вересня 2026?",
    "Скільки постанов ухвалено минулого місяця?",
    "Хто підписав постанову 1189?",               # неотвечаемый: ждём отказ
    "Яка сума виділена на програму підтримки?",   # неотвечаемый: вопрос к RAG
]


def explain_status(sql: str) -> str:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SET TRANSACTION READ ONLY"))
            conn.execute(text(f"EXPLAIN {sql}"))
        return "OK"
    except Exception as exc:  # noqa: BLE001
        return "FAIL: " + str(exc).splitlines()[0][:100]


for question in QUESTIONS:
    generated = generate_sql(question)
    print(f"\n? {question}\n  reason: {generated.reason}")
    if not generated.sql:
        print("  sql: (отказ)")
        continue
    try:
        sqlglot.parse(generated.sql, read="postgres")
        parsed = "OK"
    except sqlglot.errors.SqlglotError as exc:
        parsed = f"FAIL: {exc}"
    print(f"  sql: {generated.sql}\n  parse: {parsed} | explain: {explain_status(generated.sql)}")