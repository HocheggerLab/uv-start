# Title

A data analysis project, set up with [uv-start](https://github.com/hocheggerlab/uv-start).

## Getting started

The project has its own **virtual environment** in `.venv/`: a private copy of
Python with exactly the packages listed in `pyproject.toml`. Nothing is
installed system-wide, so this project cannot break any other.

```bash
cd {project_name}
uv sync              # create .venv and install everything in uv.lock
code .               # open the folder in VS Code
```

In VS Code:

1. Install the recommended extensions when asked (Python, Jupyter, Ruff).
2. Open `sample.ipynb`.
3. Click **Select Kernel** (top right) → **Python Environments** → `.venv`.
4. Click **Run All**. The first cell prints which Python is running — it
   should end in `.venv/bin/python`.

## Adding packages

```bash
uv add scipy         # adds it to pyproject.toml, uv.lock and .venv
```

Never `pip install` into this project — use `uv add`, so the next person who
runs `uv sync` gets the same environment.

## Layout

```
{project_name}/
├── sample.ipynb             # starter notebook
├── data/                    # raw data — read from here, never overwrite
├── results/                 # figures and tables your notebooks write
├── pyproject.toml           # the project's packages
└── uv.lock                  # exact versions, so anyone can rebuild .venv
```

Requires Python {python_version} or greater. Created by {author} ({email}).
