"""Tests for blender_mobile_3d_installer.installer orchestration logic.

Uses fake_blender (no real bpy) to exercise install/update/uninstall/doctor
decision logic in isolation; the real Blender end-to-end path is proven
separately by scripts/blender_regression.py in CI.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from blender_mobile_3d_installer import installer
from blender_mobile_3d_installer.exit_codes import (
    INVALID_ARGUMENTS,
    OFFLINE_ARTIFACT_FAILURE,
    UNINSTALL_FAILURE,
    UPDATE_FAILURE,
    InstallerError,
)


def _valid_zip(path: Path) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("blender_mobile_3d/__init__.py", "x = 1")
        zf.writestr("blender_mobile_3d/version.py", 'VERSION = "1.0.0"')
    return path


def test_install_dry_run_performs_no_mutation(fake_blender, tmp_path: Path) -> None:
    blender_path = fake_blender(version="4.9.0")
    zip_path = _valid_zip(tmp_path / "addon.zip")

    result = installer.do_install(
        explicit_blender=blender_path,
        version="1.0.0",
        manifest_url=None,
        offline_zip=str(zip_path),
        dry_run=True,
        force=False,
    )
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["artifact"] == str(zip_path)


def test_install_offline_missing_file_raises(fake_blender) -> None:
    blender_path = fake_blender(version="4.9.0")
    with pytest.raises(InstallerError) as excinfo:
        installer.do_install(
            explicit_blender=blender_path,
            version="1.0.0",
            manifest_url=None,
            offline_zip="/does/not/exist.zip",
            dry_run=False,
            force=False,
        )
    assert excinfo.value.exit_code == OFFLINE_ARTIFACT_FAILURE


def test_install_real_flow_reports_helper_result(fake_blender, tmp_path: Path) -> None:
    zip_path = _valid_zip(tmp_path / "addon.zip")
    blender_path = fake_blender(
        version="4.9.0",
        responses={"install": {"ok": True, "installed": True, "enabled": True, "version": "1.0.0"}},
    )
    result = installer.do_install(
        explicit_blender=blender_path,
        version="1.0.0",
        manifest_url=None,
        offline_zip=str(zip_path),
        dry_run=False,
        force=False,
    )
    assert result["installed"] is True
    assert result["version"] == "1.0.0"


def test_update_no_op_when_same_version(fake_blender, tmp_path: Path) -> None:
    blender_path = fake_blender(
        version="4.9.0",
        responses={"status": {"ok": True, "installed": True, "enabled": True, "version": "1.0.0"}},
    )
    result = installer.do_update(
        explicit_blender=blender_path,
        version="1.0.0",
        manifest_url=None,
        offline_zip=str(_valid_zip(tmp_path / "addon.zip")),
        dry_run=False,
        force=False,
    )
    assert result["updated"] is False
    assert "no update necessary" in result["message"].lower()


def test_update_refuses_downgrade_without_force(fake_blender, tmp_path: Path) -> None:
    blender_path = fake_blender(
        version="4.9.0",
        responses={"status": {"ok": True, "installed": True, "enabled": True, "version": "2.0.0"}},
    )
    with pytest.raises(InstallerError) as excinfo:
        installer.do_update(
            explicit_blender=blender_path,
            version="1.0.0",
            manifest_url=None,
            offline_zip=str(_valid_zip(tmp_path / "addon.zip")),
            dry_run=False,
            force=False,
        )
    assert excinfo.value.exit_code == UPDATE_FAILURE


def test_update_allows_downgrade_with_force(fake_blender, tmp_path: Path) -> None:
    blender_path = fake_blender(
        version="4.9.0",
        responses={
            "status": {"ok": True, "installed": True, "enabled": True, "version": "2.0.0"},
            "install": {"ok": True, "installed": True, "enabled": True, "version": "1.0.0"},
        },
    )
    result = installer.do_update(
        explicit_blender=blender_path,
        version="1.0.0",
        manifest_url=None,
        offline_zip=str(_valid_zip(tmp_path / "addon.zip")),
        dry_run=False,
        force=True,
    )
    assert result["updated"] is True
    assert result["version"] == "1.0.0"


def test_uninstall_requires_yes_flag(fake_blender) -> None:
    blender_path = fake_blender(
        version="4.9.0",
        responses={"status": {"ok": True, "installed": True, "enabled": True, "version": "1.0.0"}},
    )
    with pytest.raises(InstallerError) as excinfo:
        installer.do_uninstall(explicit_blender=blender_path, dry_run=False, yes=False)
    assert excinfo.value.exit_code == INVALID_ARGUMENTS


def test_uninstall_dry_run_no_mutation(fake_blender) -> None:
    blender_path = fake_blender(
        version="4.9.0",
        responses={"status": {"ok": True, "installed": True, "enabled": True, "version": "1.0.0"}},
    )
    result = installer.do_uninstall(explicit_blender=blender_path, dry_run=True, yes=True)
    assert result["dry_run"] is True
    assert result["removed"] is False


def test_uninstall_idempotent_when_already_absent(fake_blender) -> None:
    blender_path = fake_blender(
        version="4.9.0",
        responses={"status": {"ok": True, "installed": False, "enabled": False, "version": None}},
    )
    result = installer.do_uninstall(explicit_blender=blender_path, dry_run=False, yes=True)
    assert result["removed"] is False
    assert "already uninstalled" in result["message"].lower()


def test_uninstall_verifies_removal_and_fails_if_still_present(fake_blender) -> None:
    blender_path = fake_blender(
        version="4.9.0",
        responses={
            "status": {"ok": True, "installed": True, "enabled": True, "version": "1.0.0"},
            "uninstall": {"ok": True, "installed": True, "enabled": True, "version": "1.0.0"},
        },
    )
    with pytest.raises(InstallerError) as excinfo:
        installer.do_uninstall(explicit_blender=blender_path, dry_run=False, yes=True)
    assert excinfo.value.exit_code == UNINSTALL_FAILURE


def test_uninstall_success(fake_blender) -> None:
    blender_path = fake_blender(
        version="4.9.0",
        responses={
            "status": {"ok": True, "installed": True, "enabled": True, "version": "1.0.0"},
            "uninstall": {"ok": True, "installed": False, "enabled": False, "version": None},
        },
    )
    result = installer.do_uninstall(explicit_blender=blender_path, dry_run=False, yes=True)
    assert result["removed"] is True


def test_doctor_healthy_when_supported_blender_and_writable_tmp(fake_blender) -> None:
    blender_path = fake_blender(
        version="4.9.0",
        responses={"status": {"ok": True, "installed": False, "enabled": False, "version": None}},
    )
    report = installer.do_doctor(
        explicit_blender=blender_path, check_online=False, installer_version="1.0.0"
    )
    assert report["ok"] is True
    assert report["manifest_reachable"] == "skipped (offline)"
    assert report["selected_blender"]["path"] == blender_path


def test_doctor_unhealthy_without_blender() -> None:
    report = installer.do_doctor(
        explicit_blender="/does/not/exist", check_online=False, installer_version="1.0.0"
    )
    assert report["ok"] is False
    assert report["selected_blender"] is None


def test_list_blenders_reports_candidates(fake_blender) -> None:
    blender_path = fake_blender(version="4.9.0")
    result = installer.do_list_blenders(explicit_blender=blender_path)
    assert result["ok"] is True
    assert result["blenders"][0]["path"] == blender_path


def test_doctor_survives_status_query_failure(fake_blender) -> None:
    blender_path = fake_blender(version="4.9.0", responses={"status": {"ok": False, "error": "x"}})
    report = installer.do_doctor(
        explicit_blender=blender_path, check_online=False, installer_version="1.0.0"
    )
    assert report["extension_installed"] is None


def test_doctor_online_check_success(
    monkeypatch: pytest.MonkeyPatch, fake_blender, http_fixture_server
) -> None:
    import json as json_mod

    from blender_mobile_3d_installer import manifest as manifest_mod

    base_url, directory = http_fixture_server
    manifest = {
        "schema_version": "1.0.0",
        "version": "1.0.0",
        "artifacts": {
            "extension": {
                "filename": "x.zip",
                "url": f"{base_url}/x.zip",
                "sha256": "0" * 64,
                "size": 1,
            }
        },
    }
    (directory / "release-manifest.json").write_text(json_mod.dumps(manifest), encoding="utf-8")

    def _fake_fetch(version, manifest_url=None):
        return manifest_mod.fetch_manifest(
            version, manifest_url=f"{base_url}/release-manifest.json"
        )

    monkeypatch.setattr("blender_mobile_3d_installer.installer.fetch_manifest", _fake_fetch)

    blender_path = fake_blender(
        version="4.9.0",
        responses={"status": {"ok": True, "installed": False, "enabled": False, "version": None}},
    )
    report = installer.do_doctor(
        explicit_blender=blender_path, check_online=True, installer_version="1.0.0"
    )
    assert report["manifest_reachable"] is True


def test_doctor_online_check_failure(monkeypatch: pytest.MonkeyPatch, fake_blender) -> None:
    from blender_mobile_3d_installer.exit_codes import MANIFEST_FAILURE, InstallerError

    def _fake_fetch(version, manifest_url=None):
        raise InstallerError(MANIFEST_FAILURE, "unreachable")

    monkeypatch.setattr("blender_mobile_3d_installer.installer.fetch_manifest", _fake_fetch)
    blender_path = fake_blender(
        version="4.9.0",
        responses={"status": {"ok": True, "installed": False, "enabled": False, "version": None}},
    )
    report = installer.do_doctor(
        explicit_blender=blender_path, check_online=True, installer_version="1.0.0"
    )
    assert report["manifest_reachable"] is False


def test_tmp_dir_writable_false_on_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(installer.tempfile, "mkstemp", _boom)
    assert installer._tmp_dir_writable() is False


def test_resolve_artifact_online_downloads_and_validates(http_fixture_server) -> None:
    import hashlib
    import json as json_mod
    import zipfile

    base_url, directory = http_fixture_server
    zip_path = directory / "blender_mobile_3d-1.0.0.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("blender_mobile_3d/__init__.py", "x = 1")
        zf.writestr("blender_mobile_3d/version.py", 'VERSION = "1.0.0"')
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()

    manifest = {
        "schema_version": "1.0.0",
        "version": "1.0.0",
        "artifacts": {
            "extension": {
                "filename": "blender_mobile_3d-1.0.0.zip",
                "url": f"{base_url}/blender_mobile_3d-1.0.0.zip",
                "sha256": digest,
                "size": zip_path.stat().st_size,
            }
        },
    }
    (directory / "release-manifest.json").write_text(json_mod.dumps(manifest), encoding="utf-8")

    result_path = installer.resolve_artifact(
        "1.0.0", manifest_url=f"{base_url}/release-manifest.json", offline_zip=None
    )
    assert result_path.read_bytes() == zip_path.read_bytes()
