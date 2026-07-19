#!/usr/bin/env node
import process from "node:process";

import { install } from "./commands/install.js";
import { update } from "./commands/update.js";
import { uninstall } from "./commands/uninstall.js";
import { doctor } from "./commands/doctor.js";
import { listBlenders } from "./commands/list-blenders.js";
import { version } from "./commands/version.js";
import { help } from "./commands/help.js";
import { INVALID_ARGUMENTS } from "./exitCodes.js";

const commands = {
  install,
  update,
  uninstall,
  doctor,
  "list-blenders": listBlenders,
  version,
  help,
};

export async function main(argv = process.argv.slice(2)) {
  const name = argv[0];
  if (name === undefined || name === "help" || name === "--help" || name === "-h") {
    return help();
  }
  const fn = commands[name];
  if (!fn) {
    process.stderr.write(`error: unknown command: ${name}\n`);
    return INVALID_ARGUMENTS;
  }
  return fn(argv.slice(1));
}
