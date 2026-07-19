"""Base exporter interface and target-specific exporter wrappers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseExporter(ABC):
    @abstractmethod
    def export(self, context: Any, output_dir: Path) -> dict[str, Any]:
        raise NotImplementedError


class GodotExporter(BaseExporter):
    def export(self, context: Any, output_dir: Path) -> dict[str, Any]:
        path = output_dir / "godot_asset.glb"
        bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB")  # type: ignore[name-defined]
        return {"target": "godot", "format": "GLB", "path": str(path)}


class UnityExporter(BaseExporter):
    def export(self, context: Any, output_dir: Path) -> dict[str, Any]:
        path = output_dir / "unity_asset.fbx"
        bpy.ops.export_scene.fbx(
            filepath=str(path), use_selection=False, apply_scale_options="FBX_SCALE_ALL"
        )  # type: ignore[name-defined]
        return {"target": "unity", "format": "FBX", "path": str(path)}


class UnrealExporter(BaseExporter):
    def export(self, context: Any, output_dir: Path) -> dict[str, Any]:
        path = output_dir / "unreal_asset.glb"
        bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB")  # type: ignore[name-defined]
        return {"target": "unreal", "format": "GLB", "path": str(path)}


class FlutterExporter(BaseExporter):
    def export(self, context: Any, output_dir: Path) -> dict[str, Any]:
        path = output_dir / "flutter_asset.glb"
        bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB")  # type: ignore[name-defined]
        return {"target": "flutter", "format": "GLB", "path": str(path)}


class AndroidExporter(BaseExporter):
    def export(self, context: Any, output_dir: Path) -> dict[str, Any]:
        path = output_dir / "android_asset.glb"
        bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB")  # type: ignore[name-defined]
        return {"target": "kotlin", "format": "GLB", "path": str(path)}


EXPORTERS = {
    "godot": GodotExporter,
    "unity": UnityExporter,
    "unreal": UnrealExporter,
    "flutter": FlutterExporter,
    "kotlin": AndroidExporter,
}
