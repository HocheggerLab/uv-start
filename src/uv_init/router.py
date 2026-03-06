import subprocess
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path

from rich import print as rprint
from rich.prompt import Prompt

from uv_init.config import clean_env
from uv_init.exceptions import ProjectCreationError


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
        flags = self._get_project_flags()
        self._create_project(flags, workspace=self.args.workspace)

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
            # Create tests directory
            tests_dir = self.project_path / "tests"
            tests_dir.mkdir(exist_ok=True)
            # Create an empty __init__.py in tests directory
            (tests_dir / "test_init.py").touch()
            with open(tests_dir / "test_init.py", "w") as f:
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
        """Initialize workspace configuration after project creation"""
        packages_path = self.project_path / "packages"
        packages_path.mkdir(exist_ok=True)
        rprint("[green]Initializing workspace...[/green]")
        common_utils = Prompt.ask(
            "Do you want to add common utilities?",
            choices=["y", "n"],
            default="n",
        )

        if common_utils == "y":
            utils_name = Prompt.ask("Enter the name of the utils library: ")
            self._add_common_utils(utils_name)
        other_projects = Prompt.ask(
            "Do you want to add other projects?",
            choices=["y", "n"],
            default="n",
        )
        if other_projects == "y":
            project_name = Prompt.ask("Enter the project-name: ")
            self._add_other_projects(project_name)

    def _add_common_utils(self, utils_name: str) -> None:
        """Add common utilities to the workspace"""
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
            rprint("[green]✓[/green] Successfully added common_utils'")
        except subprocess.CalledProcessError as e:
            raise ProjectCreationError(
                f"Failed to create common_utils: {e}"
            ) from e

    def _add_other_projects(self, project_name: str) -> None:
        """Add other projects to the workspace"""
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
