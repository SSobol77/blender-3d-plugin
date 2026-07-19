// Minimal single-level wildcard glob for Blender discovery path patterns,
// e.g. a version-numbered directory segment such as "blender-5.2.0" matched
// by a "blender-" + wildcard segment. No recursive wildcard, "?", or
// bracket support needed. Avoids depending on Node's experimental fs.glob
// or an external package.

import { readdirSync } from "node:fs";
import path from "node:path";

function segmentToRegExp(segment) {
  const escaped = segment.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*");
  return new RegExp(`^${escaped}$`);
}

export function globSync(pattern) {
  const isAbsolute = path.isAbsolute(pattern);
  const segments = pattern.split(/[/\\]/).filter((s) => s.length > 0);
  let bases = [isAbsolute ? path.parse(pattern).root || "/" : "."];

  for (const segment of segments) {
    if (!segment.includes("*")) {
      bases = bases.map((base) => path.join(base, segment));
      continue;
    }
    const regex = segmentToRegExp(segment);
    const next = [];
    for (const base of bases) {
      let entries;
      try {
        entries = readdirSync(base);
      } catch {
        continue;
      }
      for (const entry of entries) {
        if (regex.test(entry)) next.push(path.join(base, entry));
      }
    }
    bases = next;
  }
  return bases;
}
