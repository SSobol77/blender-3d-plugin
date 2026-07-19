"""Production package initialization with safe Blender import."""

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

try:  # pragma: no cover
    import bpy  # type: ignore
except Exception:
    bpy = None  # type: ignore[assignment]

if bpy is not None:
    try:
        from blender_mobile_3d.operators.blender_ui import (  # type: ignore
            unregister_addon,
            register_addon,
        )

        def register() -> None:
            register_addon()

        def unregister() -> None:
            unregister_addon()
    except Exception:

        def register() -> None:  # type: ignore
            raise RuntimeError("Blender UI registration unavailable.")

        def unregister() -> None:  # type: ignore
            pass
else:

    def register() -> None:  # type: ignore
        raise RuntimeError("bpy is unavailable; this package requires Blender.")

    def unregister() -> None:  # type: ignore
        pass


__all__ = ["__version__", "register", "unregister", "bl_info"]
