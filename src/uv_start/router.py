import subprocess
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path

from rich import print as rprint
from rich.prompt import Prompt

from uv_start.config import clean_env
from uv_start.exceptions import ProjectCreationError
from uv_start.parse_docs import COMMON_UTILS_MODULE, copy_logging_setup
from uv_start.upgrade import ensure_cooldown

# Runtime packages for --data projects. ipykernel runs notebooks on the
# project's .venv; the full jupyter stack is not needed for VS Code.
DATA_PACKAGES = ["ipykernel", "numpy", "pandas", "matplotlib", "seaborn"]


@dataclass
class CommandDispatcher:
    """Dispatch commands based on argument pattern"""

    args: Namespace
    original_cwd: Path

    def __post_init__(self) -> None:
        self.project_path = self.original_cwd / self.args.project_name

    def check_dir_exists(self) -> None:
        if self.project_path.exists():
            raise ProjectCreationError(
                f"Cannot create project '{self.args.project_name}'\n"
                f"Directory already exists at: {self.original_cwd}\n\n"
                "Try using a different project name or remove the existing directory."
            )

    def dispatch(self) -> None:
        """Route to appropriate command handler based on argument pattern"""
        if getattr(self.args, "napari", False):
            self._create_napari_project()
            return
        if getattr(self.args, "data", False):
            self._create_data_project()
            return
        flags = self._get_project_flags()
        self._create_project(flags, workspace=self.args.workspace)

    def _add_cooldown(self) -> None:
        """Hold back releases younger than the cooldown (default 7 days).

        Written before any ``uv add`` so the first install already skips
        brand-new (unvetted) releases; see :mod:`uv_start.upgrade`.
        """
        ensure_cooldown(self.project_path / "pyproject.toml", None)

    def _get_project_flags(self) -> list[str]:
        """Convert project type to uv flags"""
        match self.args.type:
            case "lib":
                return ["--lib"]
            case "app":
                return ["--app", "--package"]
            case "package":
                return ["--package"]
            case _:
                raise ValueError(f"Unknown project type: {self.args.type}")

    def _create_project(
        self, flags: list[str], workspace: bool = False
    ) -> None:
        """Create a new project with specified flags"""
        project_type = " ".join(flag.strip("-") for flag in flags)
        rprint(
            f"[green]Creating {project_type} project at {self.original_cwd}...[/green]"
        )
        try:
            subprocess.run(
                [
                    "uv",
                    "init",
                    self.args.project_name,
                    *flags,
                    "--python",
                    self.args.python,
                ],
                check=True,
                cwd=self.original_cwd,
                env=clean_env(),
            )
            self._add_cooldown()
            # Create tests directory
            tests_dir = self.project_path / "tests"
            tests_dir.mkdir(exist_ok=True)
            # Create an empty __init__.py in tests directory
            (tests_dir / "test_init.py").touch()
            with open(
                tests_dir / "test_init.py", "w", encoding="utf-8", newline="\n"
            ) as f:
                f.write("def test_init():\n    assert True\n")

            rprint(
                f"[green]✓[/green] Successfully created {project_type} project '[bold]{self.args.project_name}[/bold]'"
            )

            if workspace:
                self._initialize_workspace()

        except subprocess.CalledProcessError as e:
            raise ProjectCreationError(
                f"Failed to create {project_type} project: {e}"
            ) from e

    def _initialize_workspace(self) -> None:
        """Initialize workspace configuration after project creation.

        A ``common-utils`` library is always created: it is the only
        cycle-free home for the shared loguru logging setup that the root
        and every member import (the root depends on its members, so the
        shared code must sit at the bottom of the dependency graph).
        """
        packages_path = self.project_path / "packages"
        packages_path.mkdir(exist_ok=True)
        rprint("[green]Initializing workspace...[/green]")

        # common-utils is mandatory — it hosts the shared logging setup.
        self._add_common_utils(COMMON_UTILS_MODULE)

        other_projects = Prompt.ask(
            "Do you want to add other projects?",
            choices=["y", "n"],
            default="n",
        )
        if other_projects == "y":
            project_name = Prompt.ask("Enter the project-name: ")
            self._add_other_projects(project_name)

    def _add_common_utils(self, utils_name: str) -> None:
        """Create the shared common-utils library with logging setup.

        Adds loguru (and python-dotenv when ``--dotenv`` is set) to the
        package, drops in ``logging_setup.py``, and registers it as an
        editable workspace dependency of the root project.
        """
        package_dir = self.project_path / "packages" / utils_name
        dotenv = getattr(self.args, "dotenv", False)
        try:
            subprocess.run(
                [
                    "uv",
                    "init",
                    utils_name,
                    "--lib",
                ],
                check=True,
                cwd=self.project_path / "packages",
                env=clean_env(),
            )
            # Logging dependencies for the shared setup module.
            deps = ["loguru"] + (["python-dotenv"] if dotenv else [])
            subprocess.run(
                ["uv", "add", *deps],
                check=True,
                cwd=package_dir,
                env=clean_env(),
            )
            copy_logging_setup(package_dir, utils_name, dotenv=dotenv)
            subprocess.run(
                [
                    "uv",
                    "add",
                    f"./packages/{utils_name}",
                    "--editable",
                ],
                check=True,
                cwd=self.project_path,
                env=clean_env(),
            )
            rprint("[green]✓[/green] Successfully added common-utils")
        except subprocess.CalledProcessError as e:
            raise ProjectCreationError(
                f"Failed to create common-utils: {e}"
            ) from e

    def _create_napari_project(self) -> None:
        """Create a napari plugin project with a hello-world widget."""
        rprint(
            f"[green]Creating napari plugin project at {self.original_cwd}...[/green]"
        )
        try:
            subprocess.run(
                [
                    "uv",
                    "init",
                    self.args.project_name,
                    "--package",
                    "--python",
                    self.args.python,
                ],
                check=True,
                cwd=self.original_cwd,
                env=clean_env(),
            )
            self._add_cooldown()
            subprocess.run(
                [
                    "uv",
                    "add",
                    "napari[all]",
                    "magicgui",
                ],
                check=True,
                cwd=self.project_path,
                env=clean_env(),
            )
            tests_dir = self.project_path / "tests"
            tests_dir.mkdir(exist_ok=True)
            with open(
                tests_dir / "test_init.py", "w", encoding="utf-8", newline="\n"
            ) as f:
                f.write("def test_init():\n    assert True\n")
            rprint(
                f"[green]✓[/green] Successfully created napari plugin project '[bold]{self.args.project_name}[/bold]'"
            )
        except subprocess.CalledProcessError as e:
            raise ProjectCreationError(
                f"Failed to create napari plugin project: {e}"
            ) from e

    def _create_data_project(self) -> None:
        """Create a flat data-analysis project for Jupyter notebooks.

        The project is not a package (``--no-package``): there is no
        ``src/`` layout or entry point, just an environment for notebooks.
        ``ipykernel`` is what lets VS Code (or any Jupyter front end) run
        notebooks on the project's ``.venv``. ``data/`` holds raw inputs,
        ``results/`` what the notebooks write.
        """
        rprint(
            f"[green]Creating data analysis project at {self.original_cwd}...[/green]"
        )
        try:
            subprocess.run(
                [
                    "uv",
                    "init",
                    self.args.project_name,
                    "--app",
                    "--no-package",
                    "--python",
                    self.args.python,
                ],
                check=True,
                cwd=self.original_cwd,
                env=clean_env(),
            )
            self._add_cooldown()
            subprocess.run(
                ["uv", "add", *DATA_PACKAGES],
                check=True,
                cwd=self.project_path,
                env=clean_env(),
            )
            # uv's hello-world main.py has no place in a notebook project.
            (self.project_path / "main.py").unlink(missing_ok=True)
            for folder in ["data", "results"]:
                (self.project_path / folder).mkdir(exist_ok=True)
                (self.project_path / folder / ".gitkeep").touch()
            rprint(
                f"[green]✓[/green] Successfully created data project '[bold]{self.args.project_name}[/bold]'"
            )
        except subprocess.CalledProcessError as e:
            raise ProjectCreationError(
                f"Failed to create data project: {e}"
            ) from e

    def _add_other_projects(self, project_name: str) -> None:
        """Add another project to the workspace.

        The member depends on ``common-utils`` (resolved via the
        workspace) so it can call the shared ``setup_logging`` at its
        entry point, and is itself registered as an editable dependency
        of the root project.
        """
        member_dir = self.project_path / "packages" / project_name
        try:
            subprocess.run(
                [
                    "uv",
                    "init",
                    project_name,
                    "--package",
                    "--app",
                ],
                check=True,
                cwd=self.project_path / "packages",
                env=clean_env(),
            )
            # Depend on the shared logging package (workspace source).
            subprocess.run(
                ["uv", "add", COMMON_UTILS_MODULE.replace("_", "-")],
                check=True,
                cwd=member_dir,
                env=clean_env(),
            )
            subprocess.run(
                [
                    "uv",
                    "add",
                    f"./packages/{project_name}",
                    "--editable",
                ],
                check=True,
                cwd=self.project_path,
                env=clean_env(),
            )
            rprint(f"[green]✓[/green] Successfully created {project_name}")
        except subprocess.CalledProcessError as e:
            raise ProjectCreationError(
                f"Failed to create {project_name}: {e}"
            ) from e
