"""User configuration management for uv-init.

Provides a fallback chain for author info: config file -> git config -> defaults.
Config is stored at ~/.config/uv-init/config.toml.
"""

import os
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from rich import print as rprint
from rich.panel import Panel

CONFIG_DIR = Path.home() / ".config" / "uv-init"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def clean_env() -> dict[str, str]:
    """Return a copy of the current environment with VIRTUAL_ENV removed.

    Prevents uv subprocess warnings when the tool is run inside an activated
    virtualenv that doesn't match the target project's environment.
    """
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    return env


@dataclass
class UserConfig:
    """User configuration for project scaffolding."""

    author_name: str
    author_email: str


def load_config() -> UserConfig:
    """Load user config with fallback chain: config file -> git -> defaults."""
    # 1. Try config file
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("rb") as f:
            data = tomllib.load(f)
        user = data.get("user", {})
        name = user.get("name")
        email = user.get("email")
        if name and email:
            return UserConfig(author_name=name, author_email=email)

    # 2. Try git config
    name = _git_config("user.name")
    email = _git_config("user.email")
    if name and email:
        return UserConfig(author_name=name, author_email=email)

    # 3. Defaults
    return UserConfig(
        author_name=name or "Unknown",
        author_email=email or "unknown@example.com",
    )


def _git_config(key: str) -> str | None:
    """Read a value from git global config."""
    try:
        result = subprocess.run(
            ["git", "config", "--global", key],
            capture_output=True,
            text=True,
            check=False,
        )
        value = result.stdout.strip()
        return value if value else None
    except FileNotFoundError:
        return None


def save_config(name: str, email: str) -> None:
    """Write user config to ~/.config/uv-init/config.toml."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    content = f'[user]\nname = "{name}"\nemail = "{email}"\n'
    CONFIG_FILE.write_text(content)
    rprint(
        Panel(
            f"[green]Configuration saved:[/green]\n"
            f"  Name:  {name}\n"
            f"  Email: {email}\n\n"
            f"  Stored in: {CONFIG_FILE}",
            title="uv-init Config",
            border_style="green",
        )
    )
