/** Real Blender executable discovery across Linux, macOS, and Windows. */

import { spawnSync } from "node:child_process";
import { accessSync, constants as fsConstants, realpathSync, statSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";

import {
  AMBIGUOUS_BLENDER,
  BLENDER_NOT_FOUND,
  InstallerError,
  UNSUPPORTED_BLENDER_VERSION,
} from "./exitCodes.js";
import { globSync } from "./glob.js";

export const MINIMUM_BLENDER_VERSION = [4, 3, 0];
export const MAXIMUM_BLENDER_VERSION_EXCLUSIVE = null;
export const BLENDER_PROBE_TIMEOUT_MS = 10_000;

const VERSION_RE = /Blender\s+(\d+)\.(\d+)(?:\.(\d+))?/;

function parseVersion(output) {
  const match = VERSION_RE.exec(output);
  if (!match) return null;
  const [, major, minor, patch] = match;
  return [Number(major), Number(minor), Number(patch ?? 0)];
}

function compareVersions(a, b) {
  for (let i = 0; i < 3; i += 1) {
    if (a[i] !== b[i]) return a[i] - b[i];
  }
  return 0;
}

function isSupported(version) {
  if (compareVersions(version, MINIMUM_BLENDER_VERSION) < 0) return false;
  if (
    MAXIMUM_BLENDER_VERSION_EXCLUSIVE !== null &&
    compareVersions(version, MAXIMUM_BLENDER_VERSION_EXCLUSIVE) >= 0
  ) {
    return false;
  }
  return true;
}

function isExecutableFile(candidatePath) {
  try {
    const stats = statSync(candidatePath);
    if (!stats.isFile()) return false;
    accessSync(candidatePath, fsConstants.X_OK);
    return true;
  } catch {
    return false;
  }
}

/** Run `<execPath> --version` and classify support; never throws. */
export function probeExecutable(execPath) {
  let result;
  try {
    result = spawnSync(execPath, ["--version"], {
      timeout: BLENDER_PROBE_TIMEOUT_MS,
      encoding: "utf8",
    });
  } catch {
    return { version: null, supported: false };
  }
  if (result.error || result.signal) {
    return { version: null, supported: false };
  }
  const version = parseVersion(`${result.stdout ?? ""}${result.stderr ?? ""}`);
  if (version === null) return { version: null, supported: false };
  return { version: version.join("."), supported: isSupported(version) };
}

function which(name) {
  const pathEnv = process.env.PATH || "";
  const exts = process.platform === "win32" ? [".exe", ".bat", ".cmd", ""] : [""];
  for (const dir of pathEnv.split(path.delimiter)) {
    if (!dir) continue;
    for (const ext of exts) {
      const candidate = path.join(dir, name + ext);
      if (isExecutableFile(candidate)) return candidate;
    }
  }
  return null;
}

function commonLocations() {
  const platform = process.platform;
  const home = os.homedir();
  if (platform === "linux") {
    return [
      "/usr/bin/blender",
      "/usr/local/bin/blender",
      ...globSync("/opt/blender*/blender"),
      path.join(home, ".local/share/flatpak/exports/bin/blender"),
      "/var/lib/flatpak/exports/bin/blender",
      "/snap/bin/blender",
    ];
  }
  if (platform === "darwin") {
    return [
      "/Applications/Blender.app/Contents/MacOS/Blender",
      path.join(home, "Applications/Blender.app/Contents/MacOS/Blender"),
      ...globSync("/Applications/Blender*.app/Contents/MacOS/Blender"),
      ...globSync(path.join(home, "Applications/Blender*.app/Contents/MacOS/Blender")),
    ];
  }
  if (platform === "win32") {
    const programFilesDirs = [
      process.env.ProgramFiles || "C:\\Program Files",
      process.env["ProgramFiles(x86)"] || "C:\\Program Files (x86)",
    ];
    const candidates = [];
    for (const base of programFilesDirs) {
      candidates.push(
        ...globSync(path.join(base, "Blender Foundation", "Blender *", "blender.exe")),
      );
    }
    return candidates;
  }
  return [];
}

function addCandidate(seen, candidatePath, source) {
  let realPath;
  try {
    realPath = realpathSync(candidatePath);
  } catch {
    realPath = candidatePath;
  }
  if (seen.has(realPath)) return;
  const { version, supported } = probeExecutable(realPath);
  seen.set(realPath, { path: realPath, version, supported, source });
}

/**
 * Return every discovered Blender candidate, deduplicated by real path.
 * When `explicit` is given it is the only candidate returned (still probed
 * for version/support so callers can report why it was rejected).
 */
export function discoverBlenders(explicit = null) {
  if (explicit) {
    if (!_internal.isExecutableFile(explicit)) return [];
    const { version, supported } = probeExecutable(explicit);
    return [{ path: explicit, version, supported, source: "explicit" }];
  }

  const seen = new Map();

  const pathCandidate = _internal.which("blender");
  if (pathCandidate) addCandidate(seen, pathCandidate, "PATH");

  for (const location of _internal.commonLocations()) {
    if (_internal.isExecutableFile(location)) addCandidate(seen, location, "well-known-location");
  }

  return [...seen.values()].sort((a, b) => {
    if (a.supported !== b.supported) return a.supported ? -1 : 1;
    return (b.version || "").localeCompare(a.version || "");
  });
}

/** Apply the discovery/selection rule from docs/installer-contract.md. */
export function selectBlender(explicit = null) {
  const candidates = discoverBlenders(explicit);
  if (candidates.length === 0) {
    throw new InstallerError(BLENDER_NOT_FOUND, "No Blender executable found.");
  }

  const supported = candidates.filter((c) => c.supported);
  if (supported.length === 0) {
    const only = candidates[0];
    throw new InstallerError(
      UNSUPPORTED_BLENDER_VERSION,
      `Blender at ${only.path} is version ${only.version || "unknown"}, ` +
        `which is not supported (requires >= ${MINIMUM_BLENDER_VERSION.join(".")}).`,
    );
  }
  if (supported.length > 1 && !explicit) {
    const listing = supported.map((c) => `${c.path} (${c.version})`).join(", ");
    throw new InstallerError(
      AMBIGUOUS_BLENDER,
      `Multiple supported Blender installations found: ${listing}. ` +
        "Select one explicitly with --blender.",
    );
  }
  return supported[0];
}

export const _internal = { commonLocations, isExecutableFile, which };
