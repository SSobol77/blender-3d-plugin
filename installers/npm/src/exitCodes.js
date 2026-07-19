/**
 * Stable process exit codes shared with the Python installer.
 * See docs/installer-contract.md for the normative definition of each code.
 */

export const SUCCESS = 0;
export const INVALID_ARGUMENTS = 2;
export const BLENDER_NOT_FOUND = 3;
export const AMBIGUOUS_BLENDER = 4;
export const UNSUPPORTED_BLENDER_VERSION = 5;
export const MANIFEST_FAILURE = 6;
export const DOWNLOAD_FAILURE = 7;
export const CHECKSUM_MISMATCH = 8;
export const EXTENSION_VALIDATION_FAILURE = 9;
export const INSTALL_FAILURE = 10;
export const UPDATE_FAILURE = 11;
export const UNINSTALL_FAILURE = 12;
export const PERMISSION_FAILURE = 13;
export const OFFLINE_ARTIFACT_FAILURE = 14;

/** Carries the exit code the CLI should return for this failure. */
export class InstallerError extends Error {
  constructor(exitCode, message) {
    super(message);
    this.name = "InstallerError";
    this.exitCode = exitCode;
  }
}
