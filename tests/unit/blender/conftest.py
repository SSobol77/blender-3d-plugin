"""A structured fake ``bpy`` module for operator and exporter tests."""

from __future__ import annotations

import sys
import types
from types import SimpleNamespace
from typing import Any

import pytest


class FakeScene:
    """Scene stand-in supporting attribute props and Blender's .get()."""

    def __init__(self) -> None:
        self.objects: list[Any] = []
        self.collection = SimpleNamespace(objects=SimpleNamespace(link=self.objects.append))
        self.unit_settings = SimpleNamespace(system="", scale_length=1.0)
        self.render = SimpleNamespace(engine="")
        self.actions: list[Any] = []

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class _RecordingOperator:
    bl_idname = ""
    bl_label = ""

    def __init__(self) -> None:
        self.reports: list[tuple[set[str], str]] = []

    def report(self, level: set[str], message: str) -> None:
        self.reports.append((level, message))


class _Panel:
    bl_idname = ""
    bl_label = ""
    bl_space_type = ""
    bl_region_type = ""
    bl_category = ""


def make_fake_bpy() -> types.ModuleType:
    bpy = types.ModuleType("bpy")

    registered: list[type] = []

    bpy.types = SimpleNamespace(
        Operator=_RecordingOperator,
        Panel=_Panel,
        Scene=FakeScene,
        Context=object,
    )
    bpy.props = SimpleNamespace(
        StringProperty=lambda **kwargs: None,
        EnumProperty=lambda **kwargs: None,
    )
    bpy.utils = SimpleNamespace(
        register_class=registered.append,
        unregister_class=lambda cls: registered.remove(cls),
    )
    bpy.registered_classes = registered

    def _write_stub(filepath: str = "", **kwargs: Any) -> dict[str, Any]:
        from pathlib import Path

        if filepath:
            Path(filepath).write_bytes(b"fake-export-data")
        return {"FINISHED"}

    bpy.ops = SimpleNamespace(
        export_scene=SimpleNamespace(gltf=_write_stub, fbx=_write_stub),
        object=SimpleNamespace(mode_set=lambda **kwargs: {"FINISHED"}),
    )
    bpy.path = SimpleNamespace(abspath=lambda p: p)

    def _new_armature(name: str) -> SimpleNamespace:
        arm = SimpleNamespace(name=name, edit_bones=SimpleNamespace(), bones=[])
        bones: list[SimpleNamespace] = []

        def new_bone(bone_name: str) -> SimpleNamespace:
            bone = SimpleNamespace(name=bone_name, head=None, tail=None, parent=None)
            bones.append(bone)
            return bone

        arm.edit_bones = SimpleNamespace(new=new_bone)
        arm.bones = bones
        return arm

    def _new_object(name: str, data: Any) -> SimpleNamespace:
        return SimpleNamespace(name=name, data=data, type="ARMATURE")

    bpy.data = SimpleNamespace(
        armatures=SimpleNamespace(new=_new_armature),
        objects=SimpleNamespace(new=_new_object),
        meshes=SimpleNamespace(),
    )

    scene = FakeScene()
    bpy.context = SimpleNamespace(
        scene=scene,
        blend_data=SimpleNamespace(filepath=""),
        view_layer=SimpleNamespace(objects=SimpleNamespace(active=None)),
        preferences=SimpleNamespace(addons={}),
    )
    return bpy


@pytest.fixture
def fake_bpy(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Install a fresh fake bpy and purge cached bpy-bound plugin modules."""
    bpy = make_fake_bpy()
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    for name in list(sys.modules):
        if name == "blender_mobile_3d.operators.blender_ui":
            monkeypatch.delitem(sys.modules, name)
    return bpy
