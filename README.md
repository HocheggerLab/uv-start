# uv-start

A command-line tool for initializing Python projects using the new uv project management tool:
https://docs.astral.sh/uv/
This package integrates uv commands with a template for development configs, commitizen versioning, precommit hooks and CI

---

## Status
Version: ![version](https://img.shields.io/badge/version-0.9.1-blue)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Development state of the program

This project is in active development.
Features and APIs may change. Please report issues on GitHub.
Tests currently run on Mac and Linux with Python 3.13 and 3.14.

---

## Versioning
This project uses [Semantic Versioning](https://semver.org/) and [Conventional Commits](https://www.conventionalcommits.org/).

---

## Authors
Helfrid Hochegger

---

## Dependencies
- Requires Python 3.13 or newer
- UV package manager installed (https://github.com/astral-sh/uv)
- GitHub CLI (`gh`) authenticated via `gh auth login`, if using GitHub features

---

## Contact
Created by Helfrid Hochegger
Email: hh65@sussex.ac.uk
GitHub Issues: https://github.com/hocheggerlab/uv-start/issues
---

## License

This project is licensed under the MIT License

---

## Features

- Create Python libraries, packages, or applications
- Workspace support for monorepo setups
- Automatic setup of development tools:
  - Ruff for linting and formatting
  - Ty for type checking
  - Pytest for testing
  - Commitizen for conventional commits
  - Pre-commit hooks
  - loguru logging (opt-in `.env` configuration via `--dotenv`)
- GitHub repository initialization with CI/CD workflows
- Semantic versioning support
- Python 3.11–3.14 support for project initialisation (3.10 is end-of-life)
- Safe upgrades: 7-day release cooldown, vulnerability audit and `uv-start --upgrade`

---

## Installation

Install as a global tool with uv (recommended):

```bash
uv tool install uv-start
```

Or with pip:

```bash
pip install uv-start
```

Configure your author details (run once):
```bash
uv-start --config "Jane Doe" "jane@example.com"
```

If you skip this step, uv-start falls back to your `git config` (`user.name` / `user.email`).

### GitHub authentication

If you plan to use the `--github` flag, authenticate the `gh` CLI first:

```bash
gh auth login
```

Follow the interactive prompts to authenticate via OAuth (browser). This stores credentials securely via the `gh` keychain — no tokens need to be stored in any file.

### Environment configuration

By default, generated projects log to the console via [loguru](https://github.com/Delgan/loguru) with no `.env` file required. Scaffold with `--dotenv` to opt into environment-driven logging — this adds `python-dotenv` and a `.env.example` you can copy to activate:

```bash
uv-start my-project --dotenv
cp .env.example .env
```

The `.env` file is gitignored by default — never commit it. Keep real credentials and environment-specific settings in `.env` only.
---

## Usage

Basic usage to install a repo with pre-configured Ruff, Ty, Commitizen and Pre-Commit Hooks settings, optional setup of github repo and basic CI pipeline including version bumps on conventional commit messages.

To run the program cd to desired parent directory (this should not be a git repo!)
The set the UV_ORIGINAL_CWD to $PWD and then execute uv run.


bash
```
cd "parent-directory"
UV_ORIGINAL_CWD="$PWD"
uv run --directory path_to/uv-start uv-start project-name [options]
```
Alternatively, add this function to your .zshrc or .bashrc config file

bash
```
uv_start() {
  UV_ORIGINAL_CWD="$PWD" uv run --directory path_to/uv-start uv-start "$@"
}
alias uv-start='uv_start'
```
The restart your shell cd to the desried parent directory and type
bash
```
uv-start project-name [options]
```

Options:
- `-t, --type [lib|package]`: The type of project to create (default: lib, alternative: package)
- `-p, --python [3.14|3.13|3.12|3.11]`: Python version to use (default: 3.14)
- `-w, --workspace`: Create a workspace (monorepo setup)
- `-g, --github`: Create and initialize a GitHub repository
- `--private`: Create a private GitHub repository (requires --github)
- `--data`: Create a flat data-analysis project for Jupyter notebooks in VS Code (ipykernel, numpy, pandas, matplotlib, seaborn)
- `--lab`: With `--data`, add the Hochegger lab matplotlib style, `COLOR` palette and a figure-style `CLAUDE.md`
- `--napari`: Create a napari plugin project (hello-world widget scaffold)
- `--dotenv`: Add `.env` handling (python-dotenv) for env-driven log configuration
- `--config NAME EMAIL`: Save author name and email for project templates
- `--upgrade`: Safely upgrade the project in the current folder (see [Safe upgrades](#safe-upgrades)); `--cooldown DAYS` and `--dry-run` refine it

### Examples

Create a basic library:
bash
```
uv-start my-package -t package -p 3.13
```

Create a workspace with GitHub repository:

bash
```
uv-start my-workspace -w -g
```
creates an upstream main branch on github (default public, use --private for private repos)

bash
```
uv-start my-workspace -w -g
```
This will generate a uv workspace (see: https://docs.astral.sh/uv/concepts/projects/workspaces/)
The user will be prompted to add a common-utils library and an additional project.

---

## Safe upgrades

Every generated project holds back releases that are less than **7 days**
old (`[tool.uv] exclude-newer = "7 days"` in `pyproject.toml`). Malicious
uploads to PyPI (such as the trojanised `litellm` 1.107.0 of October 2026,
live for under two hours) are usually caught and removed within hours, so a
week-old release has been vetted by everyone who installed it first.

To upgrade an existing project, run this from its folder:

```bash
uv-start --upgrade              # update uv + Python, upgrade, audit, sync
uv-start --upgrade --dry-run    # show what would change, touch nothing
uv-start --upgrade --cooldown 14
```

`--upgrade` updates uv itself and the project's Python patch release, warns if
the project pins a Python that no longer gets security fixes (3.10 or older),
re-locks every dependency to the newest release outside the cooldown, and runs
`uv audit` against the OSV vulnerability database. A known vulnerability whose
fix is newer than the cooldown is the one exception: that package alone gets a
dated `exclude-newer-package` entry so the fix goes in now, and the entry is
removed again once the cooldown catches up. It exits with status 1 if any
vulnerability remains (for example when no fix exists yet). Generated CI also
runs `uv audit` on every push.

## Project Structure

The generated project follows this structure:

```
project_name/
├── src/
│   └── project_name/
│       └── __init__.py
├── tests/
├── pyproject.toml
├── README.md
├── LICENSE
├── .env.example
└── .pre-commit-config.yaml
```
For workspaces:
```
workspace_name/
├── packages/
│ ├── package1/
│ └── package2/
├── pyproject.toml
├── README.md
└── .pre-commit-config.yaml
```
---

## Development Tools

UV Init sets up the following development tools:

- **Ruff**: Modern Python linter and formatter
- **Ty**: Static type checker
- **Pytest**: Testing framework
- **Commitizen**: Conventional commit tooling
- **Pre-commit**: Git hooks manager
- **loguru**: Logging with a colourised console sink by default and an
  opt-in rotating file sink; env-driven configuration available via `--dotenv`

### Development Tools Configuration

#### Ruff
- Line length: 79 characters
- Selected rules: flake8, pyupgrade, isort, and more
- Automatic fixes enabled

#### Ty
- Checks `src` and `tests`
- Sets rule severity to errors for strict enforcement
- Excludes virtualenv/build/dist/migrations paths

#### Commitizen
- Uses conventional commits
- Automatic version bumping
- Changelog generation
- Synchronized version tracking across all workspace packages

#### Logging (loguru)
- Colourised console sink at `INFO` by default — no configuration required
- Rotating file sink included (commented out) with rotation, retention and compression
- Global `logger` (`from loguru import logger`); module/function/line captured automatically
- `--dotenv` adds env-driven config (`LOG_LEVEL`, `LOG_FILE`, `ENV`) with `.env`/`.env.<ENV>` support

---

## Workspace Features
When creating a workspace (`-w` flag), UV Init:
- Sets up a monorepo structure
- Offers to create a common utilities package
- Supports adding multiple projects
- Configures dependencies between workspace packages
- **Synchronized versioning**: All packages in the workspace share a single version number. Running `cz bump` at the root updates `pyproject.toml`, `__init__.py`, and `README.md` across all sub-packages simultaneously.

---

## GitHub Integration
When using the `-g` flag, UV Init:
1. Initializes a Git repository
2. Creates a GitHub repository
3. Sets up GitHub Actions workflows for:
   - CI (linting, type checking, testing)
   - Automated releases using conventional commits

additional --private flag for optional private repos

### GitHub Workflows

#### CI Pipeline
- Runs on Python 3.13 and 3.14
- Performs:
  - Code linting with Ruff
  - Type checking with Ty
  - Unit tests with Pytest
  - Format checking

#### Release Pipeline
- Automatic version bumping on main branch
- Creates releases based on conventional commits
- Generates changelogs
- For workspaces, a single `cz bump` at the root keeps all packages in sync

---

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes using conventional commits (`cz commit`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Development

### Local environment

```bash
uv sync
```

### Tests

```bash
uv run pytest
```

### Type checking (Ty)

```bash
uv run ty check .
```

### Building the documentation (Sphinx)

```bash
uv run sphinx-build -b html docs docs/_build/html
```

Then open `docs/_build/html/index.html` in your browser.
