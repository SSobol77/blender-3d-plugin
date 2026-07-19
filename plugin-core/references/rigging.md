# rigging.md

## Ograniczenia mobilne

- Maks 60 kosci na postac (UWAGA na Unity/Android)
- Blend shapes <= 8
- Animacje: bake all constraints
- FPS: 30 lub 60 w zaleznosci od stacku

## Auto-rig (przyklad bpy)

```python
import bpy

arm = bpy.data.armatures.new("Rig")
rig = bpy.data.objects.new("Rig", arm)
bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')

# Proste hierarchie
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
    bone = arm.edit_bones.new(name)
    bone.head = pos
    bone.tail = (pos[0], pos[1], pos[2] - 0.3)
    if prev:
        bone.parent = prev
    prev = bone

bpy.ops.object.mode_set(mode='OBJECT')
```
