"""Logging configuration."""

import sys
from loguru import logger


def setup_logging():
    """Configure logging for the application."""
    logger.remove()  # Remove default handler

    # Log INFO and DEBUG to stdout
    logger.add(
        sys.stdout,
        format="<level>{level}: {message}</level>",
        level="INFO",
        filter=lambda record: record["level"].no < 30  # Less than WARNING
    )

    # Log WARNING and above to stderr
    logger.add(
        sys.stderr,
        format="<level>{level}: {message}</level>",
        level="WARNING"
    )


def get_logger():
    """Get the configured logger instance.

    Returns:
        Logger instance
    """
    return logger
