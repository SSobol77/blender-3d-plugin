"""Auto-rig operator with explicit mesh binding and mobile-safe hierarchy."""

from __future__ import annotations

from typing import Any

import blender_mobile_3d.operators.register as _reg
from blender_mobile_3d.core.blender import require_bpy


def auto_rig_character(obj_name: str, mesh_object: str | None = None) -> dict[str, Any]:
    bpy = require_bpy()
    context = _reg.get_context()
    scene = context.scene

    arm_data = bpy.data.armatures.new(obj_name or "MobileRig")
    rig = bpy.data.objects.new(arm_data.name, arm_data)
    scene.collection.objects.link(rig)
    context.view_layer.objects.active = rig

    bpy.ops.object.mode_set(mode="EDIT")
    bones = [
        ("root", (0.0, 0.0, 0.0), (0.0, 0.0, -0.2)),
        ("spine", (0.0, 0.0, 0.1), (0.0, 0.0, 0.9)),
        ("head", (0.0, 0.0, 0.9), (0.0, 0.0, 1.1)),
        ("arm_L", (-0.3, 0.0, 0.9), (-0.5, 0.0, 0.7)),
        ("arm_R", (0.3, 0.0, 0.9), (0.5, 0.0, 0.7)),
        ("leg_L", (-0.2, 0.0, 0.0), (-0.2, 0.0, -0.5)),
        ("leg_R", (0.2, 0.0, 0.0), (0.2, 0.0, -0.5)),
    ]

    prev = None
    for name, head, tail in bones:
        bone = arm_data.edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        bone.parent = prev
        prev = bone

    bpy.ops.object.mode_set(mode="OBJECT")

    mesh = next((o for o in scene.objects if o.name == mesh_object), None)
    if mesh is not None and mesh.type == "MESH":
        armature_mod = mesh.modifiers.new(name="Armature", type="ARMATURE")
        armature_mod.object = rig
        mesh.parent = rig

    return {"armature": rig.name, "bind_mesh": getattr(mesh, "name", None)}
