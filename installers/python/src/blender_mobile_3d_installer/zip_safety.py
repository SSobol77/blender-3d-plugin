"""ZIP structure validation: single top-level package, no traversal, no symlinks."""

from __future__ import annotations

import stat
import zipfile
from pathlib import Path, PureWindowsPath

from blender_mobile_3d_installer.exit_codes import EXTENSION_VALIDATION_FAILURE, InstallerError

EXPECTED_TOP_LEVEL = "blender_mobile_3d"
REQUIRED_MEMBERS = (
    f"{EXPECTED_TOP_LEVEL}/__init__.py",
    f"{EXPECTED_TOP_LEVEL}/version.py",
)


def _is_symlink_entry(info: zipfile.ZipInfo) -> bool:
    unix_mode = info.external_attr >> 16
    return unix_mode != 0 and stat.S_ISLNK(unix_mode)


def _is_unsafe_name(name: str) -> bool:
    if name.startswith("/") or name.startswith("\\"):
        return True
    if PureWindowsPath(name).drive:
        return True
    parts = Path(name.replace("\\", "/")).parts
    if ".." in parts:
        return True
    if not parts or parts[0] != EXPECTED_TOP_LEVEL:
        return True
    return False


def validate_zip_safety(path: Path) -> None:
    """Raise InstallerError(EXTENSION_VALIDATION_FAILURE) on any violation."""
    if not zipfile.is_zipfile(path):
        raise InstallerError(EXTENSION_VALIDATION_FAILURE, f"Not a valid ZIP archive: {path}")

    with zipfile.ZipFile(path) as zf:
        bad_crc = zf.testzip()
        if bad_crc is not None:
            raise InstallerError(EXTENSION_VALIDATION_FAILURE, f"Corrupt ZIP member: {bad_crc}")

        names = zf.namelist()
        for info in zf.infolist():
            if _is_symlink_entry(info):
                raise InstallerError(
                    EXTENSION_VALIDATION_FAILURE, f"ZIP contains a symlink entry: {info.filename}"
                )
            if _is_unsafe_name(info.filename):
                raise InstallerError(
                    EXTENSION_VALIDATION_FAILURE, f"ZIP contains an unsafe path: {info.filename}"
                )

        missing = [m for m in REQUIRED_MEMBERS if m not in names]
        if missing:
            raise InstallerError(
                EXTENSION_VALIDATION_FAILURE, f"ZIP is missing required members: {missing}"
            )
