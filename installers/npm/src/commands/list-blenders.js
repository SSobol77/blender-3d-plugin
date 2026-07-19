import process from "node:process";

import { parseOptions } from "../argParsing.js";
import { InstallerError } from "../exitCodes.js";
import { doListBlenders } from "../installer.js";
import { printResult } from "../output.js";

export async function listBlenders(args) {
  let opts;
  try {
    opts = parseOptions(args);
  } catch (err) {
    process.stderr.write(`error: ${err.message}\n`);
    return err instanceof InstallerError ? err.exitCode : 2;
  }

  const result = doListBlenders({ explicitBlender: opts.blender });
  printResult(result, opts.json);
  return 0;
}
