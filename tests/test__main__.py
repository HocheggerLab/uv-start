import os
import shutil
from argparse import Namespace
from unittest.mock import patch

import pytest

from uv_start.__main__ import initialize_uv_start
from uv_start.exceptions import DependencyError, GitSetupError


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary directory for project creation"""
    project_dir = tmp_path / "test-projects"
    project_dir.mkdir()

    # Store the temp directory path in the environment variable
    os.environ["UV_ORIGINAL_CWD"] = str(project_dir)

    yield project_dir

    # Cleanup
    if project_dir.exists():
        try:
            shutil.rmtree(project_dir)
        except Exception as e:  # noqa: BLE001
            print(f"Cleanup failed: {e}")

    # Clean up environment
    if "UV_ORIGINAL_CWD" in os.environ:
        del os.environ["UV_ORIGINAL_CWD"]


def test_basic_lib_project(temp_project_dir):
    """Test creating a basic library project"""
    project_name = "test-lib"
    project_path = temp_project_dir / project_name

    args = Namespace(
        project_name=project_name,
        type="lib",
        python="3.12",
        workspace=False,
        github=False,
    )

    initialize_uv_start(args)

    # Verify basic project structure
    assert (project_path / "src" / "test_lib").exists(), (
        "Source directory not created"
    )
    assert (project_path / "pyproject.toml").exists(), (
        "pyproject.toml not created"
    )
    assert (project_path / "tests").exists(), "Tests directory not created"
    assert (project_path / "README.md").exists(), "README.md not created"
    assert (project_path / ".gitignore").exists(), ".gitignore not created"
    assert (project_path / "LICENSE").exists(), "LICENSE file not created"
    assert (project_path / ".pre-commit-config.yaml").exists(), (
        "Pre-commit config not created"
    )

    # Verify lib-specific content
    pyproject_content = (project_path / "pyproject.toml").read_text()
    assert 'name = "test-lib"' in pyproject_content, (
        "Project name not correctly set in pyproject.toml"
    )
    assert 'python = ">=3.12"' in pyproject_content, (
        "Python version not correctly set in pyproject.toml"
    )

    # Verify dev dependencies configuration
    assert "[tool.ruff]" in pyproject_content, (
        "Ruff configuration missing in pyproject.toml"
    )
    assert "[tool.pytest.ini_options]" in pyproject_content, (
        "Pytest configuration missing in pyproject.toml"
    )
    assert "[tool.ty.environment]" in pyproject_content, (
        "Ty configuration missing in pyproject.toml"
    )
    assert "[tool.commitizen]" in pyproject_content, (
        "Commitizen configuration missing in pyproject.toml"
    )

    # Verify version file
    init_content = (
        project_path / "src" / "test_lib" / "__init__.py"
    ).read_text()
    assert any(
        version in init_content
        for version in ['__version__ = "0.1.0"', "__version__ = '0.1.0'"]
    ), "Version string not found in __init__.py"

    # Verify README content
    readme_content = (project_path / "README.md").read_text()
    assert "Python 3.12" in readme_content, (
        "Python version not found in README"
    )
    assert "test-lib" in readme_content, "Project name not found in README"


def test_basic_app_project(temp_project_dir):
    """Test creating a basic application project"""
    project_name = "test-app"
    project_path = temp_project_dir / project_name

    args = Namespace(
        project_name=project_name,
        type="app",
        python="3.12",
        workspace=False,
        github=False,
    )

    initialize_uv_start(args)

    # Verify app project structure
    assert (project_path / "src" / "test_app").exists(), (
        "Source directory not created"
    )
    assert (project_path / "pyproject.toml").exists(), (
        "pyproject.toml not created"
    )
    assert (project_path / "tests").exists(), "Tests directory not created"
    assert (project_path / "README.md").exists(), "README.md not created"
    assert (project_path / ".gitignore").exists(), ".gitignore not created"
    assert (project_path / "LICENSE").exists(), "LICENSE file not created"
    assert (project_path / ".pre-commit-config.yaml").exists(), (
        "Pre-commit config not created"
    )

    # Verify app-specific content
    pyproject_content = (project_path / "pyproject.toml").read_text()
    assert 'name = "test-app"' in pyproject_content, (
        "Project name not correctly set in pyproject.toml"
    )
    assert 'python = ">=3.12"' in pyproject_content, (
        "Python version not correctly set in pyproject.toml"
    )

    # Verify dev dependencies configuration
    assert "[tool.ruff]" in pyproject_content, (
        "Ruff configuration missing in pyproject.toml"
    )
    assert "[tool.pytest.ini_options]" in pyproject_content, (
        "Pytest configuration missing in pyproject.toml"
    )
    assert "[tool.ty.environment]" in pyproject_content, (
        "Ty configuration missing in pyproject.toml"
    )
    assert "[tool.commitizen]" in pyproject_content, (
        "Commitizen configuration missing in pyproject.toml"
    )

    # Verify version file
    init_content = (
        project_path / "src" / "test_app" / "__init__.py"
    ).read_text()
    assert any(
        version in init_content
        for version in ['__version__ = "0.1.0"', "__version__ = '0.1.0'"]
    ), "Version string not found in __init__.py"

    # uv's generated main() entry point must be preserved (not clobbered),
    # so the [project.scripts] console script keeps working.
    assert "def main" in init_content, (
        "uv's main() entry point was clobbered in __init__.py"
    )
    assert "[project.scripts]" in pyproject_content, (
        "Console script entry missing from pyproject.toml"
    )
    # Single-package projects still configure loguru on import via config.py
    assert "from . import config" in init_content, (
        "config import missing from __init__.py"
    )
    assert (project_path / "src" / "test_app" / "config.py").exists(), (
        "config.py not created for single-package project"
    )


def test_workspace_project(temp_project_dir):
    """Test creating a workspace project"""
    project_name = "test-workspace"
    project_path = temp_project_dir / project_name

    args = Namespace(
        project_name=project_name,
        type="lib",
        python="3.12",
        workspace=True,
        github=False,
    )

    # common-utils is always created; then we add an app member ("worker")
    # to exercise the entry-point logging wiring.
    with patch("rich.prompt.Prompt.ask", side_effect=["y", "worker"]):
        initialize_uv_start(args)

    # Verify workspace structure
    assert (project_path / "packages").exists(), (
        "Packages directory not created"
    )

    # common-utils is always scaffolded with the shared logging setup
    logging_setup = (
        project_path
        / "packages"
        / "common_utils"
        / "src"
        / "common_utils"
        / "logging_setup.py"
    )
    assert logging_setup.exists(), "common-utils logging_setup.py not created"
    setup_src = logging_setup.read_text()
    assert "def setup_logging" in setup_src, (
        "setup_logging not defined in common-utils"
    )
    assert "def setup_logging_once" in setup_src, (
        "setup_logging_once guard not defined in common-utils"
    )

    # common-utils is a library: it must NOT configure logging on import
    common_init = (
        project_path
        / "packages"
        / "common_utils"
        / "src"
        / "common_utils"
        / "__init__.py"
    ).read_text()
    assert "setup_logging" not in common_init, (
        "common-utils must not configure logging on import"
    )

    # The app member configures logging once at its main() entry point
    worker_init = (
        project_path / "packages" / "worker" / "src" / "worker" / "__init__.py"
    ).read_text()
    assert "def main" in worker_init, "App member should keep a main() entry"
    assert "setup_logging_once()" in worker_init, (
        "App member should configure logging in main()"
    )

    # The lib root is a library: no config.py, no logging on import
    assert not (
        project_path / "src" / "test_workspace" / "config.py"
    ).exists(), "Workspace lib root should not have its own config.py"
    assert (project_path / "pyproject.toml").exists(), (
        "pyproject.toml not created"
    )
    assert (project_path / "README.md").exists(), "README.md not created"
    assert (project_path / ".gitignore").exists(), ".gitignore not created"
    assert (project_path / "LICENSE").exists(), "LICENSE file not created"
    assert (project_path / ".pre-commit-config.yaml").exists(), (
        "Pre-commit config not created"
    )

    # Verify workspace-specific content
    pyproject_content = (project_path / "pyproject.toml").read_text()
    assert 'name = "test-workspace"' in pyproject_content, (
        "Project name not correctly set in pyproject.toml"
    )
    assert "[tool.uv.workspace]" in pyproject_content, (
        "Workspace configuration missing in pyproject.toml"
    )
    assert "[tool.uv.sources]" in pyproject_content, (
        "Sources configuration missing in pyproject.toml"
    )

    # Verify dev dependencies configuration
    assert "[tool.ruff]" in pyproject_content, (
        "Ruff configuration missing in pyproject.toml"
    )
    assert "[tool.pytest.ini_options]" in pyproject_content, (
        "Pytest configuration missing in pyproject.toml"
    )
    assert "[tool.ty.environment]" in pyproject_content, (
        "Ty configuration missing in pyproject.toml"
    )
    assert "[tool.commitizen]" in pyproject_content, (
        "Commitizen configuration missing in pyproject.toml"
    )

    # Verify README content
    readme_content = (project_path / "README.md").read_text()
    assert "test-workspace" in readme_content, (
        "Project name not found in README"
    )


def test_project_with_different_python(temp_project_dir):
    """Test creating a project with different Python version"""
    project_name = "test-python"
    project_path = temp_project_dir / project_name

    args = Namespace(
        project_name=project_name,
        type="lib",
        python="3.11",
        workspace=False,
        github=False,
    )

    initialize_uv_start(args)

    # Verify Python version in configs
    pyproject_content = (project_path / "pyproject.toml").read_text()
    assert 'python = ">=3.11"' in pyproject_content


def test_rollback_on_phase1_failure(temp_project_dir):
    """Test that project directory is removed when Phase 1 fails."""
    project_name = "test-rollback"
    project_path = temp_project_dir / project_name

    args = Namespace(
        project_name=project_name,
        type="lib",
        python="3.12",
        workspace=False,
        github=False,
    )

    with patch(
        "uv_start.__main__.add_dev_dependencies",
        side_effect=DependencyError("mock dep failure"),
    ):
        with pytest.raises(SystemExit) as exc_info:
            initialize_uv_start(args)

        assert exc_info.value.code == 1

    # Project directory should have been cleaned up
    assert not project_path.exists(), (
        "Project directory should be removed after rollback"
    )


def test_github_failure_keeps_project(temp_project_dir):
    """Test that GitHub failure warns but keeps the local project."""
    project_name = "test-gh-fail"
    project_path = temp_project_dir / project_name

    args = Namespace(
        project_name=project_name,
        type="lib",
        python="3.12",
        workspace=False,
        github=True,
        private=False,
    )

    with patch(
        "uv_start.__main__.setup_git_repo",
        side_effect=GitSetupError("mock gh failure"),
    ):
        # Should NOT raise — just warn
        initialize_uv_start(args)

    # Project should still exist
    assert project_path.exists(), (
        "Project directory should be kept after GitHub failure"
    )
    assert (project_path / "pyproject.toml").exists(), (
        "pyproject.toml should exist after GitHub failure"
    )
