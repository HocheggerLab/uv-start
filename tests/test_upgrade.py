import json
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from uv_start.exceptions import UpgradeError
from uv_start.upgrade import (
    add_exemptions,
    check_python_version,
    ensure_cooldown,
    parse_audit,
    read_locked_versions,
    safe_upgrade,
)

NOW = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)


def _audit_json(*vulns: tuple[str, str, list[str]]) -> str:
    return json.dumps(
        {
            "vulnerabilities": [
                {
                    "dependency": {"name": name, "version": version},
                    "id": f"GHSA-{name}",
                    "summary": "bad",
                    "fix_versions": fixes,
                }
                for name, version, fixes in vulns
            ]
        }
    )


@pytest.fixture
def pyproject(tmp_path: Path) -> Path:
    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "demo"\nversion = "0.1.0"\n')
    return path


def _uv_settings(path: Path) -> dict:
    return tomllib.loads(path.read_text())["tool"]["uv"]


def test_ensure_cooldown_adds_default(pyproject):
    assert ensure_cooldown(pyproject, None, now=NOW) == 7
    assert _uv_settings(pyproject)["exclude-newer"] == "7 days"


def test_ensure_cooldown_keeps_project_setting(pyproject):
    pyproject.write_text(
        pyproject.read_text() + '\n[tool.uv]\nexclude-newer = "14 days"\n'
    )
    assert ensure_cooldown(pyproject, None, now=NOW) == 14


def test_ensure_cooldown_explicit_days_win(pyproject):
    ensure_cooldown(pyproject, None, now=NOW)
    assert ensure_cooldown(pyproject, 3, now=NOW) == 3
    assert _uv_settings(pyproject)["exclude-newer"] == "3 days"


def test_ensure_cooldown_rejects_fixed_date(pyproject):
    pyproject.write_text(
        pyproject.read_text()
        + '\n[tool.uv]\nexclude-newer = "2026-01-01T00:00:00Z"\n'
    )
    with pytest.raises(UpgradeError, match="--cooldown"):
        ensure_cooldown(pyproject, None, now=NOW)


def test_exemptions_added_then_pruned(pyproject):
    ensure_cooldown(pyproject, 7, now=NOW)
    add_exemptions(pyproject, {"pillow"}, now=NOW)
    assert _uv_settings(pyproject)["exclude-newer-package"] == {
        "pillow": "2026-10-31T12:00:00Z"
    }
    # Six days later the exemption is still needed...
    ensure_cooldown(pyproject, None, now=datetime(2026, 11, 6, tzinfo=UTC))
    assert "exclude-newer-package" in _uv_settings(pyproject)
    # ...after the cooldown it would hold pillow back, so it goes.
    ensure_cooldown(pyproject, None, now=datetime(2026, 11, 8, tzinfo=UTC))
    assert "exclude-newer-package" not in _uv_settings(pyproject)


def test_read_locked_versions(tmp_path):
    lock = tmp_path / "uv.lock"
    lock.write_text(
        'version = 1\n[[package]]\nname = "numpy"\nversion = "2.5.4"\n'
        '[[package]]\nname = "demo"\nsource = { editable = "." }\n'
    )
    assert read_locked_versions(lock) == {"numpy": "2.5.4"}
    assert read_locked_versions(tmp_path / "missing.lock") == {}


def test_parse_audit():
    (vuln,) = parse_audit(_audit_json(("pillow", "12.2.0", ["12.2.1"])))
    assert vuln.package == "pillow"
    assert vuln.fix_versions == ("12.2.1",)


@pytest.mark.parametrize(
    ("pin", "warns"), [("3.10", True), ("3.9.18", True), ("3.11", False)]
)
def test_check_python_version(tmp_path, pin, warns):
    (tmp_path / ".python-version").write_text(pin + "\n")
    assert (check_python_version(tmp_path) is not None) is warns


def test_safe_upgrade_needs_pyproject(tmp_path):
    with pytest.raises(UpgradeError, match="pyproject.toml"):
        safe_upgrade(tmp_path)


def _fake_uv(audits: list[str]):
    """Return a subprocess.run stand-in recording uv commands."""
    calls: list[list[str]] = []
    reports = iter(audits)

    def run(cmd, **kwargs):
        calls.append(cmd)
        stdout = next(reports) if cmd[1] == "audit" else ""
        return Mock(returncode=0, stdout=stdout, stderr="")

    return run, calls


def test_safe_upgrade_lets_security_fix_through(pyproject):
    run, calls = _fake_uv(
        [_audit_json(("pillow", "12.2.0", ["12.2.1"])), _audit_json()]
    )
    with patch("uv_start.upgrade.subprocess.run", side_effect=run):
        assert safe_upgrade(pyproject.parent) == 0
    locks = [c for c in calls if c[1] == "lock"]
    assert locks == [
        ["uv", "lock", "--upgrade"],
        ["uv", "lock", "-P", "pillow"],
    ]
    assert "pillow" in _uv_settings(pyproject)["exclude-newer-package"]
    assert ["uv", "sync"] in calls


def test_safe_upgrade_reports_unfixed(pyproject):
    run, _ = _fake_uv([_audit_json(("pkg", "1.0", []))])
    with patch("uv_start.upgrade.subprocess.run", side_effect=run):
        assert safe_upgrade(pyproject.parent) == 1


def test_safe_upgrade_dry_run_restores_files(pyproject):
    original = pyproject.read_text()
    run, calls = _fake_uv([_audit_json()])
    with patch("uv_start.upgrade.subprocess.run", side_effect=run):
        safe_upgrade(pyproject.parent, dry_run=True)
    assert pyproject.read_text() == original
    assert not (pyproject.parent / "uv.lock").exists()
    assert ["uv", "sync"] not in calls
    assert ["uv", "self", "update"] not in calls
