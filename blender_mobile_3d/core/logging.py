"""Structured logging for blender_mobile_3d."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class Diagnostic:
    def __init__(
        self,
        code: str,
        severity: str,
        explanation: str,
        affected: str,
        measured: Any,
        limit: Any,
        remediation: str,
    ):
        self.code = code
        self.severity = severity
        self.explanation = explanation
        self.affected = affected
        self.measured = measured
        self.limit = limit
        self.remediation = remediation
        self.timestamp = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "explanation": self.explanation,
            "affected": self.affected,
            "measured": self.measured,
            "limit": self.limit,
            "remediation": self.remediation,
            "timestamp": self.timestamp,
        }


class Report:
    def __init__(self) -> None:
        self.diagnostics: list[Diagnostic] = []

    def add(self, diagnostic: Diagnostic) -> None:
        self.diagnostics.append(diagnostic)

    @property
    def passed(self) -> bool:
        return not any(d.severity == "error" for d in self.diagnostics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }
