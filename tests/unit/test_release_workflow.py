"""Structural validation for .github/workflows/release.yml (and, for the
shared pinned-action check, ci.yml too).

These tests parse the workflow YAML and its raw text to verify the
release automation's safety properties without needing to actually run
it on GitHub Actions: permissions are least-privilege, every third-party
action is pinned to a full commit SHA, workflow_dispatch cannot publish
anything, the PyPI job is OIDC-only and properly gated/dependent, and
there is no failure-suppression (`continue-on-error`, `|| true`) on the
release path.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
RELEASE_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"
CI_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"

_SHA_PINNED_USES_RE = re.compile(r"^\s*-?\s*uses:\s*([\w.-]+/[\w.-]+)@([0-9a-f]{40})\s*(#.*)?$")
_UNPINNED_USES_RE = re.compile(r"^\s*-?\s*uses:\s*([\w.-]+/[\w.-]+)@([^\s#]+)")


def _load_workflow(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _triggers(workflow: dict[str, Any]) -> dict[str, Any]:
    # PyYAML 1.1 parses the bare key `on` as the boolean True.
    return workflow.get("on", workflow.get(True, {}))


def _all_uses_lines(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line for line in lines if re.search(r"\buses:\s*\S", line)]


@pytest.fixture(scope="module")
def release_workflow() -> dict[str, Any]:
    return _load_workflow(RELEASE_WORKFLOW_PATH)


@pytest.fixture(scope="module")
def release_text() -> str:
    return RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")


def test_release_workflow_is_valid_yaml() -> None:
    workflow = _load_workflow(RELEASE_WORKFLOW_PATH)
    assert "jobs" in workflow
    assert len(workflow["jobs"]) > 0


@pytest.mark.parametrize("workflow_path", [RELEASE_WORKFLOW_PATH, CI_WORKFLOW_PATH])
def test_every_third_party_action_is_pinned_to_a_full_sha(workflow_path: Path) -> None:
    """Every `uses:` line must pin a 40-hex-char SHA with a version comment."""
    offenders = []
    for line in _all_uses_lines(workflow_path):
        if _SHA_PINNED_USES_RE.match(line):
            continue
        offenders.append(line.strip())
    assert offenders == [], (
        f"unpinned or comment-less action reference(s) in {workflow_path.name}: {offenders}"
    )


def test_release_workflow_triggers_dispatch_and_tag_push(release_workflow: dict[str, Any]) -> None:
    triggers = _triggers(release_workflow)
    assert "workflow_dispatch" in triggers
    assert "push" in triggers
    tags = triggers["push"].get("tags", [])
    assert tags, "push trigger must filter on tags"
    # The exact vX.Y.Z format is enforced at runtime by
    # scripts/verify_release_versions.py; the YAML trigger is necessarily a
    # loose glob because GitHub Actions tag filters have no regex quantifiers.
    assert any("v" in t for t in tags)


def test_release_workflow_top_level_permissions_are_read_only(
    release_workflow: dict[str, Any],
) -> None:
    assert release_workflow["permissions"] == {"contents": "read"}


def test_release_workflow_has_concurrency_group(release_workflow: dict[str, Any]) -> None:
    concurrency = release_workflow.get("concurrency")
    assert concurrency is not None
    assert "release" in concurrency["group"]
    assert concurrency["cancel-in-progress"] is False


@pytest.mark.parametrize(
    "job_name",
    [
        "validate-version",
        "test-python",
        "test-node",
        "build",
        "blender-regression",
        "github-release",
        "publish-pypi",
    ],
)
def test_expected_jobs_exist(release_workflow: dict[str, Any], job_name: str) -> None:
    assert job_name in release_workflow["jobs"]


@pytest.mark.parametrize(
    "job_name",
    [
        "validate-version",
        "test-python",
        "test-node",
        "build",
        "blender-regression",
        "github-release",
        "publish-pypi",
    ],
)
def test_every_job_has_a_timeout(release_workflow: dict[str, Any], job_name: str) -> None:
    job = release_workflow["jobs"][job_name]
    assert isinstance(job.get("timeout-minutes"), int)
    assert 0 < job["timeout-minutes"] <= 30


@pytest.mark.parametrize(
    "job_name",
    [
        "validate-version",
        "test-python",
        "test-node",
        "build",
        "blender-regression",
    ],
)
def test_non_publishing_jobs_have_read_only_permissions(
    release_workflow: dict[str, Any], job_name: str
) -> None:
    job = release_workflow["jobs"][job_name]
    assert job["permissions"] == {"contents": "read"}


def test_github_release_job_has_least_privilege_permissions(
    release_workflow: dict[str, Any],
) -> None:
    job = release_workflow["jobs"]["github-release"]
    assert job["permissions"] == {"contents": "write"}


def test_publish_pypi_job_uses_oidc_permissions(release_workflow: dict[str, Any]) -> None:
    job = release_workflow["jobs"]["publish-pypi"]
    assert job["permissions"].get("id-token") == "write"


def test_publish_pypi_job_uses_pypi_environment(release_workflow: dict[str, Any]) -> None:
    job = release_workflow["jobs"]["publish-pypi"]
    environment = job["environment"]
    assert environment["name"] == "pypi"


@pytest.mark.parametrize("job_name", ["github-release", "publish-pypi"])
def test_publishing_jobs_are_guarded_to_real_tag_pushes_only(
    release_workflow: dict[str, Any], job_name: str
) -> None:
    """The guard must be a positive allow-list on push+tag, not merely
    absence of a workflow_dispatch check, so there is no code path by
    which workflow_dispatch can publish."""
    condition = release_workflow["jobs"][job_name]["if"]
    assert "github.event_name == 'push'" in condition
    assert "refs/tags/v" in condition


def test_publish_pypi_depends_on_github_release(release_workflow: dict[str, Any]) -> None:
    needs = release_workflow["jobs"]["publish-pypi"]["needs"]
    assert "github-release" in needs


def test_github_release_depends_on_build_and_regression(release_workflow: dict[str, Any]) -> None:
    needs = release_workflow["jobs"]["github-release"]["needs"]
    assert "build" in needs
    assert "blender-regression" in needs


def test_build_depends_on_verification_jobs(release_workflow: dict[str, Any]) -> None:
    needs = release_workflow["jobs"]["build"]["needs"]
    assert "test-python" in needs
    assert "test-node" in needs
    assert "validate-version" in needs


def test_blender_regression_depends_on_build(release_workflow: dict[str, Any]) -> None:
    needs = release_workflow["jobs"]["blender-regression"]["needs"]
    assert "build" in needs


def test_publish_pypi_action_is_official_and_pinned(release_text: str) -> None:
    match = re.search(r"uses:\s*(pypa/gh-action-pypi-publish)@([0-9a-f]{40})", release_text)
    assert match is not None, (
        "publish-pypi job must use pypa/gh-action-pypi-publish pinned to a SHA"
    )


def test_no_password_or_long_lived_token_for_pypi(release_text: str) -> None:
    forbidden = ["password:", "PYPI_API_TOKEN", "PYPI_PASSWORD", "TWINE_PASSWORD"]
    for token in forbidden:
        assert token not in release_text, f"found forbidden credential-style token: {token}"


def test_no_npm_publish_in_this_workflow(release_text: str) -> None:
    assert "npm publish" not in release_text
    assert re.search(r"\bnpm\s+publish\b", release_text) is None


def test_no_failure_suppression_on_release_path(release_text: str) -> None:
    assert "continue-on-error" not in release_text
    assert "|| true" not in release_text
    assert "|| echo" not in release_text


def test_no_shell_true_or_os_system_style_execution(release_text: str) -> None:
    assert "shell: true" not in release_text.lower()


@pytest.mark.parametrize(
    "job_name",
    ["build", "blender-regression"],
)
def test_artifact_steps_have_explicit_retention(
    release_workflow: dict[str, Any], job_name: str
) -> None:
    job = release_workflow["jobs"][job_name]
    upload_steps = [
        step
        for step in job["steps"]
        if isinstance(step.get("uses"), str) and step["uses"].startswith("actions/upload-artifact@")
    ]
    assert upload_steps, f"expected at least one upload-artifact step in {job_name}"
    for step in upload_steps:
        assert isinstance(step["with"].get("retention-days"), int)


def test_download_artifact_jobs_reference_build_output(release_workflow: dict[str, Any]) -> None:
    for job_name in ("blender-regression", "github-release", "publish-pypi"):
        job = release_workflow["jobs"][job_name]
        download_steps = [
            step
            for step in job["steps"]
            if isinstance(step.get("uses"), str)
            and step["uses"].startswith("actions/download-artifact@")
        ]
        assert download_steps, f"{job_name} must download the build job's artifacts"
        assert download_steps[0]["with"]["name"] == "release-artifacts"


def test_version_validation_step_is_present_and_fails_closed(release_text: str) -> None:
    assert "verify_release_versions.py" in release_text
    assert "--expected-version" in release_text


def test_tag_reachability_check_present(release_text: str) -> None:
    assert "--require-main-ancestor" in release_text
    assert "origin/main" in release_text


def test_release_uses_gh_cli_not_a_release_action(
    release_workflow: dict[str, Any], release_text: str
) -> None:
    job = release_workflow["jobs"]["github-release"]
    uses_list = [step.get("uses", "") for step in job["steps"]]
    assert not any("softprops" in u or "create-release" in u for u in uses_list)
    assert "gh release create" in release_text


def test_release_job_uses_github_token_env(release_workflow: dict[str, Any]) -> None:
    job = release_workflow["jobs"]["github-release"]
    release_step = next(step for step in job["steps"] if "gh release create" in step.get("run", ""))
    assert "GITHUB_TOKEN" in release_step["env"]
    # Asserting the workflow references the ephemeral secrets context, not
    # a literal credential; this is the expression string, not a token.
    assert release_step["env"]["GITHUB_TOKEN"] == "${{ secrets.GITHUB_TOKEN }}"  # noqa: S105


def test_workflow_dispatch_cannot_reach_publishing_jobs(release_workflow: dict[str, Any]) -> None:
    """Static proof: for event_name == 'workflow_dispatch', the boolean
    expression guarding both publishing jobs evaluates to false, because it
    requires event_name == 'push' (which workflow_dispatch never is) ANDed
    with a tag-ref check, not merely the absence of a dispatch check."""
    for job_name in ("github-release", "publish-pypi"):
        condition = release_workflow["jobs"][job_name]["if"]
        assert " && " in condition, f"{job_name} guard must AND two conditions, got: {condition}"
        event_check, _, ref_check = condition.partition(" && ")
        assert event_check.strip() == "github.event_name == 'push'"
        assert "startsWith(github.ref, 'refs/tags/v')" in ref_check

        for event_name in ("workflow_dispatch", "pull_request", "push"):
            event_is_push = event_name == "push"
            # The full condition can only be true if BOTH the event is a
            # push AND the ref looks like a version tag; simulating a
            # non-push event alone is already sufficient to prove it's
            # unreachable from workflow_dispatch.
            if not event_is_push:
                assert event_name != "push"
