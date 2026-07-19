# formats.md

## Godot

- Extension: `.glb`, `.gltf`
- Materials: PBR (Metallic + Roughness)
- Scene: Single root node recommended
- Scale: 1 Blender unit = 1 meter

## Unity

- Extension: `.fbx`, `.prefab`
- Materials: Legacy RP or URP with PBR
- Scale: 1 Blender unit = 1 unit in Unity
- Animation: baked keyframes only

## Unreal Engine 5.4

- Extension: `.glb`, `.datatable`
- Pipeline: Use glTF importer or Datasmith
- Material: Material Function mobile compatible
- Nanite: Optional, UE5 only

## Flutter

- Extension: `.glb`
- Integration: `package:three_js` or custom engine
- Size: base64 or file asset
- Naming: snake_case only

## Java / Kotlin

- Extension: `.glb`, `.obj` + `.mtl`
- Engine: jMonkeyEngine, libGDX, custom OpenGL
- Material: simple PBR or basic color
- Asset pipeline: Android Studio resources or raw assets
