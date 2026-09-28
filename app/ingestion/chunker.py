import re
from dataclasses import dataclass, field

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

HEADERS_TO_SPLIT_ON: list[tuple[str, str]] = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]

# A line separating the old wording from the replacement in an amendment clause,
# e.g. "замінити такою позицією:" (singular) or "замінити такими позиціями:" (plural).
AMENDMENT_DELIMITER_RE = re.compile(r"(?m)^(?P<line>.*замінити\s+так\w+\s+позиці\w+:.*)$")

# Start of a position entry: optional opening quote followed by a numeric code.
POSITION_ENTRY_RE = re.compile(r'(?m)^"?\d{6,}\b')


@dataclass
class Chunk:
    text: str
    chunk_index: int
    source: str = "unknown"
    section: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def metadata(self) -> dict:
        return {"source": self.source, "section": self.section, "chunk_index": self.chunk_index, **self.extra}


def _split_entries(part: str) -> list[str]:
    """Split an old/new block into individual position entries."""
    starts = [match.start() for match in POSITION_ENTRY_RE.finditer(part)]
    entries: list[str] = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(part)
        entry = part[start:end].strip().strip('"').strip()
        if entry:
            entries.append(entry)
    return entries


def _split_amendment_pairs(body: str) -> tuple[str, list[str], list[str]] | None:
    """Split an amendment clause into (delimiter, old entries, new entries).

    Returns None when the section is not an old->new amendment
    or entries cannot be paired one-to-one; the caller then falls back
    to plain recursive splitting.
    """
    match = AMENDMENT_DELIMITER_RE.search(body)
    if not match:
        return None
    old_entries = _split_entries(body[: match.start()])
    new_entries = _split_entries(body[match.end() :])
    if not old_entries or len(old_entries) != len(new_entries):
        return None
    return match.group("line").strip(), old_entries, new_entries


def split_markdown_into_chunks(
    text: str,
    source: str = "unknown",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[Chunk]:
    """
    Split Markdown into retrieval-ready chunks.

    Two-stage strategy:
      1. Split by Markdown headers so chunks never mix unrelated sections.
         The header path (e.g. "Intro > Pricing") is stored in Chunk.section.
      2. Within each section, pair old->new amendment entries: a clause such as
         "position 4" holding 3 old + 3 new positions becomes 3 small chunks,
         each chunk a self-contained old->new pair with the clause title
         prepended for context.
      3. Sections without the amendment pattern fall back to a recursive
         character splitter (paragraph -> line -> word) with overlap.

    Args:
        text: Markdown text, e.g. output of document_processor.parse_pdf_to_markdown.
        source: Document identifier stored in every chunk (file path or doc id).
        chunk_size: Max chunk size for the recursive fallback, in characters.
        chunk_overlap: Overlap for the recursive fallback, in characters.

    Returns:
        Ordered list of Chunk objects with section/source metadata.
    """
    if not text or not text.strip():
        return []

    header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=HEADERS_TO_SPLIT_ON)
    sections = header_splitter.split_text(text)

    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    chunks: list[Chunk] = []
    for section in sections:
        headers = section.metadata
        section_path = " > ".join(str(headers[key]) for key in ("h1", "h2", "h3") if key in headers)
        clause_title = str(headers.get("h3") or headers.get("h2") or headers.get("h1") or "")

        pairs = _split_amendment_pairs(section.page_content)
        if pairs is not None:
            delimiter, old_entries, new_entries = pairs
            total = len(old_entries)
            for i, (old, new) in enumerate(zip(old_entries, new_entries)):
                pair_text = f"{old}\n\n{delimiter}\n\n{new}"
                if clause_title:
                    pair_text = f"### {clause_title}\n\n{pair_text}"
                chunks.append(
                    Chunk(
                        text=pair_text,
                        chunk_index=len(chunks),
                        source=source,
                        section=section_path,
                        extra={"pair_index": i, "pairs_total": total},
                    )
                )
            continue

        parts = char_splitter.split_text(section.page_content)
        for part in parts:
            if not part.strip():
                continue
            chunks.append(
                Chunk(
                    text=part,
                    chunk_index=len(chunks),
                    source=source,
                    section=section_path,
                )
            )
    return chunks


if __name__ == "__main__":
    from pathlib import Path

    sample_path = Path("data/output/output.md")
    if not sample_path.exists():
        raise SystemExit(f"Sample file not found: {sample_path}")

    sample_text = sample_path.read_text(encoding="utf-8")
    chunks = split_markdown_into_chunks(sample_text, source=str(sample_path), chunk_overlap=0)

    print(f"Total chunks: {len(chunks)}")
    for chunk in chunks:
        print(f"{'-' * 50}\nChunk {chunk.chunk_index} [{chunk.section}]:\n{chunk.text}\n{'-' * 50}")
