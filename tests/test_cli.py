from unittest.mock import patch

import pytest
import rich_click as click
from click.testing import CliRunner

from uv_start.cli import cli, validate_project_name


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
    assert args.python == "3.13"
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
