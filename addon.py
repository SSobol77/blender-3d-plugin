"""Blender add-on entrypoint for Blender Mobile 3D Plugin."""

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


def register() -> None:
    from blender_mobile_3d.operators import register_addon  # noqa: F401
    register_addon()


def unregister() -> None:
    from blender_mobile_3d.operators import unregister_addon  # noqa: F401
    unregister_addon()
