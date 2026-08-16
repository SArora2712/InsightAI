"""
InsightAI - Structured logging.

Central logger that replaces scattered `print()` debug calls, so app +
FastAPI logs are consistent, leveled, and timestamped. Builds DEBUG/INFO/
WARNING/ERROR hierarchies on a shared root logger.
"""
import logging
import sys
from contextlib import contextmanager
from typing import Iterator

_ROOT_LOGGER_NAME = "insightai"
_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """Return a child logger, e.g. get_logger('core.llm_client')."""
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")


def configure_logging(level: int = logging.INFO) -> None:
    """
    Idempotent root-logger setup: a single StreamHandler with LEVEL + format.
    Safe to call from every entry point (app.py, api/main.py, scripts, tests).
    """
    root = logging.getLogger(_ROOT_LOGGER_NAME)
    if root.handlers:
        return  # already configured

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root.addHandler(handler)
    root.setLevel(level)
    root.propagate = False


@contextmanager
def timed(name: str) -> Iterator[None]:
    """
    Context manager that logs an INFO line with elapsed seconds on exit,
    e.g. `with timed("setup_resources"): ...`.
    """
    import time as _time

    logger = get_logger(name)
    start = _time.perf_counter()
    try:
        yield
    finally:
        elapsed = _time.perf_counter() - start
        logger.info("%s completed in %.3fs", name, elapsed)