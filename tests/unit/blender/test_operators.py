"""Mocked Blender tests for operators, UI registration, and exporters."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest


def _make_mesh_obj(name: str, obj_type: str = "MESH") -> SimpleNamespace:
    def _fresh_data() -> SimpleNamespace:
        return SimpleNamespace(
            materials=[],
            uv_layers=[],
            shape_keys=None,
            polygons=[SimpleNamespace(vertices=(0, 1, 2))],
            vertices=[0, 1, 2],
            edges=[0, 1, 2],
            loop_triangles=None,
        )

    source = SimpleNamespace(name=name, type=obj_type)
    source.data = _fresh_data()
    source.data.copy = _fresh_data
    source.modifiers = _modifier_list()
    source.matrix_world = SimpleNamespace(is_identity=True)

    def copy() -> SimpleNamespace:
        new = SimpleNamespace(name=source.name, type=source.type)
        new.data = _fresh_data()
        new.data.copy = _fresh_data
        new.modifiers = _modifier_list()
        new.matrix_world = SimpleNamespace(is_identity=True)
        return new

    source.copy = copy
    return source


class _modifier_list(list):
    def new(self, name: str, type: str) -> SimpleNamespace:  # noqa: A002
        mod = SimpleNamespace(name=name, type=type, ratio=1.0, object=None)
        self.append(mod)
        return mod


def test_register_addon_idempotent(fake_bpy: Any) -> None:
    from blender_mobile_3d.operators.blender_ui import register_addon, unregister_addon

    register_addon()
    assert len(fake_bpy.registered_classes) == 4
    assert hasattr(fake_bpy.types.Scene, "mobile_3d_target")

    # A second register call must not duplicate registrations.
    register_addon()
    assert len(fake_bpy.registered_classes) == 4

    unregister_addon()
    assert len(fake_bpy.registered_classes) == 0
    assert not hasattr(fake_bpy.types.Scene, "mobile_3d_target")

    # A second unregister call must be a clean no-op.
    unregister_addon()
    assert len(fake_bpy.registered_classes) == 0


def test_operator_panel_classes(fake_bpy: Any) -> None:
    from blender_mobile_3d.operators.blender_ui import (
        MOBILE_3D_OT_analyze,
        MOBILE_3D_OT_export,
        MOBILE_3D_OT_generate_lod,
        MOBILE_3D_PT_panel,
    )

    assert issubclass(MOBILE_3D_OT_analyze, fake_bpy.types.Operator)
    assert issubclass(MOBILE_3D_OT_export, fake_bpy.types.Operator)
    assert issubclass(MOBILE_3D_OT_generate_lod, fake_bpy.types.Operator)
    assert issubclass(MOBILE_3D_PT_panel, fake_bpy.types.Panel)


def test_analyze_operator_reports_metrics(fake_bpy: Any) -> None:
    from blender_mobile_3d.operators.blender_ui import MOBILE_3D_OT_analyze

    scene = fake_bpy.context.scene
    scene.objects.append(_make_mesh_obj("Hero"))
    scene.mobile_3d_preset_path = ""
    scene.mobile_3d_report = ""

    op = MOBILE_3D_OT_analyze()
    result = op.execute(fake_bpy.context)
    assert result == {"FINISHED"}
    payload = json.loads(scene.mobile_3d_report)
    assert payload["metrics"]["triangle_count"] == 1
    assert payload["passed"] is True


def test_analyze_operator_bad_preset_cancels(fake_bpy: Any, tmp_path: Path) -> None:
    from blender_mobile_3d.operators.blender_ui import MOBILE_3D_OT_analyze

    scene = fake_bpy.context.scene
    scene.mobile_3d_preset_path = str(tmp_path / "missing_preset.json")

    op = MOBILE_3D_OT_analyze()
    assert op.execute(fake_bpy.context) == {"CANCELLED"}
    assert op.reports and op.reports[0][0] == {"ERROR"}


def test_lod_operator(fake_bpy: Any) -> None:
    from blender_mobile_3d.operators.blender_ui import MOBILE_3D_OT_generate_lod

    scene = fake_bpy.context.scene
    scene.objects.append(_make_mesh_obj("Player"))
    scene.mobile_3d_active_object = "Player"

    op = MOBILE_3D_OT_generate_lod()
    assert op.execute(fake_bpy.context) == {"FINISHED"}
    names = {o.name for o in scene.objects}
    assert {"Player_LOD0", "Player_LOD1", "Player_LOD2", "Player_LOD3"} <= names


def test_lod_operator_missing_object_cancels(fake_bpy: Any) -> None:
    from blender_mobile_3d.operators.blender_ui import MOBILE_3D_OT_generate_lod

    fake_bpy.context.scene.mobile_3d_active_object = "Ghost"
    op = MOBILE_3D_OT_generate_lod()
    assert op.execute(fake_bpy.context) == {"CANCELLED"}


def test_export_operator(fake_bpy: Any, tmp_path: Path) -> None:
    from blender_mobile_3d.operators.blender_ui import MOBILE_3D_OT_export

    scene = fake_bpy.context.scene
    scene.mobile_3d_target = "godot"
    scene.mobile_3d_output_dir = str(tmp_path)

    op = MOBILE_3D_OT_export()
    assert op.execute(fake_bpy.context) == {"FINISHED"}
    exported = tmp_path / "godot_asset.glb"
    assert exported.is_file() and exported.stat().st_size > 0


def test_export_operator_failure_cancels(fake_bpy: Any, tmp_path: Path) -> None:
    from blender_mobile_3d.operators.blender_ui import MOBILE_3D_OT_export

    def _boom(**kwargs: Any) -> None:
        raise RuntimeError("export backend unavailable")

    fake_bpy.ops.export_scene.gltf = _boom
    scene = fake_bpy.context.scene
    scene.mobile_3d_target = "godot"
    scene.mobile_3d_output_dir = str(tmp_path)

    op = MOBILE_3D_OT_export()
    assert op.execute(fake_bpy.context) == {"CANCELLED"}
    assert op.reports and op.reports[0][0] == {"ERROR"}


def test_panel_draw(fake_bpy: Any) -> None:
    from blender_mobile_3d.operators.blender_ui import MOBILE_3D_PT_panel

    scene = fake_bpy.context.scene
    scene.mobile_3d_report = "{}"
    panel = MOBILE_3D_PT_panel()
    panel.layout = MagicMock()
    panel.draw(fake_bpy.context)
    assert panel.layout.operator.call_count == 3


def test_generate_lod_function(fake_bpy: Any) -> None:
    from blender_mobile_3d.operators.generate_lod import generate_lod

    fake_bpy.context.scene.objects.append(_make_mesh_obj("Quad"))
    chain = generate_lod("Quad")
    assert chain == ["Quad_LOD0", "Quad_LOD1", "Quad_LOD2", "Quad_LOD3"]


def test_generate_lod_missing_raises(fake_bpy: Any) -> None:
    from blender_mobile_3d.operators.generate_lod import generate_lod

    with pytest.raises(ValueError, match="Mesh object not found"):
        generate_lod("Nope")


def test_export_for_target_unity(fake_bpy: Any, tmp_path: Path) -> None:
    from blender_mobile_3d.operators.export import export_for_target

    out = export_for_target("unity", tmp_path)
    assert out["target"] == "unity"
    assert out["format"] == "FBX"
    assert Path(out["path"]).is_file()


def test_export_for_target_glb(fake_bpy: Any, tmp_path: Path) -> None:
    from blender_mobile_3d.operators.export import export_for_target

    out = export_for_target("godot", tmp_path)
    assert out["format"] == "GLB"
    assert Path(out["path"]).is_file()


def test_prepare_scene_sets_units(fake_bpy: Any) -> None:
    from blender_mobile_3d.operators.prepare_scene import prepare_scene

    res = prepare_scene()
    assert res["unit_scale"] == 0.01
    assert res["engine"] == "BLENDER_EEVEE_NEXT"
    assert fake_bpy.context.scene.unit_settings.system == "METRIC"


def test_auto_rig_character(fake_bpy: Any) -> None:
    from blender_mobile_3d.operators.auto_rig import auto_rig_character

    mesh = _make_mesh_obj("Body")
    fake_bpy.context.scene.objects.append(mesh)
    result = auto_rig_character("HeroRig", mesh_object="Body")
    assert result["armature"] == "HeroRig"
    assert result["bind_mesh"] == "Body"
    assert mesh.parent.name == "HeroRig"


def test_exporters_dispatch(fake_bpy: Any, tmp_path: Path) -> None:
    from blender_mobile_3d.exporters.base import EXPORTERS, get_exporter

    for target in EXPORTERS:
        result = get_exporter(target).export(None, tmp_path)
        assert result["target"] == target
        assert Path(result["path"]).is_file()


def test_get_exporter_unknown_target() -> None:
    from blender_mobile_3d.core.errors import ExportError
    from blender_mobile_3d.exporters.base import get_exporter

    with pytest.raises(ExportError, match="Unknown export target"):
        get_exporter("gamecube")


def test_register_module_helpers(fake_bpy: Any) -> None:
    import blender_mobile_3d.operators.register as _reg

    assert _reg.get_context() is fake_bpy.context
    _reg.register_addon()
    assert len(fake_bpy.registered_classes) == 4
    _reg.unregister_addon()
    assert len(fake_bpy.registered_classes) == 0


def test_operators_package_lazy_exports(fake_bpy: Any) -> None:
    import blender_mobile_3d.operators as ops

    assert callable(ops.register_addon)
    assert callable(ops.unregister_addon)
    with pytest.raises(AttributeError):
        _ = ops.does_not_exist
