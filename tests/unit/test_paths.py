"""Unit tests for blender_mobile_3d.core.paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from blender_mobile_3d.core.paths import safe_join
from blender_mobile_3d.core.errors import PathSafetyError


def test_safe_join_allowed(tmp_path: Path) -> None:
    target = safe_join(tmp_path, "export/mobile")
    assert target.parent.name == "export"


def test_safe_join_escape(tmp_path: Path) -> None:
    with pytest.raises(PathSafetyError):
        safe_join(tmp_path, "../outside")
