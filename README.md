# blender-3d-plugin

Professional plugin for preparing 3D assets for mobile games in Blender.

![Blender Mobile 3D](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-green.svg)
![Hermes](https://img.shields.io/badge/Hermes-compatible-lightgrey.svg)
![Claude%20Code](https://img.shields.io/badge/Claude%20Code-supported-lightgrey.svg)
![Codex%20CLI](https://img.shields.io/badge/Codex%20CLI-supported-lightgrey.svg)
![Kimi](https://img.shields.io/badge/Kimi%20K2-supported-lightgrey.svg)

## Documentation

- [English](README.en.md) | [Polski](README.pl.md) | [Русский](README.ru.md) | [正體中文](README.zh-Hant.md)

## Requirements

- Blender 4.3+
- Python 3.11+
- Blender UI usage does not require an AI agent
- Optional agent adapter support: Hermes, Claude Code, Codex CLI, Kimi/Kimi K2
- Optional `blender-mcp` adapter for agent-based workflows

## Quick Install

### Blender add-on

1. Download the release ZIP from `https://github.com/SSobol77/blender-3d-plugin/releases`
2. In Blender: `Edit > Preferences > Add-ons > Install...` and select the ZIP
3. Enable `Blender Mobile 3D`

### Agent compatibility package

```bash
cp -r blender-3d-plugin/plugin-core ~/.hermes/skills/creative/blender-mobile-3d-plugin
```

## License

GPL-2.0-only. See `LICENSE` in the repository root.

## Project layout

```text
blender-3d-plugin/
  blender_mobile_3d/    production package/core
  presets/              target/asset presets
  schemas/              manifest and preset schemas
  scripts/              CLI wrapper
  tests/                unit and integration tests
  docs/                 multilingual documentation
  plugin-core/          agent-compatible compatibility package
```

Full documentation:
- [Documentation (All languages)](docs/)
