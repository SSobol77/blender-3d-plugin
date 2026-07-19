"""Scene preparation operator and script entrypoint."""

from __future__ import annotations

from typing import Any

import blender_mobile_3d.operators.register as _reg


def prepare_scene(unit_scale: float = 0.01, engine: str = "BLENDER_EEVEE_NEXT") -> dict[str, Any]:
    context = _reg.get_context()
    scene = context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = unit_scale
    scene.render.engine = engine
    return {"unit_scale": unit_scale, "engine": engine}
