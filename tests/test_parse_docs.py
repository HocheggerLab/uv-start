import shutil
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

import uv_init.parse_docs
from uv_init.config import UserConfig
from uv_init.exceptions import TemplateError
from uv_init.parse_docs import (
    _copy_template,
    _parse_replacement,
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
    monkeypatch.setattr(uv_init.parse_docs, "TEMPLATE_DIR", template_dir)

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
    with patch("uv_init.parse_docs.load_config", return_value=mock_config):
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


def test_python_version_matrix():
    """Test Python version matrix generation for different Python versions"""
    test_cases = [
        ("3.14", 'python-version: ["3.14"]'),
        ("3.13", 'python-version: ["3.13"]'),
        ("3.12", 'python-version: ["3.12"]'),
        ("3.11", 'python-version: ["3.11"]'),
        ("3.10", 'python-version: ["3.10"]'),
    ]

    mock_config = UserConfig(
        author_name="Test Author", author_email="test@example.com"
    )
    with patch("uv_init.parse_docs.load_config", return_value=mock_config):
        for python_version, expected in test_cases:
            args = Namespace(
                python=python_version, project_name="test-project"
            )
            replacements = _parse_replacement(args, Path("/fake/path"))

            actual_matrix = replacements['python-version: ["3.12"]']
            assert actual_matrix == expected, (
                f"For Python {python_version}, expected {expected} "
                f"but got {actual_matrix}"
            )
