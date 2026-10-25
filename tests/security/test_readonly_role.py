import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.clients import get_readonly_engine
from app.db.readonly import run_readonly_query
from app.db.sql_guard import SqlRejected


def test_role_cannot_write():
    with pytest.raises(DBAPIError):
        with get_readonly_engine().begin() as conn:
            conn.execute(text("DELETE FROM documents"))


def test_role_cannot_read_other_tables():
    with pytest.raises(DBAPIError):
        with get_readonly_engine().connect() as conn:
            conn.execute(text("SELECT * FROM conversations")).fetchall()


def test_expensive_query_rejected():
    cross = ", ".join(f"documents d{i}" for i in range(7))
    with pytest.raises(SqlRejected):
        run_readonly_query(f"SELECT COUNT(*) FROM {cross}")