"""Scene measurement utilities for Blender dependency graph data."""

from __future__ import annotations

from typing import Any


def count_triangles(mesh: Any) -> int:
    """Return the actual triangle count for the supplied mesh.

    Blender meshes expose ``mesh.calc_loop_triangles()`` and
    ``mesh.loop_triangles`` after evaluation when modifiers are applied.
    When those are unavailable, each n-gon contributes ``n - 2`` triangles
    (fan triangulation), never fewer than one.
    """

    loop_triangles = getattr(mesh, "loop_triangles", None)
    if loop_triangles:
        return len(loop_triangles)
    return sum(
        max(1, len(getattr(polygon, "vertices", [])) - 2)
        for polygon in getattr(mesh, "polygons", [])
    )


def measure_mesh(mesh: Any) -> dict[str, int]:
    if mesh is None:
        return {"vertices": 0, "edges": 0, "polygons": 0, "triangles": 0}
    return {
        "vertices": len(getattr(mesh, "vertices", [])),
        "edges": len(getattr(mesh, "edges", [])),
        "polygons": len(getattr(mesh, "polygons", [])),
        "triangles": count_triangles(mesh),
    }


def texture_dimensions(image: Any) -> tuple[int, int]:
    if image is None:
        return (0, 0)
    try:
        return (int(image.size[0]), int(image.size[1]))
    except Exception:  # pragma: no cover - defensive fallback
        return (0, 0)


def mesh_texture_dimensions(mesh: Any) -> list[tuple[int, int]]:
    dims: list[tuple[int, int]] = []
    if mesh is None:
        return dims
    for material in getattr(mesh, "materials", []) or []:
        if material is None:
            continue
        if not getattr(material, "use_nodes", False):
            continue
        for node in getattr(getattr(material, "node_tree", None), "nodes", []) or []:
            image = getattr(node, "image", None)
            if image is not None:
                dims.append(texture_dimensions(image))
    return dims


def object_world_bounds(obj: Any) -> tuple[float, float, float, float, float, float]:
    import mathutils

    matrix = obj.matrix_world
    corners = [matrix @ mathutils.Vector(corner) for corner in obj.bound_box]
    xs = [float(v.x) for v in corners]
    ys = [float(v.y) for v in corners]
    zs = [float(v.z) for v in corners]
    return (
        min(xs),
        max(xs),
        min(ys),
        max(ys),
        min(zs),
        max(zs),
    )
