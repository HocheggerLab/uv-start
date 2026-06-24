Usage
=====

Basic command
-------------

.. code-block:: bash

   uv-start <project-name> [options]

The project name must not contain spaces or underscores.

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Flag
     - Description
   * - ``-t, --type [lib|package]``
     - Project type to create. **lib** (default) creates a simple library
       with a ``src/`` layout. **package** creates an installable package
       with an entry-point script.
   * - ``-p, --python [3.14|3.13|3.12|3.11|3.10]``
     - Python version for the new project (default: **3.13**).
   * - ``-w, --workspace``
     - Create a `uv workspace <https://docs.astral.sh/uv/concepts/projects/workspaces/>`_
       (monorepo). You will be prompted to add a shared utilities library
       and additional sub-projects.
   * - ``-g, --github``
     - Initialise a Git repository **and** create a GitHub remote.
       Sets up CI/CD workflows automatically.
   * - ``--private``
     - Make the GitHub repository private. Requires ``--github``.
   * - ``--data``
     - Create a data analysis project. Installs Jupyter, pandas, matplotlib,
       and seaborn. No ``src/`` layout — just a flat project with a starter
       notebook, lab matplotlib style, and colour palette.
   * - ``--napari``
     - Create a `napari <https://napari.org/>`_ plugin project. Installs
       ``napari[all]`` and ``magicgui``, scaffolds a hello-world dock widget,
       a ``napari.yaml`` manifest, and the
       ``[project.entry-points."napari.manifest"]`` block in
       ``pyproject.toml``. Uses the standard ``src/`` layout and full
       dev-tool configuration.
   * - ``--dotenv``
     - Add ``.env`` handling for environment-driven logging. Installs
       ``python-dotenv``, ships a ``.env.example``, and uses the
       env-var-aware logging config (``LOG_LEVEL``/``LOG_FILE``/``ENV``).
       Omit it for the default loguru config (console only, no ``.env``).
   * - ``--config NAME EMAIL``
     - Save author name and email for project templates.
       Stored in ``~/.config/uv-start/config.toml``.

Examples
--------

Create a library (default)
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv-start my-lib

Creates a ``my-lib/`` directory with a ``src/my_lib/`` package, test
directory, and all dev-tool configuration.

Create an installable package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv-start my-cli -t package

Same as a library but also registers a console script entry-point so the
package can be run from the command line.

Specify a Python version
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv-start my-project -p 3.12

Target Python 3.12 instead of the default 3.13.

Create a project with a GitHub repo
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv-start my-project -g

Initialises a local Git repo, creates a **public** GitHub remote, pushes
an initial commit, and sets up CI workflows.

.. code-block:: bash

   uv-start my-project -g --private

Same as above but the GitHub repository is **private**.

Create a workspace (monorepo)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv-start my-workspace -w

Sets up a uv workspace. You will be interactively prompted to:

1. Add a ``common-utils`` shared library
2. Add additional sub-projects to the workspace

Combine workspace and GitHub:

.. code-block:: bash

   uv-start my-workspace -w -g

Create a data analysis project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv-start my-analysis --data

Creates a flat project (no ``src/`` layout) pre-configured for interactive
data analysis:

- **Jupyter**, **pandas**, **matplotlib**, and **seaborn** installed in the
  ``.venv``
- Lab matplotlib style (``hhlab_style01.mplstyle``) at the project root
- ``colors.py`` — a ``COLOR`` enum with the lab's standard palette
- ``sample.ipynb`` — starter notebook that applies the style and imports
  ``COLOR``
- ``CLAUDE.md`` — instructions for AI-assisted work that enforce consistent
  figure styling

Combine with ``--github`` to create a GitHub repository at the same time:

.. code-block:: bash

   uv-start my-analysis --data -g

Create a napari plugin project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv-start my-plugin --napari

Creates a standard ``src/my_plugin/`` package pre-wired as a napari plugin:

- **napari[all]** and **magicgui** installed as runtime dependencies
- ``src/my_plugin/napari.yaml`` — plugin manifest with one widget contribution
- ``src/my_plugin/_widget.py`` — hello-world ``magic_factory`` dock widget
- ``[project.entry-points."napari.manifest"]`` block appended to
  ``pyproject.toml`` so the manifest is discovered when the package is
  installed
- Full dev-tool stack (ruff, ty, pytest, commitizen, pre-commit)

After scaffolding, run the widget end-to-end with:

.. code-block:: bash

   cd my-plugin
   uv sync
   uv run napari

Then in napari, open ``Plugins → my-plugin → Hello Widget`` to see the
``Say hello`` button.

Combine with ``--github`` to publish the plugin repository at the same
time:

.. code-block:: bash

   uv-start my-plugin --napari -g

Generated project structure
---------------------------

Standard project
^^^^^^^^^^^^^^^^

.. code-block:: text

   project-name/
   ├── src/
   │   └── project_name/
   │       ├── __init__.py
   │       └── config.py            ← loguru logging setup
   ├── tests/
   ├── pyproject.toml
   ├── README.md
   ├── LICENSE
   ├── .env.example                 ← only with --dotenv
   └── .pre-commit-config.yaml

