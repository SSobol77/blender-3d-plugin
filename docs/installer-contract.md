# Installer Contract (npm and Python)

This document is the single normative specification that both installer
frontends (`installers/npm` and `installers/python`) implement. Neither
frontend is the "reference" implementation; both must satisfy this contract
and are tested against the same scenarios (see `tests/fixtures/installer/`).

## Commands

| Command | Purpose |
|---|---|
| `install` | Discover Blender, resolve/verify a release artifact, install and enable the add-on |
| `update` | Re-resolve the artifact, install only if the version changed (or `--force`) |
| `uninstall` | Disable and remove the add-on from the selected Blender |
| `doctor` | Report the real state of the system: Blender discovery, extension state, filesystem writability |
| `list-blenders` | Print every discovered Blender candidate and whether it is supported |
| `version` | Print the installer's own version |
| `help` | Print usage |

## Options

| Option | Applies to | Meaning |
|---|---|---|
| `--blender PATH` | install, update, uninstall, doctor | Use this Blender executable explicitly; skips discovery/ambiguity checks |
| `--version VERSION` | install, update | Requested add-on version (defaults to the installer's bundled version) |
| `--json` | all | Machine-readable output on stdout |
| `--dry-run` | install, update, uninstall | Resolve and validate everything; perform no mutation |
| `--offline ZIP_PATH` | install, update | Use a local release ZIP instead of downloading one |
| `--yes` | uninstall | Required to actually remove files in non-interactive contexts |
| `--force` | install, update | Allow overwrite / allow downgrade |
| `--manifest-url URL` | install, update | Override the manifest URL (testing/mirrors only) |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 2 | invalid arguments |
| 3 | Blender not found |
| 4 | multiple Blender installations require explicit `--blender` selection |
| 5 | unsupported Blender version |
| 6 | release manifest failure (unreachable, malformed, fails schema/structure checks) |
| 7 | download failure (network error while fetching the artifact) |
| 8 | checksum mismatch |
| 9 | extension validation failure (unsafe or structurally invalid ZIP) |
| 10 | installation failure |
| 11 | update failure (e.g. downgrade attempted without `--force`) |
| 12 | uninstall failure |
| 13 | permission/path failure (e.g. temp directory not writable) |
| 14 | offline artifact failure (file missing or unreadable) |

Both frontends raise a typed internal error carrying one of these codes; the
CLI entrypoint is the only place that turns it into a process exit code.

## Blender discovery

Candidates are gathered from, in priority order:

1. `--blender PATH` (explicit; used as the sole candidate when given)
2. `PATH` (`which`/`where` equivalent)
3. common per-OS install locations:
   - **Linux**: `/usr/bin/blender`, `/usr/local/bin/blender`, `/opt/blender*/blender`,
     Flatpak (`~/.local/share/flatpak/exports/bin/blender`,
     `/var/lib/flatpak/exports/bin/blender`), Snap (`/snap/bin/blender`)
   - **macOS**: `/Applications/Blender.app/Contents/MacOS/Blender`,
     `~/Applications/Blender.app/Contents/MacOS/Blender`,
     versioned variants (`/Applications/Blender*.app/...`)
   - **Windows**: `%ProgramFiles%\Blender Foundation\Blender *\blender.exe`, PATH

Each candidate is deduplicated by resolved real path, checked for
"is a regular file and executable", then probed with
`<path> --version` (argument array, never a shell string) under a timeout.
The reported version is parsed and compared against the add-on's declared
`minimum_blender_version` / `maximum_blender_version_exclusive` to classify
it as supported or unsupported.

Selection rule used by `install`/`update`/`uninstall`/`doctor`:

- zero candidates at all → exit 3
- exactly one candidate and it is unsupported → exit 5
- exactly one supported candidate → use it
- more than one supported candidate and no `--blender` → exit 4
- `--blender` always short-circuits discovery; an invalid or unsupported
  explicit path still returns exit 3 / 5 respectively

`list-blenders` never fails on ambiguity; it lists every candidate found
(supported or not) so the user can choose one with `--blender`.

## Manifest and artifact verification

Online mode:

1. Build the manifest URL from `--manifest-url` or the default template
   `https://github.com/SSobol77/blender-3d-plugin/releases/download/v<version>/release-manifest.json`.
2. The URL scheme must be `https`, except loopback hosts
   (`localhost`/`127.0.0.1`/`::1`), which are permitted so tests and private
   mirrors can serve fixtures over plain `http` without a certificate. This
   is a deliberate, narrow testability exception, not a general HTTP allowance.
3. Fetch with a bounded timeout and a maximum response size; anything larger
   is rejected before being fully buffered.
4. Parse as JSON and structurally validate: `schema_version == "1.0.0"`,
   `version` matches `\d+\.\d+\.\d+`, and `artifacts.extension` has
   `filename`, `url`, a 64-hex-character `sha256`, and a non-negative
   `size`. Any failure here is exit 6.
5. Download `artifacts.extension.url` into a temporary file **next to** the
   final destination (so the final rename is atomic), enforcing the same
   HTTPS-or-loopback rule, a timeout, and a maximum size (network/transport
   failures are exit 7).
6. Compute the SHA-256 of the downloaded bytes and compare to the manifest;
   mismatch is exit 8, and the partial file is deleted.
7. Open the ZIP and validate its structure (exit 9 on any violation):
   it must be a valid ZIP, contain only members under a single top-level
   `blender_mobile_3d/` prefix, contain no absolute paths, no `..` segments,
   and no symlink entries.

Offline mode (`--offline ZIP_PATH`):

1. The path must exist and be readable (exit 14 otherwise).
2. The same ZIP structure validation from step 7 above still runs (exit 9
   on violation).
3. If a manifest is available for the requested version it is used to
   cross-check the checksum; if not, the checksum check is skipped and this
   is reported explicitly in `--json` output (never silently assumed valid).

All temporary/partial download files are removed on every failure path.

### A note on test isolation

`BLENDER_USER_RESOURCES` / `BLENDER_USER_SCRIPTS` correctly redirect where
`bpy.ops.preferences.addon_install` *writes* an add-on
(`bpy.utils.user_resource(...)` honors them), but in the Blender versions
this project targets, `addon_utils.paths()` — what `addon_utils.modules()`
scans to answer "is it installed" — does **not** consult those variables
and always falls back to the literal `~/.config/blender/<version>/scripts/addons`.
The practical effect: two sequential operations *inside the same Blender
process* stay consistent (install refreshes the runtime's known script
paths for that session), but a **separate** process's status/doctor query
will still see whatever is actually sitting in the real
`~/.config/blender` tree, regardless of any `BLENDER_USER_RESOURCES`
override.

The only reliable way to get a genuinely isolated Blender profile per test
run is to override `HOME` itself for the Blender subprocess, so the
default `~/.config/blender` resolves inside the isolated directory. This
is a **test/CI concern only** — the installer itself must never override
`HOME` for a real user's `install`/`update`/`uninstall`/`doctor` run, since
the entire point of those commands is to act on the user's actual Blender
profile. CI's Blender regression job uses a distinct isolated `HOME` per
frontend (npm vs Python) so neither can pass because the other already
installed the extension.

## Installation mechanism

Both frontends invoke the **same** small Blender-side helper script
(`blender_helper.py`, kept identical in both packages and verified so by
a byte-equality test) via:

```text
<blender> --background --factory-startup --python blender_helper.py -- <json-args>
```

The helper uses Blender's official extension mechanism
(`bpy.ops.preferences.addon_install`, `addon_enable`, `addon_disable`,
`addon_remove`) and `addon_utils` to query installed/enabled state and the
add-on's own `bl_info["version"]`. It prints exactly one JSON line to
stdout that the calling installer parses; both installers check the
subprocess's exit code **and** parse that JSON — a zero exit code alone is
never treated as success.

Neither installer ever uses `shell=True`, string-interpolated shell
commands, or `os.system`/uncontrolled `exec`. Blender is always invoked
with an explicit argument array.

`install`/`update` are idempotent: installing the same version twice, or
enabling an already-enabled add-on, succeeds without error. `--force` is
required to overwrite with `overwrite=True` semantics beyond the default
(the default already allows same-version reinstall; `--force` is what
allows an explicit downgrade in `update`). `--dry-run` performs every
resolution and validation step and reports what would happen, but never
invokes the Blender install/update/uninstall helper actions.

This add-on defines no persistent `AddonPreferences` and stores no
configuration outside the current `.blend` file, so "preserve user
settings" on update and "preserve user configuration" on uninstall are
satisfied by construction: removing or reinstalling the add-on's files
never touches scene data.

## `doctor`

Reports (human-readable or `--json`):

- `platform`
- `installer_version`
- `blender_candidates` (from discovery, each with path/version/supported)
- `selected_blender` (path, version, supported) or `null`
- `extension_installed`, `extension_enabled`, `extension_version`
  (queried from the selected Blender via the helper's `status` action; all
  `null` when no Blender is selected)
- `tmp_dir_writable` (a real write-then-delete probe, not assumed)
- `manifest_reachable` (only probed when `--online` is passed; otherwise
  reported as `"skipped (offline)"`)

`doctor` exits non-zero (matching the relevant code above) when a required
check fails: no supported Blender found (3), or the temp directory is not
writable (13). Extension/manifest state is informational and does not by
itself fail `doctor`.

## Shared test vectors

`tests/fixtures/installer/*.json` holds the golden manifest fixtures
(`manifest_valid.json`, `manifest_malformed.json`,
`manifest_schema_invalid.json`) that both the Python and Node test suites
load, so a manifest that one frontend accepts or rejects is guaranteed to
be judged identically by the other.
