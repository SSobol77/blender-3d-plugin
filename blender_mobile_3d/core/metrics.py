"""Scene metrics collection without mutating source data."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SceneMetrics:
    object_count: int = 0
    mesh_count: int = 0
    vertex_count: int = 0
    edge_count: int = 0
    polygon_count: int = 0
    triangle_count: int = 0
    material_slots: int = 0
    unique_materials: int = 0
    texture_count: int = 0
    texture_dimensions: list[tuple[int, int]] = field(default_factory=list)
    uv_map_count: int = 0
    armature_count: int = 0
    bone_count: int = 0
    deform_bone_count: int = 0
    action_count: int = 0
    keyframe_range: tuple[int, int] = (0, 0)
    shape_key_count: int = 0
    modifier_count: int = 0
    modifier_types: list[str] = field(default_factory=list)
    unapplied_transforms: int = 0
    bounding_box: tuple[float, float, float, float, float, float] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
