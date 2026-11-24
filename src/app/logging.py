"""Structured logging configuration using structlog.

Produces JSON logs in production and human-friendly console logs locally. The
``request_id`` context variable (populated by the request-id middleware) is
merged into every log record so logs can be correlated with a single request.
"""

from __future__ import annotations

import logging
import sys

import structlog
from structlog.contextvars import merge_contextvars
from structlog.types import FilteringBoundLogger, Processor

from app.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure structlog and the stdlib logging bridge.

    Args:
        settings: Validated application settings controlling log level/format.
    """
    log_level = logging.getLevelName(settings.log_level)

    shared_processors: list[Processor] = [
        merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.log_json:
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging (uvicorn, third-party libs) through structlog so all
    # output shares one format. Remove default handlers to avoid duplicates.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            # stdlib records carry a logger name; structlog's PrintLogger does
            # not, so add_logger_name only runs on the stdlib bridge.
            foreign_pre_chain=[*shared_processors, structlog.stdlib.add_logger_name],
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    for noisy in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logging.getLogger(noisy).handlers = []
        logging.getLogger(noisy).propagate = True


def get_logger(name: str | None = None) -> FilteringBoundLogger:
    """Return a lazily-bound structlog logger.

    Args:
        name: Optional logger name, emitted as the ``logger_name`` key on every record.
    """
    logger: FilteringBoundLogger = (
        structlog.get_logger(logger_name=name) if name else structlog.get_logger()
    )
    return logger
