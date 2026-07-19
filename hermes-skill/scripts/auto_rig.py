# auto_rig.py
# Prosty autorig dla postaci mobilnych

import bpy

def auto_rig_character(obj_name="Character"):
    arm_data = bpy.data.armatures.new("MobileRig")
    rig = bpy.data.objects.new("MobileRig", arm_data)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')

    bones = [
        ("root", (0, 0, 0)),
        ("spine", (0, 0, 1)),
        ("head", (0, 0, 2)),
        ("arm_L", (-1, 0, 1.5)),
        ("arm_R", (1, 0, 1.5)),
        ("leg_L", (-0.5, 0, 0)),
        ("leg_R", (0.5, 0, 0)),
    ]

    prev = None
    for name, pos in bones:
        bone = arm_data.edit_bones.new(name)
        bone.head = pos
        bone.tail = (pos[0], pos[1], pos[2] - 0.3)
        if prev:
            bone.parent = prev
        prev = bone

    bpy.ops.object.mode_set(mode='OBJECT')
    return rig.name

if __name__ == "__main__":
    auto_rig_character()
