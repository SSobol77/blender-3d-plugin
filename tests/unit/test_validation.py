"""Unit tests for blender_mobile_3d.core.validation."""

from __future__ import annotations

from blender_mobile_3d.core.validation import ValidationEngine


def test_triangle_overage() -> None:
    engine = ValidationEngine(limits={"tri_limit": 120})
    issues = engine.validate_metrics({"triangle_count": 130})
    assert any(i["code"] == "TRIANGLE_OVERAGE" for i in issues)
    assert any(i["severity"] == "error" for i in issues)


def test_passing_when_within_limits() -> None:
    engine = ValidationEngine(limits={"tri_limit": 120})
    issues = engine.validate_metrics({"triangle_count": 100})
    assert issues == []
