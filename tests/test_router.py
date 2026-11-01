import subprocess
from argparse import Namespace
from pathlib import Path
from unittest.mock import ANY, Mock, patch

import pytest

from uv_start.exceptions import ProjectCreationError
from uv_start.router import CommandDispatcher


@pytest.fixture
def temp_cwd(tmp_path):
    """Create a temporary working directory"""
    project_dir = tmp_path / "test-project"
    tests_dir = project_dir / "tests"
    project_dir.mkdir(exist_ok=True)
    tests_dir.mkdir(exist_ok=True)
    return tmp_path


@pytest.fixture(autouse=True)
def mock_cooldown():
    """Skip writing the cooldown; the mocked uv init creates no pyproject."""
    with patch("uv_start.router.ensure_cooldown") as mock_ensure:
        yield mock_ensure


@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls"""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        yield mock_run


@pytest.fixture
def mock_rprint():
    """Mock rich.print"""
    with patch("uv_start.router.rprint") as mock_print:
        yield mock_print


@pytest.fixture
def base_args():
    return Namespace(
        project_name="test-project",
        python="3.12",
        workspace=False,
    )


@pytest.fixture
def mock_fs():
    """Mock all filesystem operations"""
    with (
        patch("pathlib.Path.exists", return_value=True) as mock_exists,
        patch("pathlib.Path.mkdir", return_value=None) as mock_mkdir,
        patch("pathlib.Path.is_dir", return_value=True) as mock_is_dir,
        patch(
            "pathlib.Path.absolute", return_value=Path("/fake/path")
        ) as mock_abs,
    ):
        yield {
            "exists": mock_exists,
            "mkdir": mock_mkdir,
            "is_dir": mock_is_dir,
            "absolute": mock_abs,
        }


@pytest.fixture
def dispatcher(base_args, temp_cwd, mock_fs):
    """Create a CommandDispatcher instance"""
    return CommandDispatcher(base_args, temp_cwd)


def test_lib_project(mock_subprocess, dispatcher, base_args, mock_fs):
    """Test creating a library project"""
    base_args.type = "lib"
    dispatcher.dispatch()

    mock_subprocess.assert_called_once_with(
        ["uv", "init", "test-project", "--lib", "--python", "3.12"],
        check=True,
        cwd=dispatcher.original_cwd,
        env=ANY,
    )


def test_package_project(mock_subprocess, dispatcher, base_args, mock_fs):
    """Test creating a package project"""
    base_args.type = "package"
    dispatcher.dispatch()

    mock_subprocess.assert_called_once_with(
        ["uv", "init", "test-project", "--package", "--python", "3.12"],
        check=True,
        cwd=dispatcher.original_cwd,
        env=ANY,
    )


def test_invalid_project_type(base_args, temp_cwd, mock_fs):
    """Test handling invalid project type"""
    args = base_args
    args.type = "invalid"

    dispatcher = CommandDispatcher(args, temp_cwd)
    with pytest.raises(ValueError, match="Unknown project type: invalid"):
        dispatcher.dispatch()


def test_napari_project(mock_subprocess, base_args, temp_cwd, mock_fs):
    """Test creating a napari plugin project"""
    base_args.type = "lib"
    base_args.napari = True
    base_args.data = False

    with patch("builtins.open", create=True):
        dispatcher = CommandDispatcher(base_args, temp_cwd)
        dispatcher.dispatch()

    calls = mock_subprocess.call_args_list
    assert calls[0].args[0] == [
        "uv",
        "init",
        "test-project",
        "--package",
        "--python",
        "3.12",
    ]
    assert calls[1].args[0] == ["uv", "add", "napari[all]", "magicgui"]


def test_subprocess_error(mock_subprocess, base_args, temp_cwd, mock_fs):
    """Test handling subprocess error"""
    args = base_args
    args.type = "lib"

    error = subprocess.CalledProcessError(1, ["uv", "init"])
    mock_subprocess.side_effect = error

    dispatcher = CommandDispatcher(args, temp_cwd)
    with pytest.raises(ProjectCreationError):
        dispatcher.dispatch()


def test_data_project(mock_subprocess, base_args, tmp_path):
    """A data project is a flat, non-package uv project for notebooks."""
    base_args.type = "lib"
    base_args.napari = False
    base_args.data = True
    (tmp_path / "test-project").mkdir()
    (tmp_path / "test-project" / "main.py").write_text("print('hi')\n")

    dispatcher = CommandDispatcher(base_args, tmp_path)
    dispatcher.dispatch()

    calls = mock_subprocess.call_args_list
    assert calls[0].args[0] == [
        "uv",
        "init",
        "test-project",
        "--app",
        "--no-package",
        "--python",
        "3.12",
    ]
    assert calls[1].args[0] == [
        "uv",
        "add",
        "ipykernel",
        "numpy",
        "pandas",
        "matplotlib",
        "seaborn",
    ]
    project = tmp_path / "test-project"
    assert not (project / "main.py").exists()
    assert (project / "data" / ".gitkeep").exists()
    assert (project / "results" / ".gitkeep").exists()


def test_cooldown_written_before_dependencies(
    mock_subprocess, mock_cooldown, base_args, tmp_path
):
    """The cooldown lands in pyproject.toml before any `uv add` runs."""
    base_args.data = True
    base_args.lab = False
    (tmp_path / "test-project").mkdir()
    calls: list[str] = []
    mock_cooldown.side_effect = lambda *a, **k: calls.append("cooldown")
    mock_subprocess.side_effect = lambda cmd, **k: (
        calls.append(cmd[1]) or Mock(returncode=0)
    )
    CommandDispatcher(args=base_args, original_cwd=tmp_path).dispatch()
    assert calls[:3] == ["init", "cooldown", "add"]
    mock_cooldown.assert_called_once_with(
        tmp_path / "test-project" / "pyproject.toml", None
    )
