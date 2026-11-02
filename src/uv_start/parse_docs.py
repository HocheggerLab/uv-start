"""
Module to copy the README.md, LICENCE, .gitignore and .pre-commit-config.yaml files
to the build directory and add author information.
"""

import shutil
from argparse import Namespace
from pathlib import Path

from rich import print as rprint

from uv_start.config import load_config
from uv_start.exceptions import TemplateError

TEMPLATE_DIR = Path(__file__).resolve().parent / "template"

# Name of the shared utilities package always created in a workspace. It
# is the cycle-free home for the loguru logging setup that the root and
# every member import.
COMMON_UTILS_MODULE = "common_utils"


def parse_docs(args: Namespace, project_dir: Path) -> None:
    """Parse the README.md file and update the content with project information."""
    for template in [
        "README.md",
        "LICENSE",
        ".gitignore",
        ".pre-commit-config.yaml",
    ]:
        _copy_template(template, project_dir)

    # .env handling is opt-in (python-dotenv + .env.example).
    if getattr(args, "dotenv", False):
        _copy_template(".env.example", project_dir)

    # Copy the loguru logging config to src/project_name. The dotenv
    # variant reads LOG_LEVEL/LOG_FILE/ENV from the environment.
    # Workspaces are the exception: their shared logging lives in the
    # common-utils package (see _init_version), so the root must not also
    # configure loguru on import or the two would clobber each other.
    module_name = args.project_name.replace("-", "_")
    src_dir = project_dir / "src" / module_name
    src_dir.mkdir(parents=True, exist_ok=True)
    if not getattr(args, "workspace", False):
        _copy_config(args, src_dir)
    _copy_vscode(project_dir)
    if args.github:
        _add_github_workflows(project_dir)
        _update_content(project_dir, args, ".github/workflows/ci.yml")
        _update_content(project_dir, args, ".github/workflows/release.yml")
    _update_configs(project_dir, args)
    _init_version(args, project_dir)


def parse_docs_data(args: Namespace, project_dir: Path) -> None:
    """Set up template files for a data analysis project.

    Copies .gitignore, a data-project README and a starter
    ``sample.ipynb`` into the project root, plus VS Code settings and
    recommended extensions. With ``--lab`` the notebook uses the hhlab
    matplotlib style and COLOR palette, which are copied alongside a
    CLAUDE.md. No ``src/`` structure is created.
    """
    _copy_template(".gitignore", project_dir)

    if getattr(args, "dotenv", False):
        _copy_template(".env.example", project_dir)

    # Template files stored under other names: data-README.md is the
    # notebook-project README, lab-sample.ipynb the styled notebook, and
    # data-CLAUDE.md avoids clashing with this repo's own CLAUDE.md.
    copies = [("data-README.md", "README.md")]
    if getattr(args, "lab", False):
        # --lab: the Hochegger lab figure style, palette and AI guidance.
        _copy_template("hhlab_style01.mplstyle", project_dir)
        _copy_template("colors.py", project_dir)
        copies += [
            ("lab-sample.ipynb", "sample.ipynb"),
            ("data-CLAUDE.md", "CLAUDE.md"),
        ]
    else:
        copies.append(("sample.ipynb", "sample.ipynb"))
    for source, dest in copies:
        shutil.copy(TEMPLATE_DIR / source, project_dir / dest)
        rprint(f"[green]{dest} copied to project root[/green]")
        _update_content(project_dir, args, dest)
    _copy_vscode(project_dir, launch=False)
    if args.github:
        _add_github_workflows(project_dir)
        _update_content(project_dir, args, ".github/workflows/ci.yml")
        _update_content(project_dir, args, ".github/workflows/release.yml")
    rprint("[green]Data project template files copied successfully.[/green]")


def _copy_vscode(project_dir: Path, *, launch: bool = True) -> None:
    """Copy VS Code settings and recommended extensions into ``.vscode/``.

    Args:
        project_dir: Root of the generated project.
        launch: Also copy ``launch.json`` (debug configuration). Not
            needed for notebook-only data projects.
    """
    vs_code_dir = project_dir / ".vscode"
    vs_code_dir.mkdir(parents=True, exist_ok=True)
    files = ["settings.json", "extensions.json"]
    if launch:
        files.append("launch.json")
    for name in files:
        _copy_template(name, vs_code_dir)


