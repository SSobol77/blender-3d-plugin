/**
 * ZIP structure validation: single top-level package, no traversal, no
 * symlinks. Parses only the central directory (entry names + external
 * attributes), never extracts, so no dependency on a zip-extraction
 * library is needed just to validate structure.
 */

import { open } from "node:fs/promises";

import { EXTENSION_VALIDATION_FAILURE, InstallerError } from "./exitCodes.js";

export const EXPECTED_TOP_LEVEL = "blender_mobile_3d";
export const REQUIRED_MEMBERS = [
  `${EXPECTED_TOP_LEVEL}/__init__.py`,
  `${EXPECTED_TOP_LEVEL}/version.py`,
];

const END_OF_CENTRAL_DIR_SIG = 0x06054b50;
const CENTRAL_DIR_HEADER_SIG = 0x02014b50;
const S_IFLNK = 0xa000;
const S_IFMT = 0xf000;

function fail(message) {
  throw new InstallerError(EXTENSION_VALIDATION_FAILURE, message);
}

/** Read the whole file and locate/parse the End Of Central Directory record. */
async function readCentralDirectoryEntries(zipPath) {
  const handle = await open(zipPath, "r");
  let buffer;
  try {
    const { size } = await handle.stat();
    if (size < 22) fail(`Not a valid ZIP archive: ${zipPath}`);
    buffer = Buffer.alloc(size);
    await handle.read(buffer, 0, size, 0);
  } finally {
    await handle.close();
  }

  let eocdOffset = -1;
  const searchStart = Math.max(0, buffer.length - 22 - 65_536);
  for (let i = buffer.length - 22; i >= searchStart; i -= 1) {
    if (buffer.readUInt32LE(i) === END_OF_CENTRAL_DIR_SIG) {
      eocdOffset = i;
      break;
    }
  }
  if (eocdOffset === -1) fail(`Not a valid ZIP archive: ${zipPath}`);

  const entryCount = buffer.readUInt16LE(eocdOffset + 10);
  const centralDirOffset = buffer.readUInt32LE(eocdOffset + 16);

  const entries = [];
  let offset = centralDirOffset;
  for (let i = 0; i < entryCount; i += 1) {
    if (buffer.readUInt32LE(offset) !== CENTRAL_DIR_HEADER_SIG) {
      fail(`Corrupt or unsupported ZIP central directory in: ${zipPath}`);
    }
    const externalAttr = buffer.readUInt32LE(offset + 38);
    const nameLen = buffer.readUInt16LE(offset + 28);
    const extraLen = buffer.readUInt16LE(offset + 30);
    const commentLen = buffer.readUInt16LE(offset + 32);
    const name = buffer.toString("utf8", offset + 46, offset + 46 + nameLen);
    entries.push({ name, externalAttr });
    offset += 46 + nameLen + extraLen + commentLen;
  }
  return entries;
}

function isSymlinkEntry(externalAttr) {
  const unixMode = externalAttr >>> 16;
  return unixMode !== 0 && (unixMode & S_IFMT) === S_IFLNK;
}

function isUnsafeName(name) {
  if (name.startsWith("/") || name.startsWith("\\")) return true;
  if (/^[a-zA-Z]:/.test(name)) return true;
  const parts = name.split(/[/\\]/).filter((p) => p.length > 0);
  if (parts.includes("..")) return true;
  if (parts.length === 0 || parts[0] !== EXPECTED_TOP_LEVEL) return true;
  return false;
}

/** Throws InstallerError(EXTENSION_VALIDATION_FAILURE) on any violation. */
export async function validateZipSafety(zipPath) {
  const entries = await readCentralDirectoryEntries(zipPath);

  for (const entry of entries) {
    if (isSymlinkEntry(entry.externalAttr)) {
      fail(`ZIP contains a symlink entry: ${entry.name}`);
    }
    if (isUnsafeName(entry.name)) {
      fail(`ZIP contains an unsafe path: ${entry.name}`);
    }
  }

  const names = new Set(entries.map((e) => e.name));
  const missing = REQUIRED_MEMBERS.filter((m) => !names.has(m));
  if (missing.length > 0) {
    fail(`ZIP is missing required members: ${JSON.stringify(missing)}`);
  }
}
