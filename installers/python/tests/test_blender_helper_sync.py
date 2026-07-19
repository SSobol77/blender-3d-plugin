"""Guard against the two installer frontends drifting on the Blender helper."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_python_helper_matches_shared_source() -> None:
    shared = (REPO_ROOT / "installers" / "shared" / "blender_helper.py").read_bytes()
    packaged = (
        REPO_ROOT
        / "installers"
        / "python"
        / "src"
        / "blender_mobile_3d_installer"
        / "data"
        / "blender_helper.py"
    ).read_bytes()
    assert shared == packaged


def test_npm_helper_matches_shared_source() -> None:
    shared = (REPO_ROOT / "installers" / "shared" / "blender_helper.py").read_bytes()
    packaged = (
        REPO_ROOT / "installers" / "npm" / "src" / "data" / "blender_helper.py"
    ).read_bytes()
    assert shared == packaged
