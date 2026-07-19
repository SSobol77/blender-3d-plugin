"""Tests for blender_mobile_3d.core.manifests."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from blender_mobile_3d.core.manifests import build_zip, sha256_file


def test_sha256_file(tmp_path: Path) -> None:
    file_a = tmp_path / "a.txt"
    file_a.write_text("alpha", encoding="utf-8")
    digest = sha256_file(file_a)
    assert isinstance(digest, str)
    assert len(digest) == 64


def test_build_zip_creates_archive(tmp_path: Path) -> None:
    (tmp_path / "src.txt").write_text("data", encoding="utf-8")
    zpath = tmp_path / "out.zip"
    manifest = build_zip(tmp_path, [tmp_path / "src.txt"], zpath)
    assert zpath.exists()
    assert zipfile.is_zipfile(zpath)
    assert len(manifest) == 1


def test_build_zip_rejects_outside_member(tmp_path: Path):
    export_dir = tmp_path / "export"
    export_dir.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    zpath = tmp_path / "out.zip"
    with pytest.raises(ValueError, match="outside export dir"):
        build_zip(export_dir, [outside], zpath)
