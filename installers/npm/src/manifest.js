/**
 * Manifest fetching and structural validation.
 *
 * Hand-validated (no schema library dependency) identically to the Python
 * installer so the two frontends can never diverge on what they accept or
 * reject; see docs/installer-contract.md and tests/fixtures/installer/.
 */

import { InstallerError, MANIFEST_FAILURE } from "./exitCodes.js";

export const MANIFEST_MAX_BYTES = 1 * 1024 * 1024;
export const MANIFEST_TIMEOUT_MS = 15_000;
const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1", "::1"]);
const VERSION_RE = /^\d+\.\d+\.\d+$/;
const SHA256_RE = /^[0-9a-f]{64}$/;

export const DEFAULT_MANIFEST_URL_TEMPLATE =
  "https://github.com/SSobol77/blender-3d-plugin/releases/download/" +
  "v{version}/release-manifest.json";

function requireHttpsOrLoopback(url, exitCode) {
  const parsed = new URL(url);
  if (parsed.protocol === "https:") return;
  if (parsed.protocol === "http:" && LOOPBACK_HOSTS.has(parsed.hostname)) return;
  throw new InstallerError(
    exitCode,
    `Refusing non-HTTPS URL (loopback exempt for testing only): ${url}`,
  );
}

/** Throws InstallerError(MANIFEST_FAILURE) on any structural defect. */
export function validateManifestStructure(data) {
  if (data === null || typeof data !== "object" || Array.isArray(data)) {
    throw new InstallerError(MANIFEST_FAILURE, "Manifest root must be a JSON object.");
  }
  if (data.schema_version !== "1.0.0") {
    throw new InstallerError(
      MANIFEST_FAILURE,
      `Unsupported manifest schema_version: ${JSON.stringify(data.schema_version)}`,
    );
  }
  if (typeof data.version !== "string" || !VERSION_RE.test(data.version)) {
    throw new InstallerError(
      MANIFEST_FAILURE,
      `Invalid manifest version: ${JSON.stringify(data.version)}`,
    );
  }
  const ext = data.artifacts && data.artifacts.extension;
  if (!ext || typeof ext !== "object") {
    throw new InstallerError(MANIFEST_FAILURE, "Manifest missing artifacts.extension object.");
  }
  if (typeof ext.filename !== "string" || ext.filename.length === 0) {
    throw new InstallerError(MANIFEST_FAILURE, "Manifest extension.filename missing or invalid.");
  }
  if (typeof ext.url !== "string" || ext.url.length === 0) {
    throw new InstallerError(MANIFEST_FAILURE, "Manifest extension.url missing or invalid.");
  }
  if (typeof ext.sha256 !== "string" || !SHA256_RE.test(ext.sha256)) {
    throw new InstallerError(
      MANIFEST_FAILURE,
      `Manifest extension.sha256 invalid: ${JSON.stringify(ext.sha256)}`,
    );
  }
  if (!Number.isInteger(ext.size) || ext.size < 0) {
    throw new InstallerError(
      MANIFEST_FAILURE,
      `Manifest extension.size invalid: ${JSON.stringify(ext.size)}`,
    );
  }

  return {
    schemaVersion: data.schema_version,
    version: data.version,
    minimumBlenderVersion: data.minimum_blender_version ?? null,
    maximumBlenderVersionExclusive: data.maximum_blender_version_exclusive ?? null,
    extension: {
      filename: ext.filename,
      url: ext.url,
      sha256: ext.sha256,
      size: ext.size,
    },
  };
}

/** Fetch and validate the manifest for `version` over the network. */
export async function fetchManifest(version, manifestUrl = null) {
  const url = manifestUrl || DEFAULT_MANIFEST_URL_TEMPLATE.replace("{version}", version);
  requireHttpsOrLoopback(url, MANIFEST_FAILURE);

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), MANIFEST_TIMEOUT_MS);
  let response;
  try {
    response = await fetch(url, {
      signal: controller.signal,
      headers: { "User-Agent": "blender-mobile-3d-installer" },
    });
  } catch (err) {
    throw new InstallerError(MANIFEST_FAILURE, `Could not fetch manifest from ${url}: ${err.message}`);
  } finally {
    clearTimeout(timer);
  }

  if (!response.ok) {
    throw new InstallerError(
      MANIFEST_FAILURE,
      `Could not fetch manifest from ${url}: HTTP ${response.status}`,
    );
  }

  const buffer = await response.arrayBuffer();
  if (buffer.byteLength > MANIFEST_MAX_BYTES) {
    throw new InstallerError(MANIFEST_FAILURE, `Manifest at ${url} exceeds the size limit.`);
  }

  let data;
  try {
    data = JSON.parse(Buffer.from(buffer).toString("utf8"));
  } catch (err) {
    throw new InstallerError(MANIFEST_FAILURE, `Manifest at ${url} is not valid JSON: ${err.message}`);
  }

  return validateManifestStructure(data);
}
