# export_mobile.py
# Eksport assetow do wybranego stacku mobilnego

import bpy, os, json, zipfile

EXPORT_MAP = {
    "godot": ("/tmp/godot_mobile", "GLB"),
    "unity": ("/tmp/unity_mobile", "FBX"),
    "unreal": ("/tmp/ue5_mobile", "GLB"),
    "flutter": ("/tmp/flutter_mobile", "GLB"),
    "kotlin": ("/tmp/kotlin_mobile", "GLB"),
}

def export_for_stack(stack, preset_path=None):
    if stack not in EXPORT_MAP:
        raise ValueError(f"Nieznany stack: {stack}")

    export_dir, fmt = EXPORT_MAP[stack]
    os.makedirs(export_dir, exist_ok=True)

    filename = os.path.join(export_dir, f"{stack}_asset.glb" if fmt == "GLB" else f"{stack}_asset.fbx")

    if fmt == "GLB":
        bpy.ops.export_scene.gltf(filepath=filename, export_format="GLB")
    else:
        bpy.ops.export_scene.fbx(filepath=filename, use_selection=False, apply_scale_options="FBX_SCALE_ALL")

    manifest = {"stack": stack, "export_format": fmt, "filename": os.path.basename(filename)}
    manifest_path = os.path.join(export_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # optional zip
    zip_path = os.path.join(export_dir, f"{stack}_mobile.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(export_dir):
            for file in files:
                if file.endswith((".glb", ".fbx", ".json")):
                    z.write(os.path.join(root, file), file)

    return filename, manifest_path, zip_path

if __name__ == "__main__":
    export_for_stack("godot")
