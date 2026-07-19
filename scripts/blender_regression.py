#!/usr/bin/env python3
"""Headless Blender regression suite for the release add-on ZIP.

Run inside Blender:

    blender --background --factory-startup \
        --python scripts/blender_regression.py -- \
        --zip dist/blender_mobile_3d-1.0.0.zip --output /path/to/workdir

Covers: installation from the canonical ZIP, enablement, repeated
register/unregister, triangle/quad/pentagon measurement, LOD generation,
validation, manifest generation, GLB and FBX export, non-empty outputs.

Prints ``REGRESSION_RESULT: PASS`` and exits 0 only when every check
passes; any failure prints ``REGRESSION_RESULT: FAIL`` and exits 1.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

import bpy

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(passed), detail))
    status = "ok" if passed else "FAIL"
    print(f"check[{status}] {name} {detail}".rstrip())


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(prog="blender_regression")
    parser.add_argument("--zip", required=True, help="Path to the release add-on ZIP")
    parser.add_argument("--output", required=True, help="Writable working directory")
    return parser.parse_args(argv)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def make_ngon(name: str, sides: int) -> bpy.types.Object:
    """Create a single flat n-gon mesh object with ``sides`` vertices."""
    import math

    mesh = bpy.data.meshes.new(name)
    verts = [
        (math.cos(2 * math.pi * i / sides), math.sin(2 * math.pi * i / sides), 0.0)
        for i in range(sides)
    ]
    mesh.from_pydata(verts, [], [tuple(range(sides))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def run(args: argparse.Namespace) -> None:
    from blender_mobile_3d.config.models import Preset
    from blender_mobile_3d.core.pipeline import Pipeline
    from blender_mobile_3d.core.scene import measure_scene
    from blender_mobile_3d.core.validation import ValidationEngine
    from blender_mobile_3d.operators.export import export_for_target
    from blender_mobile_3d.operators.generate_lod import generate_lod

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    # Repeated enable/disable cycles must stay stable.
    for _ in range(2):
        bpy.ops.preferences.addon_disable(module="blender_mobile_3d")
        bpy.ops.preferences.addon_enable(module="blender_mobile_3d")
    check(
        "repeated_register_unregister",
        "blender_mobile_3d" in bpy.context.preferences.addons,
    )
    check(
        "scene_properties_registered",
        hasattr(bpy.types.Scene, "mobile_3d_target"),
    )

    # Known-topology measurement: triangle=1, quad=2, pentagon=3 triangles.
    clear_scene()
    make_ngon("Tri", 3)
    make_ngon("Quad", 4)
    make_ngon("Penta", 5)
    metrics = measure_scene(bpy.context.scene)
    check(
        "triangle_quad_pentagon_measurement",
        metrics["triangle_count"] == 6 and metrics["mesh_count"] == 3,
        f"triangle_count={metrics['triangle_count']} mesh_count={metrics['mesh_count']}",
    )

    # LOD generation on the quad.
    chain = generate_lod("Quad")
    names = {o.name for o in bpy.context.scene.objects}
    check(
        "lod_generation",
        chain == ["Quad_LOD0", "Quad_LOD1", "Quad_LOD2", "Quad_LOD3"]
        and set(chain).issubset(names),
        f"chain={chain}",
    )

    # Validation must flag overage and pass within budget.
    engine_fail = ValidationEngine(limits={"tri_limit": 2})
    issues = engine_fail.validate_metrics(measure_scene(bpy.context.scene))
    check(
        "validation_flags_overage",
        any(i["code"] == "TRIANGLE_OVERAGE" for i in issues),
        f"issues={[i['code'] for i in issues]}",
    )
    engine_pass = ValidationEngine(limits={"tri_limit": 100000})
    check(
        "validation_passes_within_budget",
        engine_pass.validate_metrics(measure_scene(bpy.context.scene)) == [],
    )

    # Pipeline: manifest generation plus real GLB export.
    pipeline_dir = output / "pipeline_godot"
    preset = Preset()
    result = Pipeline(preset, output_dir=pipeline_dir).run(bpy.context, dry_run=False)
    manifest_path = pipeline_dir / "manifest.json"
    glb_path = pipeline_dir / "godot_asset.glb"
    manifest_ok = False
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_ok = (
            manifest["schema_version"] == "1.0.0"
            and manifest["target"] == "godot"
            and manifest["metrics"]["triangle_count"] > 0
        )
    check("manifest_generation", manifest_ok, str(manifest_path))
    check(
        "glb_export_non_empty",
        glb_path.is_file() and glb_path.stat().st_size > 0,
        f"size={glb_path.stat().st_size if glb_path.is_file() else 'missing'}",
    )
    check("pipeline_artifacts_reported", len(result.artifacts) >= 2)

    # Direct FBX export for the Unity target.
    fbx_dir = output / "unity_export"
    fbx_result = export_for_target("unity", fbx_dir)
    fbx_path = Path(fbx_result["path"])
    check(
        "fbx_export_non_empty",
        fbx_path.is_file() and fbx_path.stat().st_size > 0,
        f"size={fbx_path.stat().st_size if fbx_path.is_file() else 'missing'}",
    )


def main() -> int:
    try:
        args = parse_args()
        zip_path = Path(args.zip).resolve()
        if not zip_path.is_file():
            raise RuntimeError(f"Release ZIP not found: {zip_path}")

        # Installation from the canonical ZIP, then enablement.
        bpy.ops.preferences.addon_install(overwrite=True, filepath=str(zip_path))
        bpy.ops.preferences.addon_enable(module="blender_mobile_3d")
        check(
            "addon_installed_and_enabled",
            "blender_mobile_3d" in bpy.context.preferences.addons,
        )

        run(args)
    except Exception:
        traceback.print_exc()
        print("REGRESSION_RESULT: FAIL")
        return 1

    failed = [name for name, passed, _ in CHECKS if not passed]
    if failed:
        print(f"failed checks: {failed}")
        print("REGRESSION_RESULT: FAIL")
        return 1
    print(f"all {len(CHECKS)} checks passed")
    print("REGRESSION_RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
