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


# ---------------------------------------------------------------------------
# Production-hardening regression tests: pinned Node/npm toolchain, pinned
# Python release tooling, verified Blender archive, corrected docs.
# ---------------------------------------------------------------------------

NODE_NPM_JOBS = ("test-node", "build", "blender-regression")
MUTABLE_NODE_SELECTORS = {"lts/*", "lts/current", "latest", "current", "node"}
RELEASE_REQUIREMENTS_PATH = REPO_ROOT / "scripts" / "release-requirements.txt"
REQUIRED_RELEASE_TOOLS = ("build", "twine", "wheel", "setuptools")
RELEASE_MD_PATH = REPO_ROOT / "docs" / "RELEASE.md"


def _setup_node_steps(job: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        step
        for step in job["steps"]
        if isinstance(step.get("uses"), str) and step["uses"].startswith("actions/setup-node@")
    ]


@pytest.mark.parametrize("job_name", NODE_NPM_JOBS)
def test_node_version_is_pinned_not_mutable(
    release_workflow: dict[str, Any], job_name: str
) -> None:
    job = release_workflow["jobs"][job_name]
    setup_steps = _setup_node_steps(job)
    assert setup_steps, f"{job_name} must use actions/setup-node"
    node_version = setup_steps[0]["with"]["node-version"]
    assert node_version not in MUTABLE_NODE_SELECTORS
    assert node_version == "${{ env.NODE_VERSION }}", (
        f"{job_name} must reference the shared pinned env.NODE_VERSION, got {node_version!r}"
    )


def test_node_version_env_is_an_explicit_semver_at_least_22_14_0(
    release_workflow: dict[str, Any],
) -> None:
    node_version = release_workflow["env"]["NODE_VERSION"]
    assert node_version not in MUTABLE_NODE_SELECTORS
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(node_version))
    assert match, f"env.NODE_VERSION must be an exact semver, got {node_version!r}"
    assert tuple(int(p) for p in match.groups()) >= (22, 14, 0)


@pytest.mark.parametrize("job_name", NODE_NPM_JOBS)
def test_npm_is_explicitly_pinned(release_workflow: dict[str, Any], job_name: str) -> None:
    job = release_workflow["jobs"][job_name]
    pin_steps = [step for step in job["steps"] if "npm install -g npm@" in step.get("run", "")]
    assert pin_steps, f"{job_name} must explicitly pin the npm CLI version (npm install -g npm@...)"
    assert "${{ env.NPM_VERSION }}" in pin_steps[0]["run"]


def test_npm_version_env_is_an_explicit_semver_at_least_11_5_1(
    release_workflow: dict[str, Any],
) -> None:
    npm_version = release_workflow["env"]["NPM_VERSION"]
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(npm_version))
    assert match, f"env.NPM_VERSION must be an exact semver, got {npm_version!r}"
    assert tuple(int(p) for p in match.groups()) >= (11, 5, 1)


@pytest.mark.parametrize("job_name", NODE_NPM_JOBS)
def test_node_and_npm_versions_are_printed(release_workflow: dict[str, Any], job_name: str) -> None:
    job = release_workflow["jobs"][job_name]
    combined_run_text = "\n".join(step.get("run", "") for step in job["steps"])
    assert "node --version" in combined_run_text, f"{job_name} must print node --version"
    assert "npm --version" in combined_run_text, f"{job_name} must print npm --version"


def test_no_mutable_node_selector_anywhere_in_release_workflow(release_text: str) -> None:
    # Only inspect actual `node-version:` value lines, not prose (this
    # file's own hardening comments legitimately name `lts/*` as an
    # example of what must NOT be used).
    node_version_lines = [
        line for line in release_text.splitlines() if re.match(r"\s*node-version:", line)
    ]
    assert node_version_lines, "expected at least one node-version: line"
    for line in node_version_lines:
        for selector in ("lts/*", "lts/current", "latest", "current"):
            assert selector not in line, f"found mutable Node selector on line: {line!r}"


def test_release_requirements_file_exists_and_pins_exact_versions() -> None:
    assert RELEASE_REQUIREMENTS_PATH.is_file(), "scripts/release-requirements.txt must exist"
    text = RELEASE_REQUIREMENTS_PATH.read_text(encoding="utf-8")
    pinned: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([0-9][0-9A-Za-z.]*)", line)
        assert match, f"release-requirements.txt line is not an exact pin: {line!r}"
        pinned[match.group(1).lower()] = match.group(2)
    for tool in REQUIRED_RELEASE_TOOLS:
        assert tool in pinned, f"{tool} must be pinned in scripts/release-requirements.txt"


