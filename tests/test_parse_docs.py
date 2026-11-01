import shutil
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

import uv_start.parse_docs
from uv_start.config import UserConfig
from uv_start.exceptions import TemplateError
from uv_start.parse_docs import (
    _copy_template,
    _update_content,
)


@pytest.fixture
def temp_project_structure(tmp_path, monkeypatch):
    """Create a temporary project structure with template files.

    Returns:
        tuple: (project_dir, template_dir) paths
    """
    # Create template directory
    template_dir = tmp_path / "template"
    template_dir.mkdir()

    # Create project directory
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create sample template files
    (template_dir / "README.md").write_text("# Sample README")
    (template_dir / "LICENSE").write_text("Sample License")
    (template_dir / ".gitignore").write_text("*.pyc\n__pycache__/")

    # Monkeypatch TEMPLATE_DIR to point at our temp template directory
    monkeypatch.setattr(uv_start.parse_docs, "TEMPLATE_DIR", template_dir)

    yield project_dir, template_dir


def test_copy_template_success(temp_project_structure):
    """Test successful template file copying."""
    project_dir, template_dir = temp_project_structure

    # Test copying each template file
    for template in ["README.md", "LICENSE", ".gitignore"]:
        _copy_template(template, project_dir)
        assert (project_dir / template).exists()
        assert (project_dir / template).read_text() == (
            template_dir / template
        ).read_text()


def test_copy_template_file_not_found(temp_project_structure):
    """Test handling of missing template file."""
    project_dir, _ = temp_project_structure

    with pytest.raises(TemplateError):
        _copy_template("nonexistent.txt", project_dir)


def test_update_content(tmp_path: Path):
    # Setup temporary project directory and files
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create mock template files directly in the temp directory
    template_dir = tmp_path / "template"
    template_dir.mkdir()

    # Create mock README.md with the exact placeholders used in _parse_replacement
    readme_content = """# Title

A project using Python {python_version}

## Author
{author} ({email})
"""
    (template_dir / "README.md").write_text(readme_content)

    # Create mock LICENSE file
    license_content = "Copyright (c) {year} {author}"
    (template_dir / "LICENSE").write_text(license_content)

    # Copy mock templates to project directory
    for template in ["README.md", "LICENSE"]:
        shutil.copy(template_dir / template, project_dir / template)

    # Define args
    args = Namespace(project_name="TestProject", python="3.9")

    # Mock the config to return test author info
    mock_config = UserConfig(
        author_name="Test Author", author_email="test@example.com"
    )
    with patch("uv_start.parse_docs.load_config", return_value=mock_config):
        _update_content(project_dir, args, "README.md")

    # Check README.md content
    readme_path = project_dir / "README.md"
    readme_content = readme_path.read_text()
    print(f"Generated content:\n{readme_content}")  # Debug print

    # Verify replacements
    assert "# project" in readme_content  # parent_dir_name will be "project"
    assert "Python 3.9" in readme_content
    assert "Test Author" in readme_content
    assert "test@example.com" in readme_content


def test_ci_template_uses_chosen_python(tmp_path):
    """CI tests the -p version; release takes it from .python-version."""
    from uv_start.parse_docs import _add_github_workflows

    mock_config = UserConfig(
        author_name="Test Author", author_email="test@example.com"
    )
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    with patch("uv_start.parse_docs.load_config", return_value=mock_config):
        for version in ["3.14", "3.12"]:
            args = Namespace(python=version, project_name="test-project")
            _add_github_workflows(project_dir)
            _update_content(project_dir, args, ".github/workflows/ci.yml")
            _update_content(project_dir, args, ".github/workflows/release.yml")
            ci = (project_dir / ".github/workflows/ci.yml").read_text()
            release = (
                project_dir / ".github/workflows/release.yml"
            ).read_text()
            assert f'python-version: ["{version}"]' in ci
            assert "python-version" not in release
            assert "${{ env." not in release  # no shell injection
            assert "uv sync --locked" in release


@pytest.mark.parametrize("lab", [False, True])
def test_parse_docs_data(tmp_path, lab):
    """A data project gets the notebook template set, and no launch.json.

    The lab style, palette and CLAUDE.md only come with --lab.
    """
    from uv_start.parse_docs import parse_docs_data

    mock_config = UserConfig(
        author_name="Test Author", author_email="test@example.com"
    )
    project_dir = tmp_path / "my-analysis"
    project_dir.mkdir()
    args = Namespace(
        python="3.14",
        project_name="my-analysis",
        github=False,
        dotenv=False,
        lab=lab,
    )
    with patch("uv_start.parse_docs.load_config", return_value=mock_config):
        parse_docs_data(args, project_dir)

    for name in [
        "README.md",
        "sample.ipynb",
        ".gitignore",
        ".vscode/settings.json",
        ".vscode/extensions.json",
    ]:
        assert (project_dir / name).exists(), name
    assert not (project_dir / ".vscode/launch.json").exists()
    for name in ["CLAUDE.md", "colors.py", "hhlab_style01.mplstyle"]:
        assert (project_dir / name).exists() == lab, name
    readme = (project_dir / "README.md").read_text()
    assert readme.startswith("# my-analysis")
    assert "Select Kernel" in readme and "{project_name}" not in readme
    notebook = (project_dir / "sample.ipynb").read_text()
    assert "# my-analysis" in notebook and "sys.executable" in notebook
    assert ("COLOR" in notebook) == lab
    assert ("hhlab_style01" in notebook) == lab
    gitignore = (project_dir / ".gitignore").read_text()
    assert ".vscode/" not in gitignore.replace(".vscode/ are shared", "")
