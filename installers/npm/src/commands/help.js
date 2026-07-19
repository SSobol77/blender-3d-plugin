
export async function help() {
  const lines = [
    "blender-mobile-3d commands:",
    "  install",
    "  update",
    "  uninstall",
    "  doctor",
    "  list-blenders",
    "  version",
    "  help",
  ];
  for (const line of lines) console.log(line);
  return 0;
}
