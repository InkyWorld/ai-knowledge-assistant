from app.core.clients import get_qdrant
from app.core.config import settings
from app.db.catalog import upsert_document_catalog
from app.db.qdrant import list_sources, source_filter


def main() -> None:
    qdrant = get_qdrant()
    for source in list_sources():
        count = qdrant.count(settings.qdrant_collection, count_filter=source_filter(source), exact=True).count
        upsert_document_catalog(source, count)
        print(f"{count:3d}  {source}")


if __name__ == "__main__":
    main()