import process from "node:process";

import { parseOptions } from "../argParsing.js";
import { InstallerError } from "../exitCodes.js";
import { doUpdate } from "../installer.js";
import { printResult } from "../output.js";

export async function update(args) {
  let opts;
  try {
    opts = parseOptions(args);
  } catch (err) {
    process.stderr.write(`error: ${err.message}\n`);
    return err instanceof InstallerError ? err.exitCode : 2;
  }

  try {
    const result = await doUpdate({
      explicitBlender: opts.blender,
      version: opts.addonVersion,
      manifestUrl: opts.manifestUrl,
      offlineZip: opts.offlineZip,
      dryRun: opts.dryRun,
      force: opts.force,
    });
    printResult(result, opts.json);
    return 0;
  } catch (err) {
    if (!(err instanceof InstallerError)) throw err;
    if (opts.json) {
      console.log(JSON.stringify({ ok: false, error: err.message, exitCode: err.exitCode }));
    } else {
      process.stderr.write(`error: ${err.message}\n`);
    }
    return err.exitCode;
  }
}
