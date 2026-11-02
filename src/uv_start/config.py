"""User configuration management for uv-start.

Provides a fallback chain for author info: config file -> git config -> defaults.
Config is stored at ~/.config/uv-start/config.toml.
"""

import os
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from rich import print as rprint
from rich.panel import Panel

CONFIG_DIR = Path.home() / ".config" / "uv-start"
CONFIG_FILE = CONFIG_DIR / "config.toml"


_ENV_ALLOWLIST = {
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "SHELL",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TMPDIR",
    "TEMP",
    "TMP",
    "XDG_CACHE_HOME",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    # Proxies and custom CA bundles (university networks).
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    # Windows: without these, git, uv and pre-commit cannot find their own
    # executables, caches or config (pre-commit reports "git failed").
    "USERPROFILE",
    "USERNAME",
    "APPDATA",
    "LOCALAPPDATA",
    "PROGRAMDATA",
    "PROGRAMFILES",
    "PROGRAMFILES(X86)",
    "COMMONPROGRAMFILES",
    "SYSTEMROOT",
    "SYSTEMDRIVE",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "HOMEDRIVE",
    "HOMEPATH",
    "OS",
    "PROCESSOR_ARCHITECTURE",
    "NUMBER_OF_PROCESSORS",
}


def clean_env() -> dict[str, str]:
    """Return a minimal environment safe for uv/git subprocesses.

    Only passes through variables needed for process execution, explicitly
    excluding secrets and tokens that may be exported in the shell session.
    """
    # Windows environment names are case-insensitive ("Path", "SystemRoot").
    return {k: v for k, v in os.environ.items() if k.upper() in _ENV_ALLOWLIST}


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
            encoding="utf-8",
            check=False,
        )
        value = result.stdout.strip()
        return value if value else None
    except FileNotFoundError:
        return None


def save_config(name: str, email: str) -> None:
    """Write user config to ~/.config/uv-start/config.toml."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    content = f'[user]\nname = "{name}"\nemail = "{email}"\n'
    CONFIG_FILE.write_text(content, encoding="utf-8", newline="\n")
    rprint(
        Panel(
            f"[green]Configuration saved:[/green]\n"
            f"  Name:  {name}\n"
            f"  Email: {email}\n\n"
            f"  Stored in: {CONFIG_FILE}",
            title="uv-start Config",
            border_style="green",
        )
    )
