"""Tests for blender_mobile_3d.config.schema (fail-closed behavior)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import blender_mobile_3d.config.schema as schema_mod
from blender_mobile_3d.config.schema import validate_preset_schema
from blender_mobile_3d.core.errors import ConfigurationError


def _valid_preset() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "plugin_version": "1.0.0",
        "preset": "low_poly",
        "target": "godot",
        "limits": {"tri_limit": 120, "tex_max": 512, "material_limit": 4, "bone_limit": 60},
        "paths": {"use_project_output": True, "output_relative": "export/mobile"},
        "export": {},
    }


def test_valid_preset_passes() -> None:
    validate_preset_schema(_valid_preset())


def test_validator_unavailable_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(schema_mod, "jsonschema", None)
    with pytest.raises(ConfigurationError, match="jsonschema is required"):
        validate_preset_schema(_valid_preset())


def test_schema_file_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="schema not found"):
        validate_preset_schema(_valid_preset(), schema_path=tmp_path / "missing.schema.json")


def test_schema_file_malformed_raises(tmp_path: Path) -> None:
    bad_schema = tmp_path / "broken.schema.json"
    bad_schema.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="unreadable or malformed"):
        validate_preset_schema(_valid_preset(), schema_path=bad_schema)


def test_schema_document_invalid_raises(tmp_path: Path) -> None:
    invalid_schema = tmp_path / "invalid.schema.json"
    invalid_schema.write_text(json.dumps({"type": "no-such-type"}), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="schema is invalid"):
        validate_preset_schema(_valid_preset(), schema_path=invalid_schema)


def test_missing_required_field_raises() -> None:
    preset = _valid_preset()
    del preset["target"]
    with pytest.raises(ConfigurationError, match="validation failed"):
        validate_preset_schema(preset)


def test_invalid_field_value_raises() -> None:
    preset = _valid_preset()
    preset["target"] = "playstation"
    with pytest.raises(ConfigurationError, match="validation failed"):
        validate_preset_schema(preset)


def test_invalid_limit_type_raises() -> None:
    preset = _valid_preset()
    preset["limits"]["tri_limit"] = "many"
    with pytest.raises(ConfigurationError, match="validation failed"):
        validate_preset_schema(preset)


@pytest.mark.parametrize("root", [None, [], "text", 42])
def test_non_object_root_raises(root: Any) -> None:
    with pytest.raises(ConfigurationError, match="must be a JSON object"):
        validate_preset_schema(root)


def test_default_schema_path_exists() -> None:
    assert schema_mod.default_schema_path().is_file()
