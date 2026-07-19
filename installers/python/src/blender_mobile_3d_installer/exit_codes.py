"""Stable process exit codes shared with the npm installer.

See docs/installer-contract.md for the normative definition of each code.
"""

from __future__ import annotations

SUCCESS = 0
INVALID_ARGUMENTS = 2
BLENDER_NOT_FOUND = 3
AMBIGUOUS_BLENDER = 4
UNSUPPORTED_BLENDER_VERSION = 5
MANIFEST_FAILURE = 6
DOWNLOAD_FAILURE = 7
CHECKSUM_MISMATCH = 8
EXTENSION_VALIDATION_FAILURE = 9
INSTALL_FAILURE = 10
UPDATE_FAILURE = 11
UNINSTALL_FAILURE = 12
PERMISSION_FAILURE = 13
OFFLINE_ARTIFACT_FAILURE = 14


class InstallerError(Exception):
    """Carries the exit code the CLI should return for this failure."""

    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.message = message
