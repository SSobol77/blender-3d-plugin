"""Tests for scripts/release_artifacts.py (artifact contract)."""

from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import release_artifacts  # noqa: E402


def test_build_release_produces_all_artifacts(tmp_path: Path) -> None:
    artifacts = release_artifacts.build_release(REPO_ROOT, dist_dir=tmp_path)

    zip_path = artifacts["zip"]
    assert zip_path.name == "blender_mobile_3d-1.0.0.zip"
    assert zip_path.is_file() and zip_path.stat().st_size > 0
    assert zipfile.is_zipfile(zip_path)

    checksum_path = artifacts["sha256"]
    digest, name = checksum_path.read_text(encoding="utf-8").split()
    assert digest == release_artifacts.sha256_file(zip_path)
    assert name == zip_path.name

    manifest = json.loads(artifacts["manifest"].read_text(encoding="utf-8"))
    assert manifest["version"] == "1.0.0"
    assert manifest["artifacts"]["extension"]["sha256"] == digest
    assert manifest["artifacts"]["extension"]["size"] == zip_path.stat().st_size


def test_zip_contains_required_members(tmp_path: Path) -> None:
    artifacts = release_artifacts.build_release(REPO_ROOT, dist_dir=tmp_path)
    with zipfile.ZipFile(artifacts["zip"]) as zf:
        names = set(zf.namelist())
    for member in release_artifacts.REQUIRED_ZIP_MEMBERS:
        assert member in names
    assert not any("__pycache__" in n for n in names)


def test_build_release_is_deterministic(tmp_path: Path) -> None:
    first = release_artifacts.build_release(REPO_ROOT, dist_dir=tmp_path / "a")
    second = release_artifacts.build_release(REPO_ROOT, dist_dir=tmp_path / "b")
    assert release_artifacts.sha256_file(first["zip"]) == release_artifacts.sha256_file(
        second["zip"]
    )


def test_build_release_fails_without_package(tmp_path: Path) -> None:
    with pytest.raises(release_artifacts.ReleaseError, match="Package directory missing"):
        release_artifacts.build_release(tmp_path)


def test_build_release_fails_without_data_dirs(tmp_path: Path) -> None:
    fake_root = tmp_path / "root"
    shutil.copytree(REPO_ROOT / "blender_mobile_3d", fake_root / "blender_mobile_3d")
    with pytest.raises(release_artifacts.ReleaseError, match="Data directory missing"):
        release_artifacts.build_release(fake_root)


def test_build_release_fails_without_license(tmp_path: Path) -> None:
    fake_root = tmp_path / "root"
    shutil.copytree(REPO_ROOT / "blender_mobile_3d", fake_root / "blender_mobile_3d")
    shutil.copytree(REPO_ROOT / "presets", fake_root / "presets")
    shutil.copytree(REPO_ROOT / "schemas", fake_root / "schemas")
    with pytest.raises(release_artifacts.ReleaseError, match="LICENSE missing"):
        release_artifacts.build_release(fake_root)


def test_verify_zip_rejects_missing_and_invalid(tmp_path: Path) -> None:
    with pytest.raises(release_artifacts.ReleaseError, match="missing or empty"):
        release_artifacts.verify_zip(tmp_path / "nope.zip")

    not_zip = tmp_path / "not.zip"
    not_zip.write_bytes(b"this is not a zip archive")
    with pytest.raises(release_artifacts.ReleaseError, match="not a valid zip"):
        release_artifacts.verify_zip(not_zip)

    incomplete = tmp_path / "incomplete.zip"
    with zipfile.ZipFile(incomplete, "w") as zf:
        zf.writestr("random.txt", "data")
    with pytest.raises(release_artifacts.ReleaseError, match="missing required members"):
        release_artifacts.verify_zip(incomplete)


def test_main_returns_nonzero_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(root: Path, dist_dir: Path | None = None) -> dict[str, Path]:
        raise release_artifacts.ReleaseError("synthetic failure")

    monkeypatch.setattr(release_artifacts, "build_release", _boom)
    assert release_artifacts.main() == 1
