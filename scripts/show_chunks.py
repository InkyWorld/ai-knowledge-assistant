import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.db.qdrant_client import client, source_filter


def list_sources() -> list[str]:
    seen, offset = set(), None
    while True:
        points, offset = client.scroll(
            settings.qdrant_collection,
            limit=256,
            offset=offset,
            with_payload=["file_source"],
            with_vectors=False,
        )
        seen.update(p.payload["file_source"] for p in points if p.payload is not None)
        if offset is None:
            return sorted(seen)


def show(file_source: str) -> None:
    points, _ = client.scroll(
        settings.qdrant_collection,
        scroll_filter=source_filter(file_source),
        limit=200,
        with_payload=True,
        with_vectors=False,
    )
    for p in sorted(points, key=lambda p: (p.payload or {}).get("chunk_index", -1)):
        if not p.payload:
            continue
        print(f"--- chunk_index={p.payload['chunk_index']} ---\n{p.payload['content'][:400]}\n")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("\n".join(list_sources()))
    else:
        show(sys.argv[1])
