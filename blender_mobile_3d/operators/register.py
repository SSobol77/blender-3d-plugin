"""Blender add-on registration helpers shared by operator modules."""

from __future__ import annotations

from typing import Any

from blender_mobile_3d.core.blender import require_bpy


def get_context() -> Any:
    """Return the live Blender context."""
    return require_bpy().context


def register_addon() -> None:
    """Register the add-on UI (delegates to the UI module)."""
    from blender_mobile_3d.operators.blender_ui import register_addon as _register

    _register()


def unregister_addon() -> None:
    """Unregister the add-on UI (delegates to the UI module)."""
    from blender_mobile_3d.operators.blender_ui import unregister_addon as _unregister

    _unregister()
