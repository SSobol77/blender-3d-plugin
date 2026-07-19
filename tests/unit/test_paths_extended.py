"""Expanded tests for blender_mobile_3d.core.paths."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from blender_mobile_3d.core.errors import PathSafetyError
from blender_mobile_3d.core.paths import project_root_from_blend, safe_join


def test_project_root_from_blend_falls_back_to_cwd(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("BM3D_BLEND_PATH", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(project_root_from_blend, "__module__", "_tests_fake")
    p = project_root_from_blend()
    assert p == tmp_path


def test_project_root_from_blend_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("BM3D_BLEND_PATH", raising=False)
    fake_bpy = types.ModuleType("bpy")
    fake_bpy.context = types.SimpleNamespace(
        blend_data=types.SimpleNamespace(filepath=str(tmp_path / "a.blend"))
    )
    p = project_root_from_blend()
    assert p == tmp_path


def test_safe_join_within_base(tmp_path: Path) -> None:
    out = safe_join(tmp_path, "sub/file.txt")
    assert out == tmp_path / "sub" / "file.txt"


def test_safe_join_escape(tmp_path: Path) -> None:
    with pytest.raises(PathSafetyError):
        safe_join(tmp_path, "../outside")


def test_safe_join_nested_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    with pytest.raises(PathSafetyError):
        safe_join(tmp_path, str(outside))
