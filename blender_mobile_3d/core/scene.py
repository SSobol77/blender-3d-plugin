"""Scene measurement utilities with Blender-optional import safety."""

from __future__ import annotations

from typing import Any

from blender_mobile_3d.core.geometry import count_triangles


def texture_dimensions(image: Any) -> tuple[int, int]:
    if image is None:
        return (0, 0)
    try:
        return (int(image.size[0]), int(image.size[1]))
    except Exception:
        return (0, 0)


def texture_dimensions_from_material(material: Any) -> list[tuple[int, int]]:
    dims: list[tuple[int, int]] = []
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


def measure_mesh(mesh: Any) -> dict[str, int]:
    if mesh is None:
        return {}
    poly_data = getattr(mesh, "polygons", []) or []
    return {
        "vertices": len(getattr(mesh, "vertices", [])),
        "edges": len(getattr(mesh, "edges", [])),
        "polygons": len(poly_data),
        "triangles": count_triangles(mesh),
    }


def measure_scene(scene: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {
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

    material_usage: dict[str, int] = {}
    texture_dims: list[tuple[int, int]] = []
    modifiers: list[str] = []
    unapplied_transforms = 0

    if scene is None:
        return summary

    objects = list(getattr(scene, "objects", []) or [])
    summary["object_count"] = len(objects)

    for obj in objects:
        obj_type = getattr(obj, "type", None)
        if obj_type == "ARMATURE":
            summary["armature_count"] += 1
            armature = getattr(obj, "data", None)
            bones = list(getattr(armature, "bones", []) or [])
            summary["bone_count"] += len(bones)
            summary["deform_bone_count"] += sum(
                1 for bone in bones if getattr(bone, "use_deform", True)
            )
        if obj_type == "MESH":
            mesh = getattr(obj, "data", None)
            summary["mesh_count"] += 1
            if mesh is not None:
                mesh_summary = measure_mesh(mesh)
                summary["triangle_count"] += int(mesh_summary.get("triangles", 0))

                for slot in getattr(mesh, "materials", []) or []:
                    if slot is not None:
                        summary["material_slots"] += 1
                        material_usage[slot.name] = material_usage.get(slot.name, 0) + 1
                        texture_dims.extend(texture_dimensions_from_material(slot))

                if getattr(mesh, "uv_layers", None):
                    summary["uv_map_count"] += len(getattr(mesh, "uv_layers", []) or [])

                shape_keys = getattr(mesh, "shape_keys", None)
                if shape_keys is not None:
                    summary["shape_key_count"] += max(
                        0, len(getattr(shape_keys, "key_blocks", [])) - 1
                    )

            for modifier in getattr(obj, "modifiers", []) or []:
                modifiers.append(modifier.type)

            matrix = getattr(obj, "matrix_world", None)
            if matrix is not None and not getattr(matrix, "is_identity", True):
                unapplied_transforms += 1

    summary["unique_materials"] = len(material_usage)
    summary["texture_count"] = len(texture_dims)
    summary["texture_dimensions"] = texture_dims
    summary["modifier_count"] = len(modifiers)
    summary["modifier_types"] = sorted(set(modifiers))
    summary["unapplied_transforms"] = unapplied_transforms

    return summary


def scene_metrics(scene: Any) -> dict[str, Any]:
    return measure_scene(scene)
