"""Access to the Blender Python runtime with a clear failure mode."""

from __future__ import annotations

from typing import Any


def require_bpy() -> Any:
    """Return the ``bpy`` module or raise a descriptive error outside Blender."""
    try:
        import bpy
    except ImportError as exc:
        raise RuntimeError(
            "The Blender Python runtime (bpy) is unavailable; run this operation inside Blender."
        ) from exc
    return bpy
