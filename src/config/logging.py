from __future__ import annotations

import logging
import sys

import structlog

from src.config.settings import Settings


def configure_logging(settings: Settings) -> None:
    processors: list[structlog.types.Processor] = [
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.add_log_level,
        structlog.contextvars.merge_contextvars,
    ]
    if settings.log_format.lower() == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    logging.basicConfig(level=settings.log_level.upper(), format="%(message)s", stream=sys.stdout)
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(settings.log_level.upper())),
        cache_logger_on_first_use=True,
    )
