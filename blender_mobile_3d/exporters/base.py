"""Base exporter interface and target-specific exporter wrappers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from blender_mobile_3d.core.blender import require_bpy
from blender_mobile_3d.core.errors import ExportError


class BaseExporter(ABC):
    @abstractmethod
    def export(self, context: Any, output_dir: Path) -> dict[str, Any]:
        """Write the scene to ``output_dir`` and return an artifact record."""

    @staticmethod
    def _export_gltf(path: Path) -> None:
        bpy = require_bpy()
        bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB")

    @staticmethod
    def _export_fbx(path: Path) -> None:
        bpy = require_bpy()
        bpy.ops.export_scene.fbx(
            filepath=str(path), use_selection=False, apply_scale_options="FBX_SCALE_ALL"
        )


class GodotExporter(BaseExporter):
    def export(self, context: Any, output_dir: Path) -> dict[str, Any]:
        path = output_dir / "godot_asset.glb"
        self._export_gltf(path)
        return {"target": "godot", "format": "GLB", "path": str(path)}


class UnityExporter(BaseExporter):
    def export(self, context: Any, output_dir: Path) -> dict[str, Any]:
        path = output_dir / "unity_asset.fbx"
        self._export_fbx(path)
        return {"target": "unity", "format": "FBX", "path": str(path)}


class UnrealExporter(BaseExporter):
    def export(self, context: Any, output_dir: Path) -> dict[str, Any]:
        path = output_dir / "unreal_asset.glb"
        self._export_gltf(path)
        return {"target": "unreal", "format": "GLB", "path": str(path)}


class FlutterExporter(BaseExporter):
    def export(self, context: Any, output_dir: Path) -> dict[str, Any]:
        path = output_dir / "flutter_asset.glb"
        self._export_gltf(path)
        return {"target": "flutter", "format": "GLB", "path": str(path)}


class AndroidExporter(BaseExporter):
    def export(self, context: Any, output_dir: Path) -> dict[str, Any]:
        path = output_dir / "android_asset.glb"
        self._export_gltf(path)
        return {"target": "kotlin", "format": "GLB", "path": str(path)}


EXPORTERS: dict[str, type[BaseExporter]] = {
    "godot": GodotExporter,
    "unity": UnityExporter,
    "unreal": UnrealExporter,
    "flutter": FlutterExporter,
    "kotlin": AndroidExporter,
}


def get_exporter(target: str) -> BaseExporter:
    """Return an exporter instance for ``target`` or raise ExportError."""
    try:
        exporter_cls = EXPORTERS[target]
    except KeyError as exc:
        known = ", ".join(sorted(EXPORTERS))
        raise ExportError(f"Unknown export target: {target!r} (known: {known})") from exc
    return exporter_cls()
