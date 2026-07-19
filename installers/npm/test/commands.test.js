import assert from "node:assert/strict";
import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import { main } from "../src/main.js";
import { BLENDER_NOT_FOUND, INVALID_ARGUMENTS, OFFLINE_ARTIFACT_FAILURE } from "../src/exitCodes.js";
import { applyEnv, makeFakeBlender } from "../test-support/testHelpers.js";
import { writeTestZip } from "../test-support/zipTestUtil.js";

function captureStdout() {
  const original = console.log;
  const lines = [];
  console.log = (...args) => lines.push(args.join(" "));
  return {
    restore: () => {
      console.log = original;
    },
    text: () => lines.join("\n"),
  };
}

test("main help returns zero", async () => {
  assert.equal(await main(["help"]), 0);
});

test("main with no args shows help and returns zero", async () => {
  assert.equal(await main([]), 0);
});

test("main version prints and returns zero", async () => {
  const capture = captureStdout();
  try {
    assert.equal(await main(["version"]), 0);
    assert.equal(capture.text().trim(), "1.0.0");
  } finally {
    capture.restore();
  }
});

test("main unknown command returns INVALID_ARGUMENTS", async () => {
  assert.equal(await main(["unknown"]), INVALID_ARGUMENTS);
});

test("main doctor without blender reports BLENDER_NOT_FOUND", async () => {
  const capture = captureStdout();
  try {
    const bd = await import("../src/blenderDiscovery.js");
    const originalWhich = bd._internal.which;
    const originalCommon = bd._internal.commonLocations;
    bd._internal.which = () => null;
    bd._internal.commonLocations = () => [];
    try {
      const code = await main(["doctor", "--json"]);
      assert.equal(code, BLENDER_NOT_FOUND);
      const payload = JSON.parse(capture.text());
      assert.equal(payload.ok, false);
    } finally {
      bd._internal.which = originalWhich;
      bd._internal.commonLocations = originalCommon;
    }
  } finally {
    capture.restore();
  }
});

test("main doctor with fake blender is healthy", async () => {
  const fake = await makeFakeBlender({
    version: "4.9.0",
    responses: { status: { ok: true, installed: false, enabled: false, version: null } },
  });
  const restore = applyEnv(fake.env);
  const capture = captureStdout();
  try {
    const code = await main(["doctor", "--blender", fake.path, "--json"]);
    assert.equal(code, 0);
    const payload = JSON.parse(capture.text());
    assert.equal(payload.ok, true);
  } finally {
    capture.restore();
    restore();
  }
});

test("main list-blenders json", async () => {
  const fake = await makeFakeBlender({ version: "4.9.0" });
  const restore = applyEnv(fake.env);
  const capture = captureStdout();
  try {
    const code = await main(["list-blenders", "--blender", fake.path, "--json"]);
    assert.equal(code, 0);
    const payload = JSON.parse(capture.text());
    assert.equal(payload.blenders[0].path, fake.path);
  } finally {
    capture.restore();
    restore();
  }
});

test("main install offline missing artifact exit code", async () => {
  const fake = await makeFakeBlender({ version: "4.9.0" });
  const restore = applyEnv(fake.env);
  try {
    const code = await main([
      "install",
      "--blender",
      fake.path,
      "--offline",
      "/does/not/exist.zip",
      "--json",
    ]);
    assert.equal(code, OFFLINE_ARTIFACT_FAILURE);
  } finally {
    restore();
  }
});

test("main install dry-run", async () => {
  const fake = await makeFakeBlender({ version: "4.9.0" });
  const restore = applyEnv(fake.env);
  const capture = captureStdout();
  try {
    const dir = await mkdtemp(path.join(tmpdir(), "bm3d-cmd-test-"));
    const zipPath = path.join(dir, "addon.zip");
    await writeTestZip(zipPath, [
      { name: "blender_mobile_3d/__init__.py", data: "x = 1" },
      { name: "blender_mobile_3d/version.py", data: 'VERSION = "1.0.0"' },
    ]);
    const code = await main([
      "install",
      "--blender",
      fake.path,
      "--offline",
      zipPath,
      "--dry-run",
      "--json",
    ]);
    assert.equal(code, 0);
    const payload = JSON.parse(capture.text());
    assert.equal(payload.dryRun, true);
  } finally {
    capture.restore();
    restore();
  }
});

test("main uninstall without --yes returns INVALID_ARGUMENTS", async () => {
  const fake = await makeFakeBlender({
    version: "4.9.0",
    responses: { status: { ok: true, installed: true, enabled: true, version: "1.0.0" } },
  });
  const restore = applyEnv(fake.env);
  try {
    const code = await main(["uninstall", "--blender", fake.path, "--json"]);
    assert.equal(code, INVALID_ARGUMENTS);
  } finally {
    restore();
  }
});
