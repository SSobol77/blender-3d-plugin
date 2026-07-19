# low_poly_lod.py
# Decimate + LOD chain generator (mobile)

import bpy

def apply_lod(obj_name, lod_ratios=(0.6, 0.3, 0.15), as_linked=False):
    obj = bpy.data.objects.get(obj_name)
    if obj is None or obj.type != 'MESH':
        return []

    prev = obj
    lod_objects = [obj.name]
    for i, ratio in enumerate(lod_ratios, start=1):
        if as_linked:
            lod = obj.copy()
            lod.data = obj.data.copy()
            lod.name = f"{obj.name}_LOD{i}"
        else:
            lod = obj
            lod.name = f"{obj.name}_LOD{i}"

        mod = lod.modifiers.new(name='Decimate', type='DECIMATE')
        mod.ratio = ratio

        if not as_linked:
            lod = lod.copy()
            lod.data = lod.data.copy()
            bpy.collection.objects.link(lod)
            lod.name = f"{obj.name}_LOD{i}"

        lod_objects.append(lod.name)

    obj.name = f"{obj_name}_LOD0"
    return lod_objects

if __name__ == "__main__":
    apply_lod("Cube")
