"""Initialize a new Python project with uv.

Raises:
    argparse.ArgumentTypeError: If the project name contains spaces or under-scores

Returns:
    argparse.Namespace: The parsed arguments
"""

import argparse
import sys
from typing import IO, NoReturn

from rich import print as rprint
from rich.panel import Panel
from rich.text import Text


class RichArgumentParser(argparse.ArgumentParser):
    def format_help(self) -> str:
        help_text = Text()

        # Program description
        help_text.append("\nDescription:\n", style="bold cyan")
        help_text.append(f"  {self.description}\n\n")

        # Usage
        help_text.append("Usage:\n", style="bold cyan")
        help_text.append(f"  {self.usage}\n\n")

        # Arguments
        help_text.append("Arguments:\n", style="bold cyan")
        help_text.append("  project_name ", style="bold yellow")
        help_text.append(
            "The name of the project (no spaces or under-scores allowed)\n"
        )

        # Options
        help_text.append("\nOptions:\n", style="bold cyan")
        help_text.append("  -t, --type ", style="bold yellow")
        help_text.append("[lib|package|app] ", style="italic green")
        help_text.append("The type of project to create (default: lib)\n")

        help_text.append("  -p, --python ", style="bold yellow")
        help_text.append("[3.14|3.13|3.12|3.11|3.10] ", style="italic green")
        help_text.append("The python version to use (default: 3.12)\n")

        help_text.append("  -w, --workspace ", style="bold yellow")
        help_text.append("Create a workspace\n")

        help_text.append("  -g, --github ", style="bold yellow")
        help_text.append("Create and initialize a GitHub repository\n")

        help_text.append("  --private ", style="bold yellow")
        help_text.append(
            "Create a private GitHub repository (requires --github)\n"
        )

        help_text.append("\n  --config NAME EMAIL ", style="bold yellow")
        help_text.append(
            "Configure author name and email for project templates\n"
        )

        # Epilog
        help_text.append(f"\n{self.epilog}\n", style="bold blue")

        return str(help_text)

    def print_help(self, file: IO[str] | None = None) -> None:  # type: ignore[override]
        help_text = self.format_help()
        rprint(
            Panel(help_text, title="UV Init Help", border_style="cyan"),
            file=file,
        )

    def error(self, message: str) -> NoReturn:
        error_message = Text()
        error_message.append("Error: ", style="bold red")
        error_message.append(f"{message}\n\n")
        error_message.append("Usage: ", style="bold")
        error_message.append(self.usage or "No usage information available.")

        panel = Panel(
            error_message, title="Command Line Error", border_style="red"
        )
        rprint(panel)
        sys.exit(2)


def parse_args() -> argparse.Namespace:
    parser = RichArgumentParser(
        description="Initialize a new Python project with uv",
        usage=(
            "uv-init project_name "
            "[-t lib|package|app] "
            "[-p 3.14|3.13|3.12|3.11|3.10] "
            "[-w] [-g] [--private]\n"
            "       uv-init --config NAME EMAIL"
        ),
        epilog="Thanks for using uv_init!",
    )

    parser.add_argument(
        "project_name",
        nargs="?",
        help="The name of the project (no spaces or under-scores allowed)",
        type=validate_project_name,
    )

    parser.add_argument(
        "--config",
        nargs=2,
        metavar=("NAME", "EMAIL"),
        help="Configure author name and email for project templates",
    )

    parser.add_argument(
        "-t",
        "--type",
        help="The type of project to create (lib, package, or app)",
        default="lib",
        choices=["lib", "package"],
    )

    parser.add_argument(
        "-p",
        "--python",
        help="The python version to use",
        default="3.13",
        choices=["3.14", "3.13", "3.12", "3.11", "3.10"],
    )

    parser.add_argument(
        "-w",
        "--workspace",
        help="Create a workspace",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-g",
        "--github",
        help="Create a GitHub repository",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--private",
        help="Create a private GitHub repository (requires --github)",
        action="store_true",
        default=False,
    )

    args = parser.parse_args()

    # --config mode: no project_name needed
    if args.config:
        return args

    # Normal mode: project_name is required
    if args.project_name is None:
        parser.error("project_name is required (or use --config NAME EMAIL)")

    # Validate that --private is only used with --github
    if args.private and not args.github:
        parser.error("--private can only be used with --github")

    return args


def validate_project_name(name: str) -> str:
    if " " in name or "_" in name:
        raise argparse.ArgumentTypeError(
            "Project name cannot contain spaces or under-scores"
        )
    return name
