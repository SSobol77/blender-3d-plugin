"""Export operator with target-aware Bluray operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import blender_mobile_3d.operators.register as _reg


def export_for_target(target: str, output_dir: Path) -> dict[str, Any]:
    context = _reg.get_context()
    scene = context.scene
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = output_dir / f"{target}_asset.glb"
    if target == "unity":
        filename = output_dir / f"{target}_asset.fbx"

    if filename.suffix == ".glb":
        bpy.ops.export_scene.gltf(filepath=str(filename), export_format="GLB")
    else:
        bpy.ops.export_scene.fbx(
            filepath=str(filename), use_selection=False, apply_scale_options="FBX_SCALE_ALL"
        )

    return {
        "target": target,
        "format": filename.suffix.lstrip(".").upper(),
        "filename": filename.name,
        "path": str(filename),
    }


if __name__ == "__main__":
    print(export_for_target("godot", Path("/tmp/export_test")))
