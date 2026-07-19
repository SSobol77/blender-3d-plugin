"""Safe path handling and project-root detection."""

from __future__ import annotations

import os
from pathlib import Path

from blender_mobile_3d.core.errors import PathSafetyError


def project_root_from_blend() -> Path:
    """Return current blend file directory or cwd."""
    try:
        import bpy  # type: ignore
    except Exception:
        return Path.cwd()
    path = bpy.context.blend_data.filepath  # type: ignore[attr-defined]
    if path:
        return Path(path).resolve().parent
    return Path.cwd()


def safe_join(base: Path, child: str) -> Path:
    """Join child without escaping base."""
    target = base / child
    try:
        target.relative_to(base.resolve())
    except ValueError:
        raise PathSafetyError("Output path escapes project root")
    return target


def default_output_dir(preset: dict) -> Path:
    root = project_root_from_blend()
    rel = preset.get("paths", {}).get("output_relative", "export/mobile")
    return safe_join(root, rel)
