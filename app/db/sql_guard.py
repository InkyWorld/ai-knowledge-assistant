import sqlglot
from sqlglot import exp

ALLOWED_TABLES = {"documents"}
DENY_FUNCS = {
    "pg_sleep", "pg_read_file", "pg_read_binary_file", "pg_ls_dir", "pg_stat_file", "lo_import", "lo_export",
    "dblink", "set_config", "current_setting", "query_to_xml", "pg_terminate_backend", "pg_cancel_backend",
}
MAX_LIMIT = 100

FORBIDDEN = tuple(
    getattr(exp, name) for name in
    ("Insert", "Update", "Delete", "Drop", "Alter", "AlterTable", "TruncateTable",
     "Create", "Command", "Into", "Copy", "Merge")
    if hasattr(exp, name)
)


class SqlRejected(Exception):
    pass


def validate_and_normalize(sql: str) -> str:
    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except sqlglot.errors.SqlglotError as exc:
        raise SqlRejected(f"не вдалося розібрати запит: {exc}") from exc
    if len(statements) != 1:
        raise SqlRejected("дозволено рівно один запит")
    tree = statements[0]
    if not isinstance(tree, exp.Select):
        raise SqlRejected("дозволено лише звичайний SELECT")
    if tree.find(*FORBIDDEN):
        raise SqlRejected("заборонена конструкція")

    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        if table.db or table.catalog:
            raise SqlRejected("назви зі схемою заборонені")
        if table.name.lower() not in ALLOWED_TABLES | cte_names:
            raise SqlRejected(f"таблиця не дозволена: {table.name or '(функція)'}")

    for func in tree.find_all(exp.Func):
        name = (func.name if isinstance(func, exp.Anonymous) else func.sql_name()).lower()
        if name in DENY_FUNCS:
            raise SqlRejected(f"функція заборонена: {name}")

    limit = tree.args.get("limit")
    if limit is None:
        tree = tree.limit(MAX_LIMIT)
    else:
        count = limit.args["count"] if isinstance(limit, exp.Fetch) else limit.expression
        try:
            too_big = int(count.name) > MAX_LIMIT
        except (AttributeError, ValueError):
            raise SqlRejected("LIMIT має бути числом") from None
        if too_big:
            if isinstance(limit, exp.Fetch):
                limit.set("count", exp.Literal.number(MAX_LIMIT))
            else:
                tree = tree.limit(MAX_LIMIT)
    return tree.sql(dialect="postgres")