import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import {
  doDoctor,
  doInstall,
  doListBlenders,
  doUninstall,
  doUpdate,
  resolveArtifact,
} from "../src/installer.js";
import {
  INVALID_ARGUMENTS,
  OFFLINE_ARTIFACT_FAILURE,
  UNINSTALL_FAILURE,
  UPDATE_FAILURE,
} from "../src/exitCodes.js";
import { applyEnv, makeFakeBlender, startFixtureServer } from "../test-support/testHelpers.js";
import { writeTestZip } from "../test-support/zipTestUtil.js";

async function validZip() {
  const dir = await mkdtemp(path.join(tmpdir(), "bm3d-installer-test-"));
  const zipPath = path.join(dir, "addon.zip");
  await writeTestZip(zipPath, [
    { name: "blender_mobile_3d/__init__.py", data: "x = 1" },
    { name: "blender_mobile_3d/version.py", data: 'VERSION = "1.0.0"' },
  ]);
  return zipPath;
}

test("install dry-run performs no mutation", async () => {
  const fake = await makeFakeBlender({ version: "4.9.0" });
  const restore = applyEnv(fake.env);
  try {
    const zipPath = await validZip();
    const result = await doInstall({
      explicitBlender: fake.path,
      version: "1.0.0",
      manifestUrl: null,
      offlineZip: zipPath,
      dryRun: true,
      force: false,
    });
    assert.equal(result.ok, true);
    assert.equal(result.dryRun, true);
    assert.equal(result.artifact, zipPath);
  } finally {
    restore();
  }
});

test("install offline missing file raises OFFLINE_ARTIFACT_FAILURE", async () => {
  const fake = await makeFakeBlender({ version: "4.9.0" });
  const restore = applyEnv(fake.env);
  try {
    await assert.rejects(
      () =>
        doInstall({
          explicitBlender: fake.path,
          version: "1.0.0",
          manifestUrl: null,
          offlineZip: "/does/not/exist.zip",
          dryRun: false,
          force: false,
        }),
      (err) => err.exitCode === OFFLINE_ARTIFACT_FAILURE,
    );
  } finally {
    restore();
  }
});

test("install real flow reports helper result", async () => {
  const fake = await makeFakeBlender({
    version: "4.9.0",
    responses: { install: { ok: true, installed: true, enabled: true, version: "1.0.0" } },
  });
  const restore = applyEnv(fake.env);
  try {
    const zipPath = await validZip();
    const result = await doInstall({
      explicitBlender: fake.path,
      version: "1.0.0",
      manifestUrl: null,
      offlineZip: zipPath,
      dryRun: false,
      force: false,
    });
    assert.equal(result.installed, true);
    assert.equal(result.version, "1.0.0");
  } finally {
    restore();
  }
});

test("update is a no-op when the same version is already installed", async () => {
  const fake = await makeFakeBlender({
    version: "4.9.0",
    responses: { status: { ok: true, installed: true, enabled: true, version: "1.0.0" } },
  });
  const restore = applyEnv(fake.env);
  try {
    const zipPath = await validZip();
    const result = await doUpdate({
      explicitBlender: fake.path,
      version: "1.0.0",
      manifestUrl: null,
      offlineZip: zipPath,
      dryRun: false,
      force: false,
    });
    assert.equal(result.updated, false);
    assert.match(result.message, /no update necessary/i);
  } finally {
    restore();
  }
});

test("update refuses a downgrade without --force", async () => {
  const fake = await makeFakeBlender({
    version: "4.9.0",
    responses: { status: { ok: true, installed: true, enabled: true, version: "2.0.0" } },
  });
  const restore = applyEnv(fake.env);
  try {
    const zipPath = await validZip();
    await assert.rejects(
      () =>
        doUpdate({
          explicitBlender: fake.path,
          version: "1.0.0",
          manifestUrl: null,
          offlineZip: zipPath,
          dryRun: false,
          force: false,
        }),
      (err) => err.exitCode === UPDATE_FAILURE,
    );
  } finally {
    restore();
  }
});

test("update allows a downgrade with --force", async () => {
  const fake = await makeFakeBlender({
    version: "4.9.0",
    responses: {
      status: { ok: true, installed: true, enabled: true, version: "2.0.0" },
      install: { ok: true, installed: true, enabled: true, version: "1.0.0" },
    },
  });
  const restore = applyEnv(fake.env);
  try {
    const zipPath = await validZip();
    const result = await doUpdate({
      explicitBlender: fake.path,
      version: "1.0.0",
      manifestUrl: null,
      offlineZip: zipPath,
      dryRun: false,
      force: true,
    });
    assert.equal(result.updated, true);
    assert.equal(result.version, "1.0.0");
  } finally {
    restore();
  }
});

test("uninstall requires --yes", async () => {
  const fake = await makeFakeBlender({
    version: "4.9.0",
    responses: { status: { ok: true, installed: true, enabled: true, version: "1.0.0" } },
  });
  const restore = applyEnv(fake.env);
  try {
    assert.throws(
      () => doUninstall({ explicitBlender: fake.path, dryRun: false, yes: false }),
      (err) => err.exitCode === INVALID_ARGUMENTS,
    );
  } finally {
    restore();
  }
});

