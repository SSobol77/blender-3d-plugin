import assert from "node:assert/strict";
import { chmod, copyFile, mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import {
  discoverBlenders,
  probeExecutable,
  selectBlender,
  _internal,
} from "../src/blenderDiscovery.js";
import { AMBIGUOUS_BLENDER, BLENDER_NOT_FOUND, UNSUPPORTED_BLENDER_VERSION } from "../src/exitCodes.js";
import { applyEnv, makeFakeBlender } from "../test-support/testHelpers.js";

test("probeExecutable parses a supported version", async () => {
  const fake = await makeFakeBlender({ version: "5.1.2" });
  const restore = applyEnv(fake.env);
  try {
    const { version, supported } = probeExecutable(fake.path);
    assert.equal(version, "5.1.2");
    assert.equal(supported, true);
  } finally {
    restore();
  }
});

test("probeExecutable rejects an old version", async () => {
  const fake = await makeFakeBlender({ version: "3.6.0" });
  const restore = applyEnv(fake.env);
  try {
    const { version, supported } = probeExecutable(fake.path);
    assert.equal(version, "3.6.0");
    assert.equal(supported, false);
  } finally {
    restore();
  }
});

test("probeExecutable returns null for a missing path", () => {
  const { version, supported } = probeExecutable("/does/not/exist/blender");
  assert.equal(version, null);
  assert.equal(supported, false);
});

test("discoverBlenders with a nonexistent explicit path yields no candidates", () => {
  assert.deepEqual(discoverBlenders("/does/not/exist"), []);
});

test("discoverBlenders with an existing explicit path", async () => {
  const fake = await makeFakeBlender({ version: "4.9.0" });
  const restore = applyEnv(fake.env);
  try {
    const candidates = discoverBlenders(fake.path);
    assert.equal(candidates.length, 1);
    assert.equal(candidates[0].path, fake.path);
    assert.equal(candidates[0].source, "explicit");
    assert.equal(candidates[0].supported, true);
  } finally {
    restore();
  }
});

test("selectBlender raises BLENDER_NOT_FOUND", () => {
  assert.throws(
    () => selectBlender("/does/not/exist"),
    (err) => err.exitCode === BLENDER_NOT_FOUND,
  );
});

test("selectBlender raises UNSUPPORTED_BLENDER_VERSION", async () => {
  const fake = await makeFakeBlender({ version: "2.0.0" });
  const restore = applyEnv(fake.env);
  try {
    assert.throws(
      () => selectBlender(fake.path),
      (err) => err.exitCode === UNSUPPORTED_BLENDER_VERSION,
    );
  } finally {
    restore();
  }
});

test("selectBlender returns an explicit supported candidate", async () => {
  const fake = await makeFakeBlender({ version: "4.5.0" });
  const restore = applyEnv(fake.env);
  try {
    const candidate = selectBlender(fake.path);
    assert.equal(candidate.path, fake.path);
  } finally {
    restore();
  }
});

test("selectBlender is ambiguous with multiple supported candidates", async () => {
  const fake = await makeFakeBlender({ version: "4.9.0" });
  const restore = applyEnv(fake.env);
  try {
    const secondDir = await mkdtemp(path.join(tmpdir(), "bm3d-fake-blender2-"));
    const second = path.join(secondDir, "blender");
    await copyFile(fake.path, second);
    await chmod(second, 0o755);

    const originalWhich = _internal.which;
    _internal.which = () => fake.path;
    try {
      const commonLocationsOriginal = _internal.commonLocations;
      _internal.commonLocations = () => [second];
      try {
        assert.throws(
          () => selectBlender(null),
          (err) => err.exitCode === AMBIGUOUS_BLENDER,
        );
      } finally {
        _internal.commonLocations = commonLocationsOriginal;
      }
    } finally {
      _internal.which = originalWhich;
    }
  } finally {
    restore();
  }
});

test("discoverBlenders with no candidates at all", () => {
  const originalWhich = _internal.which;
  const originalCommon = _internal.commonLocations;
  _internal.which = () => null;
  _internal.commonLocations = () => [];
  try {
    assert.throws(
      () => selectBlender(null),
      (err) => err.exitCode === BLENDER_NOT_FOUND,
    );
  } finally {
    _internal.which = originalWhich;
    _internal.commonLocations = originalCommon;
  }
});
