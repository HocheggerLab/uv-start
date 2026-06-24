# test_dev_deps.py
import subprocess
from pathlib import Path
from unittest.mock import ANY, call, mock_open, patch

import pytest

from uv_start.dev_deps import add_dev_dependencies, parse_dev_configs
from uv_start.exceptions import ConfigError, DependencyError


def test_add_dev_dependencies_success():
    project_path = Path("/fake/path")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0

        add_dev_dependencies("fake_project", project_path)

        # loguru is always added as the runtime logging dependency
        assert mock_run.call_args_list[0] == call(
            ["uv", "add", "loguru"],
            check=True,
            cwd=project_path,
            env=ANY,
        ), "Failed to install loguru"

        # python-dotenv must NOT be added without the --dotenv flag
        assert (
            call(
                ["uv", "add", "python-dotenv"],
                check=True,
                cwd=project_path,
                env=ANY,
            )
            not in mock_run.call_args_list
        ), "python-dotenv should not be added by default"

        # Check dev dependencies installation
        assert mock_run.call_args_list[1] == call(
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
            env=ANY,
        ), "Failed to install dev dependencies with uv add"

        # Check pre-commit hooks installation
        assert mock_run.call_args_list[2] == call(
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
            env=ANY,
        ), "Failed to install pre-commit hooks"


def test_add_dev_dependencies_with_dotenv():
    """With dotenv=True, python-dotenv is added right after loguru."""
    project_path = Path("/fake/path")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0

        add_dev_dependencies("fake_project", project_path, dotenv=True)

        assert mock_run.call_args_list[0] == call(
            ["uv", "add", "loguru"],
            check=True,
            cwd=project_path,
            env=ANY,
        ), "loguru should be added first"

        assert mock_run.call_args_list[1] == call(
            ["uv", "add", "python-dotenv"],
            check=True,
            cwd=project_path,
            env=ANY,
        ), "python-dotenv should be added when dotenv=True"


def test_add_dev_dependencies_failure():
    project_path = Path("/fake/path")

    with patch(
        "subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd")
    ) as mock_run:
        with pytest.raises(DependencyError):
            add_dev_dependencies("fake_project", project_path)

        mock_run.assert_called_once()


def test_parse_dev_configs_success():
    project_path = Path("/fake/path")

    config_content = "fake config content"

    mock_file = mock_open(read_data=config_content)

    # Create a mock Path object for the packages directory
    mock_package_path = Path("/fake/path/packages/some_package")

    with (
        patch.object(Path, "exists") as mock_exists,
        patch.object(Path, "mkdir") as _,
        patch.object(Path, "iterdir") as mock_iterdir,
    ):
        mock_exists.return_value = True
        # Mock iterdir to return an iterable with a mock package path
        mock_iterdir.return_value = [mock_package_path]

        with patch.object(Path, "open", mock_file):
            parse_dev_configs(project_path)

            # Get the mock calls
            mock_calls = mock_file.mock_calls

            # Verify that files were opened with correct modes
            assert any(
                call.args[0] == "a" for call in mock_calls if call.args
            ), "No file was opened in append mode"
            assert any(
                call.args[0] == "r" for call in mock_calls if call.args
            ), "No file was opened in read mode"

            # Verify write operations
            handle = mock_file()
            handle.write.assert_any_call(f"\n{config_content}\n")


def test_parse_dev_configs_missing_file():
    project_path = Path("/fake/path")

    with (
        patch.object(Path, "exists", return_value=False),
        patch.object(Path, "open") as mock_open,
    ):
        mock_open.side_effect = FileNotFoundError(
            "[Errno 2] No such file or directory: '/fake/path/pyproject.toml'"
        )

        with pytest.raises(ConfigError):
            parse_dev_configs(project_path)


def test_parse_dev_configs_pyproject_missing():
    project_path = Path("/fake/path")

    with patch("builtins.open", mock_open()) as mock_file:
        mock_file.side_effect = FileNotFoundError

        with pytest.raises(ConfigError):
            parse_dev_configs(project_path)
