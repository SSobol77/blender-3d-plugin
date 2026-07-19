"""Validation primitives for mobile asset rules."""

from __future__ import annotations

from typing import Any

from blender_mobile_3d.core.errors import ConfigurationError, ValidationError
from blender_mobile_3d.core.metrics import SceneMetrics


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
                    "measured": metrics.get("triangle_count"),
                    "limit": tri_limit,
                }
            )

        tex_max = self.limits.get("tex_max")
        if tex_max and metrics.get("texture_max", 0) > tex_max:
            issues.append(
                {
                    "code": "TEXTURE_SIZE_OVERAGE",
                    "severity": "error",
                    "explanation": "Maximum texture size exceeds budget.",
                    "measured": metrics.get("texture_max"),
                    "limit": tex_max,
                }
            )

        bone_limit = self.limits.get("bone_limit")
        if bone_limit and metrics.get("bone_count", 0) > bone_limit:
            issues.append(
                {
                    "code": "BONE_BUDGET_OVERAGE",
                    "severity": "error",
                    "explanation": "Bone count exceeds mobile budget.",
                    "measured": metrics.get("bone_count"),
                    "limit": bone_limit,
                }
            )

        return issues
