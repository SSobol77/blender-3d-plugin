import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(HERE, "..", "..", "..");

test("npm helper matches the shared source", async () => {
  const shared = await readFile(path.join(REPO_ROOT, "installers", "shared", "blender_helper.py"));
  const packaged = await readFile(
    path.join(REPO_ROOT, "installers", "npm", "src", "data", "blender_helper.py"),
  );
  assert.deepEqual(shared, packaged);
});
