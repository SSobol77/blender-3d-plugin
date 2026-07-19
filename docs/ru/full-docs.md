# Документация - Blender Mobile 3D Plugin (RU)

## Содержание
1. [Обзор](#1-обзор)
2. [Установка](#2-установка)
3. [Быстрый_старт](#3-быстрый-старт)
4. [Мобильные_профили](#4-мобильные-профили)
5. [Workflow](#5-workflow)
6. [Скрипты](#6-скрипты)
7. [Устранение_неполадок](#7-устранение-неполадок)
8. [Мультиагентность](#8-мультиагентность)

---

## 1. Обзор

Плагин подготавливает 3D-ассеты для мобильных игр в Blender.
Работает как расширение `blender-mcp` и взаимодействует с:
Hermes, Claude Code, Codex CLI, Kimi.

## 2. Установка

### Требования
- Blender 5.2.0 LTS или 4.3+
- `blender-mcp` с TCP-сервером на порту 9876
- Hermes Agent / Claude Code / Codex CLI / Kimi

### Шаги
1. Клонируйте репозиторий:
   ```
   git clone https://github.com/SSobol77/blender-3d-plugin.git
   cd blender-3d-plugin
   ```
2. Установите skill для Hermes:
   ```
   cp -r hermes-skill ~/.hermes/skills/creative/blender-mobile-3d-plugin
   ```
3. В Blender установите `blender_mcp_addon.py`:
   - Edit > Preferences > Add-ons > Install
   - Включите "Interface: Blender MCP"
   - N-panel > BlenderMCP > Start Server
4. Проверьте соединение:
   ```
   nc -z -w2 localhost 9876 && echo "OPEN" || echo "CLOSED"
   ```

## 3. Быстрый старт

### Подготовка сцены
```python
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 0.01
bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
```

### Создание меша
```python
import bpy
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0,0,0))
```

### LOD цепочка
```python
from scripts.low_poly_lod import apply_lod
apply_lod("Sphere", lod_ratios=(0.6, 0.3, 0.15))
```

### Экспорт
```python
from scripts.export_mobile import export_for_stack
export_for_stack("godot")
```

## 4. Мобильные профили

| Профиль      | Tri limit | Tex max | LOD | Шрифт |
|--------------|-----------|---------|-----|-------|
| low_poly     | 120       | 512     | 3   | Yes   |
| environment  | 300       | 1024    | 2   | No    |
| character    | 200       | 512     | 3   | Yes   |
| ui_3d        | 80        | 1024    | 1   | No    |
| fx           | 150       | 512     | 1   | No    |

## 5. Workflow

Шаблоны для каждого стека в `workflows/`:
- `godot_mobile.json`
- `unity_mobile.json`
- `ue5_mobile.json`
- `flutter_mobile.json`
- `kotlin_mobile.json`

## 6. Скрипты

| Скрипт                       | Назначение                    |
|------------------------------|-------------------------------|
| `prepare_scene.py`           | подготовка сцены, очистка     |
| `low_poly_lod.py`            | decimate + LOD цепочка        |
| `auto_rig.py`                | авто-риггинг персонажей        |
| `export_mobile.py`           | экспорт в выбранный стек      |
| `postprocess_manifest.py`    | генерация целевых конфигов    |

## 7. Устранение неполадок

| Проблема                     | Решение                                      |
|------------------------------|----------------------------------------------|
| Порт 9876 закрыт             | Перезапустите Start Server в N-panel         |
| `no active object`           | Выберите mesh перед операцией                |
| `no UV layers`               | Добавьте UV unwrap перед экспортом            |
| Слишком много треугольников  | Уменьшите ratio Decimate ниже 0.3             |
| Текстура слишком большая     | Ограничьте 1024 или 512 px                    |
| Кость > 60                   | Уменьшите количество костей                   |

## 8. Мультиагентность

| Агент       | Действие                        | Папка вывода         |
|-------------|---------------------------------|-----------------------|
| Hermes      | execute_code через skill        | `/tmp/hermes_<stack>/` |
| Claude Code | terminal / bash                 | `/tmp/claude_<stack>/` |
| Codex CLI   | python3 scripts/...             | `/tmp/codex_<stack>/` |
| Kimi        | bash/python или TCP socket      | `/tmp/kimi_<stack>/` |

Правила:
- Одно действие на порт 9876 за раз
- Каждый агент использует отдельную папку
- Плагин не требует изменений в `blender-mcp`
