"""Expanded tests for blender_mobile_3d.core.paths."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from blender_mobile_3d.core.errors import PathSafetyError
from blender_mobile_3d.core.paths import default_output_dir, project_root_from_blend, safe_join


def _purge_bpy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "bpy", raising=False)


def test_project_root_from_blend_falls_back_to_cwd(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _purge_bpy(monkeypatch)
    monkeypatch.chdir(tmp_path)
    assert project_root_from_blend() == tmp_path


def test_project_root_from_blend_uses_blend_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_bpy = types.ModuleType("bpy")
    fake_bpy.context = types.SimpleNamespace(
        blend_data=types.SimpleNamespace(filepath=str(tmp_path / "a.blend"))
    )
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    assert project_root_from_blend() == tmp_path


def test_project_root_from_blend_unsaved_blend(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_bpy = types.ModuleType("bpy")
    fake_bpy.context = types.SimpleNamespace(blend_data=types.SimpleNamespace(filepath=""))
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    monkeypatch.chdir(tmp_path)
    assert project_root_from_blend() == tmp_path


def test_safe_join_within_base(tmp_path: Path) -> None:
    out = safe_join(tmp_path, "sub/file.txt")
    assert out == tmp_path.resolve() / "sub" / "file.txt"


def test_safe_join_escape(tmp_path: Path) -> None:
    with pytest.raises(PathSafetyError):
        safe_join(tmp_path, "../outside")


def test_safe_join_absolute_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    with pytest.raises(PathSafetyError):
        safe_join(tmp_path, str(outside))


def test_safe_join_deep_traversal(tmp_path: Path) -> None:
    with pytest.raises(PathSafetyError):
        safe_join(tmp_path, "a/../../../etc/passwd")


def test_default_output_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _purge_bpy(monkeypatch)
    monkeypatch.chdir(tmp_path)
    out = default_output_dir({"paths": {"output_relative": "export/mobile"}})
    assert out == tmp_path.resolve() / "export" / "mobile"


def test_default_output_dir_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _purge_bpy(monkeypatch)
    monkeypatch.chdir(tmp_path)
    out = default_output_dir({})
    assert out == tmp_path.resolve() / "export" / "mobile"
