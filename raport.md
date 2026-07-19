# Raport: Plugin Blender do 3D dla mobilnych gier
## Hermes Agent + Blender 5.2.0 LTS

## 1. Stan istniejacych rozwiazan

| Rozwiazanie | Dostepnosc | Zastosowanie |
|-------------|-----------|--------------|
| `blender-mcp` w `optional-skills/creative/blender-mcp` | Istnieje | Ogólna kontrola Blender przez TCP 9876 |
| Manifests `unreal-engine` w `optional-mcps` | Istnieje | Dołączanie do silnika przez lokalne HTTP |
| Brak gotowego pluginu typu "mobile game stack" | BRAK | — |

Wnioski:
- W Hermes nie ma pluginu automatyzujacego pipeline Blender → Godot / Unity / UE 5.4 / Flutter / Java-Kotlin.
- Brak przygotowanych workflow, pack opcji eksportu, szablonow konfiguracji blendera do low-poly/mobile.
- Trzeba stworzyc nowy plugin rozszerzajacy dotychczasowe mozliwosci o produkcyjny flow.

## 2. Zakres proponowanego pluginu (`blender-mobile-3d-plugin`)

Plugin kazde przez:

- staging scena z meta-danymi do eksportu
- preprocessing meshow do roztargow low-poly + LOD
- autorigging postaci na potrzeby mobilne
- materialy zgodne z PBR dla mobile
- eksport do:
  - Godot (`glb`, `gltf`, `atlas txt`)
  - Unity (`prefab`, `fbx`, `material`)
  - Unreal Engine 5.4 (`glb`, `datatable`)
  - Flutter (`package:three_js`/glb base64)
  - Java / Kotlin (`glb`, `obj`, `mtl`)
- generowanie skryptów konfiguracyjnych
- screenshots w testowym renderze
- checklist weryfikacyjna

## 3. Architektura pluginu

blender-mobile-3d-plugin/
├── SKILL.md
├── references/
│   ├── mobile-pipeline.md         # kanoniczny algorytm przygotowania assetow
│   ├── formats.md                 # formaty eksportu dla kazdego silnika
│   ├── rigging.md                 # rigging dla postaci mobilnych
│   ├── materials.md               # PBR mobile guidelines
│   └── troubleshooting.md         # bledy typowe
├── scripts/
│   ├── prepare_scene.py           # staging scena, cleanup, scale, naming
│   ├── low_poly_lod.py            # decimate modyfikator + LOD chain
│   ├── auto_rig.py                # auto-rig人物 + ik constraints
│   ├── export_mobile.py           # glb/gltf/fbx zip + manifest
│   └── postprocess_manifest.py    # generuje skrypty targetowe
└── workflows/
    ├── godot_mobile.json
    ├── unity_mobile.json
    ├── ue5_mobile.json
    ├── flutter_mobile.json
    └── kotlin_mobile.json

## 4. Zawartosc pliku instrukcja.md

Plik `instrukcja.md` (po polsku) obejmuje:

- instalacje pluginu (kopiowanie do `~/.hermes/skills/...`)
- uruchomienie Blender 5.2.0 z aktywnym MCP addonem
- lista polecen i skryptow
- typowe pipeline przykladowe dla kazdego stacku
- typowe problemy

## 5. Rekomendacja

Wdrozyc plugin `blender-mobile-3d-plugin` jako rozszerzenie
istniejacego `blender-mcp`, ktory tylko uruchamia kod
Blender Python przez gniazdo. Nowy plugin wprowadza
strukture workflow-scen, configurowalne profilemezowe
oraz generowanie gotowych manifestow offline dla kazdego
silnika gier.

## 6. Wieloagentowe wspolpracowanie (Hermes / Claude Code / Codex / Kimi)

Plugin jest **agencji-niepodlaczny** na poziomie wykonania.
Wszyscy agenci korzystaja z tego samego serwera `blender-mcp`
i tych samych skryptow z `scripts/` oraz workflow z `workflows/`.

| Agent       | Dzialanie                                                  |
|-------------|------------------------------------------------------------|
| Hermes      | load skills `blender-mcp` + `blender-mobile-3d-plugin`, `execute_code` |
| Claude Code | tool `terminal` / bash -> `python3 scripts/...`           |
| Codex CLI   | run / shell -> skrypty w `scripts/`                       |
| Kimi / Kimi K2 | `bash/python` lub socket TCP -> `execute_code` przez `blender-mcp` |

Zasady bezpieczenstwa:
- uruchamiaj tylko **jedna akcje** na porcie 9876 naraz
- kazdy agent uzywa **własnego podfolderu** wyjsciowego, np.:
  - `/tmp/hermes_<stack>_export/`
  - `/tmp/claude_<stack>_export/`
  - `/tmp/codex_<stack>_export/`
  - `/tmp/kimi_<stack>_export/`

Dodatkowy helper: `scripts/workflow_runner.py` pozwala
jedno poleceniem uruchomic pelny pipeline dla wybranego
workflow JSON, niezaleznie od agenta.
