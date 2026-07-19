# Instrukcja uzytkownika - Blender Mobile 3D Plugin

## 1. Co to jest?

To rozszerzenie do `blender-mcp`,
ktore automatyzuje przygotowywanie assetow 3D przeznaczonych
wywylacznie do gier mobilnych.

Obslugiwane stacki:
- Godot
- Unity
- Unreal Engine 5.4
- Flutter
- Java / Kotlin

Wymaga:
- Blender 5.2.0 LTS
- plugin `blender-mcp` z uruchomionym serwerem na porcie 9876

## 2. Instalacja

Plugin jest juz zainstalowany w:
`~/.hermes/skills/creative/blender-mobile-3d-plugin`

## 3. Uruchomienie Blendera

1. Uruchom Blendera
2. Edit > Preferences > Add-ons > zainstaluj `blender_mcp_addon.py`
3. Wlacz "Interface: Blender MCP"
4. W N-panel kliknij Start Server
5. Sprawdz: `nc -z -w2 localhost 9876 && echo "OPEN"`

## 4. Wczytanie pluginu w Hermes

Uruchom sesje Hermes z wczytanym skill:
`blender-mobile-3d-plugin` i `blender-mcp`.

## 5. Zastosowanie

Wiecej szczegolow w `SKILL.md` tego pluginu i w plikach references.

## 6. Kontakt

Plugin: `blender-mobile-3d-plugin` v 0.1.0

## 7. Kompatybilnosc z innymi agentami AI

Plugin dziala jako warstwa nad `blender-mcp` i nie wymaga
zmien w dodatku. Kazdy agent, ktory potrafi:
- wysylac polecenia w bash/python,
- czytac pliki JSON,
- uruchamiac pipe/mnozenie procesow,

moze uzywac tych samych skryptow i workflow.

Obslugiwane agenty:
- Hermes - execute_code przez skill
- Claude Code - terminal / bash
- Codex CLI - run python3 scripts/...
- Kimi / Kimi K2 - execute_python / bash

Zasady bezpieczenstwa:
- jedna akcja na porcie 9876 naraz
- rozne podfoldery `/tmp/<agent>_<stack>_export/`
