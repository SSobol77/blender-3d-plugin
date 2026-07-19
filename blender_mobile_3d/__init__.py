"""Production package initialization with safe Blender import."""

from __future__ import annotations

from blender_mobile_3d.version import VERSION

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

__all__ = ["__version__", "register", "unregister"]
