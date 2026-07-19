"""Tests for scripts/verify_release_versions.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify_release_versions.py"


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed argument array, test-controlled args
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def test_all_sources_agree_on_current_version() -> None:
    result = run(["--expected-version", "1.0.0", "--git-tag", "v1.0.0"])
    assert result.returncode == 0
    assert "all sources agree" in result.stdout


def test_mismatched_expected_version_fails_closed() -> None:
    result = run(["--expected-version", "9.9.9", "--git-tag", "v9.9.9"])
    assert result.returncode == 1
    assert "FAILED" in result.stderr
    assert "version.py" in result.stderr
    assert "bl_info" in result.stderr
    assert "blender_manifest.toml" in result.stderr
    assert "package.json" in result.stderr
    assert "pyproject.toml" in result.stderr


@pytest.mark.parametrize(
    "bad_tag",
    ["1.0.0", "v1.0", "v1.0.0-beta", "version1.0.0", "v1.0.0.0"],
)
def test_malformed_tag_format_fails_closed(bad_tag: str) -> None:
    result = run(["--expected-version", "1.0.0", "--git-tag", bad_tag])
    assert result.returncode == 1
    assert "tag format" in result.stderr or "does not match" in result.stderr


def test_tag_version_mismatch_with_expected_fails_closed() -> None:
    result = run(["--expected-version", "1.0.0", "--git-tag", "v2.0.0"])
    assert result.returncode == 1
    assert "tag-derived version" in result.stderr


def test_release_manifest_agreement_passes(tmp_path: Path) -> None:
    manifest = tmp_path / "release-manifest.json"
    manifest.write_text(json.dumps({"schema_version": "1.0.0", "version": "1.0.0"}))
    result = run(["--expected-version", "1.0.0", "--release-manifest", str(manifest)])
    assert result.returncode == 0


def test_release_manifest_mismatch_fails_closed(tmp_path: Path) -> None:
    manifest = tmp_path / "release-manifest.json"
    manifest.write_text(json.dumps({"schema_version": "1.0.0", "version": "9.9.9"}))
    result = run(["--expected-version", "1.0.0", "--release-manifest", str(manifest)])
    assert result.returncode == 1
    assert "release-manifest" in result.stderr


def test_release_manifest_missing_file_fails_closed(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.json"
    result = run(["--expected-version", "1.0.0", "--release-manifest", str(missing)])
    assert result.returncode == 1
    assert "missing" in result.stderr


def test_tag_reachable_from_main_passes_for_head() -> None:
    result = run(
        [
            "--expected-version",
            "1.0.0",
            "--git-tag",
            "v1.0.0",
            "--require-main-ancestor",
            "HEAD",
            "--commit",
            "HEAD",
        ]
    )
    assert result.returncode == 0


def _repo_root_commit() -> str:
    result = subprocess.run(  # noqa: S603 - fixed argument array
        ["git", "rev-list", "--max-parents=0", "HEAD"],  # noqa: S607 - git resolved via PATH
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().splitlines()[-1]


def _is_shallow_repository() -> bool:
    result = subprocess.run(  # noqa: S603 - fixed argument array
        ["git", "rev-parse", "--is-shallow-repository"],  # noqa: S607 - git resolved via PATH
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip() == "true"


def test_tag_unreachable_from_ref_fails_closed() -> None:
    # HEAD is a descendant of the repo's root commit, not the other way
    # around, so HEAD is provably NOT an ancestor of the root commit: a
    # real, reliable failure case with no network or remote dependency.
    # This only holds with full history: CI's default (shallow, depth-1)
    # checkout collapses "the root commit" to HEAD itself, which trivially
    # IS its own ancestor, so skip there rather than assert something the
    # shallow clone cannot actually test.
    if _is_shallow_repository():
        pytest.skip("requires full git history (fetch-depth: 0); repo checkout is shallow")
    root_commit = _repo_root_commit()
    result = run(
        [
            "--expected-version",
            "1.0.0",
            "--git-tag",
            "v1.0.0",
            "--require-main-ancestor",
            root_commit,
            "--commit",
            "HEAD",
        ]
    )
    assert result.returncode == 1
    assert "not reachable from" in result.stderr


def test_multiple_failures_are_all_reported_together() -> None:
    result = run(["--expected-version", "9.9.9", "--git-tag", "not-a-tag"])
    assert result.returncode == 1
    error_lines = [line for line in result.stderr.splitlines() if line.startswith("  - ")]
    assert len(error_lines) >= 5
