"""Tests for blender_mobile_3d.core.scene measurement utilities."""

from __future__ import annotations

from types import SimpleNamespace

from blender_mobile_3d.core.scene import (
    measure_mesh,
    measure_scene,
    scene_metrics,
    texture_dimensions,
    texture_dimensions_from_material,
)


def _poly(n: int) -> SimpleNamespace:
    return SimpleNamespace(vertices=tuple(range(n)))


def _mesh(*polygon_sizes: int) -> SimpleNamespace:
    return SimpleNamespace(
        polygons=[_poly(n) for n in polygon_sizes],
        vertices=list(range(sum(polygon_sizes))),
        edges=list(range(sum(polygon_sizes))),
        loop_triangles=None,
        materials=[],
        uv_layers=[],
        shape_keys=None,
    )


def _mesh_obj(name: str, mesh: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        type="MESH",
        data=mesh,
        modifiers=[],
        matrix_world=SimpleNamespace(is_identity=True),
    )


def test_texture_dimensions_none() -> None:
    assert (0, 0) == texture_dimensions(None)


def test_texture_dimensions_from_material() -> None:
    image = SimpleNamespace(size=(256, 128))
    node = SimpleNamespace(image=image)
    material = SimpleNamespace(node_tree=SimpleNamespace(nodes=[node]))
    assert texture_dimensions_from_material(material) == [(256, 128)]
    assert texture_dimensions_from_material(None) == []


def test_measure_mesh_triangle_counts() -> None:
    # A triangle is 1 triangle, a quad 2, a pentagon 3.
    out = measure_mesh(_mesh(3, 4, 5))
    assert out["polygons"] == 3
    assert out["triangles"] == 1 + 2 + 3


def test_measure_mesh_prefers_loop_triangles() -> None:
    mesh = _mesh(4)
    mesh.loop_triangles = [object(), object()]
    assert measure_mesh(mesh)["triangles"] == 2


def test_measure_scene_empty() -> None:
    scene = SimpleNamespace(objects=[], actions=[])
    out = measure_scene(scene)
    assert out["object_count"] == 0
    assert out["triangle_count"] == 0


def test_measure_scene_none() -> None:
    out = measure_scene(None)
    assert out["object_count"] == 0


def test_measure_scene_counts_meshes_and_materials() -> None:
    mesh = _mesh(3)
    mesh.materials = [SimpleNamespace(name="Mat", node_tree=None)]
    scene = SimpleNamespace(objects=[_mesh_obj("Tri", mesh)], actions=[])
    out = measure_scene(scene)
    assert out["triangle_count"] == 1
    assert out["mesh_count"] == 1
    assert out["unique_materials"] == 1
    assert out["material_slots"] == 1


def test_measure_scene_counts_armatures_and_transforms() -> None:
    bones = [SimpleNamespace(use_deform=True), SimpleNamespace(use_deform=False)]
    armature = SimpleNamespace(name="Rig", type="ARMATURE", data=SimpleNamespace(bones=bones))
    moved = _mesh_obj("Moved", _mesh(4))
    moved.matrix_world = SimpleNamespace(is_identity=False)
    moved.modifiers = [SimpleNamespace(type="DECIMATE")]
    scene = SimpleNamespace(objects=[armature, moved], actions=[])
    out = measure_scene(scene)
    assert out["armature_count"] == 1
    assert out["bone_count"] == 2
    assert out["deform_bone_count"] == 1
    assert out["unapplied_transforms"] == 1
    assert out["modifier_types"] == ["DECIMATE"]


def test_scene_metrics_wrapper() -> None:
    scene = SimpleNamespace(objects=[], actions=[])
    out = scene_metrics(scene)
    assert isinstance(out, dict)
    assert out["object_count"] == 0