def parse_docs_napari(args: Namespace, project_dir: Path) -> None:
    """Set up template files for a napari plugin project.

    Runs the standard project template setup, then copies napari.yaml and
    a hello-world widget into src/<module>/, and appends the napari
    manifest entry point to pyproject.toml.
    """
    parse_docs(args, project_dir)

    module_name = args.project_name.replace("-", "_")
    src_dir = project_dir / "src" / module_name

    shutil.copy(TEMPLATE_DIR / "napari.yaml", src_dir / "napari.yaml")
    shutil.copy(TEMPLATE_DIR / "_widget.py", src_dir / "_widget.py")
    rprint("[green]napari.yaml and _widget.py copied to package[/green]")

    replacements = {
        "{project_name}": args.project_name,
        "{module_name}": module_name,
    }
    manifest_path = src_dir / "napari.yaml"
    content = manifest_path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        content = content.replace(old, new)
    manifest_path.write_text(content, encoding="utf-8", newline="\n")

    entry_points_template = (
        TEMPLATE_DIR / "napari-entry-points.toml"
    ).read_text(encoding="utf-8")
    for old, new in replacements.items():
        entry_points_template = entry_points_template.replace(old, new)
    with (project_dir / "pyproject.toml").open(
        "a", encoding="utf-8", newline="\n"
    ) as f:
        f.write(f"\n{entry_points_template}\n")
    rprint("[green]napari entry points appended to pyproject.toml[/green]")


def _copy_template(template: str, project_dir: Path) -> None:
    """Copy template files to the build directory"""
    try:
        copy_path = TEMPLATE_DIR / template
        paste_path = project_dir / f"{template}"
        shutil.copy(copy_path, paste_path)
        rprint(f"[green]{template} copied to root project[/green]")
        if template == "README.md" and (project_dir / "packages").exists():
            for package in (project_dir / "packages").iterdir():
                if package.is_dir():
                    shutil.copy(copy_path, package)
            rprint(f"[green]{template} successfully copied[/green]")
    except FileNotFoundError as e:
        raise TemplateError(f"{template} template not found") from e


def _copy_config(args: Namespace, src_dir: Path) -> None:
    """Copy the logging config into ``src/<module>/config.py``.

    Uses ``config_dotenv.py`` (env-driven) when ``--dotenv`` is set,
    otherwise the minimal loguru ``config.py``. Either way the file lands
    as ``config.py`` in the package.
    """
    source = (
        "config_dotenv.py" if getattr(args, "dotenv", False) else "config.py"
    )
    try:
        shutil.copy(TEMPLATE_DIR / source, src_dir / "config.py")
        rprint("[green]config.py copied to package[/green]")
    except FileNotFoundError as e:
        raise TemplateError(f"{source} template not found") from e


def copy_logging_setup(
    package_dir: Path, module_name: str, *, dotenv: bool = False
) -> None:
    """Copy the shared loguru logging setup into a workspace utils package.

    Lands as ``<package_dir>/src/<module_name>/logging_setup.py``. Uses the
    ``logging_setup_dotenv.py`` variant when ``dotenv`` is True, otherwise
    the minimal console-only ``logging_setup.py``.

    Args:
        package_dir: Path to the common-utils package directory.
        module_name: Import name of the package (e.g. ``common_utils``).
        dotenv: When True, use the env-driven (python-dotenv) variant.
    """
    source = "logging_setup_dotenv.py" if dotenv else "logging_setup.py"
    dest = package_dir / "src" / module_name / "logging_setup.py"
    try:
        shutil.copy(TEMPLATE_DIR / source, dest)
        rprint("[green]logging_setup.py copied to common-utils[/green]")
    except FileNotFoundError as e:
        raise TemplateError(f"{source} template not found") from e


def _update_configs(project_dir: Path, args: Namespace) -> None:
    """Update the configuration files with project information."""
    for template in ["README.md", "LICENSE", "pyproject.toml"]:
        _update_content(project_dir, args, template)


def _parse_replacement(args: Namespace, content_path: Path) -> dict[str, str]:
    """Load replacements for the README.md files into dictionary."""
    user_config = load_config()
    AUTHOR_NAME = user_config.author_name
    AUTHOR_EMAIL = user_config.author_email

    parent_dir_name = content_path.parent.name
    module_name = parent_dir_name.replace("-", "_")
    return {
        "# Title": f"# {parent_dir_name}",
        "{project_name}": parent_dir_name,
        "{python_version}": args.python,
        "{author}": AUTHOR_NAME,
        "{email}": AUTHOR_EMAIL,
        "{package_name}": parent_dir_name,
        "{module_name}": module_name,
        "src/{module_name}/__init__.py": f"src/{module_name}/__init__.py",
    }


def _update_content(
    project_dir: Path, args: Namespace, content_type: str
) -> None:
    """Update the content of a file with project information."""
    try:
        # Files that should only exist in root directory
        root_only_files = [
            "LICENSE",
            ".github/workflows/ci.yml",
            ".github/workflows/release.yml",
        ]

        content_path = [project_dir / content_type] + (
            [
                package / content_type
                for package in (project_dir / "packages").iterdir()
                if package.is_dir()
            ]
            if (project_dir / "packages").exists()
            and content_type not in root_only_files
            else []
        )
        for file in content_path:
            replacements = _parse_replacement(args, file)
            with file.open("r", encoding="utf-8") as f:
                content = f.read()
            for old, new in replacements.items():
                content = content.replace(old, new)
            with file.open("w", encoding="utf-8", newline="\n") as f:
                f.write(content)
        rprint(f"[green]{content_type} successfully updated[/green]")
    except FileNotFoundError as e:
        raise TemplateError(f"Failed to update {content_type}: {e}") from e


