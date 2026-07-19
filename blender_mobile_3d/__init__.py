"""Blender Mobile 3D production package and add-on entrypoint."""

from __future__ import annotations

from blender_mobile_3d.version import VERSION

bl_info = {
    "name": "Blender Mobile 3D",
    "author": "SSobol77",
    "version": (1, 0, 0),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > Mobile 3D",
    "description": "Prepare, validate, optimize, and export mobile 3D assets.",
    "category": "Import-Export",
    "doc_url": "https://github.com/SSobol77/blender-3d-plugin",
    "license": "GPL-2.0-only",
}

__version__ = VERSION


def register() -> None:
    """Register the add-on inside Blender.

    Raises a descriptive error when the Blender runtime is unavailable.
    """
    try:
        from blender_mobile_3d.operators.blender_ui import register_addon
    except ImportError as exc:
        raise RuntimeError(
            "bpy is unavailable; this add-on can only be registered inside Blender."
        ) from exc
    register_addon()


def unregister() -> None:
    """Unregister the add-on inside Blender; idempotent and symmetric."""
    try:
        from blender_mobile_3d.operators.blender_ui import unregister_addon
    except ImportError:
        # Registration never happened (bpy unavailable), so there is
        # nothing to tear down; unregister stays idempotent.
        return
    unregister_addon()


__all__ = ["__version__", "register", "unregister", "bl_info"]
