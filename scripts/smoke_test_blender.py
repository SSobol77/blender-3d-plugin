#!/usr/bin/env python3
"""Headless add-on install and registration smoke test."""

from pathlib import Path

try:
    import bpy  # type: ignore
except Exception:
    print("blender_not_available")
    raise SystemExit(0)

zip_path = str(Path("/home/astra/blender-3d-plugin/dist/blender_mobile_3d-1.0.0.zip"))
bpy.ops.preferences.addon_install(overwrite=True, filepath=zip_path)
bpy.ops.preferences.addon_enable(module="blender_mobile_3d")
print("addon_enabled=blender_mobile_3d")
