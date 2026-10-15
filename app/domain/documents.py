from dataclasses import dataclass


@dataclass
class Chunk:
    file_source: str
    headers: str
    content: str
    chunk_index: int

    def __str__(self):
        return f"Chunk(chunk_index={self.chunk_index}, file_source={self.file_source}, headers={self.headers})"
