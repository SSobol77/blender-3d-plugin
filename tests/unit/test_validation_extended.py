"""Expanded tests for blender_mobile_3d.core.validation."""

from __future__ import annotations

from typing import Any

from blender_mobile_3d.core.validation import ValidationEngine


def _limits(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    base = {
        "tri_limit": 120,
        "tex_max": 512,
        "material_limit": 4,
        "bone_limit": 60,
    }
    if overrides:
        base.update(overrides)
    return base


def _run(**metrics):
    engine = ValidationEngine(limits=_limits())
    return engine.validate_metrics(metrics)


def test_validate_asset_pass() -> None:
    issues = _run(triangle_count=20, texture_max=256, bone_count=10)
    assert issues == []


def test_validate_asset_fail_triangles() -> None:
    issues = _run(triangle_count=500, texture_max=256, bone_count=10)
    codes = [i["code"] for i in issues]
    assert any(code == "TRIANGLE_OVERAGE" for code in codes)


def test_validate_asset_fail_texture_size() -> None:
    issues = _run(triangle_count=20, texture_max=2000, bone_count=10)
    codes = [i["code"] for i in issues]
    assert any(code == "TEXTURE_SIZE_OVERAGE" for code in codes)


def test_validate_asset_fail_bones() -> None:
    issues = _run(triangle_count=20, texture_max=256, bone_count=1000)
    codes = [i["code"] for i in issues]
    assert any(code == "BONE_BUDGET_OVERAGE" for code in codes)
