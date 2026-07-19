"""CLI-level tests for blender_mobile_3d_installer.commands.main."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from blender_mobile_3d_installer.commands import main
from blender_mobile_3d_installer.exit_codes import (
    BLENDER_NOT_FOUND,
    INVALID_ARGUMENTS,
    OFFLINE_ARTIFACT_FAILURE,
)


def test_main_help_returns_zero() -> None:
    assert main(["help"]) == 0


def test_main_no_args_shows_help_returns_zero() -> None:
    assert main([]) == 0


def test_main_version_returns_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == "1.0.0"


def test_main_unknown_command_returns_invalid_arguments() -> None:
    assert main(["unknown"]) == INVALID_ARGUMENTS


def test_main_doctor_json_without_blender_reports_not_found(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "blender_mobile_3d_installer.blender_discovery.shutil.which", lambda n: None
    )
    monkeypatch.setattr(
        "blender_mobile_3d_installer.blender_discovery._common_locations", lambda: []
    )
    exit_code = main(["doctor", "--json"])
    assert exit_code == BLENDER_NOT_FOUND
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["selected_blender"] is None


def test_main_doctor_with_fake_blender_is_healthy(
    monkeypatch: pytest.MonkeyPatch, fake_blender, capsys: pytest.CaptureFixture[str]
) -> None:
    blender_path = fake_blender(
        version="4.9.0",
        responses={"status": {"ok": True, "installed": False, "enabled": False, "version": None}},
    )
    exit_code = main(["doctor", "--blender", blender_path, "--json"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True


def test_main_list_blenders_json(fake_blender, capsys: pytest.CaptureFixture[str]) -> None:
    blender_path = fake_blender(version="4.9.0")
    exit_code = main(["list-blenders", "--blender", blender_path, "--json"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["blenders"][0]["path"] == blender_path


def test_main_install_offline_missing_artifact_exit_code(fake_blender) -> None:
    blender_path = fake_blender(version="4.9.0")
    exit_code = main(
        ["install", "--blender", blender_path, "--offline", "/does/not/exist.zip", "--json"]
    )
    assert exit_code == OFFLINE_ARTIFACT_FAILURE


def test_main_install_dry_run(
    fake_blender, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    zip_path = tmp_path / "addon.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("blender_mobile_3d/__init__.py", "x = 1")
        zf.writestr("blender_mobile_3d/version.py", 'VERSION = "1.0.0"')
    blender_path = fake_blender(version="4.9.0")

    exit_code = main(
        ["install", "--blender", blender_path, "--offline", str(zip_path), "--dry-run", "--json"]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["dry_run"] is True


def test_main_uninstall_without_yes_returns_invalid_arguments(fake_blender) -> None:
    blender_path = fake_blender(
        version="4.9.0",
        responses={"status": {"ok": True, "installed": True, "enabled": True, "version": "1.0.0"}},
    )
    exit_code = main(["uninstall", "--blender", blender_path, "--json"])
    assert exit_code == INVALID_ARGUMENTS


def test_main_list_blenders_human_readable_output(
    fake_blender, capsys: pytest.CaptureFixture[str]
) -> None:
    blender_path = fake_blender(version="4.9.0")
    exit_code = main(["list-blenders", "--blender", blender_path])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "blenders:" in out
    assert blender_path in out


def test_main_update_dispatches(fake_blender, tmp_path: Path) -> None:
    zip_path = tmp_path / "addon.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("blender_mobile_3d/__init__.py", "x = 1")
        zf.writestr("blender_mobile_3d/version.py", 'VERSION = "1.0.0"')
    blender_path = fake_blender(
        version="4.9.0",
        responses={"status": {"ok": True, "installed": False, "enabled": False, "version": None}},
    )
    exit_code = main(["update", "--blender", blender_path, "--offline", str(zip_path), "--dry-run"])
    assert exit_code == 0


def test_main_error_path_human_readable(fake_blender, capsys: pytest.CaptureFixture[str]) -> None:
    blender_path = fake_blender(version="4.9.0")
    exit_code = main(["install", "--blender", blender_path, "--offline", "/does/not/exist.zip"])
    assert exit_code == OFFLINE_ARTIFACT_FAILURE
    assert "error:" in capsys.readouterr().err


def test_main_doctor_permission_failure_when_tmp_not_writable(
    monkeypatch: pytest.MonkeyPatch, fake_blender
) -> None:
    blender_path = fake_blender(
        version="4.9.0",
        responses={"status": {"ok": True, "installed": False, "enabled": False, "version": None}},
    )
    monkeypatch.setattr("blender_mobile_3d_installer.installer._tmp_dir_writable", lambda: False)
    exit_code = main(["doctor", "--blender", blender_path, "--json"])
    from blender_mobile_3d_installer.exit_codes import PERMISSION_FAILURE

    assert exit_code == PERMISSION_FAILURE
