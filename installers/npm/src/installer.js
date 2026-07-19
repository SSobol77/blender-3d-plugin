/**
 * Orchestration for install/update/uninstall/doctor/list-blenders.
 * Blender itself is the source of truth for installed/enabled state and
 * version (queried via blenderOps.status); this module keeps no separate
 * state file.
 */

import { mkdtemp, stat, unlink, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import process from "node:process";

import * as blenderOps from "./blenderOps.js";
import { discoverBlenders, selectBlender } from "./blenderDiscovery.js";
import { downloadArtifact } from "./download.js";
import {
  INVALID_ARGUMENTS,
  OFFLINE_ARTIFACT_FAILURE,
  UNINSTALL_FAILURE,
  UPDATE_FAILURE,
  InstallerError,
} from "./exitCodes.js";
import { fetchManifest } from "./manifest.js";
import { validateZipSafety } from "./zipSafety.js";

function versionTuple(version) {
  return version.split(".").map(Number);
}

function compareVersionTuples(a, b) {
  for (let i = 0; i < Math.max(a.length, b.length); i += 1) {
    const diff = (a[i] || 0) - (b[i] || 0);
    if (diff !== 0) return diff;
  }
  return 0;
}

async function pathExists(candidate) {
  try {
    const info = await stat(candidate);
    return info.isFile();
  } catch {
    return false;
  }
}

/** Return a local, validated ZIP path; downloads it if not offline. */
export async function resolveArtifact(
  version,
  manifestUrl,
  offlineZip,
  maxSizeBytes = 200 * 1024 * 1024,
) {
  if (offlineZip) {
    if (!(await pathExists(offlineZip))) {
      throw new InstallerError(
        OFFLINE_ARTIFACT_FAILURE,
        `Offline artifact not found: ${offlineZip}`,
      );
    }
    await validateZipSafety(offlineZip);
    return offlineZip;
  }

  const manifest = await fetchManifest(version, manifestUrl);
  const destDir = await mkdtemp(path.join(os.tmpdir(), "bm3d-download-"));
  const destPath = path.join(destDir, manifest.extension.filename);
  await downloadArtifact(manifest.extension.url, destPath, manifest.extension.sha256, maxSizeBytes);
  await validateZipSafety(destPath);
  return destPath;
}

export async function doInstall({
  explicitBlender,
  version,
  manifestUrl,
  offlineZip,
  dryRun,
  force: _force,
}) {
  const candidate = selectBlender(explicitBlender);
  const artifactPath = await resolveArtifact(version, manifestUrl, offlineZip);

  if (dryRun) {
    return { ok: true, dryRun: true, blender: candidate, artifact: artifactPath };
  }

  // install always overwrites (safe: same-version reinstall is idempotent);
  // --force is meaningful for update's downgrade check, not here.
  const result = blenderOps.install(candidate.path, artifactPath, true);
  return { ok: true, dryRun: false, blender: candidate, ...result };
}

export async function doUpdate({
  explicitBlender,
  version,
  manifestUrl,
  offlineZip,
  dryRun,
  force,
}) {
  const candidate = selectBlender(explicitBlender);
  const current = blenderOps.status(candidate.path);

  if (current.installed && current.version) {
    const currentV = versionTuple(current.version);
    const requestedV = versionTuple(version);
    if (compareVersionTuples(requestedV, currentV) < 0 && !force) {
      throw new InstallerError(
        UPDATE_FAILURE,
        `Refusing to downgrade from ${current.version} to ${version} without --force.`,
      );
    }
    if (compareVersionTuples(requestedV, currentV) === 0 && !force) {
      return {
        ok: true,
        dryRun,
        updated: false,
        blender: candidate,
        version: current.version,
        message: "Already up to date; no update necessary.",
      };
    }
  }

  const artifactPath = await resolveArtifact(version, manifestUrl, offlineZip);

  if (dryRun) {
    return { ok: true, dryRun: true, updated: true, blender: candidate, artifact: artifactPath };
  }

  const result = blenderOps.install(candidate.path, artifactPath, true);
  return { ok: true, dryRun: false, updated: true, blender: candidate, ...result };
}

export function doUninstall({ explicitBlender, dryRun, yes }) {
  const candidate = selectBlender(explicitBlender);
  const current = blenderOps.status(candidate.path);

  if (!current.installed) {
    return { ok: true, dryRun, removed: false, blender: candidate, message: "Already uninstalled." };
  }

  if (dryRun) {
    return { ok: true, dryRun: true, removed: false, blender: candidate };
  }

  if (!yes) {
    throw new InstallerError(
      INVALID_ARGUMENTS,
      "Refusing to uninstall without --yes in a non-interactive context.",
    );
  }

  const result = blenderOps.uninstall(candidate.path);
  if (result.installed) {
    throw new InstallerError(UNINSTALL_FAILURE, "Blender still reports the add-on as installed.");
  }
  return { ok: true, dryRun: false, removed: true, blender: candidate, ...result };
}

export async function tmpDirWritable() {
  const probe = path.join(os.tmpdir(), `bm3d-doctor-${process.pid}-${Date.now()}`);
  try {
    await writeFile(probe, "ok", "utf8");
    await unlink(probe);
    return true;
  } catch {
    return false;
  }
}

export async function doDoctor({ explicitBlender, checkOnline, installerVersion }) {
  const candidates = discoverBlenders(explicitBlender);
  const supported = candidates.filter((c) => c.supported);
  let selected = supported.length === 1 ? supported[0] : null;
  if (explicitBlender && candidates.length > 0) selected = candidates[0];

  let extensionState = { installed: null, enabled: null, version: null };
  if (selected !== null) {
    try {
      const status = blenderOps.status(selected.path);
      extensionState = {
        installed: status.installed,
        enabled: status.enabled,
        version: status.version,
      };
    } catch {
      // Query failure is reported as null state, not a doctor crash.
    }
  }

  let manifestReachable = "skipped (offline)";
  if (checkOnline) {
    try {
      await fetchManifest(installerVersion);
      manifestReachable = true;
    } catch {
      manifestReachable = false;
    }
  }

  const tmpWritable = await tmpDirWritable();

  return {
    platform: `${os.type()} ${os.release()} ${os.arch()}`,
    installerVersion,
    blenderCandidates: candidates,
    selectedBlender: selected,
    extensionInstalled: extensionState.installed,
    extensionEnabled: extensionState.enabled,
    extensionVersion: extensionState.version,
    tmpDirWritable: tmpWritable,
    manifestReachable,
    ok: supported.length > 0 && tmpWritable,
  };
}

export function doListBlenders({ explicitBlender }) {
  return { ok: true, blenders: discoverBlenders(explicitBlender) };
}
