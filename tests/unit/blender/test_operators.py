"""Mocked Blender tests for operators and exporters."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest


class _Scene:
    mobile_3d_target = ""
    mobile_3d_preset_path = ""
    mobile_3d_output_dir = ""
    mobile_3d_active_object = ""
    mobile_3d_report = ""

    unit_settings = SimpleNamespace(system="METRIC", scale_length=0.01)
    render = SimpleNamespace(engine="BLENDER_EEVEE_NEXT")


class _BpyTypes:
    class Operator:
        bl_idname = ""
        bl_label = ""

    class Panel:
        bl_idname = ""
        bl_label = ""
        bl_space_type = ""
        bl_region_type = ""
        bl_category = ""

    Scene = _Scene


class _BpyProps:
    @staticmethod
    def StringProperty(**kwargs):
        pass

    @staticmethod
    def EnumProperty(**kwargs):
        pass


class _BpyUtils:
    @staticmethod
    def register_class(cls):
        pass

    @staticmethod
    def unregister_class(cls):
        pass


class _BpyOps:
    class export_scene:
        @staticmethod
        def gltf(**kwargs):
            return {"finished": True}

        @staticmethod
        def fbx(**kwargs):
            return {"finished": True}

    class preferences:
        @staticmethod
        def addon_install(**kwargs):
            return {"finished": True}

        @staticmethod
        def addon_enable(**kwargs):
            return {"finished": True}


_bpy = types.ModuleType("bpy")
_bpy.types = _BpyTypes()
_bpy.props = _BpyProps()
_bpy.utils = _BpyUtils()
_bpy.ops = _BpyOps()
_bpy.context = SimpleNamespace(
    blend_data=SimpleNamespace(filepath="/tmp/test.blend"),
    preferences=SimpleNamespace(addons={}),
    scene=_Scene(),
)
sys.modules.setdefault("bpy", _bpy)


def test_register_addon_init():
    from blender_mobile_3d.operators.blender_ui import register_addon, unregister_addon

    assert "blender_mobile_3d" not in _bpy.context.preferences.addons
    register_addon()
    assert "blender_mobile_3d" in _bpy.context.preferences.addons
    unregister_addon()


def test_operator_panel_classes():
    from blender_mobile_3d.operators.blender_ui import (
        MOBILE_3D_OT_analyze,
        MOBILE_3D_OT_export,
        MOBILE_3D_OT_generate_lod,
        MOBILE_3D_PT_panel,
    )

    assert issubclass(MOBILE_3D_OT_analyze, _bpy.types.Operator)
    assert issubclass(MOBILE_3D_PT_panel, _bpy.types.Panel)


def _make_obj(name, obj_type="MESH"):
    source = SimpleNamespace(name=name, type=obj_type)

    def copy():
        new = SimpleNamespace(name=source.name, type=source.type)
        new.data = SimpleNamespace(materials=[], uv_layers=[], shape_keys=None)
        new.modifiers = []
        new.matrix_world = SimpleNamespace(is_identity=True)
        return new

    source.copy = copy
    source.data = SimpleNamespace(materials=[], uv_layers=[], shape_keys=None)
    source.modifiers = []
    source.matrix_world = SimpleNamespace(is_identity=True)
    return source


def _fake_scene():
    cube = _make_obj("Player", "MESH")
    return SimpleNamespace(
        objects=[cube],
        collection=SimpleNamespace(objects=lambda: [cube]),
    )


def test_lod_chain(monkeypatch):
    import blender_mobile_3d.operators.generate_lod as g
    monkeypatch.setattr("blender_mobile_3d.operators.register.get_context", lambda: SimpleNamespace(scene=_fake_scene()))
    chain = g.generate_lod("Player")
    assert isinstance(chain, list)


def test_export_unity(monkeypatch, tmp_path: Path):
    import blender_mobile_3d.operators.export as e
    monkeypatch.setattr("blender_mobile_3d.operators.register.get_context", lambda: SimpleNamespace(scene=_fake_scene()))
    out = e.export_for_target("unity", tmp_path)
    assert out["target"] == "unity"
    assert out["format"] == "FBX"


def test_prepare_scene_sets_units(monkeypatch):
    from blender_mobile_3d.operators.prepare_scene import prepare_scene

    ctx = SimpleNamespace(scene=_fake_scene())
    import blender_mobile_3d.operators.register as _reg
    monkeypatch.setattr(_reg, "get_context", lambda: ctx)
    res = prepare_scene()
    assert res["unit_scale"] == 0.01
    assert res["engine"] == "BLENDER_EEVEE_NEXT"
