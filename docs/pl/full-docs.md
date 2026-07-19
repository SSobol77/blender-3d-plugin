# Dokumentacja - Blender Mobile 3D Plugin (PL)

## Spis tresci
1. [Przeglad](#1-przeglad)
2. [Instalacja](#2-instalacja)
3. [Szybki_start](#3-szybki-start)
4. [Profile_mobilne](#4-profile-mobilne)
5. [Workflow](#5-workflow)
6. [Skrypty](#6-skrypty)
7. [Rozwiazywanie_problemow](#7-rozwiazywanie-problemow)
8. [Wieloagentowe_wspolpracowanie](#8-wieloagentowe-wspolpracowanie)

---

## 1. Przeglad

Plugin przygotowuje assety 3D do gier mobilnych w Blenderze.
Dziala jako rozszerzenie `blender-mcp` i wspolpracuje z Hermes,
Claude Code, Codex CLI oraz Kimi.

## 2. Instalacja

### Wymagania
- Blender 5.2.0 LTS lub 4.3+
- `blender-mcp` z uruchomionym serwerem TCP na porcie 9876
- Hermes Agent / Claude Code / Codex / Kimi

### Kroki
1. Sklonuj repozytorium:
   ```
   git clone https://github.com/SSobol77/blender-3d-plugin.git
   cd blender-3d-plugin
   ```
2. Skopiuj skill do Hermes:
   ```
   cp -r hermes-skill ~/.hermes/skills/creative/blender-mobile-3d-plugin
   ```
3. W Blenderze zainstaluj `blender_mcp_addon.py`:
   - Edit > Preferences > Add-ons > Install
   - Wlacz "Interface: Blender MCP"
   - N-panel > BlenderMCP > Start Server
4. Sprawdz polaczenie:
   ```
   nc -z -w2 localhost 9876 && echo "OPEN" || echo "CLOSED"
   ```

## 3. Szybki start

### Przygotowanie sceny
```python
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 0.01
bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
```

### Stworzenie mesha
```python
import bpy
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0,0,0))
```

### LOD chain
```python
from scripts.low_poly_lod import apply_lod
apply_lod("Sphere", lod_ratios=(0.6, 0.3, 0.15))
```

### Eksport
```python
from scripts.export_mobile import export_for_stack
export_for_stack("godot")
```

## 4. Profile mobilne

| Profil       | Tri limit | Tex max | LOD | Font |
|--------------|-----------|---------|-----|------|
| low_poly     | 120       | 512     | 3   | Yes  |
| environment  | 300       | 1024    | 2   | No   |
| character    | 200       | 512     | 3   | Yes  |
| ui_3d        | 80        | 1024    | 1   | No   |
| fx           | 150       | 512     | 1   | No   |

## 5. Workflow

Szablony dla kazdego stacku znajduja sie w `workflows/`:
- `godot_mobile.json`
- `unity_mobile.json`
- `ue5_mobile.json`
- `flutter_mobile.json`
- `kotlin_mobile.json`

## 6. Skrypty

| Skrypt                  | Cel                          |
|-------------------------|------------------------------|
| `prepare_scene.py`      | staging scena, cleanup       |
| `low_poly_lod.py`       | decimate + LOD chain         |
| `auto_rig.py`           | autorigging postaci          |
| `export_mobile.py`      | eksport do wybranego stacku  |
| `postprocess_manifest.py` | generacja konfiguracji docelowych |

## 7. Rozwiazywanie problemow

| Blad                           | Rozwiazanie                                      |
|--------------------------------|--------------------------------------------------|
| Port 9876 zamkniety            | Wlacz ponownie Start Server w N-panel            |
| `no active object`             | Wybierz mesh przed operacja                      |
| `no UV layers`                 | Dodaj UV unwrap przed eksportem                  |
| Tri count za wysoki            | Zmniejsz ratio Decimate do ponizej 0.3           |
| Texture too large              | Ogranicz do 1024 lub 512 px                      |
| Bone count > 60                | Zmniejsz liczbe kosci                            |

## 8. Wieloagentowe wspolpracowanie

| Agent       | Dzialanie                     | Podfolder wyjsciowy      |
|-------------|-------------------------------|--------------------------|
| Hermes      | execute_code przez skill      | `/tmp/hermes_<stack>/`   |
| Claude Code | terminal / bash               | `/tmp/claude_<stack>/`   |
| Codex CLI   | python3 scripts/...           | `/tmp/codex_<stack>/`    |
| Kimi        | bash/python / socket          | `/tmp/kimi_<stack>/`     |

Zasady:
- Jedna akcja na porcie 9876 naraz
- Kazdy agent uzywa wlasnego podfolderu
- Plugin nie wymaga zmian w `blender-mcp`
