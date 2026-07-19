"""Validation primitives for mobile asset rules."""

from __future__ import annotations

from typing import Any


def _max_texture_dimension(metrics: dict[str, Any]) -> int:
    explicit = metrics.get("texture_max")
    if explicit is not None:
        return int(explicit)
    dims = metrics.get("texture_dimensions") or []
    return max((max(int(w), int(h)) for w, h in dims), default=0)


class ValidationEngine:
    def __init__(self, limits: dict[str, Any] | None = None) -> None:
        self.limits = limits or {}

    def validate_metrics(self, metrics: dict[str, Any]) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []

        tri_limit = self.limits.get("tri_limit")
        if tri_limit and metrics.get("triangle_count", 0) > tri_limit:
            issues.append(
                {
                    "code": "TRIANGLE_OVERAGE",
                    "severity": "error",
                    "explanation": "Triangle count exceeds budget.",
                    "affected": "scene",
                    "measured": metrics.get("triangle_count"),
                    "limit": tri_limit,
                    "remediation": "Apply a Decimate modifier or reduce mesh density.",
                }
            )

        tex_max = self.limits.get("tex_max")
        measured_tex = _max_texture_dimension(metrics)
        if tex_max and measured_tex > tex_max:
            issues.append(
                {
                    "code": "TEXTURE_SIZE_OVERAGE",
                    "severity": "error",
                    "explanation": "Maximum texture size exceeds budget.",
                    "affected": "materials",
                    "measured": measured_tex,
                    "limit": tex_max,
                    "remediation": "Resize textures to the profile maximum or below.",
                }
            )

        bone_limit = self.limits.get("bone_limit")
        if bone_limit and metrics.get("bone_count", 0) > bone_limit:
            issues.append(
                {
                    "code": "BONE_BUDGET_OVERAGE",
                    "severity": "error",
                    "explanation": "Bone count exceeds mobile budget.",
                    "affected": "armatures",
                    "measured": metrics.get("bone_count"),
                    "limit": bone_limit,
                    "remediation": "Simplify the rig below the per-character bone budget.",
                }
            )

        material_limit = self.limits.get("material_limit")
        if material_limit and metrics.get("unique_materials", 0) > material_limit:
            issues.append(
                {
                    "code": "MATERIAL_OVERAGE",
                    "severity": "error",
                    "explanation": "Unique material count exceeds budget.",
                    "affected": "materials",
                    "measured": metrics.get("unique_materials"),
                    "limit": material_limit,
                    "remediation": "Merge materials or atlas textures to reduce material count.",
                }
            )

        return issues
