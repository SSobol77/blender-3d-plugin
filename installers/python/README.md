# blender-mobile-3d (Python installer)

Secure installer and command-line manager for the Blender Mobile 3D
add-on. Full normative reference (commands, options, exit codes,
discovery rules, security guarantees):
[docs/installer-contract.md](../../docs/installer-contract.md).

**Not yet published to PyPI.** Install from source for now:

```bash
cd installers/python
pip install -e .
```

## Commands

```bash
blender-mobile-3d install   [--blender PATH] [--version V] [--offline ZIP] [--manifest-url URL] [--dry-run] [--force] [--json]
blender-mobile-3d update    [--blender PATH] [--version V] [--offline ZIP] [--manifest-url URL] [--dry-run] [--force] [--json]
blender-mobile-3d uninstall [--blender PATH] [--yes] [--dry-run] [--json]
blender-mobile-3d doctor    [--blender PATH] [--online] [--json]
blender-mobile-3d list-blenders [--blender PATH] [--json]
blender-mobile-3d version
blender-mobile-3d help
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 2 | invalid arguments |
| 3 | Blender not found |
| 4 | multiple Blender installations require `--blender` |
| 5 | unsupported Blender version |
| 6 | release manifest failure |
| 7 | download failure |
| 8 | checksum mismatch |
| 9 | extension validation failure (unsafe/invalid ZIP) |
| 10 | installation failure |
| 11 | update failure (e.g. downgrade without `--force`) |
| 12 | uninstall failure |
| 13 | permission/path failure |
| 14 | offline artifact failure |

## Example

```bash
blender-mobile-3d doctor --json
blender-mobile-3d install --offline dist/blender_mobile_3d-1.0.0.zip --dry-run
blender-mobile-3d install --offline dist/blender_mobile_3d-1.0.0.zip
blender-mobile-3d uninstall --yes
```

## License

GPL-2.0-only
