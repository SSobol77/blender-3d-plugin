"""Pipeline orchestration with dry-run and export options."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from blender_mobile_3d.config.models import Preset
from blender_mobile_3d.core.errors import ConfigurationError, ExportError, PathSafetyError
from blender_mobile_3d.core.logging import Report
from blender_mobile_3d.core.manifests import build_zip, sha256_file
from blender_mobile_3d.core.metrics import SceneMetrics
from blender_mobile_3d.core.pipeline import PipelineResult
from blender_mobile_3d.core.scene import measure_scene
from blender_mobile_3d.core.validation import ValidationEngine


class Pipeline:
    def __init__(self, preset: Preset, output_dir: Path | None = None) -> None:
        self.preset = preset
        self.output_dir = output_dir or preset.paths.output_relative

    def run(self, context: Any, dry_run: bool = True) -> PipelineResult:
        report = Report()

        try:
            scene = context.scene
        except Exception:
            scene = None

        metrics = self._collect_metrics(scene)
        validation = self._validate(metrics)
        report.add(validation)

        artifacts: list[str] = []
        if not dry_run and scene is not None:
            try:
                artifacts = self._export(context, scene)
            except Exception as exc:
                raise ExportError(str(exc)) from exc

        manifest = self._build_manifest(metrics, report.to_dict(), artifacts)
        manifest_path = self._write_manifest(manifest)
        artifacts.append(str(manifest_path))

        if not dry_run and artifacts:
            zip_manifest = build_zip(
                self.output_dir,
                [Path(a) for a in artifacts],
                self.output_dir / f"{self.preset.target}_mobile.zip",
            )

        return PipelineResult(passed=report.passed, report=report.to_dict(), artifacts=artifacts)

    def _collect_metrics(self, scene: Any) -> dict[str, Any]:
        if scene is None:
            return {}
        return measure_scene(scene)

    def _validate(self, metrics: dict[str, Any]) -> Any:
        engine = ValidationEngine(limits=self.preset.limits.__dict__)
        issues = engine.validate_metrics(metrics)
        for issue in issues:
            from blender_mobile_3d.core.logging import Diagnostic
            report.add(Diagnostic(**issue))
        return report

    def _export(self, context: Any, scene: Any) -> list[str]:  # pragma: no cover - adapter boundary
        raise NotImplementedError("Export adapters implement actual export operations.")

    def _build_manifest(self, metrics: dict[str, Any], report: dict[str, Any], artifacts: list[str]) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "plugin_version": self.preset.plugin_version,
            "preset": self.preset.preset,
            "target": self.preset.target,
            "limits": self.preset.limits.__dict__,
            "export_options": self.preset.export.__dict__,
            "paths": self.preset.paths.__dict__,
            "metrics": metrics,
            "validation": report,
            "artifacts": artifacts,
        }

    def _write_manifest(self, manifest: dict[str, Any]) -> Path:
        target = self.output_dir / "manifest.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        return target
