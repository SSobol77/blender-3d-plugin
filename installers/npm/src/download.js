/** Secure artifact download: HTTPS-or-loopback, bounded size, atomic rename. */

import { createHash } from "node:crypto";
import { createWriteStream } from "node:fs";
import { mkdir, mkdtemp, rename, rm, stat } from "node:fs/promises";
import path from "node:path";
import { Transform } from "node:stream";
import { pipeline } from "node:stream/promises";

import { CHECKSUM_MISMATCH, DOWNLOAD_FAILURE, InstallerError } from "./exitCodes.js";

export const DOWNLOAD_TIMEOUT_MS = 60_000;
const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1", "::1"]);

function requireHttpsOrLoopback(url) {
  const parsed = new URL(url);
  if (parsed.protocol === "https:") return;
  if (parsed.protocol === "http:" && LOOPBACK_HOSTS.has(parsed.hostname)) return;
  throw new InstallerError(
    DOWNLOAD_FAILURE,
    `Refusing non-HTTPS download URL (loopback exempt for testing only): ${url}`,
  );
}

/**
 * Download `url` to `destPath`, verifying size and checksum. Writes to a
 * temporary file in the destination's own directory and performs an atomic
 * rename only after the checksum matches. Any failure removes the partial
 * file and throws InstallerError.
 */
export async function downloadArtifact(url, destPath, expectedSha256, maxSizeBytes) {
  requireHttpsOrLoopback(url);
  await mkdir(path.dirname(destPath), { recursive: true });

  const tmpDir = await mkdtemp(path.join(path.dirname(destPath), ".download-"));
  const tmpPath = path.join(tmpDir, "artifact.tmp");

  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), DOWNLOAD_TIMEOUT_MS);
    let response;
    try {
      response = await fetch(url, {
        signal: controller.signal,
        headers: { "User-Agent": "blender-mobile-3d-installer" },
      });
    } catch (err) {
      throw new InstallerError(DOWNLOAD_FAILURE, `Download failed for ${url}: ${err.message}`);
    } finally {
      clearTimeout(timer);
    }

    if (!response.ok || !response.body) {
      throw new InstallerError(DOWNLOAD_FAILURE, `Download failed for ${url}: HTTP ${response.status}`);
    }

    const hash = createHash("sha256");
    let total = 0;
    const sizeGuard = new Transform({
      transform(chunk, _enc, callback) {
        total += chunk.length;
        if (total > maxSizeBytes) {
          callback(new Error(`exceeded the ${maxSizeBytes}-byte limit`));
          return;
        }
        hash.update(chunk);
        callback(null, chunk);
      },
    });

    try {
      await pipeline(response.body, sizeGuard, createWriteStream(tmpPath));
    } catch (err) {
      throw new InstallerError(DOWNLOAD_FAILURE, `Download failed for ${url}: ${err.message}`);
    }

    if (total === 0) {
      throw new InstallerError(DOWNLOAD_FAILURE, `Download from ${url} was empty.`);
    }

    const actual = hash.digest("hex");
    if (actual !== expectedSha256) {
      throw new InstallerError(
        CHECKSUM_MISMATCH,
        `Checksum mismatch for ${url}: expected ${expectedSha256}, got ${actual}.`,
      );
    }

    await rename(tmpPath, destPath);
    return destPath;
  } finally {
    await rm(tmpDir, { recursive: true, force: true });
  }
}

export async function fileExists(candidatePath) {
  try {
    await stat(candidatePath);
    return true;
  } catch {
    return false;
  }
}
