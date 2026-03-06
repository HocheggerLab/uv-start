uv-init
=======

**uv-init** is a command-line tool that wraps the
`uv <https://docs.astral.sh/uv/>`_ package manager to scaffold
well-configured Python projects in seconds.

The problem
-----------

Every new Python project needs the same boilerplate: a ``pyproject.toml``
with linter/formatter settings, a test directory, pre-commit hooks,
CI workflows, conventional-commit tooling, and so on.
Setting all of this up by hand is tedious and error-prone.

**uv-init** automates the entire process. Run one command and get a
production-ready project layout with modern development tools
pre-configured and ready to go.

Key features
------------

- **Project types** — create libraries (``lib``) or installable packages
  (``package``)
- **Development tools** — Ruff, Ty, pytest, commitizen, and pre-commit
  are configured out of the box
- **GitHub integration** — initialise a Git repo, create a GitHub remote,
  and set up CI/CD workflows with a single flag
- **Workspace support** — scaffold monorepo workspaces with shared
  utilities and multiple sub-projects
- **Python version selection** — target Python 3.10 through 3.14

Quick start
-----------

.. code-block:: bash

   # Clone and install
   git clone https://github.com/Helfrid/uv-init.git
   cd uv-init && uv sync

   # Create a new library project
   UV_ORIGINAL_CWD="$PWD" uv run --directory /path/to/uv-init uv-init my-project

See :doc:`installation` for full setup instructions and :doc:`usage` for
all available options and examples.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   usage
   api
   contributing
   ty-migration-notes
