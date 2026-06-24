"""Shared logging setup for the workspace, configured with loguru.

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
      :func:`setup_logging`, so their records flow into whatever sinks the
      running application set up.
    - :func:`setup_logging_once` is the idempotent variant for entry
      points that may fire repeatedly (e.g. a napari widget).
"""

import sys

from loguru import logger

# Whether setup_logging() has already run in this process.
_configured = False


def setup_logging(*, level: str = "INFO", log_file: str | None = None) -> None:
    """Configure loguru's sinks for the whole process.

    Call this ONCE, from an application entry point (a CLI ``main()``),
    never as an import side effect. Because loguru's ``logger`` is a
    single process-global object, this one call governs logging for every
    module in every package in the process. Library packages must never
    call it — they just ``from loguru import logger`` and emit.

    Args:
        level: Minimum level for the console (and file) sink.
        log_file: If given, also write a rotating log file to this path.
    """
    global _configured

    logger.remove()
    logger.add(sys.stderr, level=level, colorize=True)
    if log_file:
        logger.add(
            log_file,
            level=level,
            rotation="1 MB",
            retention=5,
            compression="zip",
            backtrace=True,
            diagnose=True,
        )
    _configured = True


def setup_logging_once(
    *, level: str = "INFO", log_file: str | None = None
) -> None:
    """Configure logging only if it has not been configured yet.

    For entry points that may fire more than once (e.g. a napari widget
    factory): the first call configures, later calls are no-ops, and an
    explicit earlier :func:`setup_logging` call always wins.
    """
    if not _configured:
        setup_logging(level=level, log_file=log_file)
