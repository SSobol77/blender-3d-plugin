# Documentation - Blender Mobile 3D Plugin (EN)

## Table of Contents
1. [Overview](#1-overview)
2. [Installation](#2-installation)
3. [Quick_Start](#3-quick-start)
4. [Mobile_Profiles](#4-mobile-profiles)
5. [Workflows](#5-workflows)
6. [Scripts](#6-scripts)
7. [Troubleshooting](#7-troubleshooting)
8. [Multi_Agent_Support](#8-multi-agent-support)

---

## 1. Overview

Plugin prepares 3D assets for mobile games in Blender.
Operates as an extension of `blender-mcp` and cooperates with:
Hermes, Claude Code, Codex CLI, Kimi.

## 2. Installation

### Requirements
- Blender 5.2.0 LTS or 4.3+
- `blender-mcp` with TCP server on port 9876
- Hermes Agent / Claude Code / Codex CLI / Kimi

### Steps
1. Clone repository:
   ```
   git clone https://github.com/SSobol77/blender-3d-plugin.git
   cd blender-3d-plugin
   ```
2. Install Hermes skill:
   ```
   cp -r hermes-skill ~/.hermes/skills/creative/blender-mobile-3d-plugin
   ```
3. In Blender install `blender_mcp_addon.py`:
   - Edit > Preferences > Add-ons > Install
   - Enable "Interface: Blender MCP"
   - N-panel > BlenderMCP > Start Server
4. Verify connection:
   ```
   nc -z -w2 localhost 9876 && echo "OPEN" || echo "CLOSED"
   ```

## 3. Quick Start

### Scene staging
```python
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 0.01
bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
```

### Create mesh
```python
import bpy
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0,0,0))
```

### LOD chain
```python
from scripts.low_poly_lod import apply_lod
apply_lod("Sphere", lod_ratios=(0.6, 0.3, 0.15))
```

### Export
```python
from scripts.export_mobile import export_for_stack
export_for_stack("godot")
```

## 4. Mobile Profiles

| Profile       | Tri limit | Tex max | LOD | Font |
|---------------|-----------|---------|-----|------|
| low_poly      | 120       | 512     | 3   | Yes  |
| environment   | 300       | 1024    | 2   | No   |
| character     | 200       | 512     | 3   | Yes  |
| ui_3d         | 80        | 1024    | 1   | No   |
| fx            | 150       | 512     | 1   | No   |

## 5. Workflows

Templates for each stack in `workflows/`:
- `godot_mobile.json`
- `unity_mobile.json`
- `ue5_mobile.json`
- `flutter_mobile.json`
- `kotlin_mobile.json`

## 6. Scripts

| Script                    | Purpose                          |
|---------------------------|----------------------------------|
| `prepare_scene.py`        | scene staging, cleanup           |
| `low_poly_lod.py`         | decimate + LOD chain             |
| `auto_rig.py`             | character auto-rigging           |
| `export_mobile.py`        | export to selected stack         |
| `postprocess_manifest.py` | generate target configuration    |

## 7. Troubleshooting

| Issue                           | Solution                                       |
|---------------------------------|------------------------------------------------|
| Port 9876 closed                 | Restart Start Server in N-panel                |
| `no active object`               | Select mesh before operation                   |
| `no UV layers`                   | Add UV unwrap before export                    |
| Tri count too high               | Lower Decimate ratio below 0.3                 |
| Texture too large                | Limit to 1024 or 512 px                        |
| Bone count > 60                  | Reduce bone count                              |

## 8. Multi-Agent Support

| Agent       | Action                              | Output folder        |
|-------------|-------------------------------------|----------------------|
| Hermes      | execute_code via skill              | `/tmp/hermes_<stack>/` |
| Claude Code | terminal / bash                     | `/tmp/claude_<stack>/` |
| Codex CLI   | python3 scripts/...                 | `/tmp/codex_<stack>/` |
| Kimi        | bash/python or TCP socket           | `/tmp/kimi_<stack>/` |

Rules:
- One action on port 9876 at a time
- Each agent uses its own temp folder
- Plugin is `blender-mcp`-agnostic at execution level
