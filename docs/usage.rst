Usage
=====

Basic command
-------------

.. code-block:: bash

   uv-init <project-name> [options]

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
   * - ``--config NAME EMAIL``
     - Save author name and email for project templates.
       Stored in ``~/.config/uv-init/config.toml``.

Examples
--------

Create a library (default)
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv-init my-lib

Creates a ``my-lib/`` directory with a ``src/my_lib/`` package, test
directory, and all dev-tool configuration.

Create an installable package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv-init my-cli -t package

Same as a library but also registers a console script entry-point so the
package can be run from the command line.

Specify a Python version
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv-init my-project -p 3.12

Target Python 3.12 instead of the default 3.13.

Create a project with a GitHub repo
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv-init my-project -g

Initialises a local Git repo, creates a **public** GitHub remote, pushes
an initial commit, and sets up CI workflows.

.. code-block:: bash

   uv-init my-project -g --private

Same as above but the GitHub repository is **private**.

Create a workspace (monorepo)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv-init my-workspace -w

Sets up a uv workspace. You will be interactively prompted to:

1. Add a ``common-utils`` shared library
2. Add additional sub-projects to the workspace

Combine workspace and GitHub:

.. code-block:: bash

   uv-init my-workspace -w -g

Generated project structure
---------------------------

Standard project
^^^^^^^^^^^^^^^^

.. code-block:: text

   project-name/
   ├── src/
   │   └── project_name/
   │       └── __init__.py
   ├── tests/
   ├── pyproject.toml
   ├── README.md
   ├── LICENSE
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

Logging system
--------------

Every generated project includes a ready-to-use logging module at
``src/<package_name>/config.py``. It provides environment-variable-driven
configuration with sensible defaults, console and rotating file handlers,
and environment-specific overrides.

Getting a logger
^^^^^^^^^^^^^^^^

Import ``get_logger`` from your package's ``config`` module:

.. code-block:: python

   from my_package.config import get_logger

   logger = get_logger(__name__)

   logger.debug("Detailed diagnostic info")
   logger.info("General operational messages")
   logger.warning("Something unexpected happened")
   logger.error("Something failed")

The first call to ``get_logger`` configures the root logger based on
environment variables. Subsequent calls return child loggers that inherit
this configuration.

Environment variables
^^^^^^^^^^^^^^^^^^^^^

Control logging behaviour via the ``.env`` file or shell environment:

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Variable
     - Default
     - Description
   * - ``LOG_LEVEL``
     - ``INFO``
     - Minimum level to capture (``DEBUG``, ``INFO``, ``WARNING``,
       ``ERROR``, ``CRITICAL``)
   * - ``ENABLE_CONSOLE_LOGGING``
     - ``true``
     - Print log messages to the terminal
   * - ``ENABLE_FILE_LOGGING``
     - ``true``
     - Write log messages to a rotating file
   * - ``LOG_FILE_PATH``
     - ``logs/app.log``
     - Path to the log file
   * - ``LOG_MAX_BYTES``
     - ``1048576``
     - Max size per log file before rotation (1 MB)
   * - ``LOG_BACKUP_COUNT``
     - ``5``
     - Number of rotated log files to keep
   * - ``LOG_FORMAT``
     - see below
     - Python `logging format string
       <https://docs.python.org/3/library/logging.html#logrecord-attributes>`_
   * - ``ENV``
     - ``development``
     - Active environment; loads ``.env.<ENV>`` overrides if present

Default log format::

   %(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s

Environment-specific configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create environment-specific ``.env`` files to override defaults:

- ``.env`` — base defaults (checked into version control)
- ``.env.development`` — local development overrides
- ``.env.production`` — production settings

Example ``.env.production``:

.. code-block:: bash

   LOG_LEVEL=WARNING
   ENABLE_CONSOLE_LOGGING=false
   LOG_FILE_PATH=/var/log/myapp/app.log

Activate an environment:

.. code-block:: bash

   export ENV=production

The configuration strategy is:

1. Load hard-coded defaults
2. Load the base ``.env`` file (if present)
3. Load ``.env.<ENV>`` (if present), overriding previous values
