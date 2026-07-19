"""Tests for package entrypoints, adapters, and small core helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import blender_mobile_3d
from blender_mobile_3d.adapters.agents import AGENT_NOTES, notes_for
from blender_mobile_3d.adapters.blender_mcp import default_socket_path
from blender_mobile_3d.core.blender import require_bpy
from blender_mobile_3d.core.errors import (
    BlenderMobileError,
    ConfigurationError,
    ExportError,
    PathSafetyError,
    ValidationError,
)
from blender_mobile_3d.core.geometry import (
    count_triangles,
    measure_mesh,
    mesh_texture_dimensions,
)
from blender_mobile_3d.core.manifests import sig_hash, write_artifact_manifest
from blender_mobile_3d.core.metrics import SceneMetrics
from blender_mobile_3d.core.types import Context, Scene


def _purge_blender_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "bpy", raising=False)
    monkeypatch.delitem(sys.modules, "blender_mobile_3d.operators.blender_ui", raising=False)


def test_version_and_bl_info() -> None:
    assert blender_mobile_3d.__version__ == "1.0.0"
    assert blender_mobile_3d.bl_info["blender"] == (4, 3, 0)
    assert blender_mobile_3d.bl_info["license"] == "GPL-2.0-only"


def test_register_outside_blender_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _purge_blender_modules(monkeypatch)
    with pytest.raises(RuntimeError, match="bpy is unavailable"):
        blender_mobile_3d.register()


def test_unregister_outside_blender_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    _purge_blender_modules(monkeypatch)
    blender_mobile_3d.unregister()


def test_require_bpy_outside_blender(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "bpy", raising=False)
    with pytest.raises(RuntimeError, match="bpy.*unavailable"):
        require_bpy()


def test_get_context_outside_blender(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "bpy", raising=False)
    import blender_mobile_3d.operators.register as _reg

    with pytest.raises(RuntimeError):
        _reg.get_context()


def test_agent_notes() -> None:
    assert set(AGENT_NOTES) == {"hermes", "claude_code", "codex", "kimi"}
    assert "terminal" in notes_for("claude_code")
    assert "Blender CLI" in notes_for("unknown-agent")


def test_default_socket_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BM3D_MCP_HOST", raising=False)
    monkeypatch.delenv("BM3D_MCP_PORT", raising=False)
    assert default_socket_path() == "127.0.0.1:9876"
    monkeypatch.setenv("BM3D_MCP_HOST", "0.0.0.0")  # noqa: S104 - test value only
    monkeypatch.setenv("BM3D_MCP_PORT", "1234")
    assert default_socket_path() == "0.0.0.0:1234"  # noqa: S104 - test value only


def test_errors_hierarchy() -> None:
    for err in (ConfigurationError, ValidationError, ExportError, PathSafetyError):
        assert issubclass(err, BlenderMobileError)


def test_geometry_count_triangles_fallback() -> None:
    from types import SimpleNamespace

    mesh = SimpleNamespace(
        loop_triangles=None,
        polygons=[SimpleNamespace(vertices=(0, 1, 2, 3))],
    )
    assert count_triangles(mesh) == 2


def test_geometry_measure_mesh_none() -> None:
    assert measure_mesh(None) == {"vertices": 0, "edges": 0, "polygons": 0, "triangles": 0}


def test_geometry_mesh_texture_dimensions() -> None:
    from types import SimpleNamespace

    image = SimpleNamespace(size=(64, 32))
    node = SimpleNamespace(image=image)
    material = SimpleNamespace(use_nodes=True, node_tree=SimpleNamespace(nodes=[node]))
    mesh = SimpleNamespace(materials=[material, None])
    assert mesh_texture_dimensions(mesh) == [(64, 32)]
    assert mesh_texture_dimensions(None) == []


def test_manifests_helpers(tmp_path: Path) -> None:
    f = tmp_path / "a.bin"
    f.write_bytes(b"payload")
    assert len(sig_hash(f)) == 64
    manifest = write_artifact_manifest([f])
    assert manifest["artifact_count"] == 1
    assert manifest["artifacts"][0]["filename"] == "a.bin"


def test_scene_metrics_dataclass_defaults() -> None:
    metrics = SceneMetrics()
    assert metrics.triangle_count == 0
    assert metrics.texture_dimensions == []
    assert metrics.bounding_box == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def test_types_aliases() -> None:
    assert Context is object
    assert Scene is object


def test_config_defaults() -> None:
    from blender_mobile_3d.config.defaults import DEFAULT_LIMITS, DEFAULT_PRESET, DEFAULT_TARGET

    assert DEFAULT_PRESET == "low_poly"
    assert DEFAULT_TARGET == "godot"
    assert DEFAULT_LIMITS["tri_limit"] == 120
