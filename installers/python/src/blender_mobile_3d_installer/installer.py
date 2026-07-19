"""Orchestration for install/update/uninstall/doctor/list-blenders.

Blender itself is the source of truth for installed/enabled state and
version (queried via blender_ops.status); this module keeps no separate
state file.
"""

from __future__ import annotations

import tempfile
from dataclasses import asdict
from pathlib import Path

from blender_mobile_3d_installer import blender_ops
from blender_mobile_3d_installer.blender_discovery import (
    BlenderCandidate,
    discover_blenders,
    select_blender,
)
from blender_mobile_3d_installer.exit_codes import (
    INVALID_ARGUMENTS,
    OFFLINE_ARTIFACT_FAILURE,
    UNINSTALL_FAILURE,
    UPDATE_FAILURE,
    InstallerError,
)
from blender_mobile_3d_installer.manifest import fetch_manifest
from blender_mobile_3d_installer.zip_safety import validate_zip_safety


def _version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def resolve_artifact(
    version: str,
    manifest_url: str | None,
    offline_zip: str | None,
    max_size_bytes: int = 200 * 1024 * 1024,
) -> Path:
    """Return a local, validated ZIP path; downloads it if not offline."""
    if offline_zip:
        offline_path = Path(offline_zip)
        if not offline_path.is_file():
            raise InstallerError(
                OFFLINE_ARTIFACT_FAILURE, f"Offline artifact not found: {offline_path}"
            )
        validate_zip_safety(offline_path)
        return offline_path

    manifest = fetch_manifest(version, manifest_url)
    from blender_mobile_3d_installer.download import download_artifact

    dest_dir = Path(tempfile.mkdtemp(prefix="bm3d-download-"))
    dest_path = dest_dir / manifest.extension.filename
    download_artifact(manifest.extension.url, dest_path, manifest.extension.sha256, max_size_bytes)
    validate_zip_safety(dest_path)
    return dest_path


def do_install(
    *,
    explicit_blender: str | None,
    version: str,
    manifest_url: str | None,
    offline_zip: str | None,
    dry_run: bool,
    force: bool,
) -> dict:
    candidate = select_blender(explicit_blender)
    artifact_path = resolve_artifact(version, manifest_url, offline_zip)

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "blender": asdict(candidate),
            "artifact": str(artifact_path),
        }

    # install always overwrites (safe: same-version reinstall is idempotent);
    # --force is meaningful for do_update's downgrade check, not here.
    result = blender_ops.install(candidate.path, artifact_path, overwrite=True)
    return {"ok": True, "dry_run": False, "blender": asdict(candidate), **result}


def do_update(
    *,
    explicit_blender: str | None,
    version: str,
    manifest_url: str | None,
    offline_zip: str | None,
    dry_run: bool,
    force: bool,
) -> dict:
    candidate = select_blender(explicit_blender)
    current = blender_ops.status(candidate.path)

    if current.get("installed") and current.get("version"):
        current_v = _version_tuple(current["version"])
        requested_v = _version_tuple(version)
        if requested_v < current_v and not force:
            raise InstallerError(
                UPDATE_FAILURE,
                f"Refusing to downgrade from {current['version']} to {version} without --force.",
            )
        if requested_v == current_v and not force:
            return {
                "ok": True,
                "dry_run": dry_run,
                "updated": False,
                "blender": asdict(candidate),
                "version": current["version"],
                "message": "Already up to date; no update necessary.",
            }

    artifact_path = resolve_artifact(version, manifest_url, offline_zip)

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "updated": True,
            "blender": asdict(candidate),
            "artifact": str(artifact_path),
        }

    result = blender_ops.install(candidate.path, artifact_path, overwrite=True)
    return {"ok": True, "dry_run": False, "updated": True, "blender": asdict(candidate), **result}


def do_uninstall(*, explicit_blender: str | None, dry_run: bool, yes: bool) -> dict:
    candidate = select_blender(explicit_blender)
    current = blender_ops.status(candidate.path)

    if not current.get("installed"):
        return {
            "ok": True,
            "dry_run": dry_run,
            "removed": False,
            "blender": asdict(candidate),
            "message": "Already uninstalled.",
        }

    if dry_run:
        return {"ok": True, "dry_run": True, "removed": False, "blender": asdict(candidate)}

    if not yes:
        raise InstallerError(
            INVALID_ARGUMENTS, "Refusing to uninstall without --yes in a non-interactive context."
        )

    result = blender_ops.uninstall(candidate.path)
    if result.get("installed"):
        raise InstallerError(UNINSTALL_FAILURE, "Blender still reports the add-on as installed.")
    return {"ok": True, "dry_run": False, "removed": True, "blender": asdict(candidate), **result}


def _tmp_dir_writable() -> bool:
    try:
        probe = Path(tempfile.mkstemp(prefix="bm3d-doctor-")[1])
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def do_doctor(*, explicit_blender: str | None, check_online: bool, installer_version: str) -> dict:
    import platform as platform_mod

    candidates = discover_blenders(explicit_blender)
    supported = [c for c in candidates if c.supported]
    selected: BlenderCandidate | None = supported[0] if len(supported) == 1 else None
    if explicit_blender and candidates:
        selected = candidates[0]

    extension_state: dict = {"installed": None, "enabled": None, "version": None}
    if selected is not None:
        try:
            status = blender_ops.status(selected.path)
            extension_state = {
                "installed": status.get("installed"),
                "enabled": status.get("enabled"),
                "version": status.get("version"),
            }
        except InstallerError:
            pass

    manifest_reachable: bool | str = "skipped (offline)"
    if check_online:
        try:
            fetch_manifest(installer_version)
            manifest_reachable = True
        except InstallerError:
            manifest_reachable = False

    tmp_writable = _tmp_dir_writable()

    report = {
        "platform": platform_mod.platform(),
        "installer_version": installer_version,
        "blender_candidates": [asdict(c) for c in candidates],
        "selected_blender": asdict(selected) if selected else None,
        "extension_installed": extension_state["installed"],
        "extension_enabled": extension_state["enabled"],
        "extension_version": extension_state["version"],
        "tmp_dir_writable": tmp_writable,
        "manifest_reachable": manifest_reachable,
    }

    healthy = bool(supported) and tmp_writable
    report["ok"] = healthy
    return report


def do_list_blenders(*, explicit_blender: str | None) -> dict:
    candidates = discover_blenders(explicit_blender)
    return {"ok": True, "blenders": [asdict(c) for c in candidates]}


__all__ = [
    "do_doctor",
    "do_install",
    "do_list_blenders",
    "do_uninstall",
    "do_update",
    "resolve_artifact",
]
