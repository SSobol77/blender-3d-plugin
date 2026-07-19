"""Tests for blender_mobile_3d_installer.zip_safety."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from blender_mobile_3d_installer import zip_safety
from blender_mobile_3d_installer.exit_codes import EXTENSION_VALIDATION_FAILURE, InstallerError

FIXTURES = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "installer"


def _make_zip(path: Path, extra_names: list[str]) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("blender_mobile_3d/__init__.py", "x = 1")
        zf.writestr("blender_mobile_3d/version.py", 'VERSION = "1.0.0"')
        for name in extra_names:
            zf.writestr(name, "payload")


def test_valid_zip_passes(tmp_path: Path) -> None:
    zip_path = tmp_path / "good.zip"
    _make_zip(zip_path, [])
    zip_safety.validate_zip_safety(zip_path)  # must not raise


def test_not_a_zip_file_raises(tmp_path: Path) -> None:
    bad = tmp_path / "notazip.zip"
    bad.write_bytes(b"this is not a zip")
    with pytest.raises(InstallerError) as excinfo:
        zip_safety.validate_zip_safety(bad)
    assert excinfo.value.exit_code == EXTENSION_VALIDATION_FAILURE


def test_missing_required_members_raises(tmp_path: Path) -> None:
    zip_path = tmp_path / "incomplete.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("blender_mobile_3d/only_this.py", "x = 1")
    with pytest.raises(InstallerError, match="missing required members"):
        zip_safety.validate_zip_safety(zip_path)


@pytest.mark.parametrize(
    "entry_set",
    ["absolute_path", "parent_traversal", "unexpected_top_level", "windows_absolute"],
)
def test_unsafe_entries_from_shared_fixture_are_rejected(tmp_path: Path, entry_set: str) -> None:
    unsafe_entries = json.loads((FIXTURES / "unsafe_zip_entries.json").read_text(encoding="utf-8"))
    zip_path = tmp_path / f"{entry_set}.zip"
    _make_zip(zip_path, unsafe_entries[entry_set])
    with pytest.raises(InstallerError) as excinfo:
        zip_safety.validate_zip_safety(zip_path)
    assert excinfo.value.exit_code == EXTENSION_VALIDATION_FAILURE


def test_symlink_entry_rejected(tmp_path: Path) -> None:
    zip_path = tmp_path / "symlink.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("blender_mobile_3d/__init__.py", "x = 1")
        zf.writestr("blender_mobile_3d/version.py", 'VERSION = "1.0.0"')
        info = zipfile.ZipInfo("blender_mobile_3d/evil_link")
        info.external_attr = 0o120777 << 16  # S_IFLNK | rwxrwxrwx
        zf.writestr(info, "/etc/passwd")
    with pytest.raises(InstallerError, match="symlink"):
        zip_safety.validate_zip_safety(zip_path)
