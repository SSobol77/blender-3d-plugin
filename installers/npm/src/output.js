/** Shared human/JSON output formatting for CLI commands. */

export function printResult(result, asJson) {
  if (asJson) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }
  for (const [key, value] of Object.entries(result)) {
    console.log(`${key}: ${typeof value === "object" ? JSON.stringify(value) : value}`);
  }
}
