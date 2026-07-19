"""Blender Mobile 3D Plugin operators package."""

from __future__ import annotations

from typing import Any

_LAZY_UI_EXPORTS = {"register_addon", "unregister_addon"}


def __getattr__(name: str) -> Any:
    # blender_ui imports bpy at module scope; defer that import so the
    # operators package stays importable outside Blender.
    if name in _LAZY_UI_EXPORTS:
        from blender_mobile_3d.operators import blender_ui

        return getattr(blender_ui, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
