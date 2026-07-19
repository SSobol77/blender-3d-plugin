"""Tests for blender_mobile_3d.core.pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from blender_mobile_3d.config.models import Preset
from blender_mobile_3d.core.errors import ExportError
from blender_mobile_3d.core.pipeline import Pipeline, PipelineResult


def _context_with_triangles(count: int) -> SimpleNamespace:
    polys = [SimpleNamespace(vertices=(0, 1, 2)) for _ in range(count)]
    mesh = SimpleNamespace(
        polygons=polys,
        vertices=[0, 1, 2],
        edges=[],
        loop_triangles=None,
        materials=[],
        uv_layers=[],
        shape_keys=None,
    )
    obj = SimpleNamespace(
        name="Obj",
        type="MESH",
        data=mesh,
        modifiers=[],
        matrix_world=SimpleNamespace(is_identity=True),
    )
    return SimpleNamespace(scene=SimpleNamespace(objects=[obj], actions=[]))


def test_pipeline_init(tmp_path: Path) -> None:
    p = Pipeline(preset=Preset(), output_dir=tmp_path)
    assert isinstance(p, Pipeline)
    assert p.output_dir == tmp_path


def test_run_pipeline_no_context(tmp_path: Path) -> None:
    p = Pipeline(preset=Preset(), output_dir=tmp_path)
    result = p.run(None, dry_run=True)
    assert isinstance(result, PipelineResult)
    assert result.passed is True
    assert result.artifacts == [str(tmp_path / "manifest.json")]


def test_run_pipeline_writes_valid_manifest(tmp_path: Path) -> None:
    p = Pipeline(preset=Preset(), output_dir=tmp_path)
    p.run(_context_with_triangles(2), dry_run=True)
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "1.0.0"
    assert manifest["target"] == "godot"
    assert manifest["metrics"]["triangle_count"] == 2
    assert manifest["validation"]["passed"] is True


def test_run_pipeline_flags_overage(tmp_path: Path) -> None:
    preset = Preset()
    preset.limits.tri_limit = 1
    p = Pipeline(preset=preset, output_dir=tmp_path)
    result = p.run(_context_with_triangles(5), dry_run=True)
    assert result.passed is False
    codes = [d["code"] for d in result.report["diagnostics"]]
    assert "TRIANGLE_OVERAGE" in codes


def test_run_pipeline_exports_and_zips(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeExporter:
        def export(self, context: Any, output_dir: Path) -> dict[str, Any]:
            path = output_dir / "godot_asset.glb"
            path.write_bytes(b"fake-glb")
            return {"target": "godot", "format": "GLB", "path": str(path)}

    monkeypatch.setattr(
        "blender_mobile_3d.core.pipeline.get_exporter", lambda target: FakeExporter()
    )
    p = Pipeline(preset=Preset(), output_dir=tmp_path)
    result = p.run(_context_with_triangles(1), dry_run=False)
    assert (tmp_path / "godot_asset.glb").is_file()
    assert (tmp_path / "manifest.json").is_file()
    assert (tmp_path / "godot_mobile.zip").is_file()
    assert len(result.artifacts) == 2


def test_run_pipeline_export_failure_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(target: str) -> Any:
        raise RuntimeError("exporter exploded")

    monkeypatch.setattr("blender_mobile_3d.core.pipeline.get_exporter", _boom)
    p = Pipeline(preset=Preset(), output_dir=tmp_path)
    with pytest.raises(ExportError, match="exporter exploded"):
        p.run(_context_with_triangles(1), dry_run=False)


def test_pipeline_default_output_dir() -> None:
    preset = Preset()
    p = Pipeline(preset=preset)
    assert p.output_dir == Path(preset.paths.output_relative)
