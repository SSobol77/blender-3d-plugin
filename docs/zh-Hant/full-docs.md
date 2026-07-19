# 文件說明 - Blender Mobile 3D Plugin (zh-Hant)

## 目錄
1. [概覽](#1-概覽)
2. [安裝](#2-安裝)
3. [快速開始](#3-快速開始)
4. [行動裝置配置檔](#4-行動裝置配置檔)
5. [工作流程](#5-工作流程)
6. [腳本](#6-腳本)
7. [疑難排解](#7-疑難排解)
8. [多代理支援](#8-多代理支援)

---

## 1. 概覽

本外掛可在 Blender 中準備適用於手機遊戲的 3D 資源。
作為 `blender-mcp` 的延伸，並與以下代理搭配使用：
Hermes、Claude Code、Codex CLI、Kimi。

## 2. 安裝

### 需求
- Blender 5.2.0 LTS 或 4.3+
- 已啟動 `blender-mcp` TCP 伺服器（埠 9876）
- Hermes Agent / Claude Code / Codex CLI / Kimi

### 步驟
1. 克隆儲存庫：
   ```
   git clone https://github.com/SSobol77/blender-3d-plugin.git
   cd blender-3d-plugin
   ```
2. 安裝 Hermes 技能：
   ```
   cp -r hermes-skill ~/.hermes/skills/creative/blender-mobile-3d-plugin
   ```
3. 在 Blender 中安裝 `blender_mcp_addon.py`：
   - Edit > Preferences > Add-ons > Install
   - 啟用 "Interface: Blender MCP"
   - N-panel > BlenderMCP > Start Server
4. 檢查連線：
   ```
   nc -z -w2 localhost 9876 && Echo "OPEN" || Echo "CLOSED"
   ```

## 3. 快速開始

### 場景準備
```python
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 0.01
bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
```

### 建立網格
```python
import bpy
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0,0,0))
```

### LOD 階層
```python
from scripts.low_poly_lod import apply_lod
apply_lod("Sphere", lod_ratios=(0.6, 0.3, 0.15))
```

### 匯出
```python
from scripts.export_mobile import export_for_stack
export_for_stack("godot")
```

## 4. 行動裝置配置檔

| 配置檔      | 三角限制 | 紋理最大 | LOD | 字型 |
|-------------|----------|----------|-----|------|
| low_poly    | 120      | 512      | 3   | Yes  |
| environment | 300      | 1024     | 2   | No   |
| character   | 200      | 512      | 3   | Yes  |
| ui_3d       | 80       | 1024     | 1   | No   |
| fx          | 150      | 512      | 1   | No   |

## 5. 工作流程

每個技術堆疊的模板位於 `workflows/`：
- `godot_mobile.json`
- `unity_mobile.json`
- `ue5_mobile.json`
- `flutter_mobile.json`
- `kotlin_mobile.json`

## 6. 腳本

| 腳本                      | 用途                   |
|---------------------------|------------------------|
| `prepare_scene.py`        | 場景準備、清理         |
| `low_poly_lod.py`         | decimate + LOD 階層   |
| `auto_rig.py`             | 角色自動綁定           |
| `export_mobile.py`        | 匯出至指定技術堆疊     |
| `postprocess_manifest.py` | 產生目標設定檔         |

## 7. 疑難排解

| 問題                         | 解法                                       |
|------------------------------|--------------------------------------------|
| 埠 9876 關閉                | 重新啟動 N-panel 中的 Start Server         |
| `no active object`           | 操作前先選取 mesh                          |
| `no UV layers`               | 匯出前加入 UV unwrap                       |
| 三角過多                     | 將 Decimate ratio 調至 0.3 以下            |
| 紋理過大                     | 限制為 1024 或 512 px                      |
| 骨骼數 > 60                  | 減少骨骼數量                                |

## 8. 多代理支援

| 代理       | 操作方式                       | 輸出資料夾         |
|------------|--------------------------------|--------------------|
| Hermes     | 經技能使用 execute_code        | `/tmp/hermes_<stack>/` |
| Claude Code| terminal / bash                | `/tmp/claude_<stack>/` |
| Codex CLI  | python3 scripts/...            | `/tmp/codex_<stack>/` |
| Kimi       | bash/python 或 TCP socket      | `/tmp/kimi_<stack>/` |

規則：
- 埠 9876 一次僅處理一個動作
- 每個代理使用各自的暫存資料夾
- 外掛於執行層級不依賴 `blender-mcp` 的變更
