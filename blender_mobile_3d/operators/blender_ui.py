"""Blender add-on operators and panels."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import bpy

from blender_mobile_3d.config.loader import load_preset
from blender_mobile_3d.config.models import Preset
from blender_mobile_3d.core.scene import measure_scene
from blender_mobile_3d.core.validation import ValidationEngine
from blender_mobile_3d.operators.export import export_for_target
from blender_mobile_3d.operators.generate_lod import generate_lod


class MOBILE_3D_OT_analyze(bpy.types.Operator):
    bl_idname = "mobile_3d.analyze"
    bl_label = "Analyze Scene"
    bl_description = "Collect mobile asset metrics from the current scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        preset_path = context.scene.mobile_3d_preset_path
        try:
            if preset_path:
                preset = Preset.from_dict(load_preset(preset_path))
            else:
                preset = Preset()
            metrics = measure_scene(context.scene)
            engine = ValidationEngine(limits=asdict(preset.limits))
            issues = engine.validate_metrics(metrics)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        payload = {"metrics": metrics, "issues": issues, "passed": not issues}
        context.scene.mobile_3d_report = json.dumps(payload)
        self.report({"INFO"}, f"Analysis complete: {context.scene.mobile_3d_report[:120]}")
        return {"FINISHED"}


class MOBILE_3D_OT_generate_lod(bpy.types.Operator):
    bl_idname = "mobile_3d.generate_lod"
    bl_label = "Generate LOD"
    bl_description = "Generate deterministic LOD chain copies"

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj_name = context.scene.mobile_3d_active_object
        try:
            chain = generate_lod(obj_name)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.report({"INFO"}, f"LOD chain: {', '.join(chain)}")
        return {"FINISHED"}


class MOBILE_3D_OT_export(bpy.types.Operator):
    bl_idname = "mobile_3d.export"
    bl_label = "Export"
    bl_description = "Export the active asset for the selected target"

    def execute(self, context: bpy.types.Context) -> set[str]:
        target = context.scene.mobile_3d_target
        export_dir = Path(bpy.path.abspath(context.scene.mobile_3d_output_dir))
        try:
            result = export_for_target(target, export_dir)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.report({"INFO"}, f"Exported: {result['path']}")
        return {"FINISHED"}


class MOBILE_3D_PT_panel(bpy.types.Panel):
    bl_label = "Mobile 3D Assets"
    bl_idname = "MOBILE_3D_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Mobile 3D"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "mobile_3d_target")
        layout.prop(scene, "mobile_3d_preset_path")
        layout.prop(scene, "mobile_3d_output_dir")
        layout.prop(scene, "mobile_3d_active_object")
        layout.operator("mobile_3d.analyze")
        layout.operator("mobile_3d.generate_lod")
        layout.operator("mobile_3d.export")
        if scene.get("mobile_3d_report"):
            layout.label(text="Last analysis:")
            layout.label(text=str(scene.get("mobile_3d_report"))[:120])


classes = [
    MOBILE_3D_OT_analyze,
    MOBILE_3D_OT_generate_lod,
    MOBILE_3D_OT_export,
    MOBILE_3D_PT_panel,
]

_SCENE_PROPERTIES = (
    "mobile_3d_target",
    "mobile_3d_preset_path",
    "mobile_3d_output_dir",
    "mobile_3d_active_object",
    "mobile_3d_report",
)

_registered = False


def register_addon() -> None:
    """Register classes and scene properties; safe to call repeatedly."""
    global _registered
    if _registered:
        return

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.mobile_3d_target = bpy.props.EnumProperty(  # type: ignore[attr-defined]
        name="Target",
        items=[
            ("godot", "Godot", "Godot GLB"),
            ("unity", "Unity", "Unity FBX"),
            ("unreal", "Unreal", "Unreal GLB"),
            ("flutter", "Flutter", "Flutter GLB"),
            ("kotlin", "Kotlin", "Android GLB"),
        ],
        default="godot",
    )
    bpy.types.Scene.mobile_3d_preset_path = bpy.props.StringProperty(  # type: ignore[attr-defined]
        name="Preset",
        subtype="FILE_PATH",
        default="",
    )
    bpy.types.Scene.mobile_3d_output_dir = bpy.props.StringProperty(  # type: ignore[attr-defined]
        name="Output",
        subtype="DIR_PATH",
        default="//export/mobile",
    )
    bpy.types.Scene.mobile_3d_active_object = bpy.props.StringProperty(  # type: ignore[attr-defined]
        name="Active Object",
        default="",
    )
    bpy.types.Scene.mobile_3d_report = bpy.props.StringProperty(  # type: ignore[attr-defined]
        name="Report",
        default="",
    )
    _registered = True


def unregister_addon() -> None:
    """Remove classes and scene properties; safe to call repeatedly."""
    global _registered
    if not _registered:
        return

    for prop in _SCENE_PROPERTIES:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    _registered = False
