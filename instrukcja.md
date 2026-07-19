#              Blender 3D - Plugin uzytych assetow do gier mobilnych
#              dla Hermes Agent - instrukcja uzytkownika (PL)

## 1. Co to jest ten plugin?

Plugin `blender-mobile-3d-plugin` rozszerza Hermes o mozliwosci
produkcyjnego przygotowywania assetow 3D przeznaczonych do gier
mobilnych, z gotowymi profilami eksportu do:

- Godot
- Unity
- Unreal Engine 5.4
- Flutter
- Java / Kotlin

Jest to dodatek do pluginu `blender-mcp` i wymaga:
- Blender 5.2.0 LTS (lub 4.3+)
- zainstalowanego addon `blender_mcp_addon.py`
- uruchomionego serwera TCP na porcie 9876 w Blenderze

## 2. Instalacja

### 2.1 Wymagania wstepne

1. Zainstaluj Blender 5.2.0 i dodaj do PATH `~/.bashrc` (gotowe w tym systemie).
2. Nainstaluj addon:
   ```
   1. pobierz: https://raw.githubusercontent.com/ahujasid/blender-mcp/main/addon.py
   2. W Blenderze: Edit > Preferences > Add-ons > Install > wybierz plik addon.py
   3. Wlacz "Interface: Blender MCP"
   4. W N-panel w widoku Viewport kliknij "Start Server"
   ```
3. Sprawdz gniazdo w terminalu:
   ```
   nc -z -w2 localhost 9876 && echo "OPEN" || echo "CLOSED"
   ```

### 2.2 Instalacja pluginu mobile-3d

Skopiuj folder `~/.hermes/skills/creative/blender-mobile-3d-plugin` do:
```
~/.hermes/skills/blender-mobile-3d-plugin
```

Lub uzyj skryptu instalacyjnego, jesli zostanie dostarczony.

### 2.3 Weryfikacja

W nowym seansie Hermesa load skill `blender-mobile-3d-plugin` + `blender-mcp`.
Pierwsze wywolanie to zwykle:
- sprawdzenie `get_scene_info`
- pobranie listy workflow dostepnych profilow

## 3. Struktura pluginu

blender-mobile-3d-plugin/
├── SKILL.md
├── references/
│   ├── mobile-pipeline.md       # flow prac
│   ├── formats.md               # specyfikacja formatow
│   ├── rigging.md               # guidelines rigingu
│   ├── materials.md             # PBR mobile
│   └── troubleshooting.md       # rozwijanie bledow
├── scripts/
│   ├── prepare_scene.py
│   ├── low_poly_lod.py
│   ├── auto_rig.py
│   ├── export_mobile.py
│   └── postprocess_manifest.py
└── workflows/
    ├── godot_mobile.json
    ├── unity_mobile.json
    ├── ue5_mobile.json
    ├── flutter_mobile.json
    └── kotlin_mobile.json

## 4. Szybki start - konkretny scenario

### 4.1 Przygotowanie nowej sceny

1. Utworz nowa pusty plik blendera, zapisz jako `asset_pack.blend`.
2. Wladaj blendert z aktywnym MCP addonem.
3. Hermes wywoluje ladowanie artefaktow 3D, cleanup i staging metadata.

### 4.2 Eksport do Godot

Wymagane:
- `asset_id`, ` lod_level`, ` materials_overrides`
- raportuje jako archiwum `assets/godot_mobile/` z `trescn`

Dominanta:
- format `glb`
- metryki: triangle count, material count, textura size

### 4.3 Eksport do Unity

Wymagane:
- `asset_id`, ` lod_count`
- generuje pakiet z `prefab`, `fbx` i regula `material`

Korzysta z `fbx` z optymalna hierarchia nodow.

### 4.4 Ekport do Unreal Engine 5.4

Wymagane:
- `asset_id`, ` lod_count`, ` nanite_indirect`
- generuje `glb` i `datatable`

### 4.5 Eksport do Flutter

Wymagane:
- `asset_id`, ` theme`
- generuje pakiety w `assets/flutter/` z glb base64 i
  klasy konfiguracyjne Dart

### 4.6 Eksport do java / klkotlin

Wymagane:
- `asset_id`, ` platform`
- generuje glb/obj/mtl i mapowania wrywcze
- pakiet archiwalny w `assets/kotlin/android/`

## 5. Profile parametrow pluginu

Dostepne profile dla mobile:

- `low_poly_profile`:
  - decimate 0.3-0.5 ratio
  - LOD 3 poziomy
  - bez bump smooth
- `villain_profile`:
  - uproszczona hierarchia kostna
  - blend shape do min 8 kluczy
  - tex 256/512
- `ui_3d_profile`:
  - uv space 2k
  - double side
  - alpha cutout

## 6. Typowe bledy i rozwiazania

| Blad | Rozwiazanie |
|------|-------------|
| `socket CLOSED` | Uruchom ponownie "Start Server" w Blender MCP N-panel |
| `export failed: no named UV` | Dodaj UV map przed eksportem |
| `too many triangles` | zmniejsz ratio decimate modyfikatora |
| `texture too large` | ogranicz do 2048 max, prefer 1024 |
| `missing material slot` | utworz material, przypisz do mesh |
| `rigging: bone count > 60` | zmniejsz liczbę kosci | 

## 7. Dodatkowe odczyty

- `references/mobile-pipeline.md`
- `references/formats.md`
- `references/rigging.md`
- `references/materials.md`
- `references/troubleshooting.md`
- `workflows/<stack>_mobile.json`

## 8. Wersja i kontakt

- Plugin: `blender-mobile-3d-plugin` v 0.1.0 (początkowa)
- Hermes Agent + Blender 5.2.0 LTS
- System: Debian 13 (trixie), Linux x86_64
