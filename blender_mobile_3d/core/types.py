"""Type aliases for Blender runtime context objects."""

from __future__ import annotations

if False:  # pragma: no cover
    import bpy as _bpy  # noqa: F401

    Context = _bpy.types.Context
    Scene = _bpy.types.Scene

    try:
        from bpy.types import Context as ContextType  # type: ignore
        from bpy.types import Scene as SceneType  # type: ignore

        Context = ContextType  # type: ignore[misc,assignment]
        Scene = SceneType  # type: ignore[misc,assignment]
    except Exception:
        Scene = object  # type: ignore[misc,assignment]
else:
    Context = object  # type: ignore[misc,assignment]
    Scene = object  # type: ignore[misc,assignment]

__all__ = ["Context", "Scene"]
