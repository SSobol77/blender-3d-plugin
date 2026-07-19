import process from "node:process";

import { parseOptions } from "../argParsing.js";
import { InstallerError, PERMISSION_FAILURE, BLENDER_NOT_FOUND } from "../exitCodes.js";
import { doDoctor } from "../installer.js";
import { printResult } from "../output.js";

const INSTALLER_VERSION = "1.0.0";

export async function doctor(args) {
  let opts;
  try {
    opts = parseOptions(args);
  } catch (err) {
    process.stderr.write(`error: ${err.message}\n`);
    return err instanceof InstallerError ? err.exitCode : 2;
  }

  const report = await doDoctor({
    explicitBlender: opts.blender,
    checkOnline: opts.online,
    installerVersion: INSTALLER_VERSION,
  });
  printResult(report, opts.json);

  if (!report.ok) {
    return report.tmpDirWritable ? BLENDER_NOT_FOUND : PERMISSION_FAILURE;
  }
  return 0;
}
