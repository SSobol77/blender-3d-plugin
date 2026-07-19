"""Unit tests for blender_mobile_3d.config.loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from blender_mobile_3d.config.loader import load_preset, available_presets
from blender_mobile_3d.core.errors import ConfigurationError


def test_available_presets() -> None:
    presets = available_presets()
    assert "low_poly" in presets
    assert "character" in presets


def test_load_preset(tmp_path: Path) -> None:
    payload = {
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
    path = tmp_path / "low_poly.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    data = load_preset(path)
    assert data["target"] == "godot"


def test_load_preset_missing(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        load_preset(tmp_path / "missing.json")
