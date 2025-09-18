"""Logging utilities for Voluntier platform."""

import logging
import sys
from typing import Any, Dict

import structlog
from rich.logging import RichHandler

from voluntier.config import settings


def setup_logging() -> None:
    """Setup structured logging for the application."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="ISO", utc=True),
            structlog.dev.ConsoleRenderer() if settings.is_development else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.observability.log_level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, settings.observability.log_level.upper()),
        format="%(message)s",
        handlers=[
            RichHandler(rich_tracebacks=True) if settings.is_development else logging.StreamHandler(sys.stdout)
        ],
    )
    
    # Set third-party library log levels
    logging.getLogger("temporalio").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)


def log_context(**kwargs: Any) -> Dict[str, Any]:
    """
    Create logging context.
    
    Args:
        **kwargs: Context key-value pairs
        
    Returns:
        Context dictionary
    """
    return kwargs