import bpy, sys

print("addons=", sorted(bpy.context.preferences.addons.keys()))
sys.stdout.flush()
