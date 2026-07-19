/** Shared test helpers: fake Blender executable, HTTP fixture server. */

import { createServer } from "node:http";
import { chmod, copyFile, mkdtemp, readFile, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const FIXTURES_DIR = path.resolve(HERE, "..", "..", "..", "tests", "fixtures", "installer");

/** Copy fake_blender.py to a fresh temp dir and return its path plus env. */
export async function makeFakeBlender({ version = "4.9.0", responses = {}, exitCode = 0 } = {}) {
  const dir = await mkdtemp(path.join(tmpdir(), "bm3d-fake-blender-"));
  const target = path.join(dir, "blender");
  await copyFile(path.join(FIXTURES_DIR, "fake_blender.py"), target);
  await chmod(target, 0o755);
  return {
    path: target,
    env: {
      FAKE_BLENDER_VERSION: version,
      FAKE_BLENDER_RESPONSES: JSON.stringify(responses),
      FAKE_BLENDER_EXIT_CODE: String(exitCode),
    },
  };
}

/** Apply a fake-blender env onto process.env, returning a restore function. */
export function applyEnv(env) {
  const previous = {};
  for (const key of Object.keys(env)) {
    previous[key] = Object.prototype.hasOwnProperty.call(process.env, key)
      ? process.env[key]
      : undefined;
    process.env[key] = env[key];
  }
  return () => {
    for (const key of Object.keys(env)) {
      if (previous[key] === undefined) delete process.env[key];
      else process.env[key] = previous[key];
    }
  };
}

/** Serve `directory` (static GET-only) over HTTP on 127.0.0.1. */
export function startFixtureServer(directory) {
  return new Promise((resolve) => {
    const server = createServer(async (req, res) => {
      try {
        const requestedPath = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
        const filePath = path.join(directory, requestedPath);
        if (!filePath.startsWith(path.resolve(directory))) {
          res.writeHead(403);
          res.end();
          return;
        }
        await stat(filePath);
        const body = await readFile(filePath);
        res.writeHead(200);
        res.end(body);
      } catch {
        res.writeHead(404);
        res.end("not found");
      }
    });
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      resolve({
        baseUrl: `http://127.0.0.1:${port}`,
        close: () => new Promise((r) => server.close(r)),
      });
    });
  });
}
