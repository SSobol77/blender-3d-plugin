# prepare_scene.py
# Staging scena, cleanup, jednostki, scale, naming

import bpy

def prepare_scene(name="asset_pack", unit_cm=True):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    bpy.context.scene.unit_settings.system = 'METRIC'
    if unit_cm:
        bpy.context.scene.unit_settings.scale_length = 0.01
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
    return True

if __name__ == "__main__":
    prepare_scene()
