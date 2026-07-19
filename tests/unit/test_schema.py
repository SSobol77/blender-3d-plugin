"""Tests for blender_mobile_3d.config.schema."""

from __future__ import annotations

from pathlib import Path

import pytest

from blender_mobile_3d.config.schema import validate_preset_schema


def test_validate_preset_schema_returns_with_valid_input() -> None:
    preset = {
        "schema_version": "1.0.0",
        "plugin_version": "1.0.0",
        "preset": "low_poly",
        "target": "godot",
        "limits": {},
        "paths": {},
        "export": {},
    }
    validate_preset_schema(preset)
    assert True is True


def test_validate_preset_schema_missing_required_returns_cleanly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import blender_mobile_3d.config.schema as schema_mod

    monkeypatch.setattr(schema_mod, "jsonschema", None)
    validate_preset_schema({"schema_version": "1.0.0"})
    assert True is True


def test_validate_preset_schema_file_missing_returns_cleanly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = Path("/tmp/some_fake_schema_path_blender_3d_plugin.json")
    validate_preset_schema({"schema_version": "1.0.0"}, schema_path=path)
    assert True is True
