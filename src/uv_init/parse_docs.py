"""
Module to copy the README.md, LICENCE, .gitignore and .pre-commit-config.yaml files
to the build directory and add author information.
"""

import shutil
from argparse import Namespace
from pathlib import Path

from rich import print as rprint

from uv_init.config import load_config
from uv_init.exceptions import TemplateError

TEMPLATE_DIR = Path(__file__).resolve().parent / "template"


def parse_docs(args: Namespace, project_dir: Path) -> None:
    """Parse the README.md file and update the content with project information."""
    for template in [
        "README.md",
        "LICENSE",
        ".gitignore",
        ".pre-commit-config.yaml",
        ".env",
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
