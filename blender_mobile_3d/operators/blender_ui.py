"""Blender add-on operators and panels."""

from __future__ import annotations

from typing import Any

import bpy
from blender_mobile_3d import __version__
from blender_mobile_3d.config.loader import load_preset
from blender_mobile_3d.core.logging import Report
from blender_mobile_3d.operators.auto_rig import auto_rig_character
from blender_mobile_3d.operators.export import export_for_target
from blender_mobile_3d.operators.generate_lod import generate_lod
from blender_mobile_3d.operators.prepare_scene import prepare_scene


class MOBILE_3D_OT_analyze(bpy.types.Operator):
    bl_idname = "mobile_3d.analyze"
    bl_label = "Analyze Scene"
    bl_description = "Collect mobile asset metrics from the current scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        preset_path = context.scene.mobile_3d_preset_path
        try:
            preset = load_preset(preset_path)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        report = Report()
        context.scene.mobile_3d_report = str(report.to_dict())
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
        export_dir = context.scene.mobile_3d_output_dir
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


def register_addon() -> None:
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


def unregister_addon() -> None:
    del bpy.types.Scene.mobile_3d_target  # type: ignore[attr-defined]
    del bpy.types.Scene.mobile_3d_preset_path  # type: ignore[attr-defined]
    del bpy.types.Scene.mobile_3d_output_dir  # type: ignore[attr-defined]
    del bpy.types.Scene.mobile_3d_active_object  # type: ignore[attr-defined]
    del bpy.types.Scene.mobile_3d_report  # type: ignore[attr-defined]
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
