import json

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.clients import get_readonly_engine
from app.db.sql_guard import SqlRejected, validate_and_normalize

MAX_COST = 10_000
MAX_ROWS = 100


def check_cost(conn, sql: str) -> None:
    raw = conn.execute(text(f"EXPLAIN (FORMAT JSON) {sql}")).scalar_one()
    plan = (json.loads(raw) if isinstance(raw, str) else raw)[0]["Plan"]
    if plan["Total Cost"] > MAX_COST:
        raise SqlRejected(f"запит надто дорогий (cost={plan['Total Cost']:.0f})")


def run_readonly_query(sql: str) -> list[dict]:
    safe_sql = validate_and_normalize(sql)
    try:
        with get_readonly_engine().connect() as conn:
            conn.execute(text("SET TRANSACTION READ ONLY"))
            check_cost(conn, safe_sql)
            result = conn.execute(text(safe_sql))
            return [dict(row._mapping) for row in result.fetchmany(MAX_ROWS)]
    except DBAPIError as exc:
        raise SqlRejected(f"помилка бази: {str(exc.orig).splitlines()[0]}") from exc