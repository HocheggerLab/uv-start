"""Application logging, configured with loguru and python-dotenv.

Importing this module loads environment variables (optionally from
``.env`` / ``.env.<ENV>``) and configures loguru's sinks accordingly.
It is imported once from the package ``__init__``; after that, use the
global logger anywhere::

    from loguru import logger

    logger.info("hello")

Recognised environment variables (all optional):
    LOG_LEVEL   console/file level (default: INFO)
    LOG_FILE    if set, also write a rotating log file to this path
    ENV         selects the ``.env.<ENV>`` overrides file (default: development)
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger


def _load_env() -> None:
    """Load ``.env`` then ``.env.<ENV>`` (the latter overriding) if present."""
    env = os.getenv("ENV", "development").lower()
    for path in (Path(".env"), Path(f".env.{env}")):
        if path.exists():
            load_dotenv(path, override=True)


_load_env()
_level = os.getenv("LOG_LEVEL", "INFO").upper()

# Replace loguru's default handler with our own configuration.
logger.remove()
logger.add(sys.stderr, level=_level, colorize=True)

# Optional rotating file sink, enabled by setting LOG_FILE.
if _log_file := os.getenv("LOG_FILE"):
    logger.add(
        _log_file,
        level=_level,
        rotation="1 MB",
        retention=5,
        compression="zip",
        backtrace=True,
        diagnose=True,
    )
