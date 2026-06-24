# Logging Setup for Generated Projects

Projects scaffolded by `uv-start` use [loguru](https://github.com/Delgan/loguru)
for logging. This replaces the older stdlib `logging` + `RotatingFileHandler`
setup with a much smaller, friendlier configuration while keeping the same
"works out of the box" philosophy.

## Core Design Philosophy

- **Sensible defaults**: colourised console logging works immediately, no setup.
- **One place to configure**: all sink configuration lives in
  `src/<package>/config.py`.
- **Simple developer experience**: a single global `logger`, no per-module
  factory.
- **Opt-in environment control**: env-var-driven configuration is available via
  the `--dotenv` flag for projects that need it.

## The config module

Importing the package runs `from . import config` (in `__init__.py`), which
configures loguru's sinks exactly once. The default `config.py` is tiny:

```python
import sys

from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", colorize=True)

# Uncomment to also write rotating log files:
# logger.add(
#     "logs/app.log", level="DEBUG", rotation="1 MB",
#     retention=5, compression="zip", backtrace=True, diagnose=True,
# )
```

`logger.remove()` drops loguru's default handler so we start from a clean
slate; each `logger.add(...)` registers an independent **sink** with its own
level, format and rotation policy.

## Using the logger

There is no `get_logger()` factory — import the global logger directly:

```python
from loguru import logger

def some_function():
    logger.debug("Starting function execution")
    try:
        ...
        logger.info("Operation completed successfully")
    except Exception:
        logger.exception("Operation failed")  # full diagnostic traceback
        raise
```

Loguru records the module, function and line automatically, so there is no
need to pass `__name__` or resolve `__main__` by hand.

## Console vs file, and log levels

Terminal and file output are simply two `logger.add()` calls. Each sink sets
its own minimum level via the `level=` argument — there is no separate
"logger level". This means the console can stay at `INFO` while the file
captures `DEBUG`. File rotation, retention and compression are built in:

```python
logger.add(
    "logs/app.log",
    level="DEBUG",
    rotation="1 MB",     # rotate when the file reaches 1 MB
    retention=5,         # keep 5 rotated files
    compression="zip",   # compress rotated files
)
```

## Environment-driven configuration (`--dotenv`)

Scaffolding with `uv-start <name> --dotenv` swaps in a `config.py` that reads
its configuration from environment variables (optionally loaded from `.env` /
`.env.<ENV>` via `python-dotenv`) and ships a `.env.example`:

| Variable    | Default       | Description                                          |
| ----------- | ------------- | ---------------------------------------------------- |
| `LOG_LEVEL` | `INFO`        | Minimum level for the console (and file) sink        |
| `LOG_FILE`  | *(unset)*     | If set, also write a rotating log file to this path  |
| `ENV`       | `development` | Selects the `.env.<ENV>` overrides file if present   |

The loading strategy is: base `.env` → `.env.<ENV>` (overriding) → code-level
defaults for anything unset. In production you typically set real environment
variables rather than shipping a `.env` file.

## Why loguru?

- ~25 lines instead of ~160.
- Rotation/retention/compression without `RotatingFileHandler` boilerplate.
- Colourised console output and rich tracebacks (`backtrace`/`diagnose`).
- Automatic module/function/line capture — no `__main__` inspection hacks.

Note that loguru is a separate system from stdlib `logging`; logs emitted by
third-party libraries through stdlib `logging` are **not** captured unless you
add an `InterceptHandler` bridge. The generated config keeps things minimal and
does not include one by default.
