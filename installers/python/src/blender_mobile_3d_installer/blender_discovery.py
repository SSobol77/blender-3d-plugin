"""Real Blender executable discovery across Linux, macOS, and Windows."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from glob import glob
from pathlib import Path

from blender_mobile_3d_installer.exit_codes import (
    AMBIGUOUS_BLENDER,
    BLENDER_NOT_FOUND,
    UNSUPPORTED_BLENDER_VERSION,
    InstallerError,
)

MINIMUM_BLENDER_VERSION = (4, 3, 0)
MAXIMUM_BLENDER_VERSION_EXCLUSIVE: tuple[int, int, int] | None = None
BLENDER_PROBE_TIMEOUT_SECONDS = 10
_VERSION_RE = re.compile(r"Blender\s+(\d+)\.(\d+)(?:\.(\d+))?")


@dataclass(frozen=True)
class BlenderCandidate:
    path: str
    version: str | None
    supported: bool
    source: str


def _parse_version(output: str) -> tuple[int, int, int] | None:
    match = _VERSION_RE.search(output)
    if not match:
        return None
    major, minor, patch = match.groups()
    return (int(major), int(minor), int(patch or 0))


def _is_supported(version: tuple[int, int, int]) -> bool:
    if version < MINIMUM_BLENDER_VERSION:
        return False
    if (
        MAXIMUM_BLENDER_VERSION_EXCLUSIVE is not None
        and version >= MAXIMUM_BLENDER_VERSION_EXCLUSIVE
    ):
        return False
    return True


def probe_executable(path: str) -> tuple[str | None, bool]:
    """Run ``<path> --version`` and classify support; never raises."""
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argument array
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=BLENDER_PROBE_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, False
    version = _parse_version(completed.stdout + completed.stderr)
    if version is None:
        return None, False
    return ".".join(str(p) for p in version), _is_supported(version)


def _is_executable_file(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def _common_locations() -> list[str]:
    system = platform.system()
    home = Path.home()
    if system == "Linux":
        candidates = [
            "/usr/bin/blender",
            "/usr/local/bin/blender",
            *glob("/opt/blender*/blender"),
            str(home / ".local/share/flatpak/exports/bin/blender"),
            "/var/lib/flatpak/exports/bin/blender",
            "/snap/bin/blender",
        ]
    elif system == "Darwin":
        candidates = [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            str(home / "Applications/Blender.app/Contents/MacOS/Blender"),
            *glob("/Applications/Blender*.app/Contents/MacOS/Blender"),
            *glob(str(home / "Applications/Blender*.app/Contents/MacOS/Blender")),
        ]
    elif system == "Windows":
        program_files = [
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        ]
        candidates = []
        for base in program_files:
            candidates.extend(
                glob(str(Path(base) / "Blender Foundation" / "Blender *" / "blender.exe"))
            )
    else:
        candidates = []
    return candidates


def discover_blenders(explicit: str | None = None) -> list[BlenderCandidate]:
    """Return every discovered Blender candidate, deduplicated by real path.

    When ``explicit`` is given it is the only candidate returned (still
    probed for version/support so callers can report why it was rejected).
    """
    if explicit:
        if not _is_executable_file(Path(explicit)):
            return []
        version, supported = probe_executable(explicit)
        return [
            BlenderCandidate(path=explicit, version=version, supported=supported, source="explicit")
        ]

    seen: dict[str, BlenderCandidate] = {}

    path_candidate = shutil.which("blender")
    if path_candidate:
        _add_candidate(seen, path_candidate, "PATH")

    for location in _common_locations():
        path_obj = Path(location)
        if _is_executable_file(path_obj):
            _add_candidate(seen, str(path_obj), "well-known-location")

    return sorted(seen.values(), key=lambda c: (not c.supported, c.version or ""), reverse=True)


def _add_candidate(seen: dict[str, BlenderCandidate], path: str, source: str) -> None:
    try:
        real_path = str(Path(path).resolve())
    except OSError:
        real_path = path
    if real_path in seen:
        return
    version, supported = probe_executable(real_path)
    seen[real_path] = BlenderCandidate(
        path=real_path, version=version, supported=supported, source=source
    )


def select_blender(explicit: str | None = None) -> BlenderCandidate:
    """Apply the discovery/selection rule from docs/installer-contract.md."""
    candidates = discover_blenders(explicit)
    if not candidates:
        raise InstallerError(BLENDER_NOT_FOUND, "No Blender executable found.")

    supported = [c for c in candidates if c.supported]
    if not supported:
        only = candidates[0]
        raise InstallerError(
            UNSUPPORTED_BLENDER_VERSION,
            f"Blender at {only.path} is version {only.version or 'unknown'}, "
            f"which is not supported (requires >= {'.'.join(map(str, MINIMUM_BLENDER_VERSION))}).",
        )
    if len(supported) > 1 and not explicit:
        listing = ", ".join(f"{c.path} ({c.version})" for c in supported)
        raise InstallerError(
            AMBIGUOUS_BLENDER,
            f"Multiple supported Blender installations found: {listing}. "
            "Select one explicitly with --blender.",
        )
    return supported[0]
