"""Sanity checks that exit codes match docs/installer-contract.md exactly."""

from __future__ import annotations

from blender_mobile_3d_installer import exit_codes as ec

EXPECTED = {
    "SUCCESS": 0,
    "INVALID_ARGUMENTS": 2,
    "BLENDER_NOT_FOUND": 3,
    "AMBIGUOUS_BLENDER": 4,
    "UNSUPPORTED_BLENDER_VERSION": 5,
    "MANIFEST_FAILURE": 6,
    "DOWNLOAD_FAILURE": 7,
    "CHECKSUM_MISMATCH": 8,
    "EXTENSION_VALIDATION_FAILURE": 9,
    "INSTALL_FAILURE": 10,
    "UPDATE_FAILURE": 11,
    "UNINSTALL_FAILURE": 12,
    "PERMISSION_FAILURE": 13,
    "OFFLINE_ARTIFACT_FAILURE": 14,
}


def test_exit_codes_match_contract() -> None:
    for name, value in EXPECTED.items():
        assert getattr(ec, name) == value, name


def test_exit_codes_are_unique() -> None:
    values = [getattr(ec, name) for name in EXPECTED]
    assert len(values) == len(set(values))


def test_installer_error_carries_exit_code() -> None:
    err = ec.InstallerError(ec.DOWNLOAD_FAILURE, "boom")
    assert err.exit_code == ec.DOWNLOAD_FAILURE
    assert err.message == "boom"
    assert str(err) == "boom"
