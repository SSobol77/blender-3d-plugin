"""Unit tests for blender_mobile_3d.config.loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from blender_mobile_3d.config.loader import (
    available_presets,
    default_presets_dir,
    load_preset,
)
from blender_mobile_3d.core.errors import ConfigurationError


def _payload() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "plugin_version": "1.0.0",
        "preset": "low_poly",
        "target": "godot",
        "limits": {"tri_limit": 120, "tex_max": 512, "material_limit": 4, "bone_limit": 60},
        "paths": {"use_project_output": True, "output_relative": "export/mobile"},
        "export": {
            "apply_scale": True,
            "triangulate": False,
            "bake_animation": True,
            "uv_requirements": "at_least_one",
        },
    }


def _write(tmp_path: Path, data: Any) -> Path:
    path = tmp_path / "preset.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_available_presets() -> None:
    presets = available_presets()
    assert "low_poly" in presets
    assert "character" in presets


def test_default_presets_dir_exists() -> None:
    assert default_presets_dir().is_dir()


def test_load_preset(tmp_path: Path) -> None:
    data = load_preset(_write(tmp_path, _payload()))
    assert data["target"] == "godot"


def test_load_preset_missing(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_preset(tmp_path / "missing.json")


def test_load_preset_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="unreadable or malformed"):
        load_preset(path)


def test_load_preset_non_object_root(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="must be a JSON object"):
        load_preset(_write(tmp_path, [1, 2, 3]))


def test_load_preset_bad_schema_version(tmp_path: Path) -> None:
    payload = _payload()
    payload["schema_version"] = "9.9.9"
    with pytest.raises(ConfigurationError, match="Unsupported preset schema_version"):
        load_preset(_write(tmp_path, payload))


def test_load_preset_missing_section(tmp_path: Path) -> None:
    payload = _payload()
    del payload["limits"]
    with pytest.raises(ConfigurationError, match="section missing"):
        load_preset(_write(tmp_path, payload))


def test_load_preset_schema_rejects_bad_target(tmp_path: Path) -> None:
    payload = _payload()
    payload["target"] = "dreamcast"
    with pytest.raises(ConfigurationError):
        load_preset(_write(tmp_path, payload))


def test_all_shipped_presets_load() -> None:
    presets_dir = default_presets_dir()
    for preset_file in sorted(presets_dir.glob("*.json")):
        data = load_preset(preset_file)
        assert data["schema_version"] == "1.0.0"
