import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import {
  DEFAULT_MANIFEST_URL_TEMPLATE,
  MANIFEST_MAX_BYTES,
  fetchManifest,
  validateManifestStructure,
} from "../src/manifest.js";
import { MANIFEST_FAILURE } from "../src/exitCodes.js";
import { FIXTURES_DIR, startFixtureServer } from "../test-support/testHelpers.js";

async function loadFixture(name) {
  return JSON.parse(await readFile(path.join(FIXTURES_DIR, name), "utf8"));
}

test("valid manifest fixture passes structural validation", async () => {
  const data = await loadFixture("manifest_valid.json");
  const result = validateManifestStructure(data);
  assert.equal(result.version, "1.0.0");
  assert.equal(result.extension.filename, "blender_mobile_3d-1.0.0.zip");
  assert.equal(result.extension.sha256.length, 64);
});

test("malformed manifest fixture is not valid JSON", async () => {
  const raw = await readFile(path.join(FIXTURES_DIR, "manifest_malformed.json"), "utf8");
  assert.throws(() => JSON.parse(raw));
});

test("schema-invalid manifest fixture fails structural validation", async () => {
  const data = await loadFixture("manifest_schema_invalid.json");
  assert.throws(
    () => validateManifestStructure(data),
    (err) => err.exitCode === MANIFEST_FAILURE,
  );
});

test("various structural defects raise", async () => {
  const mutations = [
    (d) => (d.schema_version = "9.9.9"),
    (d) => (d.version = "not-a-version"),
    (d) => delete d.artifacts,
    (d) => (d.artifacts.extension.sha256 = "short"),
    (d) => (d.artifacts.extension.size = -5),
    (d) => delete d.artifacts.extension.filename,
  ];
  for (const mutate of mutations) {
    const data = await loadFixture("manifest_valid.json");
    mutate(data);
    assert.throws(() => validateManifestStructure(data), `mutation ${mutate}`);
  }
});

test("non-object root raises", () => {
  for (const root of [null, [], "text", 42]) {
    assert.throws(() => validateManifestStructure(root));
  }
});

test("fetchManifest succeeds against a fixture server", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "bm3d-manifest-"));
  const { baseUrl, close } = await startFixtureServer(dir);
  try {
    const data = await loadFixture("manifest_valid.json");
    data.artifacts.extension.url = `${baseUrl}/blender_mobile_3d-1.0.0.zip`;
    await writeFile(path.join(dir, "release-manifest.json"), JSON.stringify(data));

    const fetched = await fetchManifest("1.0.0", `${baseUrl}/release-manifest.json`);
    assert.equal(fetched.version, "1.0.0");
  } finally {
    await close();
  }
});

test("fetchManifest 404 raises MANIFEST_FAILURE", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "bm3d-manifest-"));
  const { baseUrl, close } = await startFixtureServer(dir);
  try {
    await assert.rejects(
      () => fetchManifest("1.0.0", `${baseUrl}/nope.json`),
      (err) => err.exitCode === MANIFEST_FAILURE,
    );
  } finally {
    await close();
  }
});

test("fetchManifest rejects non-JSON body", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "bm3d-manifest-"));
  const { baseUrl, close } = await startFixtureServer(dir);
  try {
    await writeFile(path.join(dir, "bad.json"), "{ not json");
    await assert.rejects(() => fetchManifest("1.0.0", `${baseUrl}/bad.json`));
  } finally {
    await close();
  }
});

test("fetchManifest rejects non-HTTPS non-loopback URLs", async () => {
  await assert.rejects(
    () => fetchManifest("1.0.0", "http://example.com/release-manifest.json"),
    (err) => err.exitCode === MANIFEST_FAILURE,
  );
});

test("fetchManifest rejects an oversized response", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "bm3d-manifest-"));
  const { baseUrl, close } = await startFixtureServer(dir);
  try {
    const huge = { padding: "x".repeat(MANIFEST_MAX_BYTES + 1024) };
    await writeFile(path.join(dir, "huge.json"), JSON.stringify(huge));
    await assert.rejects(() => fetchManifest("1.0.0", `${baseUrl}/huge.json`));
  } finally {
    await close();
  }
});

test("default manifest URL template is HTTPS", () => {
  const url = DEFAULT_MANIFEST_URL_TEMPLATE.replace("{version}", "1.0.0");
  assert.ok(url.startsWith("https://"));
  assert.ok(url.includes("1.0.0"));
});
