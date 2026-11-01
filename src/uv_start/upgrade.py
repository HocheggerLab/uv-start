"""Safe dependency upgrades for uv projects.

``uv-start --upgrade`` updates a project's dependencies while keeping two
guard rails in place:

1. **Cooldown.** Only releases that have been public for a number of days
   (default 7) are considered. Most malicious uploads to PyPI are spotted
   and removed within hours, so a release that has survived a week has
   been vetted by the wider community. The cooldown lives in
   ``pyproject.toml`` (``[tool.uv] exclude-newer = "7 days"``) so every
   later ``uv add``/``uv lock``/``uv run`` honours it too.
2. **Audit.** After locking, ``uv audit`` checks every locked package
   against the OSV vulnerability database. A known vulnerability whose fix
   is still inside the cooldown is the one case where waiting is worse
   than upgrading: that package alone gets a dated exemption
   (``exclude-newer-package``), which is pruned again once the cooldown
   window has caught up with it.

The uv executable and the project's Python patch release are brought up
to date first.
"""

import json
import subprocess
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import tomlkit
from rich import print as rprint
from rich.table import Table

from uv_start.config import clean_env
from uv_start.exceptions import UpgradeError

DEFAULT_COOLDOWN_DAYS = 7
# Oldest Python minor that still receives security fixes.
OLDEST_SUPPORTED_PYTHON = (3, 11)
_AUDIT_FLAGS = ["--preview-features", "audit-command"]


@dataclass(frozen=True)
class Vulnerability:
    """A known vulnerability in a locked package.

    Attributes:
        package: Normalised package name.
        version: Locked version that is affected.
        vuln_id: Advisory ID (GHSA/PYSEC/CVE).
        summary: One-line description.
        fix_versions: Versions that fix it; empty when no fix exists.
    """

    package: str
    version: str
    vuln_id: str
    summary: str
    fix_versions: tuple[str, ...]


