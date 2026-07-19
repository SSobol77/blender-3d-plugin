<p align="center">
  <img src="assets/branding/blender-mobile-3d-logo.png"
       alt="Blender Mobile 3D"
       width="240">
</p>

<h1 align="center">Blender Mobile 3D Plugin</h1>

<p align="center">
  Production-ready Blender add-on for preparing and exporting optimized 3D assets for mobile games.
</p>

<p align="center">
  <a href="https://github.com/SSobol77/blender-3d-plugin/actions/workflows/ci.yml">
    <img src="https://github.com/SSobol77/blender-3d-plugin/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI">
  </a><!--
  --><img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version 1.0.0"><!--
  --><img src="https://img.shields.io/badge/License-GPL%20v2-blue.svg" alt="License: GPL v2"><!--
  --><img src="https://img.shields.io/badge/Python-3.11%2B-green.svg" alt="Python 3.11+"><!--
  --><a href="https://nodejs.org/en">
    <img src="https://img.shields.io/badge/Node.js-22-brightgreen.svg" alt="Node.js 22">
  </a>
</p>

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

### Installer CLI (npm / pip)

The repository also ships a real, tested installer CLI for both npm and
Python that discovers a Blender installation, downloads or takes an
offline release ZIP, verifies its checksum and structure, and installs,
updates, uninstalls, or diagnoses (`doctor`) the add-on through Blender's
own extension APIs. Full command/option/exit-code reference:
[docs/installer-contract.md](docs/installer-contract.md).

**These packages are not yet published to npm or PyPI.** Once released,
the intended interface is:

```bash
npx @glaeron/blender-mobile-3d install
```

```bash
pipx install blender-mobile-3d
blender-mobile-3d install
```

```bash
uvx blender-mobile-3d install
```

Until then, install from source for local testing:

```bash
cd installers/python && pip install -e . && blender-mobile-3d install --offline ../../dist/blender_mobile_3d-1.0.0.zip
cd installers/npm && npm install && node bin/blender-mobile-3d.js install --offline ../../dist/blender_mobile_3d-1.0.0.zip
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
