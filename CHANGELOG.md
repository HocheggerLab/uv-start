## v0.5.1 (2026-03-06)

## v0.5.0 (2026-03-06)

### Fix

- resolve .venv path ambiguity

## v0.4.1 (2026-02-25)

### Fix

- improve config handling

## v0.4.0 (2026-02-25)

### Feat

- switch to ty and add sphinx docs

### Fix

- improve config handling

### Refactor

- simplify env and logging configuration

## v0.3.10 (2025-02-18)

### Fix

- bug fixes in parse_docs.py

## v0.3.9 (2025-02-09)

### Fix

- update python in release.yml, relax bump commit conditions

## v0.3.8 (2024-12-28)

### Fix

- python version adapted dynamically in mypy config

## v0.3.7 (2024-12-26)

### Fix

- python-dotenv added as a project dependency and removed from dev dependencies

## v0.3.6 (2024-12-20)

### Fix

- final setup of logging config with template/.env file committed with tests working
- final setup of logging config with template/.env file committed

## v0.3.5 (2024-12-13)

### Fix

- **parse_docs.py**: fix problem with underscore in __init__.py versioning

## v0.3.4 (2024-12-08)

### Fix

- **__main__.py**: corrected the private functionality for github repos

## v0.3.3 (2024-12-08)

### Fix

- **cli.py**: fix type mismatch in help setup fix mypy pre-commit config

## v0.3.2 (2024-12-08)

### Fix

- **ci.yml**: remove no-coverage

## v0.3.1 (2024-12-08)

### Fix

- **cli.py**: fix print bug for help message add github options remove ap option

## v0.3.0 (2024-12-08)

### Feat

- initial project setup

### Fix

- **router.py**: add dummy test fix github action yml files
- install pytest coverage in ci.yml
- correct uv venv activation in ci.yml
- correct uv action in ci.yml
- correct venv activation in ci.yml
- bump version reverted to original in ci.yml
- bump version in ci.yml
- setup of project ready for first applications
- **parse_docs.py**: update python versions in ci.yml during initialization
- **tests**: update router test suite with proper mocking

## v0.1.0 (2024-12-07)

### Feat

- initial commit

## v0.1.7 (2024-12-07)

## v0.1.6 (2024-12-05)

## v0.1.5 (2024-12-05)

### Fix

- **global**: install pre-commit hooks
- **router.py-cli.py**: make github repo optional with flag refactor main function

## v0.1.4 (2024-12-05)

## v0.1.3 (2024-12-05)

### Feat

- **dev_deps.py-setup_git_repo.py**: add precommit hooks set up remote repo

## v0.1.2 (2024-12-04)

### Feat

- **cki.py-router.py-dev_deps.py-parse_docs.py**: add functionality to initialise project with dev dependencies and commitizen

## v0.1.1 (2024-11-28)

### Feat

- **cli.py-router.py**: add functionality to execute uv commands
