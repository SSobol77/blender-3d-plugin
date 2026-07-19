/** Invoke blender_helper.py inside Blender via an explicit argument array. */

import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import { INSTALL_FAILURE, InstallerError } from "./exitCodes.js";

export const BLENDER_OP_TIMEOUT_MS = 120_000;
export const MODULE_NAME = "blender_mobile_3d";

const HELPER_SCRIPT_PATH = fileURLToPath(new URL("./data/blender_helper.py", import.meta.url));

function runHelper(blenderPath, request) {
  const cmd = [
    "--background",
    "--factory-startup",
    "--python",
    HELPER_SCRIPT_PATH,
    "--",
    JSON.stringify(request),
  ];
  const result = spawnSync(blenderPath, cmd, {
    timeout: BLENDER_OP_TIMEOUT_MS,
    encoding: "utf8",
  });

  if (result.error) {
    throw new InstallerError(INSTALL_FAILURE, `Failed to run Blender helper: ${result.error.message}`);
  }
  if (result.status !== 0) {
    const tail = (result.stderr || "").slice(-2000);
    throw new InstallerError(INSTALL_FAILURE, `Blender exited with code ${result.status}.\n${tail}`);
  }

  const lines = (result.stdout || "").split("\n").reverse();
  const jsonLine = lines.map((l) => l.trim()).find((l) => l.startsWith("{"));
  if (!jsonLine) {
    const tail = (result.stdout || "").slice(-2000);
    throw new InstallerError(INSTALL_FAILURE, `Blender helper produced no JSON result.\n${tail}`);
  }

  let parsed;
  try {
    parsed = JSON.parse(jsonLine);
  } catch (err) {
    throw new InstallerError(INSTALL_FAILURE, `Blender helper produced invalid JSON: ${err.message}`);
  }

  if (!parsed.ok) {
    throw new InstallerError(INSTALL_FAILURE, `Blender helper reported failure: ${parsed.error}`);
  }
  return parsed;
}

export function status(blenderPath, moduleName = MODULE_NAME) {
  return runHelper(blenderPath, { action: "status", module: moduleName });
}

export function install(blenderPath, zipPath, overwrite = true, moduleName = MODULE_NAME) {
  return runHelper(blenderPath, {
    action: "install",
    module: moduleName,
    zip_path: String(zipPath),
    overwrite,
  });
}

export function uninstall(blenderPath, moduleName = MODULE_NAME) {
  return runHelper(blenderPath, { action: "uninstall", module: moduleName });
}
