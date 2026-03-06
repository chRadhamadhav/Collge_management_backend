"""
Centralized structured logger using loguru.
All modules import the `logger` object from here — never use print or console.log.
"""
import sys

from loguru import logger

# Remove the default loguru sink so we control the format entirely
logger.remove()

# Human-readable format for development
_DEV_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>"
)

# JSON-friendly format for production log aggregators
_PROD_FORMAT = "{time:YYYY-MM-DDTHH:mm:ssZ} | {level} | {name}:{line} | {message}"


def configure_logger(environment: str = "development") -> None:
    """
    Call once at application startup to configure log level and format
    based on the current environment.
    """
    is_production = environment == "production"

    logger.add(
        sys.stderr,
        format=_PROD_FORMAT if is_production else _DEV_FORMAT,
        level="INFO" if is_production else "DEBUG",
        colorize=not is_production,
    )

    if not is_production:
        # In development, also write to a rolling file
        logger.add(
            "logs/app.log",
            rotation="10 MB",
            retention="7 days",
            level="DEBUG",
            format=_DEV_FORMAT,
        )