def _run(
    cmd: list[str], project_dir: Path, *, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run a uv command in the project directory."""
    return subprocess.run(
        cmd,
        cwd=project_dir,
        env=clean_env(),
        check=False,
        text=True,
        capture_output=capture,
    )


def cooldown_span(days: int) -> str:
    """Return the uv relative-duration string for a cooldown."""
    return f"{days} days"


def read_locked_versions(lock_path: Path) -> dict[str, str]:
    """Map package name to version for every package in a ``uv.lock``.

    Args:
        lock_path: Path to ``uv.lock``; a missing file gives an empty map.

    Returns:
        Package name to locked version (packages without a version, such
        as the editable project itself, are skipped).
    """
    if not lock_path.exists():
        return {}
    lock = tomllib.loads(lock_path.read_text())
    return {
        pkg["name"]: pkg["version"]
        for pkg in lock.get("package", [])
        if "version" in pkg
    }


def ensure_cooldown(
    pyproject_path: Path,
    days: int | None,
    *,
    now: datetime | None = None,
) -> int:
    """Write the cooldown into ``pyproject.toml`` and prune old exemptions.

    Args:
        pyproject_path: The project's ``pyproject.toml``.
        days: Cooldown to set. ``None`` keeps an existing setting, or
            sets the default when there is none.
        now: Current time (injected for tests).

    Returns:
        The cooldown in days that is now in effect.

    Raises:
        UpgradeError: If an existing ``exclude-newer`` is a fixed date
            rather than a rolling ``"N days"`` span and ``days`` is None.
    """
    now = now or datetime.now(UTC)
    doc = tomlkit.parse(pyproject_path.read_text())
    tool = doc.setdefault("tool", tomlkit.table())
    uv = tool.setdefault("uv", tomlkit.table())  # type: ignore[union-attr]

    current = uv.get("exclude-newer")  # type: ignore[union-attr]
    if days is None and current is not None:
        days = _parse_days(str(current))
    days = days if days is not None else DEFAULT_COOLDOWN_DAYS
    uv["exclude-newer"] = cooldown_span(days)  # type: ignore[index]

    # Exemptions are dated; once the rolling window has passed that date
    # the exemption is stricter than the cooldown itself, so drop it.
    exemptions = uv.get("exclude-newer-package")  # type: ignore[union-attr]
    if exemptions is not None:
        window_start = now - timedelta(days=days)
        for name in list(exemptions):
            stamp = exemptions[name]
            if isinstance(stamp, str) and _parse_time(stamp) <= window_start:
                del exemptions[name]
        if not exemptions:
            del uv["exclude-newer-package"]  # type: ignore[union-attr]

    pyproject_path.write_text(tomlkit.dumps(doc))
    return days


def add_exemptions(
    pyproject_path: Path, packages: set[str], *, now: datetime | None = None
) -> None:
    """Let security fixes for ``packages`` through the cooldown.

    Each package may use releases uploaded up to ``now``; the entry is
    pruned by :func:`ensure_cooldown` once the cooldown catches up.
    """
    if not packages:
        return
    stamp = (now or datetime.now(UTC)).strftime("%Y-%m-%dT%H:%M:%SZ")
    doc = tomlkit.parse(pyproject_path.read_text())
    uv = doc["tool"]["uv"]  # type: ignore[index]
    exemptions = uv.setdefault(  # type: ignore[union-attr]
        "exclude-newer-package", tomlkit.inline_table()
    )
    for name in sorted(packages):
        exemptions[name] = stamp
    pyproject_path.write_text(tomlkit.dumps(doc))


def parse_audit(report: str) -> list[Vulnerability]:
    """Parse ``uv audit --output-format json`` output."""
    data = json.loads(report)
    return [
        Vulnerability(
            package=v["dependency"]["name"],
            version=v["dependency"]["version"],
            vuln_id=v.get("display_id") or v["id"],
            summary=v.get("summary", ""),
            fix_versions=tuple(v.get("fix_versions") or ()),
        )
        for v in data.get("vulnerabilities", [])
    ]


def audit(project_dir: Path) -> list[Vulnerability]:
    """Audit the locked dependencies with ``uv audit``.

    Raises:
        UpgradeError: If uv cannot run the audit (for example, a uv
            release that predates ``uv audit``).
    """
    result = _run(
        ["uv", "audit", "--frozen", "--output-format", "json", *_AUDIT_FLAGS],
        project_dir,
        capture=True,
    )
    try:
        return parse_audit(result.stdout)
    except (json.JSONDecodeError, KeyError) as e:
        raise UpgradeError(
            "uv audit failed. Update uv with `uv self update` and retry.\n"
            f"{result.stderr.strip()}"
        ) from e


def check_python_version(project_dir: Path) -> str | None:
    """Return a warning if the project pins an unsupported Python."""
    pin_file = project_dir / ".python-version"
    if not pin_file.exists():
        return None
    pin = pin_file.read_text().strip()
    try:
        major, minor = (int(p) for p in pin.split(".")[:2])
    except ValueError:
        return None
    if (major, minor) < OLDEST_SUPPORTED_PYTHON:
        oldest = ".".join(map(str, OLDEST_SUPPORTED_PYTHON))
        return (
            f"Python {pin} no longer receives security fixes "
            f"(oldest supported: {oldest}). Move on with "
            "`uv python pin 3.14`, then rerun this upgrade."
        )
    return None


def safe_upgrade(
    project_dir: Path,
    *,
    cooldown_days: int | None = None,
    dry_run: bool = False,
) -> int:
    """Upgrade a uv project's dependencies behind a cooldown and an audit.

    Args:
        project_dir: Directory containing ``pyproject.toml``.
        cooldown_days: Minimum age of a release, in days. ``None`` keeps
            the project's setting (or the 7-day default).
        dry_run: Show what would change, then restore the original
            ``pyproject.toml`` and ``uv.lock`` without syncing.

    Returns:
        Process exit code: 0 when no known vulnerabilities remain, 1
        otherwise.

    Raises:
        UpgradeError: If the directory is not a uv project or a uv step
            fails.
    """
    pyproject = project_dir / "pyproject.toml"
    lock = project_dir / "uv.lock"
    if not pyproject.exists():
        raise UpgradeError(
            f"No pyproject.toml in {project_dir}. "
            "Run `uv-start --upgrade` from the project folder."
        )

    backups = _backup([pyproject, lock])
    try:
        return _upgrade(project_dir, pyproject, lock, cooldown_days, dry_run)
    finally:
        if dry_run:
            _restore(backups)
            rprint("[yellow]Dry run: pyproject.toml and uv.lock restored.[/]")


def _upgrade(
    project_dir: Path,
    pyproject: Path,
    lock: Path,
    cooldown_days: int | None,
    dry_run: bool,
) -> int:
    """Run the upgrade steps; see :func:`safe_upgrade`."""
    # 1. Tooling: uv itself and the Python patch release.
    if not dry_run:
        _update_uv(project_dir)
    if warning := check_python_version(project_dir):
        rprint(f"[red]⚠ {warning}[/red]")
    pin = project_dir / ".python-version"
    if pin.exists() and not dry_run:
        version = pin.read_text().strip()
        if _run(["uv", "python", "upgrade", version], project_dir).returncode:
            rprint(f"[yellow]Could not upgrade Python {version}.[/yellow]")

    # 2. Lock everything behind the cooldown.
    before = read_locked_versions(lock)
    days = ensure_cooldown(pyproject, cooldown_days)
    rprint(f"[green]Upgrading to releases at least {days} days old...[/]")
    _lock(project_dir, ["--upgrade"])

    # 3. Audit; let fixes for known vulnerabilities through the cooldown.
    vulns = audit(project_dir)
    fixable = {v.package for v in vulns if v.fix_versions}
    if fixable:
        rprint(
            "[yellow]Security fixes newer than the cooldown, "
            f"allowed for: {', '.join(sorted(fixable))}[/yellow]"
        )
        add_exemptions(pyproject, fixable)
        _lock(
            project_dir,
            [arg for pkg in sorted(fixable) for arg in ("-P", pkg)],
        )
        vulns = audit(project_dir)

    _print_changes(before, read_locked_versions(lock), fixable)

    # 4. Install what was locked.
    if not dry_run and _run(["uv", "sync"], project_dir).returncode:
        raise UpgradeError("uv sync failed after upgrading the lockfile.")

    if vulns:
        _print_vulnerabilities(vulns)
        return 1
    rprint("[green]✓ No known vulnerabilities in the locked packages.[/]")
    return 0


def _update_uv(project_dir: Path) -> None:
    """Update uv; installs managed by Homebrew/pipx just get a hint."""
    if _run(["uv", "self", "update"], project_dir).returncode:
        rprint(
            "[yellow]uv could not update itself (installed with another "
            "tool?). Update it the way you installed it, e.g. "
            "`brew upgrade uv`.[/yellow]"
        )


def _lock(project_dir: Path, extra: list[str]) -> None:
    """Run ``uv lock`` with extra arguments."""
    if _run(["uv", "lock", *extra], project_dir).returncode:
        raise UpgradeError("uv lock failed; see the output above.")


def _backup(paths: list[Path]) -> dict[Path, bytes | None]:
    """Snapshot file contents (``None`` for files that do not exist)."""
    return {p: p.read_bytes() if p.exists() else None for p in paths}


def _restore(backups: dict[Path, bytes | None]) -> None:
    """Put snapshotted files back exactly as they were."""
    for path, content in backups.items():
        if content is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(content)


def _print_changes(
    before: dict[str, str], after: dict[str, str], security: set[str]
) -> None:
    """Show which packages changed version."""
    names = sorted(
        n
        for n in before.keys() | after.keys()
        if before.get(n) != after.get(n)
    )
    if not names:
        rprint("[green]Everything is already up to date.[/green]")
        return
    table = Table(title="Package changes")
    for column in ("Package", "From", "To", ""):
        table.add_column(column)
    for name in names:
        note = "security fix" if name in security else ""
        table.add_row(name, before.get(name, "—"), after.get(name, "—"), note)
    rprint(table)


def _print_vulnerabilities(vulns: list[Vulnerability]) -> None:
    """List vulnerabilities that the upgrade could not resolve."""
    table = Table(title="Known vulnerabilities still present")
    for column in ("Package", "Version", "Advisory", "Fixed in"):
        table.add_column(column)
    for v in vulns:
        table.add_row(
            v.package,
            v.version,
            f"{v.vuln_id}: {v.summary}",
            ", ".join(v.fix_versions) or "no fix yet",
        )
    rprint(table)
    rprint(
        "[red]Check whether your code uses the affected feature. "
        "Packages pinned by another dependency cannot move until that "
        "dependency allows it.[/red]"
    )


def _parse_days(span: str) -> int:
    """Read the number of days from a ``"N days"`` cooldown string."""
    parts = span.split()
    if len(parts) == 2 and parts[0].isdigit() and parts[1] in {"day", "days"}:
        return int(parts[0])
    raise UpgradeError(
        f'pyproject.toml sets exclude-newer = "{span}". uv-start manages '
        'a rolling cooldown ("7 days"); pass --cooldown DAYS to replace it.'
    )


def _parse_time(stamp: str) -> datetime:
    """Parse an RFC 3339 timestamp (``Z`` suffix allowed)."""
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))
