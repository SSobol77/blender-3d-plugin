# Release Process

This document describes how `blender-3d-plugin` is released, what
`.github/workflows/release.yml` automates, and what still requires a
manual, deliberate action from a maintainer. **Published versions are
immutable**: once a version is on PyPI or npm, or a GitHub Release has
assets attached, that exact version is never modified or re-uploaded —
only new versions or explicit yank/deprecate actions (see below) change
its visibility.

## What the workflow does and does not do

`.github/workflows/release.yml` has two triggers:

- **`workflow_dispatch`** — builds every artifact and runs every
  verification step (tests, lint, type checks, the Blender headless
  regression, the installer end-to-end lifecycle) but **never** creates a
  GitHub Release and **never** publishes to PyPI. Use this to dry-run the
  entire pipeline against any branch before cutting a tag.
- **A pushed tag matching `v<major>.<minor>.<patch>`** — runs the same
  build and verification, and if (and only if) every prior job succeeds,
  also creates the GitHub Release and publishes the Python package to
  PyPI via Trusted Publishing.

The `github-release` and `publish-pypi` jobs are gated by
`if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')`
— an explicit allow-list condition, not a workflow_dispatch exclusion, so
there is no code path by which a manual dispatch can publish anything.

npm publishing is **not** part of this workflow. The first publication of
`@glaeron/blender-mobile-3d` must be done manually with 2FA (npm requires
this for the first publish of a new package, and Trusted Publishing can
only be configured for a package that already exists). See step 7 below
and [Configuring npm Trusted Publishing](#configuring-npm-trusted-publishing-after-the-first-manual-publish).

## Release order

Follow these steps **in order**. Do not skip ahead — later steps assume
earlier ones are verified.

### 1. Merge release automation

Merge the PR that adds `.github/workflows/release.yml`,
`scripts/verify_release_versions.py`, and this document into `main`.
Confirm the regular CI workflow (`.github/workflows/ci.yml`) is green on
`main` after the merge.

### 2. Configure the PyPI pending trusted publisher

Before any tag is pushed, register a **pending** trusted publisher on
PyPI so the very first publish can use OIDC (no API token ever touches
this repository):

1. Sign in to <https://pypi.org> as the account that will own the
   `blender-mobile-3d` project.
2. Go to **Your account → Publishing** (or, for an existing project,
   the project's **Settings → Publishing**) and add a new pending
   publisher:
   - **PyPI Project Name:** `blender-mobile-3d`
   - **Owner:** `SSobol77`
   - **Repository name:** `blender-3d-plugin`
   - **Workflow name:** `release.yml`
   - **Environment name:** `pypi`
3. Save it. PyPI will create the project automatically the first time a
   matching workflow run publishes to it — no manual `twine upload` and
   no long-lived API token are ever needed.
4. In the GitHub repository, create an **environment** named `pypi`
   (**Settings → Environments → New environment**). Optionally add
   required reviewers here for extra protection before the `publish-pypi`
   job can run; the workflow already restricts this environment to
   `id-token: write` and nothing else.

### 3. Run a `workflow_dispatch` dry run

From the **Actions** tab, run **Release** via **Run workflow** against
`main` (or the release branch, before merging, to validate the PR
itself). Confirm:

- version cross-file agreement check passes;
- all tests, lint, type checks, and coverage gate pass;
- the Blender headless regression and both installer E2E lifecycles pass;
- artifacts (Blender ZIP, checksum, release manifest, wheel, sdist, npm
  tarball) are attached to the run;
- **no** GitHub Release or PyPI publish job ran (both should show as
  skipped, since `github.event_name` was `workflow_dispatch`).

Do not proceed to tagging until this run is fully green.

### 4. Create the `v1.0.0` tag

Tag the exact commit on `main` you intend to release, using an
**annotated and signed** tag:

```bash
git checkout main
git pull
git tag -s v1.0.0 -m "Blender Mobile 3D Plugin v1.0.0"
git push origin v1.0.0
```

(`-s` requires a configured GPG/SSH signing key; use `-a` instead of `-s`
if signing is not yet configured, but signed tags are strongly
preferred for a v1.0.0 release.)

Pushing the tag triggers `release.yml` in its full, publishing mode.

### 5. Verify the GitHub Release

Watch the workflow run to completion. Confirm the release at
`https://github.com/SSobol77/blender-3d-plugin/releases/tag/v1.0.0` has:

- generated release notes;
- the Blender add-on ZIP and its `.sha256` checksum file;
- `release-manifest.json`;
- the Python wheel and sdist;
- the npm `.tgz`.

Verify the checksum locally:

```bash
curl -sSLO https://github.com/SSobol77/blender-3d-plugin/releases/download/v1.0.0/blender_mobile_3d-1.0.0.zip
curl -sSLO https://github.com/SSobol77/blender-3d-plugin/releases/download/v1.0.0/blender_mobile_3d-1.0.0.zip.sha256
sha256sum -c blender_mobile_3d-1.0.0.zip.sha256
```

### 6. Verify PyPI installation

```bash
python -m venv /tmp/verify-pypi
/tmp/verify-pypi/bin/pip install blender-mobile-3d==1.0.0
/tmp/verify-pypi/bin/blender-mobile-3d version
```

Confirm the installed version prints `1.0.0` and `doctor --json` /
`list-blenders --json` run without error.

### 7. Manually publish the first npm package (with 2FA)

This is the one release step the automation deliberately does **not**
perform, because npm requires interactive 2FA for the first publish of a
new package and because Trusted Publishing cannot be configured until the
package exists.

```bash
cd installers/npm
npm ci
npm run lint && npm test
npm pack --dry-run   # sanity check contents one more time
npm publish --access public
```

You will be prompted for your npm 2FA one-time code. Verify afterward:

```bash
npm view @glaeron/blender-mobile-3d version   # expect 1.0.0
```

### 8. Configure npm Trusted Publishing for future versions

Once the package exists, configure OIDC-based publishing so future
versions (`v1.0.1`, `v1.1.0`, ...) can be published from CI without a
long-lived npm token:

1. On <https://www.npmjs.com>, go to the `@glaeron/blender-mobile-3d`
   package → **Settings → Trusted Publishers**.
2. Add a GitHub Actions trusted publisher:
   - **Organization or user:** `SSobol77`
   - **Repository:** `blender-3d-plugin`
   - **Workflow filename:** `release.yml`
   - **Environment name:** (optional) `npm`, if you add one.
3. **Requirements:** npm Trusted Publishing requires **npm >= 11.5.1**
   and **Node.js >= 22.14.0** in the publishing job. When this is added
   to `release.yml` in a future PR, pin `actions/setup-node` to a
   matching Node version and add `id-token: write` to that job's
   permissions (mirroring the `publish-pypi` job's OIDC setup).
4. Add the actual `npm publish` step to `release.yml` only after this is
   configured; until then, npm publishing stays manual.

### 9. Verify clean installations from PyPI and npm

As a final sanity check, from machines/containers with no prior
project-specific state:

```bash
pipx install blender-mobile-3d
blender-mobile-3d doctor --json

npx @glaeron/blender-mobile-3d doctor --json
```

Both should run cleanly and agree on `version: "1.0.0"`.

## Rollback, yank, and deprecation

Published versions are immutable — none of the procedures below modify
an already-published artifact. They only change whether it is
recommended, installable by default, or listed.

### GitHub Release

- **Wrong assets attached:** delete the GitHub Release (`gh release
  delete v1.0.0`) and the tag (`git push --delete origin v1.0.0`, `git tag
  -d v1.0.0` locally), fix the issue, and re-tag. Only do this if the
  release has not yet been picked up downstream (check PyPI/npm first —
  those cannot be un-published the same way).
- **Release is fine but superseded:** mark it as a pre-release or add a
  note in the release body pointing at the newer version; do not delete a
  release once its artifacts have been consumed by PyPI/npm publishing.

### PyPI

PyPI does not allow re-uploading a version, and deleting a version is
strongly discouraged (it breaks reproducible installs for anyone pinned
to it). To roll back a bad release:

1. **Yank** the version instead of deleting it:
   ```bash
   pip install pypi-cli-or-use-web-ui
   # Web UI: project page -> Manage -> Releases -> select version -> "Yank release"
   ```
   A yanked release is still installable by an exact pin
   (`pip install blender-mobile-3d==1.0.0`) but is excluded from
   dependency resolution for new installs (`pip install blender-mobile-3d`
   will skip it). Provide a reason when yanking.
2. Publish a corrected version (`1.0.1`) through the normal tag flow.
3. Only use PyPI's "delete" (as opposed to yank) for legal/security
   emergencies (e.g. leaked secrets in the package); deletion also frees
   the version number for reuse, which is otherwise strongly discouraged.

### npm

```bash
npm deprecate @glaeron/blender-mobile-3d@1.0.0 "Reason: <describe the issue>; use 1.0.1 instead"
```

`npm unpublish` is restricted (npm blocks unpublishing versions more than
72 hours old, and org-scoped packages have additional restrictions) and
should not be relied upon; prefer `deprecate` plus a prompt corrected
release, same as the PyPI yank procedure.

### General principle

For any published-version problem, the default response is **release a
new, fixed version**, not modify or delete the old one. Yank/deprecate
communicates "don't use this" without breaking anyone already depending
on the exact pinned version.
