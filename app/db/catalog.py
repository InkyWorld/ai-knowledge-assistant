import re
from datetime import date

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.clients import get_engine
from app.db.models import Document

_FILE_RE = re.compile(
    r"^(?P<title>.+?)\s+-\s+(?P<type>Постанова|Наказ|Розпорядження)\s+(?:№|No)\s*(?P<num>[\w\-/]+)\s+від\s+"
    r"(?P<d>\d{2})\.(?P<m>\d{2})\.(?P<y>\d{4})",
    re.IGNORECASE,
)
_FIELDS = ("doc_type", "doc_number", "adopted_date", "title", "chunk_count")


def parse_catalog_fields(file_source: str) -> dict:
    m = _FILE_RE.search(file_source)
    if not m:
        return {"doc_type": "Невідомо", "doc_number": None, "adopted_date": None, "title": file_source}
    return {
        "doc_type": m["type"].capitalize(), "doc_number": m["num"],
        "adopted_date": date(int(m["y"]), int(m["m"]), int(m["d"])), "title": m["title"],
    }


def upsert_document_catalog(file_source: str, chunk_count: int) -> None:
    values = dict(file_source=file_source, chunk_count=chunk_count, **parse_catalog_fields(file_source))
    stmt = insert(Document).values(**values)
    stmt = stmt.on_conflict_do_update(index_elements=[Document.file_source],
                                      set_={f: stmt.excluded[f] for f in _FIELDS})
    with Session(get_engine()) as session:
        session.execute(stmt)
        session.commit()