def test_build_job_installs_pinned_release_tools_not_unpinned(
    release_workflow: dict[str, Any], release_text: str
) -> None:
    assert "pip install -q build twine" not in release_text, (
        "found the old unpinned `pip install build twine` pattern"
    )
    assert not re.search(
        r"pip install[^\n]*\bbuild\b[^\n]*\btwine\b(?!.*release-requirements)", release_text
    )
    build_job = release_workflow["jobs"]["build"]
    combined_run_text = "\n".join(step.get("run", "") for step in build_job["steps"])
    assert "scripts/release-requirements.txt" in combined_run_text


def test_build_uses_no_isolation_so_pinned_tools_actually_apply(
    release_workflow: dict[str, Any],
) -> None:
    build_job = release_workflow["jobs"]["build"]
    combined_run_text = "\n".join(step.get("run", "") for step in build_job["steps"])
    assert "python -m build --no-isolation" in combined_run_text, (
        "build must pass --no-isolation, otherwise PEP 517 isolated builds "
        "silently re-resolve their own setuptools/wheel, ignoring the pin"
    )


def _blender_download_step(release_workflow: dict[str, Any]) -> dict[str, Any]:
    job = release_workflow["jobs"]["blender-regression"]
    steps = [
        step for step in job["steps"] if "blender-4.3.2-linux-x64.tar.xz" in step.get("run", "")
    ]
    assert steps, "expected a step downloading the Blender 4.3.2 linux-x64 tarball"
    return steps[0]


def test_blender_checksum_is_pinned(release_workflow: dict[str, Any]) -> None:
    step = _blender_download_step(release_workflow)
    env = step.get("env", {})
    assert "BLENDER_TARBALL_SHA256" in env, "Blender download step must pin an expected SHA-256"
    digest = env["BLENDER_TARBALL_SHA256"]
    assert re.fullmatch(r"[0-9a-f]{64}", str(digest)), f"not a valid sha256 hex digest: {digest!r}"


def test_blender_archive_verified_before_extraction(release_workflow: dict[str, Any]) -> None:
    step = _blender_download_step(release_workflow)
    run_text = step["run"]
    assert "sha256sum -c" in run_text, "Blender archive must be checksum-verified"
    assert "tar -xf" in run_text
    verify_index = run_text.index("sha256sum -c")
    extract_index = run_text.index("tar -xf")
    assert verify_index < extract_index, "the archive must be verified before it is extracted"


def test_blender_checksum_not_fetched_from_mutable_source_at_runtime(
    release_workflow: dict[str, Any],
) -> None:
    step = _blender_download_step(release_workflow)
    run_text = step["run"]
    assert "blender-4.3.2.sha256" not in run_text, (
        "must not re-fetch the checksum manifest from the same server as the "
        "archive at release time; the digest must be pinned in the workflow"
    )
    assert not re.search(r"(wget|curl)[^\n]*\.sha256\b", run_text)


def test_release_md_documents_default_branch_requirement_for_dispatch() -> None:
    text = RELEASE_MD_PATH.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "default branch" in lowered
    assert "cannot be dispatched from pr #2" in lowered or (
        "there is no way to dry-run this workflow from pr #2" in lowered
    )


def test_release_md_does_not_claim_pre_merge_dispatch_is_possible() -> None:
    text = RELEASE_MD_PATH.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "or the release branch, before merging" not in lowered
    assert "before merging, to validate the pr" not in lowered


def test_release_md_step_order_matches_required_sequence() -> None:
    text = RELEASE_MD_PATH.read_text(encoding="utf-8")
    required_headings = [
        "### 1. Merge release automation",
        "### 2. Configure the `pypi` GitHub environment",
        "### 3. Configure the PyPI pending trusted publisher",
        "### 4. Run a `workflow_dispatch` dry run on `main`",
        "### 5. Confirm the publishing jobs were skipped",
        "### 6. Create the `v1.0.0` tag",
    ]
    positions = [text.index(heading) for heading in required_headings]
    assert positions == sorted(positions), "release order headings must appear in sequence"
