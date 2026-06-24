# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**uv-start** is a Python CLI tool that wraps around the `uv` package manager to create well-configured Python projects with modern development practices. It creates projects with pre-configured development tools, optional GitHub integration, and comprehensive template files.

## Core Architecture

The project follows a modular architecture with clear separation of concerns:

- **Entry Point** (`__main__.py`): Orchestrates the entire project initialization flow
- **Command Routing** (`router.py`): Handles core project creation via `CommandDispatcher` class
- **GitHub Integration** (`setup_git_repo.py`): Manages Git repo initialization and GitHub remote setup using `gh` CLI
- **Dev Dependencies** (`dev_deps.py`): Adds development tools (ruff, pytest, mypy, commitizen, pre-commit) and configurations
- **Template Processing** (`parse_docs.py`): Copies and customizes template files with variable replacement
- **CLI Interface** (`cli.py`): Rich-enhanced argument parsing with custom `RichArgumentParser`

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_cli.py

# Run with verbose output
pytest -v
```

### Code Quality
```bash
# Run linting and formatting
ruff check
ruff format

# Type checking
mypy

# Run pre-commit hooks on all files
pre-commit run --all-files
```

### Version Management
```bash
# Bump version using conventional commits
cz bump

# Create a conventional commit
cz commit
```

### Running the Tool
```bash
# Run from development directory
UV_ORIGINAL_CWD="$PWD" uv run --directory . uv-start project-name [options]

# Install in development mode
uv pip install -e .
```

## Key Environment Variables

The tool requires a `.env` file in the project root with:
- `AUTHOR_NAME`: Author name for project templates
- `AUTHOR_EMAIL`: Author email for project templates

### GitHub Authentication

GitHub integration uses the `gh` CLI's built-in authentication (`gh auth login`).
No token needs to be stored in the `.env` file. If `GH_TOKEN` or `GITHUB_TOKEN`
is set in the shell environment, it will be passed through to `gh` automatically.

## Project Configuration

- **Python Version**: Requires Python 3.13+ (not tested on other versions)
- **Line Length**: 79 characters (configured in ruff)
- **Import Style**: Uses isort via ruff for import sorting
- **Type Checking**: Strict mypy configuration with incremental checking
- **Testing**: pytest with automatic test discovery in `tests/` directory
- **Commit Style**: Conventional commits with commitizen

## Template System

The `template/` directory contains configurable files that are copied to new projects:
- Configuration files for development tools (ruff, mypy, pytest, commitizen)
- VS Code settings and launch configurations
- GitHub Actions workflows
- README, LICENSE, and other project files

Template files support variable replacement for project name, author information, Python version, and other customizations.

## Dependencies and Tools

**Core Dependencies (the tool itself):**
- `rich`: Enhanced terminal output and CLI formatting

**Dependencies added to generated projects** (`dev_deps.py`):
- `loguru`: logging (always added)
- `python-dotenv`: only added with the `--dotenv` flag, for env-driven log config

**Development Dependencies:**
- Standard Python development stack (ruff, mypy, pytest, pre-commit, commitizen)
- `pytest-mock`: Mocking utilities for tests
- `typing-extensions`: Extended typing support

## Common Development Workflows

1. **Adding New Features**: Follow the modular architecture by adding functionality to appropriate modules
2. **Testing**: Write tests for all new functionality using pytest patterns established in `tests/`
3. **Template Updates**: Modify files in `template/` directory to change project scaffolding
4. **CLI Changes**: Update `cli.py` for new command-line options and maintain rich formatting
5. **Version Updates**: Use commitizen for conventional commits and automated version bumping

## Project Review and Improvement Analysis

### **Project Assessment**

This is a **high-quality Python project** with excellent UX and solid architecture. The codebase demonstrates good Python practices with clean modular design, comprehensive testing, and polished CLI interface.

### **Key Strengths** ✅
- **Exceptional CLI Experience**: Rich interface with beautiful panels and colors using the `rich` library
- **Clean Architecture**: Well-modularized with clear separation of concerns across modules
- **Comprehensive Testing**: 23 tests covering core functionality with good mocking patterns
- **Modern Python Practices**: Extensive type hints, dataclasses, proper error handling
- **Template System**: Flexible and extensible project scaffolding with variable replacement
- **Workspace Support**: Sophisticated monorepo capabilities with interactive setup

### **Critical Security Issues** ⚠️
1. **Path Injection** (`router.py:20`): User input used directly in file paths without sanitization

### **Priority Improvements**

#### **High Priority** 🔴
1. **Security Hardening**
   - Implement proper path validation and sanitization

2. **Error Recovery & Robustness**
   - Implement rollback mechanism for failed operations
   - Replace inconsistent `sys.exit()` calls with proper exception handling
   - Add transactional approach to project creation to handle partial failures

3. **Integration Testing**
   - End-to-end workflow testing with temporary projects
   - Template generation and content verification tests
   - Mock GitHub API integration testing

#### **Medium Priority** 🟡
4. **UX Enhancements**
   - Add `--dry-run` flag for preview mode before creation
   - Clearer documentation and help for project type differences
   - Progress indicators for long-running operations
   - Cleanup mechanism for interrupted operations

5. **Code Quality**
   - Extract constants for magic strings and file paths
   - Break down large functions (especially `parse_docs()`)
   - Add comprehensive docstrings for all public interfaces

#### **Future Features** 🔵
6. **Advanced Capabilities**
   - Plugin system for custom project types and templates
   - Configuration file support for user-specific defaults
   - Multiple built-in templates (FastAPI, Django, data science, etc.)
   - Docker integration and containerization setup
   - Enhanced IDE integration beyond VS Code

### **Potential New Features**

1. **Extended Project Templates**
   - FastAPI web service template with async patterns
   - Data science project template with Jupyter, pandas setup
   - CLI tool template with click/typer integration
   - Package/library template variations for different use cases

2. **Enhanced GitHub Integration**
   - Automatic branch protection rules setup
   - Issue and PR template generation
   - Multiple GitHub Actions workflow variants
   - Dependabot and security scanning configuration

3. **Developer Experience**
   - VS Code extension for seamless integration
   - Shell completion scripts for bash/zsh/fish
   - Project health checks and validation
   - Automated dependency update workflows

4. **Enterprise Features**
   - Organization-specific template repositories
   - Compliance and security tooling integration
   - Advanced license management
   - Corporate policy enforcement

### **Architecture Evolution Suggestions**

The current architecture is solid but could benefit from:
- **Plugin System**: Allow third-party extensions and custom templates
- **Configuration Management**: User-specific defaults and preferences
- **Template Registry**: Centralized template discovery and management
- **State Management**: Better handling of partial failures with proper rollback

### **Code Quality Observations**

- **Excellent**: Type annotations, error handling, testing patterns
- **Good**: Modular design, separation of concerns, rich CLI interface
- **Needs Attention**: Long functions, magic constants, security considerations
- **Missing**: Integration tests, comprehensive error recovery, plugin architecture
