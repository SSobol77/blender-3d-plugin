
export async function doctor(args) {
  const out = { status: "ok" };
  if (args.includes("--json")) {
    console.log(JSON.stringify(out, null, 2));
  } else {
    console.log("doctor: ok");
  }
  return 0;
}
