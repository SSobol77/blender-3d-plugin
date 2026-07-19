"""Unit tests for blender_mobile_3d.config.models."""

from __future__ import annotations

import pytest

from blender_mobile_3d.config.models import Limits, ExportOptions, PathConfig, Preset


def test_defaults() -> None:
    p = Preset()
    assert p.preset == "low_poly"
    assert p.target == "godot"
    assert p.limits.tri_limit == 120
    assert p.export.triangulate is False


def test_from_dict_override() -> None:
    p = Preset.from_dict({"preset": "character", "limits": {"tri_limit": 200}})
    assert p.preset == "character"
    assert p.limits.tri_limit == 200
