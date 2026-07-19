"""CLI behavior tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts/blender_mobile_3d_cli.py"),
        *args,
    ]
    # Fixed argument array invoking the repo's own CLI with sys.executable.
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)  # noqa: S603


def test_cli_version() -> None:
    r = run_cli(["version"])
    assert r.returncode == 0
    assert r.stdout.strip() == "1.0.0"


def test_cli_list_presets_success() -> None:
    r = run_cli(["list-presets"])
    assert r.returncode == 0
    assert "low_poly" in r.stdout


def test_cli_unknown_arguments_fail(tmp_path: Path) -> None:
    r = run_cli(["--blend", str(tmp_path / "missing.blend")])
    assert r.returncode != 0


def test_cli_validate_missing_manifest(tmp_path: Path) -> None:
    r = run_cli(["validate", "--manifest", str(tmp_path / "missing_manifest.json")])
    assert r.returncode == 2
    assert "missing:" in r.stdout


def test_cli_validate_existing_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"schema_version": "1.0.0"}', encoding="utf-8")
    r = run_cli(["validate", "--manifest", str(manifest)])
    assert r.returncode == 0
    assert "schema_version" in r.stdout


def test_cli_print_schema_default() -> None:
    r = run_cli(["print-schema"])
    assert r.returncode == 0
    assert "schema" in r.stdout.lower() or "$schema" in r.stdout


def test_cli_no_command_shows_help() -> None:
    r = run_cli([])
    assert r.returncode == 2
