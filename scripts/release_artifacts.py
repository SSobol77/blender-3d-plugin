#!/usr/bin/env python3
"""Build, verify, and manifest the canonical Blender add-on release ZIP.

Outputs (all under ``dist/``):
- ``blender_mobile_3d-<version>.zip``          the installable add-on
- ``blender_mobile_3d-<version>.zip.sha256``   checksum file (``sha256sum`` format)
- ``release-manifest.json``                    manifest validated against
  ``schemas/release-manifest.schema.json``

The script exits non-zero if any expected artifact cannot be produced or
fails verification.
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.0.0"
PACKAGE_NAME = "blender_mobile_3d"
MINIMUM_BLENDER_VERSION = "4.3.0"
RELEASE_URL_BASE = "https://github.com/SSobol77/blender-3d-plugin/releases/download/v" + VERSION

# Deterministic timestamp for reproducible archives (2026-01-01 00:00:00).
ZIP_DATE_TIME = (2026, 1, 1, 0, 0, 0)

REQUIRED_ZIP_MEMBERS = (
    f"{PACKAGE_NAME}/__init__.py",
    f"{PACKAGE_NAME}/version.py",
    f"{PACKAGE_NAME}/presets/low_poly.json",
    f"{PACKAGE_NAME}/schemas/preset.schema.json",
    f"{PACKAGE_NAME}/LICENSE",
)


class ReleaseError(RuntimeError):
    """Raised when a release artifact cannot be produced or verified."""


def sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _collect_members(root: Path) -> list[tuple[Path, str]]:
    """Return (source file, archive name) pairs for the add-on ZIP."""
    package_dir = root / PACKAGE_NAME
    if not package_dir.is_dir():
        raise ReleaseError(f"Package directory missing: {package_dir}")

    members: list[tuple[Path, str]] = []
    for path in sorted(package_dir.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        members.append((path, path.relative_to(root).as_posix()))

    for data_dir, arc_prefix in (
        (root / "presets", f"{PACKAGE_NAME}/presets"),
        (root / "schemas", f"{PACKAGE_NAME}/schemas"),
    ):
        if not data_dir.is_dir():
            raise ReleaseError(f"Data directory missing: {data_dir}")
        for path in sorted(data_dir.glob("*.json")):
            members.append((path, f"{arc_prefix}/{path.name}"))

    license_path = root / "LICENSE"
    if not license_path.is_file():
        raise ReleaseError(f"LICENSE missing: {license_path}")
    members.append((license_path, f"{PACKAGE_NAME}/LICENSE"))
    return members


def build_zip(root: Path, zip_path: Path) -> None:
    members = _collect_members(root)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for source, arcname in members:
            info = zipfile.ZipInfo(arcname, date_time=ZIP_DATE_TIME)
            info.external_attr = 0o644 << 16
            zf.writestr(info, source.read_bytes(), zipfile.ZIP_DEFLATED)


def verify_zip(zip_path: Path) -> None:
    if not zip_path.is_file() or zip_path.stat().st_size == 0:
        raise ReleaseError(f"Release ZIP missing or empty: {zip_path}")
    if not zipfile.is_zipfile(zip_path):
        raise ReleaseError(f"Release ZIP is not a valid zip archive: {zip_path}")
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        bad = zf.testzip()
        if bad is not None:
            raise ReleaseError(f"Corrupt member in release ZIP: {bad}")
    missing = [m for m in REQUIRED_ZIP_MEMBERS if m not in names]
    if missing:
        raise ReleaseError(f"Release ZIP missing required members: {missing}")


def write_checksum(zip_path: Path) -> Path:
    checksum_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    digest = sha256_file(zip_path)
    checksum_path.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
    return checksum_path


def write_release_manifest(zip_path: Path, dist_dir: Path) -> Path:
    manifest = {
        "schema_version": "1.0.0",
        "version": VERSION,
        "minimum_blender_version": MINIMUM_BLENDER_VERSION,
        "maximum_blender_version_exclusive": None,
        "artifacts": {
            "extension": {
                "filename": zip_path.name,
                "url": f"{RELEASE_URL_BASE}/{zip_path.name}",
                "sha256": sha256_file(zip_path),
                "size": zip_path.stat().st_size,
            }
        },
    }
    manifest_path = dist_dir / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def validate_release_manifest(manifest_path: Path, schema_path: Path) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise ReleaseError(
            "jsonschema is required to validate the release manifest; install it first."
        ) from exc

    if not schema_path.is_file():
        raise ReleaseError(f"Release manifest schema missing: {schema_path}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(manifest, schema)
    except jsonschema.exceptions.ValidationError as exc:
        raise ReleaseError(f"Release manifest schema validation failed: {exc.message}") from exc


def build_release(root: Path, dist_dir: Path | None = None) -> dict[str, Path]:
    """Produce all release artifacts; raise ReleaseError on any failure."""
    dist = dist_dir if dist_dir is not None else root / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    zip_path = dist / f"{PACKAGE_NAME}-{VERSION}.zip"

    build_zip(root, zip_path)
    verify_zip(zip_path)
    checksum_path = write_checksum(zip_path)
    manifest_path = write_release_manifest(zip_path, dist)
    validate_release_manifest(manifest_path, root / "schemas" / "release-manifest.schema.json")

    for artifact in (zip_path, checksum_path, manifest_path):
        if not artifact.is_file() or artifact.stat().st_size == 0:
            raise ReleaseError(f"Expected artifact missing or empty: {artifact}")

    return {"zip": zip_path, "sha256": checksum_path, "manifest": manifest_path}


def main() -> int:
    try:
        artifacts = build_release(REPO_ROOT)
    except ReleaseError as exc:
        print(f"release_artifacts: FAILED: {exc}", file=sys.stderr)
        return 1
    for kind, path in artifacts.items():
        print(f"release_artifacts: {kind}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
