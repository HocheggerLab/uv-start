"""Shared logging setup for the workspace (loguru + python-dotenv).

Loguru exposes a single global ``logger`` for the whole process, so the
configuration must live in one place that every package can import
without a dependency cycle. That place is this ``common-utils`` package,
at the bottom of the workspace dependency graph.

Logging architecture (loguru):
    - Modules use the global logger directly via ``from loguru import
      logger`` — there is no per-module logger.
    - Configuration happens **once, at an application entry point** (a CLI
      ``main()`` or, for napari, a widget factory), **never as an import
      side effect**. Library packages simply emit; they never call
      :func:`setup_logging`.
    - Environment is read at call time (argument > env var > default), not
      at import: ``.env`` then ``.env.<ENV>``, then ``LOG_LEVEL`` /
      ``LOG_FILE``. ``.env`` files are resolved relative to the current
      working directory, so run workspace commands from the workspace root.
    - :func:`setup_logging_once` is the idempotent variant for entry
      points that may fire repeatedly (e.g. a napari widget).
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Whether setup_logging() has already run in this process.
_configured = False


def _load_env() -> None:
    """Load ``.env`` then ``.env.<ENV>`` (the latter overriding) if present."""
    env = os.getenv("ENV", "development").lower()
    for path in (Path(".env"), Path(f".env.{env}")):
        if path.exists():
            load_dotenv(path, override=True)


def setup_logging(
    *, level: str | None = None, log_file: str | None = None
) -> None:
    """Load env files and configure loguru's sinks for the whole process.

    Call this ONCE, from an application entry point (a CLI ``main()``),
    never as an import side effect. Resolution precedence for both
    settings is argument > environment variable > default, read here at
    call time. Library packages must never call it — they just
    ``from loguru import logger`` and emit.

    Args:
        level: Minimum level. Falls back to ``LOG_LEVEL`` then ``"INFO"``.
        log_file: Rotating-file-sink path. Falls back to ``LOG_FILE``; if
            still unset, no file sink is added.
    """
    global _configured

    _load_env()
    resolved_level = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    if log_file is None:
        log_file = os.getenv("LOG_FILE")

    logger.remove()
    logger.add(sys.stderr, level=resolved_level, colorize=True)
    if log_file:
        logger.add(
            log_file,
            level=resolved_level,
            rotation="1 MB",
            retention=5,
            compression="zip",
            backtrace=True,
            diagnose=True,
        )
    _configured = True


def setup_logging_once(
    *, level: str | None = None, log_file: str | None = None
) -> None:
    """Configure logging only if it has not been configured yet.

    For entry points that may fire more than once (e.g. a napari widget
    factory): the first call configures, later calls are no-ops, and an
    explicit earlier :func:`setup_logging` call always wins.
    """
    if not _configured:
        setup_logging(level=level, log_file=log_file)
