import sys

from app.core.clients import get_qdrant
from app.core.config import settings
from app.db.qdrant import list_sources, source_filter


def show(file_source: str) -> None:
    points, _ = get_qdrant().scroll(
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
