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


def test_issues_carry_diagnostic_fields() -> None:
    engine = ValidationEngine(
        limits={"tri_limit": 1, "tex_max": 8, "bone_limit": 1, "material_limit": 1}
    )
    issues = engine.validate_metrics(
        {
            "triangle_count": 100,
            "texture_max": 4096,
            "bone_count": 90,
            "unique_materials": 9,
        }
    )
    assert {i["code"] for i in issues} == {
        "TRIANGLE_OVERAGE",
        "TEXTURE_SIZE_OVERAGE",
        "BONE_BUDGET_OVERAGE",
        "MATERIAL_OVERAGE",
    }
    for issue in issues:
        assert set(issue) == {
            "code",
            "severity",
            "explanation",
            "affected",
            "measured",
            "limit",
            "remediation",
        }


def test_texture_max_derived_from_dimensions() -> None:
    engine = ValidationEngine(limits={"tex_max": 512})
    issues = engine.validate_metrics({"texture_dimensions": [(256, 256), (2048, 128)]})
    assert issues and issues[0]["code"] == "TEXTURE_SIZE_OVERAGE"
    assert issues[0]["measured"] == 2048


def test_material_overage() -> None:
    engine = ValidationEngine(limits={"material_limit": 2})
    issues = engine.validate_metrics({"unique_materials": 5})
    assert issues and issues[0]["code"] == "MATERIAL_OVERAGE"


def test_no_limits_no_issues() -> None:
    engine = ValidationEngine()
    assert engine.validate_metrics({"triangle_count": 10**9}) == []
