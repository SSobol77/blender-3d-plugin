"""Tests for blender_mobile_3d.core.pipeline."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from blender_mobile_3d.core.pipeline import Pipeline, PipelineResult


class FakeLimits:
    __dict__ = {"tri_limit": 120, "tex_max": 512, "material_limit": 4, "bone_limit": 60}


class FakePaths:
    __dict__ = {"output_relative": "."}


class FakeExport:
    __dict__ = {}


class FakePreset:
    plugin_version = "1.0.0"
    preset = "low_poly"
    target = "godot"
    limits = FakeLimits()
    paths = FakePaths()
    export = FakeExport()


def _pipeline() -> Pipeline:
    return Pipeline(preset=FakePreset(), output_dir=Path("."))


def test_pipeline_init() -> None:
    p = _pipeline()
    assert isinstance(p, Pipeline)


def test_run_pipeline_no_context() -> None:
    p = _pipeline()
    result = p.run(None, dry_run=True)
    assert isinstance(result, PipelineResult)
    assert result.passed is True
    assert isinstance(result.artifacts, list)


def test_run_pipeline_writes_manifest(tmp_path: Path) -> None:
    p = _pipeline()
    result = p.run(None, dry_run=True)
    assert result.artifacts


def test_run_pipeline_with_mocked_context() -> None:
    p = _pipeline()
    ctx = MagicMock()
    ctx.scene = MagicMock()
    result = p.run(ctx, dry_run=True)
    assert isinstance(result, PipelineResult)
