import sys

from loguru import logger

from app.config.settings import get_settings

settings = get_settings()

logger.remove()

logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    colorize=True,
    enqueue=True
)

logger.add(
    "logs/application.log",
    rotation="100 MB",
    retention="30 days",
    compression="zip",
    level=settings.LOG_LEVEL,
    enqueue=True
)

logger.add(
    "logs/error.log",
    level="ERROR",
    rotation="100 MB",
    retention="60 days",
    compression="zip",
    enqueue=True
)