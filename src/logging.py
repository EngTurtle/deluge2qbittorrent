"""Logging configuration."""

import sys
from loguru import logger


def setup_logging(log_level: str = "INFO"):
    """Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger.remove()  # Remove default handler

    # Log at configured level and DEBUG to stdout
    logger.add(
        sys.stdout,
        format="<level>{level}: {message}</level>",
        level=log_level.upper(),
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
