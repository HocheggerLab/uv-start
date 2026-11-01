---
name: uv-start
description: >
  Scaffold Python projects with uv. Creates src-layout packages with
  pre-configured ruff, ty, pytest, commitizen, pre-commit, and loguru
  logging. Supports single-package projects, workspaces (monorepos),
  data-analysis projects, and napari plugin projects.
license: MIT
compatibility: Requires Python >=3.13 and uv.
metadata:
  author: hh65
  tags:
    - python
    - uv
    - scaffolding
    - cli
---

# uv-start

CLI tool that wraps `uv init` to produce fully-configured Python projects.
Run it from the **parent** directory of where the new project should live —
it must not be inside an existing git repo.

## Installation

```bash
uv tool install uv-start
uv-start --config "Your Name" "you@example.com"   # run once to save author info
```

## When to use what

| Goal | Command |
|------|---------|
| Simple importable library | `uv-start my-lib` |
| CLI app with entry-point script | `uv-start my-cli -t app` |
| Installable package (no script) | `uv-start my-pkg -t package` |
| Monorepo with shared utils | `uv-start my-workspace -w` |
| Data analysis (Jupyter + pandas) | `uv-start my-analysis --data` |
| napari plugin | `uv-start my-plugin --napari` |
| Any of the above + GitHub repo | add `-g` (and `--private` for private) |
| Env-driven log level / log file | add `--dotenv` |
| Upgrade deps safely (cooldown + audit) | `uv-start --upgrade` in the project |

## Full command reference

```
uv-start PROJECT_NAME [options]
```

| Flag | Default | Description |
|------|---------|-------------|
| `-t, --type [lib\|package\|app]` | `lib` | Project type |
| `-p, --python [3.14…3.11]` | `3.14` | Python version (3.10 is end-of-life) |
| `-w, --workspace` | off | Create a uv workspace (monorepo) |
| `-g, --github` | off | Init git repo + create GitHub remote |
| `--private` | off | Make GitHub repo private (requires `-g`) |
| `--data` | off | Data-analysis project for notebooks (ipykernel, numpy, pandas, matplotlib, seaborn) |
| `--lab` | off | With `--data`: lab matplotlib style, `COLOR` palette, CLAUDE.md |
| `--napari` | off | napari plugin project |
| `--dotenv` | off | Env-driven logging via python-dotenv |
| `--config NAME EMAIL` | — | Save author defaults, then exit |
| `--upgrade` | — | In a project folder: update uv + Python, upgrade deps past the 7-day cooldown, `uv audit`, sync |
| `--cooldown DAYS` / `--dry-run` | 7 / off | Refine `--upgrade` |

## Generated structure

### Standard project (`lib` / `package` / `app`)

```
my-project/
├── src/my_project/
│   ├── __init__.py      # __version__, loguru config import
│   └── config.py        # loguru: console sink at INFO
├── tests/
├── pyproject.toml       # ruff, ty, pytest, commitizen config
├── .pre-commit-config.yaml
├── README.md
└── LICENSE
```

`app` and `package` types also get a `[project.scripts]` entry point in
`pyproject.toml` and a `main()` function in `__init__.py`.

### Workspace (`-w`)

```
my-workspace/
├── packages/
│   ├── common_utils/    # always created — hosts shared logging setup
│   │   └── src/common_utils/logging_setup.py
│   └── my-app/          # optional — prompted during scaffolding
│       └── src/my_app/__init__.py   # calls setup_logging_once() in main()
├── pyproject.toml       # [tool.uv.workspace] + [tool.uv.sources]
└── .pre-commit-config.yaml
```

## Logging pattern

### Single-package project

Loguru is configured automatically when the package is imported:

```python
# src/my_package/__init__.py  (generated)
from . import config  # installs colourised console sink at INFO

# in any module:
from loguru import logger

logger.info("message")
```

To add a rotating file sink, uncomment in `config.py`:

```python
logger.add(
    "logs/app.log",
    level="DEBUG",
    rotation="1 MB",
    retention=5,
    compression="zip",
    backtrace=True,
    diagnose=True,
)
```

### Workspace project

Only **entry-point `main()` functions** configure logging.
Library packages only emit — never configure sinks:

```python
# app member's __init__.py  (generated)
from common_utils.logging_setup import setup_logging_once
from loguru import logger


def main() -> None:
    setup_logging_once()  # idempotent — safe to call more than once
    logger.info("Hello!")
```

### `--dotenv` variant

Control level and file path via environment variables:

```bash
LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log
ENV=production          # also loads .env.production
```

## Dev tools in every project

| Tool | Purpose | Key command |
|------|---------|-------------|
| **ruff** | Lint + format | `uv run ruff check . && uv run ruff format .` |
| **ty** | Type checking (editor) | `uv run ty check src tests` |
| **mypy** | Type checking (CI / pre-commit) | `uv run mypy .` |
| **pytest** | Tests | `uv run pytest` |
| **commitizen** | Conventional commits + versioning | `cz commit` / `cz bump` |
| **pre-commit** | Git hooks | `pre-commit run --all-files` |

## Version bumps

Generated projects use [conventional commits](https://www.conventionalcommits.org/):

| Commit prefix | Bump |
|---------------|------|
| `fix:` | PATCH |
| `feat:` | MINOR |
| `feat!:` or `BREAKING CHANGE:` | MAJOR (MINOR while version < 1.0) |

```bash
cz commit   # interactive prompt for correctly formatted commit
cz bump     # auto-bump version from commit history + tag + push
```

## Gotchas

1. **Project name**: no spaces or underscores — use hyphens (`my-project` not `my_project`).
2. **Working directory**: run from the *parent* of where the project should land, not inside a git repo.
3. `--private` requires `--github`.
4. **Workspace prompts**: after `-w`, you are prompted to add sub-projects interactively. `common_utils` is always created automatically.
5. **Loguru is global**: never call `logger.remove()` or add sinks inside a library module — only at `main()` entry points.
6. **Single-package app type**: uv generates a `main()` function in `__init__.py`; uv-start preserves it and prepends the version + config import.

## Resources

- [Documentation](https://hocheggerlab.github.io/uv-start/)
- [Source code](https://github.com/hocheggerlab/uv-start)
- [uv docs](https://docs.astral.sh/uv/)
