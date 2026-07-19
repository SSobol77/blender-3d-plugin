"""Tests for blender_mobile_3d_installer.blender_ops failure handling."""

from __future__ import annotations

from pathlib import Path

import pytest
from blender_mobile_3d_installer import blender_ops
from blender_mobile_3d_installer.exit_codes import INSTALL_FAILURE, InstallerError


def test_status_success(fake_blender) -> None:
    path = fake_blender(
        version="4.9.0",
        responses={"status": {"ok": True, "installed": True, "enabled": True, "version": "1.0.0"}},
    )
    result = blender_ops.status(path)
    assert result["installed"] is True


def test_nonexistent_executable_raises_install_failure() -> None:
    with pytest.raises(InstallerError) as excinfo:
        blender_ops.status("/does/not/exist/blender")
    assert excinfo.value.exit_code == INSTALL_FAILURE


def test_nonzero_exit_code_raises(fake_blender) -> None:
    path = fake_blender(version="4.9.0", exit_code=7)
    with pytest.raises(InstallerError, match="exited with code 7"):
        blender_ops.status(path)


def test_no_json_output_raises(tmp_path: Path) -> None:
    script = tmp_path / "silent-blender"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(0o755)
    with pytest.raises(InstallerError, match="no JSON result"):
        blender_ops.status(str(script))


def test_invalid_json_output_raises(tmp_path: Path) -> None:
    script = tmp_path / "bad-json-blender"
    script.write_text("#!/bin/sh\necho '{not valid json'\n")
    script.chmod(0o755)
    with pytest.raises(InstallerError, match="invalid JSON"):
        blender_ops.status(str(script))


def test_result_not_ok_raises(fake_blender) -> None:
    path = fake_blender(version="4.9.0", responses={"status": {"ok": False, "error": "kaboom"}})
    with pytest.raises(InstallerError, match="kaboom"):
        blender_ops.status(path)


def test_install_and_uninstall_wrappers(fake_blender, tmp_path: Path) -> None:
    path = fake_blender(
        version="4.9.0",
        responses={
            "install": {"ok": True, "installed": True, "enabled": True, "version": "1.0.0"},
            "uninstall": {"ok": True, "installed": False, "enabled": False, "version": None},
        },
    )
    zip_path = tmp_path / "addon.zip"
    zip_path.write_bytes(b"fake")
    assert blender_ops.install(path, zip_path)["installed"] is True
    assert blender_ops.uninstall(path)["installed"] is False


def test_make_temp_dir_creates_writable_directory() -> None:
    directory = blender_ops.make_temp_dir()
    try:
        assert directory.is_dir()
        probe = directory / "probe.txt"
        probe.write_text("ok", encoding="utf-8")
        assert probe.read_text(encoding="utf-8") == "ok"
    finally:
        probe.unlink(missing_ok=True)
        directory.rmdir()
