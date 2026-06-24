"""Application logging, configured with loguru.

Importing this module configures loguru's sinks for the whole
application. It is imported once from the package ``__init__``; after
that, use the global logger anywhere::

    from loguru import logger

    logger.info("hello")

By default only a colourised console sink is enabled. Uncomment the file
sink below to also write rotating log files.
"""

import sys

from loguru import logger

# Replace loguru's default handler with our own configuration.
logger.remove()
logger.add(sys.stderr, level="INFO", colorize=True)

# Uncomment to also write rotating log files:
# logger.add(
#     "logs/app.log",
#     level="DEBUG",
#     rotation="1 MB",
#     retention=5,
#     compression="zip",
#     backtrace=True,
#     diagnose=True,
# )
