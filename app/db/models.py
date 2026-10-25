from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Document(Base):
    """Каталог загруженных нормативных документов."""
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_source: Mapped[str] = mapped_column(String(512), unique=True, comment="Полная назва файлу")
    doc_type: Mapped[str] = mapped_column(String(64), comment="Тип: Постанова, Наказ, Розпорядження")
    doc_number: Mapped[str | None] = mapped_column(String(32), comment="Номер документа, напр. 1174")
    adopted_date: Mapped[date | None] = mapped_column(Date, comment="Дата ухвалення")
    title: Mapped[str | None] = mapped_column(Text, comment="Назва документа")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, comment="Кількість фрагментів у базі")
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())