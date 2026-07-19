"""Bundle exported artifacts into a deterministic ZIP."""

from __future__ import annotations

import hashlib
import os
import zipfile
from pathlib import Path


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
            if not str(resolved).startswith(str(export_dir)):
                raise ValueError(f"Member outside export dir: {resolved}")
            data = resolved.read_bytes()
            z.writestr(resolved.relative_to(export_dir).as_posix(), data)
            manifest.append(
                {
                    "filename": resolved.name,
                    "bytes": str(len(data)),
                    "sha256": sha256_file(resolved),
                }
            )
    return manifest
