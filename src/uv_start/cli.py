"""Command-line interface for uv-start, built with (rich-)click.

``rich_click`` is a drop-in superset of ``click``: the command below is an
ordinary ``click.Command`` (so it can be introspected and documented like
any click CLI), but its ``--help`` output is rendered with Rich styling.

The click callback collects options into an :class:`argparse.Namespace` and
hands off to the project-creation flow, keeping the rest of the codebase
(``router``, ``parse_docs``, ...) unchanged.
"""

from argparse import Namespace

import click as _click  # plain click — captured before rich_click patches it

# Capture originals before rich_click monkey-patches click's formatter/context.
# _docs_cli (defined at module end) uses these to stay compatible with
# great-docs' CLI introspector, which breaks on RichHelpFormatter.
_PlainCommand = _click.Command
_OriginalHelpFormatter = _click.HelpFormatter

import rich_click as click  # noqa: E402

PROJECT_TYPES = ["lib", "package", "app"]
PYTHON_VERSIONS = ["3.14", "3.13", "3.12", "3.11", "3.10"]


def validate_project_name(name: str) -> str:
    """Validate a project name.

    Args:
        name: The proposed project name.

    Returns:
        The name unchanged when valid.

    Raises:
        click.BadParameter: If the name contains spaces or underscores.
    """
    if " " in name or "_" in name:
        raise click.BadParameter(
            "Project name cannot contain spaces or underscores."
        )
    return name


def _project_name_callback(
    ctx: click.Context, param: click.Parameter, value: str | None
) -> str | None:
    """Click callback that validates the optional ``PROJECT_NAME`` argument."""
    return validate_project_name(value) if value is not None else None


@click.command()
@click.argument(
    "project_name", required=False, callback=_project_name_callback
)
@click.option(
    "-t",
    "--type",
    "project_type",
    type=click.Choice(PROJECT_TYPES),
    default="lib",
    show_default=True,
    help="The type of project to create.",
)
@click.option(
    "-p",
    "--python",
    type=click.Choice(PYTHON_VERSIONS),
    default="3.13",
    show_default=True,
    help="The Python version to use.",
)
@click.option(
    "-w", "--workspace", is_flag=True, help="Create a uv workspace (monorepo)."
)
@click.option(
    "-g",
    "--github",
    is_flag=True,
    help="Create and initialize a GitHub repository.",
)
@click.option(
    "--private",
    is_flag=True,
    help="Make the GitHub repository private (requires --github).",
)
@click.option(
    "--data",
    is_flag=True,
    help="Create a data-analysis project (jupyter, pandas, matplotlib, seaborn).",
)
@click.option(
    "--napari",
    is_flag=True,
    help="Create a napari plugin project (hello-world widget scaffold).",
)
@click.option(
    "--dotenv",
    is_flag=True,
    help="Add .env handling (python-dotenv) for env-driven log config.",
)
@click.option(
    "--config",
    nargs=2,
    type=str,
    metavar="NAME EMAIL",
    default=None,
    help="Configure author name and email for project templates, then exit.",
)
def cli(
    project_name: str | None,
    project_type: str,
    python: str,
    workspace: bool,
    github: bool,
    private: bool,
    data: bool,
    napari: bool,
    dotenv: bool,
    config: tuple[str, str] | None,
) -> None:
    """Initialize a new Python project with uv.

    Creates a uv-managed project with a src layout, dev tooling (ruff, ty,
    pytest, pre-commit, commitizen) and loguru logging. Pass PROJECT_NAME to
    create a project, or use --config to set the author defaults used in
    project templates.
    """
    # Author-config mode: store defaults and exit without creating a project.
    if config:
        from uv_start.config import save_config

        save_config(name=config[0], email=config[1])
        return

    if project_name is None:
        raise click.UsageError(
            "PROJECT_NAME is required (or use --config NAME EMAIL)."
        )
    if private and not github:
        raise click.UsageError("--private can only be used with --github.")

    # Imported lazily to avoid a circular import (``__main__`` imports this
    # module to expose the entry point).
    from uv_start.__main__ import initialize_uv_start

    args = Namespace(
        project_name=project_name,
        type=project_type,
        python=python,
        workspace=workspace,
        github=github,
        private=private,
        data=data,
        napari=napari,
        dotenv=dotenv,
        config=None,
    )
    initialize_uv_start(args)


# Plain-click alias for great-docs CLI introspection.
# rich_click's RichHelpFormatter requires a `config` kwarg that great-docs
# doesn't pass, causing AttributeError. This subclass uses the unpatched
# formatter so great-docs can document the CLI without triggering that error.
class _DocsCommand(_PlainCommand):  # type: ignore[misc, valid-type]
    formatter_class = _OriginalHelpFormatter


_docs_cli = _DocsCommand(
    name=cli.name,
    callback=cli.callback,
    params=list(cli.params),
    help=cli.help,
)