Workspace
^^^^^^^^^

.. code-block:: text

   workspace-name/
   ├── packages/
   │   ├── package1/
   │   └── package2/
   ├── pyproject.toml
   ├── README.md
   └── .pre-commit-config.yaml

Data analysis project
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

   analysis-name/
   ├── hhlab_style01.mplstyle   ← lab matplotlib style, loaded by the notebook
   ├── colors.py                ← COLOR enum with the lab palette
   ├── sample.ipynb             ← starter notebook
   ├── CLAUDE.md                ← AI instructions for consistent figure style
   ├── pyproject.toml
   ├── README.md
   ├── .env.example             ← only with --dotenv
   └── .gitignore

napari plugin project
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

   plugin-name/
   ├── src/
   │   └── plugin_name/
   │       ├── __init__.py
   │       ├── config.py
   │       ├── napari.yaml      ← plugin manifest
   │       └── _widget.py       ← hello-world magicgui widget
   ├── tests/
   ├── pyproject.toml           ← includes [project.entry-points."napari.manifest"]
   ├── README.md
   ├── LICENSE
   ├── .env.example             ← only with --dotenv
   └── .pre-commit-config.yaml

Development tools configured
-----------------------------

Every generated project comes with:

- **Ruff** — linter and formatter (line length 79, flake8 + isort rules)
- **Ty** — static type checker (checks ``src/`` and ``tests/``)
- **pytest** — test framework with automatic discovery in ``tests/``
- **commitizen** — conventional commits, automatic version bumping, and
  changelog generation (see :ref:`version-bumps` below)
- **pre-commit** — Git hooks that run linting, formatting, and type
  checking before each commit
- **loguru** — logging with a colourised console sink by default and an
  opt-in rotating file sink (env-driven configuration via ``--dotenv``;
  see :ref:`logging-system` below)

.. _data-analysis:

Data analysis project details
------------------------------

Matplotlib style
^^^^^^^^^^^^^^^^

``hhlab_style01.mplstyle`` is placed at the project root so it can be
referenced by name from any notebook in the same directory:

.. code-block:: python

   import matplotlib.pyplot as plt
   plt.style.use('hhlab_style01.mplstyle')

Always apply this style before creating any figure.

Lab colour palette
^^^^^^^^^^^^^^^^^^

``colors.py`` defines the ``COLOR`` enum with the lab's standard palette.
Use the enum values — never raw hex strings or default matplotlib colors:

.. code-block:: python

   from colors import COLOR

   ax.scatter(x, y, color=COLOR.BLUE.value)
   ax.bar(labels, heights, color=COLOR.PINK.value)

Available colours:

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Name
     - Hex
     - Typical use
   * - ``COLOR.BLUE``
     - ``#526C94``
     - Primary data series
   * - ``COLOR.LIGHT_BLUE``
     - ``#75B1CE``
     - Secondary / paired condition
   * - ``COLOR.PINK``
     - ``#DC6B83``
     - Contrast / highlight
   * - ``COLOR.YELLOW``
     - ``#D8C367``
     - Third condition
   * - ``COLOR.TURQUOISE``
     - ``#00bfb2``
     - Fourth condition
   * - ``COLOR.LIGHT_GREEN``
     - ``#CCDBA2``
     - Fifth condition
   * - ``COLOR.LAVENDER``
     - ``#C6B2D1``
     - Sixth condition
   * - ``COLOR.PURPLE``
     - ``#654875``
     - Seventh condition
   * - ``COLOR.OLIVE``
     - ``#889466``
     - Eighth condition
   * - ``COLOR.GREY``
     - ``#D4D3CF``
     - Background / negative control
   * - ``COLOR.DARKGREY``
     - ``#4A4A4A``
     - Text / annotations

To add a new colour, extend the ``COLOR`` enum in ``colors.py`` rather
than scattering raw hex values through notebooks.

Starter notebook
^^^^^^^^^^^^^^^^

``sample.ipynb`` opens with the standard imports already in place:

.. code-block:: python

   import matplotlib.pyplot as plt
   import pandas as pd
   import seaborn as sns
   from colors import COLOR

   plt.style.use('hhlab_style01.mplstyle')

It also includes a commented example scatter plot to illustrate the
expected usage pattern.

CLAUDE.md
^^^^^^^^^

The generated ``CLAUDE.md`` tells Claude Code (and other AI tools) to
always apply the lab style and use the ``COLOR`` enum. This keeps
AI-generated figure code consistent with hand-written code across the
project.

.. _version-bumps:

Conventional commits and version bumps
--------------------------------------

Generated projects use `commitizen <https://commitizen-tools.github.io/commitizen/>`_
to enforce `conventional commits <https://www.conventionalcommits.org/>`_
and automate `semantic versioning <https://semver.org/>`_.

Use ``cz commit`` instead of ``git commit`` to get an interactive prompt
that builds a correctly formatted message:

.. code-block:: bash

   cz commit

