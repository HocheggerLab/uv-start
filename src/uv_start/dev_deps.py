import subprocess
from pathlib import Path

from rich import print as rprint

from uv_start.config import clean_env
from uv_start.exceptions import ConfigError, DependencyError

TEMPLATE_DIR = Path(__file__).resolve().parent / "template"


def add_dev_dependencies(
    project_name: str, project_path: Path, *, dotenv: bool = False
) -> None:
    """Add runtime and dev dependencies to the project.

    Args:
        project_name: Name of the project (unused, kept for symmetry).
        project_path: Path to the generated project.
        dotenv: When True, also add ``python-dotenv`` for env-driven
            logging configuration.
    """
    try:
        # loguru is the runtime logging dependency for every project.
        subprocess.run(
            ["uv", "add", "loguru"],
            check=True,
            cwd=project_path,
            env=clean_env(),
        )
        # python-dotenv is only needed for the opt-in .env handling.
        if dotenv:
            subprocess.run(
                ["uv", "add", "python-dotenv"],
                check=True,
                cwd=project_path,
                env=clean_env(),
            )
        subprocess.run(
            [
                "uv",
                "add",
                "--dev",
                "ruff",
                "pytest",
                "ty",
                "commitizen",
                "pre-commit",
            ],
            check=True,
            cwd=project_path,
            env=clean_env(),
        )
        # Install pre-commit hooks
        subprocess.run(
            [
                "uv",
                "run",
                "pre-commit",
                "install",
                "--hook-type",
                "pre-commit",
                "--hook-type",
                "commit-msg",
            ],
            check=True,
            cwd=project_path,
            env=clean_env(),
        )
        rprint(
            "[green]Development dependencies and pre-commit hooks added successfully.[/green]"
        )
    except subprocess.CalledProcessError as e:
        raise DependencyError(
            f"Failed to add development dependencies: {e}"
        ) from e


def parse_dev_configs(project_path: Path) -> None:
    """Parse dev configs from the project directory.

    Shared configs (ruff, ty, pytest) are appended to all pyproject.toml
    files. Commitizen config is only added to the root pyproject.toml
    with version_files covering all sub-packages for synchronized
    versioning.
    """
    config_dir = TEMPLATE_DIR
    shared_config_files = [
        config_dir / "ty-config.toml",
        config_dir / "ruff-config.toml",
        config_dir / "pytest-config.toml",
    ]
    packages = (
        [
            package
            for package in (project_path / "packages").iterdir()
            if package.is_dir()
        ]
        if (project_path / "packages").exists()
        else []
    )
    pyproject_toml_list = [project_path / "pyproject.toml"] + [
        package / "pyproject.toml" for package in packages
    ]

    try:
        # Append shared configs to ALL pyproject.toml files
        for pyproject_toml in pyproject_toml_list:
            with pyproject_toml.open(
                "a", encoding="utf-8", newline="\n"
            ) as pyproject_file:
                for config_file in shared_config_files:
                    if config_file.exists():
                        with config_file.open("r", encoding="utf-8") as cf:
                            pyproject_file.write(f"\n{cf.read()}\n")

        # Append commitizen config ONLY to root pyproject.toml
        cz_config = config_dir / "commitizen-config.toml"
        if cz_config.exists():
            with (
                (project_path / "pyproject.toml").open(
                    "a", encoding="utf-8", newline="\n"
                ) as f,
                cz_config.open("r", encoding="utf-8") as cf,
            ):
                f.write(f"\n{cf.read()}\n")

            # Add sub-package version_files for synchronized versioning
            if packages:
                _add_workspace_version_files(project_path, packages)

        # Appending blocks leaves blank lines at the end, which the
        # end-of-file-fixer hook would rewrite on the first commit.
        for pyproject_toml in pyproject_toml_list:
            text = pyproject_toml.read_text(encoding="utf-8")
            pyproject_toml.write_text(
                text.rstrip() + "\n", encoding="utf-8", newline="\n"
            )

        rprint("[green]Added config files to pyproject[/green]")

    except FileNotFoundError as e:
        raise ConfigError(f"pyproject.toml not found: {e}") from e


def _add_workspace_version_files(
    project_path: Path, packages: list[Path]
) -> None:
    """Add sub-package paths to the root commitizen version_files.

    This ensures a single ``cz bump`` at the root updates version
    strings in all sub-packages.
    """
    root_pyproject = project_path / "pyproject.toml"
    content = root_pyproject.read_text(encoding="utf-8")

    extra_entries = ""
    for package in packages:
        pkg_module = package.name.replace("-", "_")
        rel = f"packages/{package.name}"
        extra_entries += (
            f'    "{rel}/src/{pkg_module}/__init__.py:__version__",\n'
            f'    "{rel}/pyproject.toml:version",\n'
            f'    "{rel}/README.md:version-[0-9]+\\\\.[0-9]+\\\\.[0-9]+",\n'
        )

    # Insert extra entries before the closing ] of version_files
    content = content.replace(
        '    "README.md:version-[0-9]+\\\\.[0-9]+\\\\.[0-9]+"\n]',
        '    "README.md:version-[0-9]+\\\\.[0-9]+\\\\.[0-9]+",\n'
        + extra_entries.rstrip(",\n")
        + "\n]",
    )

    root_pyproject.write_text(content, encoding="utf-8", newline="\n")
