import assert from "node:assert/strict";
import test from "node:test";

import * as ec from "../src/exitCodes.js";

const EXPECTED = {
  SUCCESS: 0,
  INVALID_ARGUMENTS: 2,
  BLENDER_NOT_FOUND: 3,
  AMBIGUOUS_BLENDER: 4,
  UNSUPPORTED_BLENDER_VERSION: 5,
  MANIFEST_FAILURE: 6,
  DOWNLOAD_FAILURE: 7,
  CHECKSUM_MISMATCH: 8,
  EXTENSION_VALIDATION_FAILURE: 9,
  INSTALL_FAILURE: 10,
  UPDATE_FAILURE: 11,
  UNINSTALL_FAILURE: 12,
  PERMISSION_FAILURE: 13,
  OFFLINE_ARTIFACT_FAILURE: 14,
};

test("exit codes match the contract", () => {
  for (const [name, value] of Object.entries(EXPECTED)) {
    assert.equal(ec[name], value, name);
  }
});

test("exit codes are unique", () => {
  const values = Object.keys(EXPECTED).map((name) => ec[name]);
  assert.equal(new Set(values).size, values.length);
});

test("InstallerError carries the exit code", () => {
  const err = new ec.InstallerError(ec.DOWNLOAD_FAILURE, "boom");
  assert.equal(err.exitCode, ec.DOWNLOAD_FAILURE);
  assert.equal(err.message, "boom");
});