To bump the version based on your commit history:

.. code-block:: bash

   cz bump

Commitizen inspects all commits since the last tag and determines the
version bump automatically:

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Commit prefix
     - Version bump
     - Example
   * - ``fix:``
     - **PATCH** (0.0.X)
     - ``fix: handle missing config file``
   * - ``feat:``
     - **MINOR** (0.X.0)
     - ``feat: add --config flag``
   * - ``BREAKING CHANGE:`` in footer, or ``!`` after type
     - **MAJOR** (X.0.0)
     - ``feat!: replace .env with config system``

Other commit types — ``chore:``, ``docs:``, ``refactor:``, ``ci:``,
``test:``, ``style:``, ``perf:``, ``build:`` — are recorded in the
changelog but **do not** trigger a version bump.

.. note::

   While ``major_version_zero`` is enabled in the commitizen
   configuration (the default for generated projects), breaking changes
   bump the **minor** version instead of major, following the
   `SemVer spec for 0.x releases <https://semver.org/#spec-item-4>`_.

Workspace versioning
^^^^^^^^^^^^^^^^^^^^

When a workspace is created with ``-w``, all packages share a **single
synchronized version**. The commitizen configuration lives only in the
root ``pyproject.toml`` and its ``version_files`` list covers every
sub-package:

- ``src/<module>/__init__.py`` — ``__version__`` string
- ``pyproject.toml`` — ``version`` field
- ``README.md`` — version badge

Running ``cz bump`` at the workspace root updates all of these files
across the root project and every sub-package in one step. The release
CI workflow does the same automatically when a conventional commit lands
on ``main``.

GitHub CI/CD workflows
----------------------

When ``--github`` is used, two GitHub Actions workflows are created:

**CI pipeline** — runs on every push and pull request:

- Ruff linting and format checking
- Ty type checking
- pytest test suite

**Release pipeline** — runs on pushes to ``main``:

- Automatic version bumping based on conventional commits
- GitHub release creation with changelog
- For workspaces, bumps the single synchronized version across all packages

.. _logging-system:

Logging system
--------------

Every generated project includes a ready-to-use logging module at
``src/<package_name>/config.py``, built on `loguru
<https://github.com/Delgan/loguru>`_. Importing the package configures
loguru's sinks once (the package ``__init__`` does ``from . import config``),
after which you use the global ``logger`` anywhere.

Getting a logger
^^^^^^^^^^^^^^^^

There is no per-module factory — import loguru's global logger directly:

.. code-block:: python

   from loguru import logger

   logger.debug("Detailed diagnostic info")
   logger.info("General operational messages")
   logger.warning("Something unexpected happened")
   logger.error("Something failed")

The module path, function and line are captured automatically, and
tracebacks are rendered with full diagnostics.

Default configuration
^^^^^^^^^^^^^^^^^^^^^^

Out of the box, ``config.py`` enables a single colourised console sink at
``INFO``:

.. code-block:: python

   import sys
   from loguru import logger

   logger.remove()
   logger.add(sys.stderr, level="INFO", colorize=True)

A rotating file sink is included but commented out. Uncomment it to also
write logs to disk — loguru handles rotation, retention and compression
for you:

.. code-block:: python

   logger.add(
       "logs/app.log",
       level="DEBUG",
       rotation="1 MB",
       retention=5,
       compression="zip",
       backtrace=True,
       diagnose=True,
   )

Environment-driven configuration (``--dotenv``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you scaffold with ``--dotenv``, the project instead gets a
``config.py`` that reads its configuration from environment variables
(optionally loaded from ``.env`` / ``.env.<ENV>`` via `python-dotenv
<https://github.com/theskumar/python-dotenv>`_), plus a ``.env.example``
to copy:

.. code-block:: bash

   uv-start my-project --dotenv
   cp .env.example .env

.. warning::

   The ``.env`` file is gitignored by default. Never commit it —
   it is for local configuration and secrets only.

Recognised variables (all optional):

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Variable
     - Default
     - Description
   * - ``LOG_LEVEL``
     - ``INFO``
     - Minimum level for the console (and file) sink (``DEBUG``,
       ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL``)
   * - ``LOG_FILE``
     - *(unset)*
     - If set, also write a rotating log file to this path
   * - ``ENV``
     - ``development``
     - Active environment; loads ``.env.<ENV>`` overrides if present

Environment-specific configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With ``--dotenv``, create environment-specific files to override defaults:

- ``.env.example`` — template with defaults (checked into version control)
- ``.env`` — your local copy of ``.env.example`` (gitignored, never commit)
- ``.env.production`` — production settings (gitignored)

Example ``.env.production``:

.. code-block:: bash

   LOG_LEVEL=WARNING
   LOG_FILE=/var/log/myapp/app.log

Activate an environment:

.. code-block:: bash

   export ENV=production

The loading strategy is:

1. Load the base ``.env`` file (if present)
2. Load ``.env.<ENV>`` (if present), overriding previous values
3. Fall back to code-level defaults (console at ``INFO``) for anything unset
