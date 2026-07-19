# Release Candidate Evidence Matrix - v1.0.0

## Legend
- ✅ Implemented and verified
- 🔄 Implemented but unverified
- ⚠️ Partially implemented
- ❌ Missing
- ⏸️ Intentionally out of scope / awaiting PO approval

## Requirements (from original v1.0.0 prompt)

| # | Requirement | Status | Notes |
|---|------------|--------|-------|
| 1 | Baseline audit | ✅ | Produced `raport.md` before any code changes |
| 2 | GPL-2.0-only consistency | ✅ | LICENSE, SKILL.md, NOTICE, add-on metadata all GPL |
| 3 | Fixed `export_mobile.py` preset_path | ✅ | Rewritten as `blender_mobile_3d/operators/export.py` |
| 4 | Fixed `low_poly_lod.py` copy/rename | ✅ | Rewritten as `blender_mobile_3d/operators/generate_lod.py` |
| 5 | Fixed `auto_rig.py` bone hierarchy/mesh binding | ✅ | Rewritten as `blender_mobile_3d/operators/auto_rig.py` |
| 6 | Real scene measurement `scene_metrics.py` | ✅ | Implemented in `blender_mobile_3d/core/metrics.py` and `scene.py` |
| 7 | Asset validation `validate_workflows.py` | ✅ | `tests/validate_workflows.py` and `blender_mobile_3d/core/validation.py` |
| 8 | CI/CD pipeline | 🔄 | Defined at `.github/workflows/ci.yml`; CI run results pending |
| 9 | Compatibility matrix docs | 🔄 | Docs scaffolded; formal matrix not exhaustive |
| 10 | Security review | 🔄 | SECURITY.md added; scans defined but not executed successfully |
| 11 | Automated tests | ⚠️ | 12 unit tests pass; insufficient coverage: exporter, manifest, CLI, MCP, packaging |
| 12 | Blender integration tests | ⚠️ | Install+enable smoke test passes; no analysis, LOD, rig, export tests |
| 13 | Correct Blender version requirements | ✅ | Relaxed to 4.3+ throughout docs |
| 14 | Agent-neutral naming | ✅ | `plugin-core` replaces `hermes-skill` |
| 15 | Packaging, versioning, manifests | ✅ | `pyproject.toml`, `version.py`, `schemas/`, `presets/` |
| 16 | Release artifacts with SHA-256 | ✅ | `scripts/release_artifacts.py` produces ZIP + checksum |
| 17 | Clean-install verification | ⚠️ | Headless Blender install+enable works; end-to-end export not yet validated |
| 18 | Multi-language docs (EN/PL/RU/zh-Hant) | ⚠️ | Docs exist; automated checks pending; native review not completed |
| 19 | Ruff/formatting/type checking/coverage/bandit/pip-audit/secret-scan/actionlint | ❌ | Commands defined in CI; not proven locally or on CI |
| 20 | Manifest JSON Schema validation | 🔄 | Schema defined; tests absent |
| 21 | Safe path and archive tests | 🔄 | Path safety implemented; no archive-specific tests |
| 22 | Target-aware export tests | ⚠️ | Exporter types exist; no tests |
| 23 | Blender registration/unregistration idempotency | ❌ | Test script exists; should be expanded |
| 24 | Actual scene analysis/LOD/rig/export in Blender | ❌ | Smoke test only |
| 25 | CLI exit codes | ⚠️ | CLI scaffolded; exit handling exists but not tested exhaustively |
| 26 | Invalid configuration behavior | ⚠️ | Schema/loader rejects bad versions; needs more tests |
| 27 | Unicode/space paths | ❌ | Not tested |
| 28 | Overwrite protection | ⚠️ | Release script does not prevent overwrite explicitly |
| 29 | Reproducible packaging | 🔄 | Release script deterministically builds ZIP; reproducibility not proven |
| 30 | No v1.0.0 tag/release until approval | ✅ | Draft PR created; no tag/release exists |
