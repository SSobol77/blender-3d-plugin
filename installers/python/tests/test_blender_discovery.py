"""Tests for blender_mobile_3d_installer.blender_discovery."""

from __future__ import annotations

from pathlib import Path

import pytest
from blender_mobile_3d_installer import blender_discovery as bd
from blender_mobile_3d_installer.exit_codes import (
    AMBIGUOUS_BLENDER,
    BLENDER_NOT_FOUND,
    UNSUPPORTED_BLENDER_VERSION,
    InstallerError,
)


def test_probe_executable_parses_version(fake_blender) -> None:
    path = fake_blender(version="5.1.2")
    version, supported = bd.probe_executable(path)
    assert version == "5.1.2"
    assert supported is True


def test_probe_executable_rejects_old_version(fake_blender) -> None:
    path = fake_blender(version="3.6.0")
    version, supported = bd.probe_executable(path)
    assert version == "3.6.0"
    assert supported is False


def test_probe_executable_missing_path_returns_none() -> None:
    version, supported = bd.probe_executable("/does/not/exist/blender")
    assert version is None
    assert supported is False


def test_discover_explicit_nonexistent_path_yields_no_candidates() -> None:
    assert bd.discover_blenders(explicit="/does/not/exist") == []


def test_discover_explicit_existing_path(fake_blender) -> None:
    path = fake_blender(version="4.9.0")
    candidates = bd.discover_blenders(explicit=path)
    assert len(candidates) == 1
    assert candidates[0].path == path
    assert candidates[0].source == "explicit"
    assert candidates[0].supported is True


def test_select_blender_not_found_raises() -> None:
    with pytest.raises(InstallerError) as excinfo:
        bd.select_blender(explicit="/does/not/exist")
    assert excinfo.value.exit_code == BLENDER_NOT_FOUND


def test_select_blender_unsupported_version_raises(fake_blender) -> None:
    path = fake_blender(version="2.0.0")
    with pytest.raises(InstallerError) as excinfo:
        bd.select_blender(explicit=path)
    assert excinfo.value.exit_code == UNSUPPORTED_BLENDER_VERSION


def test_select_blender_explicit_supported_returns_candidate(fake_blender) -> None:
    path = fake_blender(version="4.5.0")
    candidate = bd.select_blender(explicit=path)
    assert candidate.path == path
    assert candidate.supported is True


def test_select_blender_ambiguous_multiple_supported(
    monkeypatch: pytest.MonkeyPatch, fake_blender
) -> None:
    first = fake_blender(version="4.9.0")
    # A second fake executable at a different path, also supported.
    import shutil as _shutil
    import stat as _stat
    from pathlib import Path

    second_dir = Path(first).parent / "second"
    second_dir.mkdir()
    second = second_dir / "blender"
    _shutil.copy(first, second)
    second.chmod(second.stat().st_mode | _stat.S_IEXEC)

    monkeypatch.setattr(bd.shutil, "which", lambda name: first)
    monkeypatch.setattr(bd, "_common_locations", lambda: [str(second)])

    with pytest.raises(InstallerError) as excinfo:
        bd.select_blender(explicit=None)
    assert excinfo.value.exit_code == AMBIGUOUS_BLENDER


def test_select_blender_single_from_path(monkeypatch: pytest.MonkeyPatch, fake_blender) -> None:
    path = fake_blender(version="4.9.0")
    monkeypatch.setattr(bd.shutil, "which", lambda name: path)
    monkeypatch.setattr(bd, "_common_locations", lambda: [])

    candidate = bd.select_blender(explicit=None)
    assert candidate.path == path


def test_select_blender_no_candidates_at_all(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bd.shutil, "which", lambda name: None)
    monkeypatch.setattr(bd, "_common_locations", lambda: [])
    with pytest.raises(InstallerError) as excinfo:
        bd.select_blender(explicit=None)
    assert excinfo.value.exit_code == BLENDER_NOT_FOUND


def test_discover_blenders_dedupes_by_real_path(
    monkeypatch: pytest.MonkeyPatch, fake_blender
) -> None:
    path = fake_blender(version="4.9.0")
    monkeypatch.setattr(bd.shutil, "which", lambda name: path)
    monkeypatch.setattr(bd, "_common_locations", lambda: [path])
    candidates = bd.discover_blenders(explicit=None)
    assert len(candidates) == 1


def test_probe_executable_output_without_version_string(fake_blender, tmp_path: Path) -> None:
    script = tmp_path / "not-blender"
    script.write_text("#!/bin/sh\necho 'hello world'\n")
    script.chmod(0o755)
    version, supported = bd.probe_executable(str(script))
    assert version is None
    assert supported is False


def test_probe_executable_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    def _raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="blender", timeout=1)

    monkeypatch.setattr(bd.subprocess, "run", _raise_timeout)
    version, supported = bd.probe_executable("/whatever/blender")
    assert version is None
    assert supported is False


@pytest.mark.parametrize("system", ["Linux", "Darwin", "Windows", "SomeOtherOS"])
def test_common_locations_covers_every_platform_branch(
    monkeypatch: pytest.MonkeyPatch, system: str
) -> None:
    monkeypatch.setattr(bd.platform, "system", lambda: system)
    locations = bd._common_locations()
    assert isinstance(locations, list)


def test_add_candidate_handles_unresolvable_path(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(self):
        raise OSError("cannot resolve")

    monkeypatch.setattr(bd.Path, "resolve", _boom)
    seen: dict = {}
    bd._add_candidate(seen, "/some/path", "test")
    assert "/some/path" in seen
