"""Custom exceptions for uv-start."""


class UvInitError(Exception):
    """Base exception for uv-start errors."""


class ProjectCreationError(UvInitError):
    """Failed during project scaffolding (uv init, workspace setup)."""


class DependencyError(UvInitError):
    """Failed during dependency installation."""


class ConfigError(UvInitError):
    """Failed during config file generation."""


class TemplateError(UvInitError):
    """Failed during template copying/processing."""


class GitSetupError(UvInitError):
    """Failed during git/GitHub setup."""


class UpgradeError(UvInitError):
    """Failed during a safe dependency upgrade."""
