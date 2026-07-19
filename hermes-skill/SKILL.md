---
name: blender-mobile-3d-plugin
description: "Produkcyjne przygotowywanie assetow 3D do gier mobilnych w Blenderze. Rozszerzenie istniejącego pluginu blender-mcp o profile eksportu do Godot, Unity, UE 5.4, Flutter oraz Java/Kotlin. Uzywa istniejącego TCP serwera blender-mcp na porcie 9876."
version: 0.1.0
author: community
license: MIT
platforms: [linux, macos, windows]
tags: [blender, 3d, mobile, godot, unity, unreal, flutter, kotlin, android, game-assets, export]
requires:
  commands: ["blender"]
  skills: ["blender-mcp"]
---

# Blender Mobile 3D Plugin

Wtyczka produkcyjna przygotowujaca assety 3D do gier mobilnych.
Jest **rozszerzeniem** pluginu `blender-mcp` i wymaga:
- Blender 5.2.0 LTS
- zainstalowanego addonu `blender_mcp_addon.py`
- uruchomionego serwera TCP na porcie 9876 wewnątrz Blendera

## Wymagania wstepne

1. Zainstaluj i uruchom Blender 5.2.0.
2. Zainstaluj `blender-mcp` zgodnie z jego instrukcja.
3. Uruchom serwer w N-panel > BlenderMCP > Start Server.
4. Sprawdz: `nc -z -w2 localhost 9876 && echo "OPEN" || echo "CLOSED"`.

## Architektura

```
Hermes Agent -> blender-mcp (TCP 9876) -> Blender bpy
       |
       +-> blender-mobile-3d-plugin (workflow + export + manifesty)
```

Pluginy `blender-mobile-3d-plugin` nie nadpisuje `blender-mcp`.
Wykorzystuje jego `execute_code` do:
- czyszczenia sceny
- tworzenia meshy
- przypisywania materiali PBR
- generowania animacji klatkowych
- konfiguracji LOD
- eksportu plikow
- tworzenia manifest/konfiguracji dla celowych stackow

## Profily eksportu (mobile-optimized)

| Profil         | Tri limit | Tex max | LOD | Font |
|----------------|-----------|---------|-----|------|
| low_poly       | 120       | 512     | 3   | Yes  |
| environment    | 300       | 1024    | 2   | No   |
| character      | 200       | 512     | 3   | Yes  |
| ui_3d          | 80        | 1024    | 1   | No   |
| fx             | 150       | 512     | 1   | No   |

## Gniazdo poleceń

Wszystkie wywolania przekazuje przez `blender-mcp` jako kod Python.
Nie używaj bezposrednio socketu z tego pluginu. Uzyj narzedzi existujacego pluginu.

## Typowe wywolania (workflow)

### 1. Przygotowanie sceny stagingowej

```python
# execute_code via blender-mcp
import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 0.01
bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
```

### 2. Profilowanie low-poly + LOD

```python
import bpy

obj = bpy.context.active_object
if obj is None:
    raise ValueError("Brak aktywnego obiektu")

# Decimate modifier
decimate = obj.modifiers.new(name='Decimate', type='DECIMATE')
decimate.ratio = 0.4

# LOD chain
lod_objects = []
for i, ratio in enumerate([0.6, 0.3, 0.15], start=1):
    lod = obj.copy()
    lod.data = obj.data.copy()
    lod.name = f"{obj.name}_LOD{i}"
    bpy.collection.objects.link(lod)

    mod = lod.modifiers.new(name='Decimate', type='DECIMATE')
    mod.ratio = ratio

    lod_objects.append(lod.name)

obj.name = f"{obj.name}_LOD0"
```

### 3. PBR materials - mobile

```python
import bpy

mat = bpy.data.materials.new(name="Mobile_PBR")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

nodes.clear()

out = nodes.new('ShaderNodeOutputMaterial')
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
tex = nodes.new('ShaderNodeTexImage')
tex.image = bpy.data.images.new(name="Diffuse", width=512, height=512)

links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])

bsdf.inputs['Roughness'].default_value = 0.7
bsdf.inputs['Metallic'].default_value = 0.0
```

### 4. Eksport do Godot

```python
import bpy, os, zipfile, json

export_dir = "/tmp/godot_export"
os.makedirs(export_dir, exist_ok=True)

bpy.ops.export_scene.gltf(
    filepath=os.path.join(export_dir, "asset.glb"),
    export_format='GLB',
    export_materials='EXPORT'
)

manifest = {"asset_id": "char_001", "tri_count": 120, "tex_max": 512}
with open(os.path.join(export_dir, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)
```

