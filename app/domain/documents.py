from dataclasses import dataclass, field


@dataclass
class Chunk:
    file_source: str
    headers: str
    content: str
    chunk_index: int
    # SHA-256 hex всего текста документа (для дедупликации по содержимому).
    # Заполняется чанкером/ingest-пайплайном; пустая строка = хэш неизвестен.
    doc_hash: str = field(default="")

    def __str__(self):
        return f"Chunk(chunk_index={self.chunk_index}, file_source={self.file_source}, headers={self.headers})"
