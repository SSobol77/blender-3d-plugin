"""Cli behavior tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path("/home/astra/blender-3d-plugin")


def run_cli(args):
    cmd = [
        sys.executable,
        str(ROOT / "scripts/blender_mobile_3d_cli.py"),
        *args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_cli_version():
    r = run_cli(["version"])
    assert r.returncode == 0
    assert r.stdout.strip() == "1.0.0"


def test_cli_list_presets_success():
    r = run_cli(["list-presets"])
    assert r.returncode == 0
    assert "low_poly" in r.stdout


def test_cli_analyze_missing_blend():
    r = run_cli(["--blend", "/tmp/missing_xyz_123.blend"])
    assert r.returncode != 0


def test_cli_validate_missing_manifest():
    r = run_cli(["--manifest", "/tmp/missing_manifest_xyz.json"])
    assert r.returncode != 0


def test_cli_print_schema_default():
    r = run_cli(["print-schema"])
    assert r.returncode == 0
    assert "schema" in r.stdout.lower() or "$schema" in r.stdout
