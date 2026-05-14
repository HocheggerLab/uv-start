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


def parse_docs(args: Namespace, project_dir: Path) -> None:
    """Parse the README.md file and update the content with project information."""
    for template in [
        "README.md",
        "LICENSE",
        ".gitignore",
        ".pre-commit-config.yaml",
        ".env.example",
    ]:
        _copy_template(template, project_dir)

    # Copy config.py to src/project_name
    module_name = args.project_name.replace("-", "_")
    src_dir = project_dir / "src" / module_name
    src_dir.mkdir(parents=True, exist_ok=True)
    _copy_template("config.py", src_dir)
    vs_code_dir = project_dir / ".vscode"
    vs_code_dir.mkdir(parents=True, exist_ok=True)
    _copy_template("settings.json", vs_code_dir)
    _copy_template("launch.json", vs_code_dir)
    if args.github:
        _add_github_workflows(project_dir)
        _update_content(project_dir, args, ".github/workflows/ci.yml")
        _update_content(project_dir, args, ".github/workflows/release.yml")
    _update_configs(project_dir, args)
    _init_version(args, project_dir)


def parse_docs_data(args: Namespace, project_dir: Path) -> None:
    """Set up template files for a data analysis project.

    Copies .gitignore, .env.example, the hhlab matplotlib style, and a
    starter sample.ipynb into the project root. No src/ structure is created.
    """
    for template in [".gitignore", ".env.example", "README.md"]:
        _copy_template(template, project_dir)

    _copy_template("hhlab_style01.mplstyle", project_dir)
    _copy_template("colors.py", project_dir)
    _copy_template("sample.ipynb", project_dir)

    # CLAUDE.md is stored as data-CLAUDE.md in the template dir to avoid
    # conflicting with this project's own CLAUDE.md during development.
    src = TEMPLATE_DIR / "data-CLAUDE.md"
    dest = project_dir / "CLAUDE.md"
    shutil.copy(src, dest)
    rprint("[green]CLAUDE.md copied to project root[/green]")

    _update_content(project_dir, args, "README.md")
    _update_content(project_dir, args, "sample.ipynb")
    _update_content(project_dir, args, "CLAUDE.md")
    vs_code_dir = project_dir / ".vscode"
    vs_code_dir.mkdir(parents=True, exist_ok=True)
    _copy_template("settings.json", vs_code_dir)
    _copy_template("launch.json", vs_code_dir)
    if args.github:
        _add_github_workflows(project_dir)
        _update_content(project_dir, args, ".github/workflows/ci.yml")
        _update_content(project_dir, args, ".github/workflows/release.yml")
    rprint("[green]Data project template files copied successfully.[/green]")


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
    content = manifest_path.read_text()
    for old, new in replacements.items():
        content = content.replace(old, new)
    manifest_path.write_text(content)

    entry_points_template = (
        TEMPLATE_DIR / "napari-entry-points.toml"
    ).read_text()
    for old, new in replacements.items():
        entry_points_template = entry_points_template.replace(old, new)
    with (project_dir / "pyproject.toml").open("a") as f:
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


def _update_configs(project_dir: Path, args: Namespace) -> None:
    """Update the configuration files with project information."""
    for template in ["README.md", "LICENSE", "pyproject.toml"]:
        _update_content(project_dir, args, template)


def _parse_replacement(args: Namespace, content_path: Path) -> dict[str, str]:
    """Load replacements for the README.md files into dictionary."""
    user_config = load_config()
    AUTHOR_NAME = user_config.author_name
    AUTHOR_EMAIL = user_config.author_email

    target_version = args.python

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
        'python-version: ["3.12"]': f'python-version: ["{target_version}"]',
        "python-version: '3.12'": f"python-version: '{target_version}'",
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
            with file.open("r") as f:
                content = f.read()
            for old, new in replacements.items():
                content = content.replace(old, new)
            with file.open("w") as f:
                f.write(content)
        rprint(f"[green]{content_type} successfully updated[/green]")
    except FileNotFoundError as e:
        raise TemplateError(f"Failed to update {content_type}: {e}") from e


def _init_version(args: Namespace, project_dir: Path) -> None:
    """Initialize the version file with imports and version."""
    try:
        package_name = args.project_name.replace("-", "_")

        # Handle root project's __init__.py
        root_init = project_dir / "src" / package_name / "__init__.py"
        with root_init.open("w") as f:
            f.write(
                '__version__ = "0.1.0"\n\n'
                "from .config import set_env_vars\n\n"
                "# Initialize environment variables\n"
                "set_env_vars()\n"
            )
        rprint("[green]Root __init__.py initialized with config setup[/green]")

        # Handle sub-packages (if workspace)
        if (project_dir / "packages").exists():
            for sub_package in (project_dir / "packages").iterdir():
                if sub_package.is_dir():
                    sub_package_name = sub_package.name.replace("-", "_")
                    sub_init = (
                        sub_package / f"src/{sub_package_name}/__init__.py"
                    )
                    with sub_init.open("w") as f:
                        f.write('__version__ = "0.1.0"\n')
                    rprint(
                        f"[green]Version file initialized for {sub_package_name}[/green]"
                    )

    except FileNotFoundError as e:
        raise TemplateError("Version file not found") from e


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
