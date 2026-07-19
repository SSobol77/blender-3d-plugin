"""Unit tests for blender_mobile_3d.core.logging and diagnostics."""

from __future__ import annotations

from blender_mobile_3d.core.logging import Diagnostic, Report


def test_diagnostic_to_dict() -> None:
    d = Diagnostic("E1", "warning", "text", "Asset", 10, 5, "reduce")
    payload = d.to_dict()
    assert payload["code"] == "E1"
    assert "timestamp" in payload


def test_report_passed_by_default() -> None:
    r = Report()
    assert r.passed is True
    assert r.to_dict()["diagnostics"] == []


def test_report_failed_when_error() -> None:
    r = Report()
    r.add(Diagnostic("E2", "error", "b", "c", 1, 0, "d"))
    assert r.passed is False
