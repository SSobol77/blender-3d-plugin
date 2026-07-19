"""Production package initialization with safe Blender import."""

from __future__ import annotations

from blender_mobile_3d.version import VERSION

__version__ = VERSION

try:  # pragma: no cover
    import bpy  # type: ignore
except Exception:
    bpy = None  # type: ignore[assignment]

__all__ = ["__version__"]
