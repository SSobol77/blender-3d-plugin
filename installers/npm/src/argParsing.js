/** Minimal shared CLI flag parser for the installer commands. */

import { INVALID_ARGUMENTS, InstallerError } from "./exitCodes.js";

const KNOWN_VALUE_FLAGS = {
  "--blender": "blender",
  "--version": "addonVersion",
  "--offline": "offlineZip",
  "--manifest-url": "manifestUrl",
};

const KNOWN_BOOLEAN_FLAGS = {
  "--json": "json",
  "--dry-run": "dryRun",
  "--force": "force",
  "--yes": "yes",
  "--online": "online",
};

export function parseOptions(args) {
  const opts = {
    blender: null,
    addonVersion: "1.0.0",
    offlineZip: null,
    manifestUrl: null,
    json: false,
    dryRun: false,
    force: false,
    yes: false,
    online: false,
  };

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg in KNOWN_VALUE_FLAGS) {
      i += 1;
      const value = args[i];
      if (value === undefined) {
        throw new InstallerError(INVALID_ARGUMENTS, `Missing value for ${arg}`);
      }
      opts[KNOWN_VALUE_FLAGS[arg]] = value;
    } else if (arg in KNOWN_BOOLEAN_FLAGS) {
      opts[KNOWN_BOOLEAN_FLAGS[arg]] = true;
    } else {
      throw new InstallerError(INVALID_ARGUMENTS, `Unknown option: ${arg}`);
    }
  }
  return opts;
}