def _init_version(args: Namespace, project_dir: Path) -> None:
    """Initialize package ``__init__.py`` files with version and wiring.

    Logging follows the loguru rule that configuration happens once at an
    application entry point, never as an import side effect:

    - In a **workspace**, the shared ``common-utils`` package owns the
      logging setup. Application members (created with ``--app``) call
      ``setup_logging_once`` from their ``main()``; library packages
      (``common-utils``, lib/package roots) only emit and never configure.
    - In a **single-package** project, the package configures loguru on
      import via its own ``config.py`` (the simple, self-contained case).
    """
    workspace = getattr(args, "workspace", False)
    root_type = getattr(args, "type", None)
    try:
        package_name = args.project_name.replace("-", "_")

        # Handle root project's __init__.py
        root_init = project_dir / "src" / package_name / "__init__.py"
        if not workspace:
            # Preserve uv's generated entry point (e.g. main()); just add
            # version + the config import that configures loguru on import.
            _write_single_package_init(root_init)
        elif root_type == "app":
            root_init.write_text(
                _app_init_body(package_name), encoding="utf-8", newline="\n"
            )
        else:
            root_init.write_text(
                _library_init_body(), encoding="utf-8", newline="\n"
            )
        rprint("[green]Root __init__.py initialized[/green]")

        # Handle sub-packages (workspace members)
        if (project_dir / "packages").exists():
            for sub_package in (project_dir / "packages").iterdir():
                if sub_package.is_dir():
                    sub_package_name = sub_package.name.replace("-", "_")
                    sub_init = (
                        sub_package / f"src/{sub_package_name}/__init__.py"
                    )
                    # common-utils is a library (it defines the setup); it
                    # must never configure on import. Every other member is
                    # an --app, so it configures in its main().
                    body = (
                        _library_init_body()
                        if sub_package_name == COMMON_UTILS_MODULE
                        else _app_init_body(sub_package_name)
                    )
                    with sub_init.open(
                        "w", encoding="utf-8", newline="\n"
                    ) as f:
                        f.write(body)
                    rprint(
                        f"[green]Version file initialized for {sub_package_name}[/green]"
                    )

    except FileNotFoundError as e:
        raise TemplateError("Version file not found") from e


def _write_single_package_init(root_init: Path) -> None:
    """Add version + config import to uv's generated ``__init__.py``.

    Prepends the version string and the ``config`` import (which
    configures loguru on import) while **preserving** whatever uv
    generated — notably the ``main()`` entry point that
    ``[project.scripts]`` points at, so the console script keeps working.
    """
    header = (
        '__version__ = "0.1.0"\n\n'
        "# Importing config configures loguru's sinks on package import.\n"
        "from . import config  # noqa: F401\n"
    )
    existing = root_init.read_text(encoding="utf-8")
    body = f"{header}\n\n{existing.lstrip()}" if existing.strip() else header
    root_init.write_text(body, encoding="utf-8", newline="\n")


def _library_init_body() -> str:
    """Library package: emit only, never configure logging on import."""
    return '__version__ = "0.1.0"\n'


def _app_init_body(module_name: str) -> str:
    """Application package: configure logging once at the ``main()`` entry.

    The shared ``setup_logging_once`` lives in common-utils and is called
    from ``main()`` (the ``[project.scripts]`` entry point), not on
    import, so libraries imported alongside don't get reconfigured.
    """
    return (
        '__version__ = "0.1.0"\n\n'
        f"from {COMMON_UTILS_MODULE}.logging_setup import setup_logging_once\n"
        "from loguru import logger\n\n\n"
        "def main() -> None:\n"
        '    """Entry point: configure logging once, then run."""\n'
        "    setup_logging_once()\n"
        f'    logger.info("Hello from {module_name}!")\n'
    )


def _add_github_workflows(project_dir: Path) -> None:
    """Add GitHub workflow configurations to the project."""
    try:
        # Create .github/workflows directory
        workflows_dir = project_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        # Copy workflow files
        for workflow in ["ci.yml", "release.yml"]:
            source = TEMPLATE_DIR / ".github" / "workflows" / workflow
            dest = workflows_dir / workflow
            shutil.copy(source, dest)

        rprint(
            "[green]GitHub workflow configurations added successfully[/green]"
        )
    except FileNotFoundError as e:
        raise TemplateError(f"Failed to add GitHub workflows: {e}") from e
