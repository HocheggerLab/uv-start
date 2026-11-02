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

from uv_start import __version__  # noqa: E402

PROJECT_TYPES = ["lib", "package", "app"]
# Python minors that still receive security fixes (3.10 reached end of
# life in October 2026).
PYTHON_VERSIONS = ["3.14", "3.13", "3.12", "3.11"]


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
@click.version_option(__version__, "-V", "--version", prog_name="uv-start")
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
    default="3.14",
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
    help="Create a flat data-analysis project for Jupyter notebooks (numpy, pandas, matplotlib, seaborn).",
)
@click.option(
    "--lab",
    is_flag=True,
    help="With --data: add the Hochegger lab figure style, COLOR palette and CLAUDE.md.",
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
@click.option(
    "--upgrade",
    is_flag=True,
    help="Safely upgrade the project in the current folder: update uv and "
    "Python, lock releases past the cooldown, audit for vulnerabilities.",
)
@click.option(
    "--cooldown",
    type=click.IntRange(min=0),
    default=None,
    metavar="DAYS",
    help="With --upgrade: minimum release age in days "
    "(default: the project's setting, else 7).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="With --upgrade: show what would change, then restore the files.",
)
def cli(
    project_name: str | None,
    project_type: str,
    python: str,
    workspace: bool,
    github: bool,
    private: bool,
    data: bool,
    lab: bool,
    napari: bool,
    dotenv: bool,
    config: tuple[str, str] | None,
    upgrade: bool,
    cooldown: int | None,
    dry_run: bool,
) -> None:
    """Initialize a new Python project with uv.

    Creates a uv-managed project with a src layout, dev tooling (ruff, ty,
    pytest, pre-commit, commitizen) and loguru logging. Pass PROJECT_NAME to
    create a project, use --config to set the author defaults used in
    project templates, or --upgrade to safely upgrade an existing project.
    """
    # Author-config mode: store defaults and exit without creating a project.
    if config:
        from uv_start.config import save_config

        save_config(name=config[0], email=config[1])
        return

    if (cooldown is not None or dry_run) and not upgrade:
        raise click.UsageError(
            "--cooldown and --dry-run can only be used with --upgrade."
        )
    if upgrade:
        _run_upgrade(cooldown, dry_run)
        return

    if project_name is None:
        raise click.UsageError(
            "PROJECT_NAME is required (or use --config NAME EMAIL, "
            "or --upgrade)."
        )
    if private and not github:
        raise click.UsageError("--private can only be used with --github.")
    if lab and not data:
        raise click.UsageError("--lab can only be used with --data.")

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
        lab=lab,
        napari=napari,
        dotenv=dotenv,
        config=None,
    )
    initialize_uv_start(args)


def _run_upgrade(cooldown: int | None, dry_run: bool) -> None:
    """Run the safe upgrade in the current folder and exit with its code."""
    import os
    from pathlib import Path

    from uv_start.exceptions import UpgradeError
    from uv_start.upgrade import safe_upgrade

    project_dir = Path(os.environ.get("UV_ORIGINAL_CWD", os.getcwd()))
    try:
        code = safe_upgrade(
            project_dir, cooldown_days=cooldown, dry_run=dry_run
        )
    except UpgradeError as e:
        raise click.ClickException(str(e)) from e
    raise SystemExit(code)


# Plain-click alias for great-docs CLI introspection.
# rich_click's RichHelpFormatter requires a `config` kwarg that great-docs
# doesn't pass, causing AttributeError. This subclass uses the unpatched
# formatter so great-docs can document the CLI without triggering that error.
class _DocsCommand(_PlainCommand):  # type: ignore[valid-type,misc]
    formatter_class = _OriginalHelpFormatter


_docs_cli = _DocsCommand(
    name=cli.name,
    callback=cli.callback,
    params=list(cli.params),
    help=cli.help,
)
