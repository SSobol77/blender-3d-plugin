"""Bundle exported artifacts into a deterministic ZIP."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_zip(export_dir: Path, members: list[Path], zip_path: Path) -> list[dict[str, str]]:
    export_dir = export_dir.resolve()
    manifest: list[dict[str, str]] = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path in members:
            resolved = path.resolve()
            try:
                arcname = resolved.relative_to(export_dir).as_posix()
            except ValueError as exc:
                raise ValueError(f"Member outside export dir: {resolved}") from exc
            data = resolved.read_bytes()
            z.writestr(arcname, data)
            manifest.append(
                {
                    "filename": resolved.name,
                    "bytes": str(len(data)),
                    "sha256": sha256_file(resolved),
                }
            )
    return manifest


def sig_hash(path: Path) -> str:
    """Backward-compatible alias for `sha256_file`."""
    return sha256_file(path)


def write_artifact_manifest(members: list[Path]) -> dict[str, Any]:
    manifest: list[dict[str, Any]] = []
    for path in members:
        data = path.read_bytes()
        manifest.append(
            {
                "filename": path.name,
                "bytes": str(len(data)),
                "sha256": sha256_file(path),
            }
        )
    return {"artifact_count": len(manifest), "artifacts": manifest}
