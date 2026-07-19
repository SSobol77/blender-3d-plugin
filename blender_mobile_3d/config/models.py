"""Typed preset and manifest models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Limits:
    tri_limit: int = 120
    tex_max: int = 512
    material_limit: int = 4
    bone_limit: int = 60


@dataclass
class ExportOptions:
    apply_scale: bool = True
    triangulate: bool = False
    bake_animation: bool = True
    uv_requirements: str = "at_least_one"
    alpha_support: bool = False


@dataclass
class PathConfig:
    use_project_output: bool = True
    output_relative: str = "export/mobile"


@dataclass
class Preset:
    schema_version: str = "1.0.0"
    plugin_version: str = "1.0.0"
    preset: str = "low_poly"
    target: str = "godot"
    limits: Limits = field(default_factory=Limits)
    paths: PathConfig = field(default_factory=PathConfig)
    export: ExportOptions = field(default_factory=ExportOptions)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Preset:
        limits = Limits(**data.get("limits", {}))
        paths = PathConfig(**data.get("paths", {}))
        export = ExportOptions(**data.get("export", {}))
        return cls(
            schema_version=str(data.get("schema_version", cls.schema_version)),
            plugin_version=str(data.get("plugin_version", cls.plugin_version)),
            preset=str(data.get("preset", cls.preset)),
            target=str(data.get("target", cls.target)),
            limits=limits,
            paths=paths,
            export=export,
        )
