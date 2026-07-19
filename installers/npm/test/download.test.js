import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readdir, readFile, stat, writeFile } from "node:fs/promises";
import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import { downloadArtifact } from "../src/download.js";
import { CHECKSUM_MISMATCH, DOWNLOAD_FAILURE } from "../src/exitCodes.js";
import { startFixtureServer } from "../test-support/testHelpers.js";

async function exists(p) {
  try {
    await stat(p);
    return true;
  } catch {
    return false;
  }
}

test("download success and checksum match", async () => {
  const srcDir = await mkdtemp(path.join(tmpdir(), "bm3d-dl-src-"));
  const payload = Buffer.from("artifact bytes".repeat(100));
  await writeFile(path.join(srcDir, "artifact.bin"), payload);
  const digest = createHash("sha256").update(payload).digest("hex");

  const { baseUrl, close } = await startFixtureServer(srcDir);
  try {
    const destDir = await mkdtemp(path.join(tmpdir(), "bm3d-dl-dest-"));
    const dest = path.join(destDir, "out", "artifact.bin");
    const result = await downloadArtifact(`${baseUrl}/artifact.bin`, dest, digest, 10_000);
    assert.equal(result, dest);
    assert.deepEqual(await readFile(dest), payload);
  } finally {
    await close();
  }
});

test("download checksum mismatch cleans up", async () => {
  const srcDir = await mkdtemp(path.join(tmpdir(), "bm3d-dl-src-"));
  await writeFile(path.join(srcDir, "artifact.bin"), "real content");

  const { baseUrl, close } = await startFixtureServer(srcDir);
  try {
    const destDir = await mkdtemp(path.join(tmpdir(), "bm3d-dl-dest-"));
    const dest = path.join(destDir, "out", "artifact.bin");
    await assert.rejects(
      () => downloadArtifact(`${baseUrl}/artifact.bin`, dest, "f".repeat(64), 10_000),
      (err) => err.exitCode === CHECKSUM_MISMATCH,
    );
    assert.equal(await exists(dest), false);
    const leftovers = (await readdir(path.dirname(dest))).filter((f) => f.startsWith(".download-"));
    assert.deepEqual(leftovers, []);
  } finally {
    await close();
  }
});

test("download over size limit is rejected", async () => {
  const srcDir = await mkdtemp(path.join(tmpdir(), "bm3d-dl-src-"));
  await writeFile(path.join(srcDir, "big.bin"), "x".repeat(5000));

  const { baseUrl, close } = await startFixtureServer(srcDir);
  try {
    const destDir = await mkdtemp(path.join(tmpdir(), "bm3d-dl-dest-"));
    const dest = path.join(destDir, "out", "big.bin");
    await assert.rejects(
      () => downloadArtifact(`${baseUrl}/big.bin`, dest, "0".repeat(64), 100),
      (err) => err.exitCode === DOWNLOAD_FAILURE,
    );
    assert.equal(await exists(dest), false);
  } finally {
    await close();
  }
});

test("download 404 raises DOWNLOAD_FAILURE", async () => {
  const srcDir = await mkdtemp(path.join(tmpdir(), "bm3d-dl-src-"));
  const { baseUrl, close } = await startFixtureServer(srcDir);
  try {
    const destDir = await mkdtemp(path.join(tmpdir(), "bm3d-dl-dest-"));
    await assert.rejects(
      () =>
        downloadArtifact(
          `${baseUrl}/missing.bin`,
          path.join(destDir, "missing.bin"),
          "0".repeat(64),
          10_000,
        ),
      (err) => err.exitCode === DOWNLOAD_FAILURE,
    );
  } finally {
    await close();
  }
});

test("download rejects non-HTTPS non-loopback URL", async () => {
  const destDir = await mkdtemp(path.join(tmpdir(), "bm3d-dl-dest-"));
  await assert.rejects(
    () =>
      downloadArtifact(
        "http://example.com/artifact.bin",
        path.join(destDir, "out.bin"),
        "0".repeat(64),
        10_000,
      ),
    (err) => err.exitCode === DOWNLOAD_FAILURE,
  );
});

test("download connection refused raises DOWNLOAD_FAILURE", async () => {
  const destDir = await mkdtemp(path.join(tmpdir(), "bm3d-dl-dest-"));
  await assert.rejects(
    () =>
      downloadArtifact(
        "http://127.0.0.1:1/artifact.bin",
        path.join(destDir, "out.bin"),
        "0".repeat(64),
        10_000,
      ),
    (err) => err.exitCode === DOWNLOAD_FAILURE,
  );
});