test("uninstall dry-run performs no mutation", async () => {
  const fake = await makeFakeBlender({
    version: "4.9.0",
    responses: { status: { ok: true, installed: true, enabled: true, version: "1.0.0" } },
  });
  const restore = applyEnv(fake.env);
  try {
    const result = doUninstall({ explicitBlender: fake.path, dryRun: true, yes: true });
    assert.equal(result.dryRun, true);
    assert.equal(result.removed, false);
  } finally {
    restore();
  }
});

test("uninstall is idempotent when already absent", async () => {
  const fake = await makeFakeBlender({
    version: "4.9.0",
    responses: { status: { ok: true, installed: false, enabled: false, version: null } },
  });
  const restore = applyEnv(fake.env);
  try {
    const result = doUninstall({ explicitBlender: fake.path, dryRun: false, yes: true });
    assert.equal(result.removed, false);
    assert.match(result.message, /already uninstalled/i);
  } finally {
    restore();
  }
});

test("uninstall verifies removal and fails if still present", async () => {
  const fake = await makeFakeBlender({
    version: "4.9.0",
    responses: {
      status: { ok: true, installed: true, enabled: true, version: "1.0.0" },
      uninstall: { ok: true, installed: true, enabled: true, version: "1.0.0" },
    },
  });
  const restore = applyEnv(fake.env);
  try {
    assert.throws(
      () => doUninstall({ explicitBlender: fake.path, dryRun: false, yes: true }),
      (err) => err.exitCode === UNINSTALL_FAILURE,
    );
  } finally {
    restore();
  }
});

test("uninstall success", async () => {
  const fake = await makeFakeBlender({
    version: "4.9.0",
    responses: {
      status: { ok: true, installed: true, enabled: true, version: "1.0.0" },
      uninstall: { ok: true, installed: false, enabled: false, version: null },
    },
  });
  const restore = applyEnv(fake.env);
  try {
    const result = doUninstall({ explicitBlender: fake.path, dryRun: false, yes: true });
    assert.equal(result.removed, true);
  } finally {
    restore();
  }
});

test("doctor is healthy with a supported blender and writable tmp", async () => {
  const fake = await makeFakeBlender({
    version: "4.9.0",
    responses: { status: { ok: true, installed: false, enabled: false, version: null } },
  });
  const restore = applyEnv(fake.env);
  try {
    const report = await doDoctor({
      explicitBlender: fake.path,
      checkOnline: false,
      installerVersion: "1.0.0",
    });
    assert.equal(report.ok, true);
    assert.equal(report.manifestReachable, "skipped (offline)");
    assert.equal(report.selectedBlender.path, fake.path);
  } finally {
    restore();
  }
});

test("doctor is unhealthy without a blender", async () => {
  const report = await doDoctor({
    explicitBlender: "/does/not/exist",
    checkOnline: false,
    installerVersion: "1.0.0",
  });
  assert.equal(report.ok, false);
  assert.equal(report.selectedBlender, null);
});

test("doctor survives a status query failure", async () => {
  const fake = await makeFakeBlender({
    version: "4.9.0",
    responses: { status: { ok: false, error: "x" } },
  });
  const restore = applyEnv(fake.env);
  try {
    const report = await doDoctor({
      explicitBlender: fake.path,
      checkOnline: false,
      installerVersion: "1.0.0",
    });
    assert.equal(report.extensionInstalled, null);
  } finally {
    restore();
  }
});

test("list-blenders reports candidates", async () => {
  const fake = await makeFakeBlender({ version: "4.9.0" });
  const restore = applyEnv(fake.env);
  try {
    const result = doListBlenders({ explicitBlender: fake.path });
    assert.equal(result.ok, true);
    assert.equal(result.blenders[0].path, fake.path);
  } finally {
    restore();
  }
});

test("resolveArtifact online downloads and validates", async () => {
  const srcDir = await mkdtemp(path.join(tmpdir(), "bm3d-resolve-"));
  const zipPath = path.join(srcDir, "blender_mobile_3d-1.0.0.zip");
  await writeTestZip(zipPath, [
    { name: "blender_mobile_3d/__init__.py", data: "x = 1" },
    { name: "blender_mobile_3d/version.py", data: 'VERSION = "1.0.0"' },
  ]);
  const zipBytes = await readFile(zipPath);
  const digest = createHash("sha256").update(zipBytes).digest("hex");

  const { baseUrl, close } = await startFixtureServer(srcDir);
  try {
    const manifest = {
      schema_version: "1.0.0",
      version: "1.0.0",
      artifacts: {
        extension: {
          filename: "blender_mobile_3d-1.0.0.zip",
          url: `${baseUrl}/blender_mobile_3d-1.0.0.zip`,
          sha256: digest,
          size: zipBytes.length,
        },
      },
    };
    await writeFile(path.join(srcDir, "release-manifest.json"), JSON.stringify(manifest));

    const resultPath = await resolveArtifact("1.0.0", `${baseUrl}/release-manifest.json`, null);
    assert.deepEqual(await readFile(resultPath), zipBytes);
  } finally {
    await close();
  }
});
