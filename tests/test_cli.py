import re
from unittest.mock import patch

import pytest
import rich_click as click
from click.testing import CliRunner

from uv_start.cli import cli, validate_project_name


def plain_text(output: str) -> str:
    """Flatten rich-click's error panel to one line of plain words.

    On CI (GITHUB_ACTIONS / FORCE_COLOR) rich colours the panel and wraps it to
    80 columns, so a message can be split across box-drawn lines. Strip the
    ANSI codes and box characters and collapse whitespace before matching.
    """
    no_ansi = re.sub(r"\x1b\[[0-9;]*m", "", output)
    no_box = re.sub(r"[─-╿]", " ", no_ansi)
    return " ".join(no_box.split())


def test_validate_project_name_valid():
    assert validate_project_name("validname") == "validname"
    assert validate_project_name("valid-name") == "valid-name"
    assert validate_project_name("valid123") == "valid123"


def test_validate_project_name_with_space():
    with pytest.raises(click.BadParameter) as exc:
        validate_project_name("invalid name")
    assert "cannot contain spaces" in str(exc.value)


def test_validate_project_name_with_underscore():
    with pytest.raises(click.BadParameter) as exc:
        validate_project_name("invalid_name")
    assert "cannot contain spaces or underscores" in str(exc.value)


@patch("uv_start.__main__.initialize_uv_start")
def test_cli_defaults(mock_init):
    """The command dispatches with default type/python/workspace."""
    result = CliRunner().invoke(cli, ["my-project"])
    assert result.exit_code == 0, result.output
    args = mock_init.call_args.args[0]
    assert args.project_name == "my-project"
    assert args.type == "lib"  # default type
    assert args.python == "3.14"
    assert args.workspace is False


@patch("uv_start.__main__.initialize_uv_start")
def test_cli_with_options(mock_init):
    """Options map onto the dispatched Namespace."""
    result = CliRunner().invoke(
        cli,
        ["my-project", "--type", "package", "--python", "3.11", "--workspace"],
    )
    assert result.exit_code == 0, result.output
    args = mock_init.call_args.args[0]
    assert args.project_name == "my-project"
    assert args.type == "package"
    assert args.python == "3.11"
    assert args.workspace is True


@patch("uv_start.__main__.initialize_uv_start")
def test_cli_type_app_supported(mock_init):
    """--type app is accepted (router and templates support it)."""
    result = CliRunner().invoke(cli, ["my-project", "--type", "app"])
    assert result.exit_code == 0, result.output
    assert mock_init.call_args.args[0].type == "app"


def test_cli_invalid_type():
    """An unknown --type is rejected by the Choice."""
    result = CliRunner().invoke(cli, ["validname", "--type", "invalid"])
    assert result.exit_code != 0


@patch("uv_start.config.save_config")
def test_cli_config(mock_save):
    """--config saves author defaults and skips project creation."""
    result = CliRunner().invoke(
        cli, ["--config", "Test Author", "test@example.com"]
    )
    assert result.exit_code == 0, result.output
    mock_save.assert_called_once_with(
        name="Test Author", email="test@example.com"
    )


@patch("uv_start.__main__.initialize_uv_start")
def test_cli_napari_flag(mock_init):
    result = CliRunner().invoke(cli, ["my-plugin", "--napari"])
    assert result.exit_code == 0, result.output
    args = mock_init.call_args.args[0]
    assert args.napari is True
    assert args.data is False


@patch("uv_start.__main__.initialize_uv_start")
def test_cli_dotenv_flag(mock_init):
    result = CliRunner().invoke(cli, ["my-project", "--dotenv"])
    assert result.exit_code == 0, result.output
    assert mock_init.call_args.args[0].dotenv is True


@patch("uv_start.__main__.initialize_uv_start")
def test_cli_dotenv_flag_default_false(mock_init):
    result = CliRunner().invoke(cli, ["my-project"])
    assert result.exit_code == 0, result.output
    assert mock_init.call_args.args[0].dotenv is False


def test_cli_no_project_name_no_config():
    """Missing PROJECT_NAME without --config is a usage error."""
    result = CliRunner().invoke(cli, [])
    assert result.exit_code != 0


@patch("uv_start.__main__.initialize_uv_start")
def test_cli_private_requires_github(mock_init):
    """--private without --github is a usage error."""
    result = CliRunner().invoke(cli, ["my-project", "--private"])
    assert result.exit_code != 0
    mock_init.assert_not_called()


@patch("uv_start.__main__.initialize_uv_start")
def test_cli_lab_flag(mock_init):
    """--lab is passed through for data projects, and off by default."""
    result = CliRunner().invoke(cli, ["my-analysis", "--data", "--lab"])
    assert result.exit_code == 0, result.output
    assert mock_init.call_args.args[0].lab is True
    result = CliRunner().invoke(cli, ["my-analysis", "--data"])
    assert mock_init.call_args.args[0].lab is False


@patch("uv_start.__main__.initialize_uv_start")
def test_cli_lab_requires_data(mock_init):
    """--lab without --data is a usage error."""
    result = CliRunner().invoke(cli, ["my-project", "--lab"])
    assert result.exit_code != 0
    assert "--lab can only be used with --data" in plain_text(result.output)
    mock_init.assert_not_called()


@patch("uv_start.upgrade.safe_upgrade", return_value=0)
def test_cli_upgrade(mock_upgrade, tmp_path, monkeypatch):
    monkeypatch.setenv("UV_ORIGINAL_CWD", str(tmp_path))
    result = CliRunner().invoke(cli, ["--upgrade", "--cooldown", "14"])
    assert result.exit_code == 0
    mock_upgrade.assert_called_once_with(
        tmp_path, cooldown_days=14, dry_run=False
    )


@patch("uv_start.upgrade.safe_upgrade", return_value=1)
def test_cli_upgrade_exit_code_on_vulnerabilities(mock_upgrade):
    result = CliRunner().invoke(cli, ["--upgrade", "--dry-run"])
    assert result.exit_code == 1
    assert mock_upgrade.call_args.kwargs["dry_run"] is True


def test_cli_cooldown_requires_upgrade():
    result = CliRunner().invoke(cli, ["proj", "--cooldown", "3"])
    assert result.exit_code != 0
    assert "--upgrade" in result.output


def test_cli_python_310_rejected():
    result = CliRunner().invoke(cli, ["proj", "-p", "3.10"])
    assert result.exit_code != 0
