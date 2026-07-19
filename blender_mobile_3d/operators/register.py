"""Blender add-on class registration helpers."""

from __future__ import annotations

from typing import Any

classes: list[Any] = []


def register_addon() -> None:
    pass


def unregister_addon() -> None:
    pass


def get_context() -> Any:
    try:
        import bpy  # type: ignore

        return bpy.context
    except Exception as exc:
        raise RuntimeError("Blender context is unavailable outside Blender.") from exc
