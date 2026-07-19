"""LOD generation operator with deterministic copying and naming."""

from __future__ import annotations

from typing import Any

import blender_mobile_3d.operators.register as _reg


def generate_lod(obj_name: str, lod_ratios: tuple[float, ...] = (0.6, 0.3, 0.15)) -> list[str]:
    context = _reg.get_context()
    scene = context.scene
    obj = next((o for o in scene.objects if o.name == obj_name and o.type == "MESH"), None)
    if obj is None:
        raise ValueError(f"Mesh object not found: {obj_name}")

    chain = [obj.name]
    base_name = obj.name
    if base_name.endswith("_LOD0"):
        base_name = base_name[: -len("_LOD0")]

    source = obj
    for i, ratio in enumerate(lod_ratios, start=1):
        lod = source.copy()
        lod.data = source.data.copy()
        lod.name = f"{base_name}_LOD{i}"
        scene.collection.objects.link(lod)
        mod = lod.modifiers.new(name="Decimate", type="DECIMATE")
        mod.ratio = max(0.0, min(float(ratio), 1.0))
        chain.append(lod.name)

    obj.name = f"{base_name}_LOD0"
    return chain


if __name__ == "__main__":
    print(generate_lod("Cube"))
