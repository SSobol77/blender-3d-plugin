import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import { validateZipSafety } from "../src/zipSafety.js";
import { EXTENSION_VALIDATION_FAILURE } from "../src/exitCodes.js";
import { FIXTURES_DIR } from "../test-support/testHelpers.js";
import { writeTestZip } from "../test-support/zipTestUtil.js";

const BASE_ENTRIES = [
  { name: "blender_mobile_3d/__init__.py", data: "x = 1" },
  { name: "blender_mobile_3d/version.py", data: 'VERSION = "1.0.0"' },
];

async function tmpZipPath(name) {
  const dir = await mkdtemp(path.join(tmpdir(), "bm3d-zip-"));
  return path.join(dir, name);
}

test("valid zip passes", async () => {
  const zipPath = await tmpZipPath("good.zip");
  await writeTestZip(zipPath, BASE_ENTRIES);
  await validateZipSafety(zipPath); // must not throw
});

test("not a zip file raises", async () => {
  const zipPath = await tmpZipPath("notazip.zip");
  await writeFile(zipPath, "this is not a zip");
  await assert.rejects(
    () => validateZipSafety(zipPath),
    (err) => err.exitCode === EXTENSION_VALIDATION_FAILURE,
  );
});

test("missing required members raises", async () => {
  const zipPath = await tmpZipPath("incomplete.zip");
  await writeTestZip(zipPath, [{ name: "blender_mobile_3d/only_this.py", data: "x = 1" }]);
  await assert.rejects(() => validateZipSafety(zipPath), /missing required members/);
});

for (const entrySet of [
  "absolute_path",
  "parent_traversal",
  "unexpected_top_level",
  "windows_absolute",
]) {
  test(`unsafe entries from shared fixture are rejected: ${entrySet}`, async () => {
    const unsafeEntries = JSON.parse(
      await readFile(path.join(FIXTURES_DIR, "unsafe_zip_entries.json"), "utf8"),
    );
    const zipPath = await tmpZipPath(`${entrySet}.zip`);
    const extra = unsafeEntries[entrySet].map((name) => ({ name, data: "payload" }));
    await writeTestZip(zipPath, [...BASE_ENTRIES, ...extra]);
    await assert.rejects(
      () => validateZipSafety(zipPath),
      (err) => err.exitCode === EXTENSION_VALIDATION_FAILURE,
    );
  });
}

test("symlink entry rejected", async () => {
  const zipPath = await tmpZipPath("symlink.zip");
  await writeTestZip(zipPath, [
    ...BASE_ENTRIES,
    { name: "blender_mobile_3d/evil_link", data: "/etc/passwd", externalAttr: (0o120777 << 16) >>> 0 },
  ]);
  await assert.rejects(() => validateZipSafety(zipPath), /symlink/);
});
