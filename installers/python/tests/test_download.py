"""Tests for blender_mobile_3d_installer.download."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from blender_mobile_3d_installer import download as download_mod
from blender_mobile_3d_installer.exit_codes import (
    CHECKSUM_MISMATCH,
    DOWNLOAD_FAILURE,
    InstallerError,
)


def test_download_success_and_checksum_match(http_fixture_server, tmp_path: Path) -> None:
    base_url, directory = http_fixture_server
    payload = b"artifact bytes" * 100
    (directory / "artifact.bin").write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()

    dest = tmp_path / "out" / "artifact.bin"
    result = download_mod.download_artifact(
        f"{base_url}/artifact.bin", dest, digest, max_size_bytes=10_000
    )
    assert result == dest
    assert dest.read_bytes() == payload


def test_download_checksum_mismatch_cleans_up(http_fixture_server, tmp_path: Path) -> None:
    base_url, directory = http_fixture_server
    (directory / "artifact.bin").write_bytes(b"real content")

    dest = tmp_path / "out" / "artifact.bin"
    with pytest.raises(InstallerError) as excinfo:
        download_mod.download_artifact(f"{base_url}/artifact.bin", dest, "f" * 64, 10_000)
    assert excinfo.value.exit_code == CHECKSUM_MISMATCH
    assert not dest.exists()
    assert list(dest.parent.glob(".download-*")) == []


def test_download_over_size_limit_rejected(http_fixture_server, tmp_path: Path) -> None:
    base_url, directory = http_fixture_server
    (directory / "big.bin").write_bytes(b"x" * 5000)
    dest = tmp_path / "out" / "big.bin"

    with pytest.raises(InstallerError) as excinfo:
        download_mod.download_artifact(f"{base_url}/big.bin", dest, "0" * 64, max_size_bytes=100)
    assert excinfo.value.exit_code == DOWNLOAD_FAILURE
    assert not dest.exists()


def test_download_404_raises(http_fixture_server, tmp_path: Path) -> None:
    base_url, _directory = http_fixture_server
    dest = tmp_path / "out" / "missing.bin"
    with pytest.raises(InstallerError) as excinfo:
        download_mod.download_artifact(f"{base_url}/missing.bin", dest, "0" * 64, 10_000)
    assert excinfo.value.exit_code == DOWNLOAD_FAILURE


def test_download_rejects_non_https_non_loopback(tmp_path: Path) -> None:
    with pytest.raises(InstallerError) as excinfo:
        download_mod.download_artifact(
            "http://example.com/artifact.bin", tmp_path / "out.bin", "0" * 64, 10_000
        )
    assert excinfo.value.exit_code == DOWNLOAD_FAILURE


def test_download_connection_refused_raises(tmp_path: Path) -> None:
    with pytest.raises(InstallerError) as excinfo:
        download_mod.download_artifact(
            "http://127.0.0.1:1/artifact.bin", tmp_path / "out.bin", "0" * 64, 10_000
        )
    assert excinfo.value.exit_code == DOWNLOAD_FAILURE
