from dataclasses import dataclass

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


@dataclass
class Chunk:
    file_source: str
    headers: str
    content: str
    chunk_index: int

    def __str__(self):
        return f"Chunk(chunk_index={self.chunk_index}, file_source={self.file_source}, headers={self.headers})"


class LegalChunker:
    def __init__(
        self,
        chunk_size: int = 1500,
        chunk_overlap: int = 200,
    ):
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
            ],
            strip_headers=True,
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

    def split(self, input_path: Path):
        markdown = input_path.read_text(encoding="utf-8")
        documents = self.header_splitter.split_text(markdown)
        raw_chunks = self.text_splitter.split_documents(documents)
        chunks = []
        for i, raw_chunk in enumerate(raw_chunks):
            context_parts = []

            if "h1" in raw_chunk.metadata:
                context_parts.append(raw_chunk.metadata["h1"])
            if "h2" in raw_chunk.metadata:
                context_parts.append(raw_chunk.metadata["h2"])
            if "h3" in raw_chunk.metadata:
                context_parts.append(raw_chunk.metadata["h3"])
            context_prefix = " -> ".join(context_parts)
            raw_chunk.page_content = f"{context_prefix}\n\n{raw_chunk.page_content.strip()}"
            chunks.append(
                Chunk(
                    file_source=input_path.name,
                    content=raw_chunk.page_content,
                    headers=context_prefix,
                    chunk_index=i,
                )
            )

        return chunks


if __name__ == "__main__":
    import json
    from dataclasses import asdict
    from pathlib import Path

    chunker = LegalChunker()
    test_pdf_folder_input_path = Path("data/markdown/Про внесення змін до постанови КМУ")
    test_pdf_folder_output_path = Path("data/chunks/Про внесення змін до постанови КМУ")
    test_pdf_folder_output_path.mkdir(parents=True, exist_ok=True)

    for input_path in test_pdf_folder_input_path.glob("*.md"):
        output_file_path = test_pdf_folder_output_path / (input_path.stem + ".json")

        chunks = chunker.split(input_path)
        output_file_path.write_text(
            json.dumps(
                [asdict(chunk) for chunk in chunks],
                ensure_ascii=False,
                indent=4,
            ),
            encoding="utf-8",
        )

