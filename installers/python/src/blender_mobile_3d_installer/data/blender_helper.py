"""Blender-side helper invoked headlessly by both installer frontends.

Run as: blender --background --factory-startup --python blender_helper.py -- <json-args>

Reads a single JSON object from argv (after `--`) with an "action" key:
  - "status":    report install/enable state and version for a module
  - "install":   addon_install(overwrite) + addon_enable
  - "uninstall": addon_disable + addon_remove

Prints exactly one JSON line to stdout: {"ok": bool, ...}. This file is
kept byte-identical between installers/python and installers/npm
(enforced by a test) so both frontends drive Blender the same way.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable

import addon_utils
import bpy

# In --background mode several bpy.ops.preferences operators try to
# tag_redraw() a UI area that does not exist, raising a cosmetic
# AttributeError *after* the real state change (install/enable/disable/
# remove) already happened. Swallow only that specific, known-benign
# failure; anything else is a genuine error.
_HEADLESS_REDRAW_QUIRK = "'NoneType' object has no attribute 'tag_redraw'"


def _run_op(op: Callable[[], object]) -> None:
    try:
        op()
    except Exception as exc:  # noqa: BLE001 - re-raised unless it's the known quirk
        if _HEADLESS_REDRAW_QUIRK not in str(exc):
            raise


def _module_bl_info(module_name: str):
    for mod in addon_utils.modules():
        if mod.__name__ == module_name:
            return addon_utils.module_bl_info(mod)
    return None


def _status(module_name: str) -> dict:
    bl_info = _module_bl_info(module_name)
    installed = bl_info is not None
    _loaded_default, loaded_state = addon_utils.check(module_name)
    version = None
    if bl_info is not None:
        version = ".".join(str(part) for part in bl_info.get("version", ()))
    return {
        "ok": True,
        "installed": installed,
        "enabled": bool(loaded_state),
        "version": version,
    }


def _install(module_name: str, zip_path: str, overwrite: bool) -> dict:
    try:
        _run_op(lambda: bpy.ops.preferences.addon_install(overwrite=overwrite, filepath=zip_path))
        _run_op(lambda: bpy.ops.preferences.addon_enable(module=module_name))
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as JSON
        return {"ok": False, "error": str(exc)}
    return _status(module_name)


def _uninstall(module_name: str) -> dict:
    bl_info = _module_bl_info(module_name)
    if bl_info is None:
        return {"ok": True, "installed": False, "enabled": False, "version": None}
    try:
        _run_op(lambda: bpy.ops.preferences.addon_disable(module=module_name))
        _run_op(lambda: bpy.ops.preferences.addon_remove(module=module_name))
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as JSON
        return {"ok": False, "error": str(exc)}
    return _status(module_name)


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if not argv:
        print(json.dumps({"ok": False, "error": "missing JSON argument"}))
        return
    request = json.loads(argv[0])
    action = request.get("action")
    module_name = request.get("module", "blender_mobile_3d")

    if action == "status":
        result = _status(module_name)
    elif action == "install":
        result = _install(module_name, request["zip_path"], bool(request.get("overwrite", True)))
    elif action == "uninstall":
        result = _uninstall(module_name)
    else:
        result = {"ok": False, "error": f"unknown action: {action}"}

    print(json.dumps(result))


if __name__ == "__main__":
    main()