### 5. Eksport do Unity

```python
import bpy, os

export_dir = "/tmp/unity_export"
os.makedirs(export_dir, exist_ok=True)

bpy.ops.export_scene.fbx(
    filepath=os.path.join(export_dir, "asset.fbx"),
    use_selection=False,
    apply_scale_options='FBX_SCALE_ALL'
)
```

### 6. Eksport do Unreal Engine 5.4

```python
import bpy, os

export_dir = "/tmp/ue_export"
os.makedirs(export_dir, exist_ok=True)

bpy.ops.export_scene.gltf(
    filepath=os.path.join(export_dir, "asset.glb"),
    export_format='GLB'
)
```

### 7. Eksport do Flutter (GLB base64)

```python
import bpy, os, base64, json

export_dir = "/tmp/flutter_export"
os.makedirs(export_dir, exist_ok=True)

bpy.ops.export_scene.gltf(
    filepath=os.path.join(export_dir, "asset.glb"),
    export_format='GLB'
)

with open(os.path.join(export_dir, "asset.glb"), "rb") as f:
    encoded = base64.b64encode(f.read()).decode("utf-8")

with open(os.path.join(export_dir, "asset_base64.txt"), "w") as f:
    f.write(encoded)
```

### 8. Eksport do Java/Kotlin

```python
import bpy, os

export_dir = "/tmp/kotlin_export"
os.makedirs(export_dir, exist_ok=True)

bpy.ops.export_scene.gltf(
    filepath=os.path.join(export_dir, "asset.glb"),
    export_format='GLB'
)
```

## Workflows gotowe do uzycia

Pliki w `workflows/` to szablony parametrow dla kazdego stacku:
- `godot_mobile.json`
- `unity_mobile.json`
- `ue5_mobile.json`
- `flutter_mobile.json`
- `kotlin_mobile.json`

Format:
```json
{
  "stack": "godot",
  "profile": "low_poly",
  "export_dir": "/tmp/godot_mobile",
  "export_format": "GLB",
  "tri_limit": 120,
  "tex_max": 512,
  "lod_levels": 3
}
```

Uzywaj ich jako punktu startu do generowania kodu eksportu.

## Sciaganie pracy

Po uruchomieniu kodu eksportu przez blender-mcp:

1. Sprawdz pliki w katalogu tymczasowym `/tmp/<stack>_export/`.
2. Przeslij je do repo gry.
3. Zaktualizuj manifest assetow kroku produkcyjnym.

## Rozwiazywanie problemow

| Blad                              | Rozwiazanie                                        |
|-----------------------------------|----------------------------------------------------|
| Zaden obiekt nie jest wybrany     | Upewnij sie ze scena jest w Object Mode             |
| Blender zwroca `no active object` | Wybierz mesh przed wywolaniem kodu                |
| Tri count za wysoki               | Obniz ratio modyfikatora Decimate do 0.25           |
| Brak materialu                    | Utworz material PBR wedlug szablonu powyzej        |
| Port 9876 zamkniety               | Wlacz ponownie BlenderMCP > Start Server w N-panel |

## Przypomnienie bezpieczenstwa

- Plugin nie wysyla danych poza lokalny host.
- `blender-mcp` ma dostep do plikow systemowych uzytkownika.
- Uruchamiaj tylko z zaufanymi workflow.

## Kompatybilnosc z innymi agentami AI

Plugin jest **agencji-niepodlaczny** na poziomie wykonania.
Dzieki powloce `blender-mcp`, kazdy agent, ktory moze wywolywac
narzedzia `execute_code` / `terminal` / `bash` / `python`,
moze wspolpracowac z tym pluginem bez zmian w Blenderze.

Obslugiwane agenty:
- Hermes - skill `blender-mcp` + `blender-mobile-3d-plugin` execute_code
- Claude Code - tool `terminal` / bash
- Codex CLI - run `python3 scripts/...`
- Kimi / Kimi K2 - `bash` / `python` / bezposredni socket

Uwaga bezpieczenstwa:
- uruchamiaj tylko jedna akcje na porcie 9876 naraz
- uzywaj roznych podfolderow `/tmp/<agent>_<stack>_export/`

## Zobacz takze

- `blender-mcp` SKILL.md
- `references/mobile-pipeline.md`
- `references/formats.md`
- `references/rigging.md`
- `references/materials.md`
- `references/troubleshooting.md`
