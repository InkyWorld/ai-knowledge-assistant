import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured: bool = False


def setup_logging(level: int | str = logging.INFO, force: bool = False) -> None:
    global _configured
    if _configured and not force:
        return

    root = logging.getLogger()
    root.setLevel(level)

    if force:
        for h in root.handlers[:]:
            root.removeHandler(h)

    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        root.addHandler(handler)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    _configured = True


def get_logger(name: str | None = None) -> logging.Logger:
    if not _configured:
        setup_logging()
    return logging.getLogger(name if name else __name__)


setup_logging()
logger = get_logger(__name__)
