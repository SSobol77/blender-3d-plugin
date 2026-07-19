"""Tests for blender_mobile_3d.core.scene measurement utilities."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from blender_mobile_3d.core.scene import measure_mesh, measure_scene, scene_metrics, texture_dimensions


def test_texture_dimensions_none():
    assert (0, 0) == texture_dimensions(None)


def test_measure_mesh_with_polygons():
    mesh = MagicMock()
    mesh.polygons = [MagicMock(vertices=(1, 2, 3)), MagicMock(vertices=(3, 4, 5))]
    mesh.vertices = [0, 1, 2, 3, 4, 5]
    mesh.edges = [0, 1, 2, 3]
    out = measure_mesh(mesh)
    assert out["polygons"] == 2
    assert out["triangles"] == 6


def test_measure_scene_empty():
    scene = MagicMock()
    scene.objects = []
    scene.actions = []
    out = measure_scene(scene)
    assert out["object_count"] == 0
    assert out["triangle_count"] == 0


def test_measure_scene_counts_meshes():
    mesh = MagicMock()
    mesh.polygons = [MagicMock(vertices=(1, 2, 3))]
    mesh.materials = [MagicMock()]
    mesh.uv_layers = []
    mesh.shape_keys = None
    obj = MagicMock()
    obj.type = "MESH"
    obj.data = mesh
    obj.modifiers = []
    obj.matrix_world = MagicMock(is_identity=True)
    scene = MagicMock()
    scene.objects = [obj]
    scene.actions = []
    out = measure_scene(scene)
    assert out["triangle_count"] == 3


def test_scene_metrics_wrapper():
    scene = MagicMock()
    scene.objects = []
    scene.actions = []
    out = scene_metrics(scene)
    assert isinstance(out, dict)
    assert out["object_count"] == 0
