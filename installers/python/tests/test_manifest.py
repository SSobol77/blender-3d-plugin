"""Tests for blender_mobile_3d_installer.manifest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from blender_mobile_3d_installer import manifest as manifest_mod
from blender_mobile_3d_installer.exit_codes import MANIFEST_FAILURE, InstallerError

FIXTURES = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "installer"


def test_valid_manifest_fixture_passes_structural_validation() -> None:
    data = json.loads((FIXTURES / "manifest_valid.json").read_text(encoding="utf-8"))
    result = manifest_mod.validate_manifest_structure(data)
    assert result.version == "1.0.0"
    assert result.extension.filename == "blender_mobile_3d-1.0.0.zip"
    assert len(result.extension.sha256) == 64


def test_malformed_manifest_fixture_is_not_valid_json() -> None:
    raw = (FIXTURES / "manifest_malformed.json").read_text(encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        json.loads(raw)


def test_schema_invalid_manifest_fixture_fails_structural_validation() -> None:
    data = json.loads((FIXTURES / "manifest_schema_invalid.json").read_text(encoding="utf-8"))
    with pytest.raises(InstallerError) as excinfo:
        manifest_mod.validate_manifest_structure(data)
    assert excinfo.value.exit_code == MANIFEST_FAILURE


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d.__setitem__("schema_version", "9.9.9"),
        lambda d: d.__setitem__("version", "not-a-version"),
        lambda d: d.pop("artifacts"),
        lambda d: d["artifacts"]["extension"].__setitem__("sha256", "short"),
        lambda d: d["artifacts"]["extension"].__setitem__("size", -5),
        lambda d: d["artifacts"]["extension"].pop("filename"),
    ],
)
def test_various_structural_defects_raise(mutation) -> None:
    data = json.loads((FIXTURES / "manifest_valid.json").read_text(encoding="utf-8"))
    mutation(data)
    with pytest.raises(InstallerError):
        manifest_mod.validate_manifest_structure(data)


def test_non_object_root_raises() -> None:
    with pytest.raises(InstallerError):
        manifest_mod.validate_manifest_structure([1, 2, 3])


def test_fetch_manifest_success(http_fixture_server) -> None:
    base_url, directory = http_fixture_server
    data = json.loads((FIXTURES / "manifest_valid.json").read_text(encoding="utf-8"))
    data["artifacts"]["extension"]["url"] = f"{base_url}/blender_mobile_3d-1.0.0.zip"
    (directory / "release-manifest.json").write_text(json.dumps(data), encoding="utf-8")

    fetched = manifest_mod.fetch_manifest("1.0.0", manifest_url=f"{base_url}/release-manifest.json")
    assert fetched.version == "1.0.0"


def test_fetch_manifest_404_raises(http_fixture_server) -> None:
    base_url, _directory = http_fixture_server
    with pytest.raises(InstallerError) as excinfo:
        manifest_mod.fetch_manifest("1.0.0", manifest_url=f"{base_url}/nope.json")
    assert excinfo.value.exit_code == MANIFEST_FAILURE


def test_fetch_manifest_non_json_body_raises(http_fixture_server) -> None:
    base_url, directory = http_fixture_server
    (directory / "bad.json").write_text("{ not json", encoding="utf-8")
    with pytest.raises(InstallerError):
        manifest_mod.fetch_manifest("1.0.0", manifest_url=f"{base_url}/bad.json")


def test_fetch_manifest_rejects_non_https_non_loopback() -> None:
    with pytest.raises(InstallerError) as excinfo:
        manifest_mod.fetch_manifest(
            "1.0.0", manifest_url="http://example.com/release-manifest.json"
        )
    assert excinfo.value.exit_code == MANIFEST_FAILURE


def test_fetch_manifest_oversized_response_rejected(http_fixture_server) -> None:
    base_url, directory = http_fixture_server
    huge = {"padding": "x" * (manifest_mod.MANIFEST_MAX_BYTES + 1024)}
    (directory / "huge.json").write_text(json.dumps(huge), encoding="utf-8")
    with pytest.raises(InstallerError):
        manifest_mod.fetch_manifest("1.0.0", manifest_url=f"{base_url}/huge.json")


def test_default_manifest_url_template_is_https() -> None:
    url = manifest_mod.DEFAULT_MANIFEST_URL_TEMPLATE.format(version="1.0.0")
    assert url.startswith("https://")
    assert "1.0.0" in url
