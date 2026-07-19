#!/usr/bin/env node
import process from "node:process";

import { install } from "./commands/install.js";
import { update } from "./commands/update.js";
import { uninstall } from "./commands/uninstall.js";
import { doctor } from "./commands/doctor.js";
import { listBlenders } from "./commands/list-blenders.js";
import { version } from "./commands/version.js";
import { help } from "./commands/help.js";

const commands = {
  install,
  update,
  uninstall,
  doctor,
  "list-blenders": listBlenders,
  version,
  help,
};

export async function main() {
  const args = process.argv.slice(2);
  const name = args[0];
  const fn = commands[name];
  if (!fn) {
    console.error(`Unknown command: ${name}`);
    process.exitCode = 2;
    return;
  }
  const code = await fn(args.slice(1));
  if (typeof code === "number") process.exitCode = code;
}
