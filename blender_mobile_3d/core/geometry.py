"""Scene measurement utilities for Blender dependency graph data."""

from __future__ import annotations

from typing import Dict, List

from blender_mobile_3d.core.errors import BlenderMobileError


def count_triangles(mesh) -> int:
    if mesh is None:
        return 0
    return sum(len(p.vertices) for p in mesh.polygons)


def measure_mesh(mesh) -> Dict[str, int]:
    return {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "polygons": len(mesh.polygons),
        "triangles": count_triangles(mesh),
    }


def texture_dimensions(image) -> tuple[int, int]:
    if image is None:
        return (0, 0)
    try:
        return (int(image.size[0]), int(image.size[1]))
    except Exception:
        return (0, 0)


def mesh_texture_dimensions(mesh) -> List[tuple[int, int]]:
    dims: List[tuple[int, int]] = []
    if mesh is None:
        return dims
    for mat in getattr(mesh, "materials", []) or []:
        if mat is None:
            continue
        for node in getattr(mat, "node_tree", None).nodes if getattr(mat, "use_nodes", False) else []:
            image = getattr(node, "image", None)
            if image is not None:
                dims.append(texture_dimensions(image))
    return dims


def object_world_bounds(obj):
    matrix = obj.matrix_world
    bbox = [matrix @ mathutils.Vector(corner) for corner in obj.bound_box]
    xs = [v.x for v in bbox]
    ys = [v.y for v in bbox]
    zs = [v.z for v in bbox]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)
