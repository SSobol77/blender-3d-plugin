"""Scene measurement utilities with Blender-optional import safety."""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional


def texture_dimensions(image: Any) -> tuple[int, int]:
    if image is None:
        return (0, 0)
    try:
        return (int(image.size[0]), int(image.size[1]))
    except Exception:
        return (0, 0)


def texture_dimensions_from_material(material: Any) -> List[tuple[int, int]]:
    dims: List[tuple[int, int]] = []
    if material is None:
        return dims
    node_tree = getattr(material, "node_tree", None)
    if node_tree is None:
        return dims
    for node in getattr(node_tree, "nodes", []):
        image = getattr(node, "image", None)
        if image is not None:
            dims.append(texture_dimensions(image))
    return dims


def measure_mesh(mesh: Any) -> Dict[str, int]:
    if mesh is None:
        return {}
    poly_data = getattr(mesh, "polygons", []) or []
    triangles = sum(len(p.vertices) for p in poly_data)
    return {
        "vertices": len(getattr(mesh, "vertices", [])),
        "edges": len(getattr(mesh, "edges", [])),
        "polygons": len(poly_data),
        "triangles": triangles,
    }


def measure_scene(scene: Any) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "object_count": 0,
        "mesh_count": 0,
        "triangle_count": 0,
        "material_slots": 0,
        "unique_materials": 0,
        "texture_count": 0,
        "texture_dimensions": [],
        "uv_map_count": 0,
        "armature_count": 0,
        "bone_count": 0,
        "deform_bone_count": 0,
        "action_count": len(getattr(scene, "actions", [])) if hasattr(scene, "actions") else 0,
        "shape_key_count": 0,
        "modifier_count": 0,
        "modifier_types": [],
        "unapplied_transforms": 0,
        "bounding_box": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    }

    material_usage: Dict[str, int] = {}
    texture_dims: List[tuple[int, int]] = []
    modifiers: List[str] = []
    unapplied_transforms = 0

    if scene is None:
        return summary

    objects = list(getattr(scene, "objects", []) or [])
    summary["object_count"] = len(objects)

    for obj in objects:
        if getattr(obj, "type", None) == "MESH":
            mesh = getattr(obj, "data", None)
            summary["mesh_count"] += 1
            if mesh is not None:
                mesh_summary = measure_mesh(mesh)
                summary["triangle_count"] += int(mesh_summary.get("triangles", 0))

                for index, slot in enumerate(getattr(mesh, "materials", []) or []):
                    if slot is not None:
                        summary["material_slots"] += 1
                        material_usage[slot.name] = material_usage.get(slot.name, 0) + 1
                        texture_dims.extend(texture_dimensions_from_material(slot))

                if getattr(mesh, "uv_layers", None):
                    summary["uv_map_count"] += len(getattr(mesh, "uv_layers", []) or [])

                summary["shape_key_count"] += (
                    len(getattr(mesh, "shape_keys", {}).key_blocks) - 1
                    if getattr(mesh, "shape_keys", None)
                    else 0
                )

            for modifier in getattr(obj, "modifiers", []) or []:
                modifiers.append(modifier.type)
                matrix = getattr(obj, "matrix_world", None)
                if matrix is not None and not getattr(obj, "matrix_world", None).is_identity:
                    unapplied_transforms += 1

    summary["unique_materials"] = len(material_usage)
    summary["texture_count"] = len(texture_dims)
    summary["texture_dimensions"] = texture_dims
    summary["modifier_count"] = len(modifiers)
    summary["modifier_types"] = sorted(set(modifiers))
    summary["unapplied_transforms"] = unapplied_transforms

    return summary


def scene_metrics(scene: Any) -> Dict[str, Any]:
    return measure_scene(scene)
