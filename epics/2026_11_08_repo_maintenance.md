# Plan: Repo maintenance

Component: `.github/` (PR template, CODEOWNERS, workflows), Python lint config (`ruff.toml`, `tools/requirements.txt`, `tools/`, `models/`), `README.md`.

PR strategy: merge each

---

## Overview

The repository has no PR template, nobody is requested to review automatically, and the CI workflows only run when certain paths change. A check that does not run never reports a status, so it can't be made required in a GitHub ruleset (a PR that skips it would wait forever). This epic makes the repository ready to be protected by rules:

1. **PR template and reviewers:** a `.github/pull_request_template.md` that follows the [safenet template](https://github.com/safe-research/safenet/blob/main/.github/pull_request_template.md) without the CLA section, and a `.github/CODEOWNERS` that requests a review from every collaborator.
2. **Always-running checks:** both workflows lose their path filters and get short names (`CI - Models`, `CI - Webapp`), so a ruleset can require them.
3. **Hardened workflows:** actions locked with a workflow lockfile, least-privilege tokens, no persisted git credentials, and a job that verifies the lockfile and checks the workflows with zizmor.
4. **Python lint:** a ruff configuration and a one-time mechanical cleanup of the Python code (imports, formatting).
5. **Python lint in CI:** ruff runs in CI, so the code stays clean.

Phases 2 and 5 (template, ruff cleanup) don't depend on anything and can run in parallel with phase 3 (always-running checks). Phase 4 depends on phase 3, phase 6 on phases 4 and 5.

---

## Architecture Decision

- **Reviewers come from CODEOWNERS, not from the template.** A PR template is only text: it can't request reviewers. GitHub requests a review from the code owners of the changed files when a PR is opened (for PRs targeting a branch that has the file). This is a personal repository, so there are no teams; CODEOWNERS lists every collaborator with write access (`@rmeissner @rimeissner-ai @rimeissner-qa`) for `*`. GitHub never asks a PR's author to review it, so the author is skipped. A new collaborator has to be added to the file by hand.
- **Two workflows, always running.** `models.yml` (`CI - Models`) and `webapp.yml` (`CI - Webapp`) run on every `pull_request` and on `push` to `main`, without `paths` filters. Each has one job, named like its workflow; the job names are the checks the ruleset requires. Phase 4 adds a third workflow, `workflows.yml` (`CI - Workflows`), for the lockfile check and zizmor. A new or renamed job has to be added to the ruleset by hand (the reviewer prefers this over one workflow with a summary job).
- **Hardening:**
  - Actions are locked in a [workflow lockfile](https://docs.github.com/actions/concepts/security/workflow-dependency-lockfiles) (`.github/workflows/actions.lock`, generated with the `gh actions-lock` extension). Workflows reference exact tags (`actions/checkout@v5.1.0`); the lockfile holds the commits, including transitive ones. `gh actions-lock --verify` fails when the lockfile is stale, and the owner enables the "Require lockfile" Actions policy.
  - `permissions: {}` at the top of the workflow, `contents: read` per job.
  - `actions/checkout` with `persist-credentials: false`.
  - `zizmor` (pinned version) checks for security problems (template injection, excessive permissions, …) in the `CI - Workflows` job. actionlint was dropped in review: its extra value is mostly syntax checks, and a broken workflow already fails its own run.
- **Ruff for Python.** `ruff.toml` at the repository root, target Python 3.13, rules `E, F, W, I, B, UP, RUF` with `E501` ignored (the formatter handles line length). `ruff` is pinned in `tools/requirements.txt` next to pytest. CI runs `ruff check` and `ruff format --check` in the `CI - Models` job, so no second Python setup is needed.

### Alternatives Considered

- **Keep path filters and skip jobs with a "changes" job (e.g. `dorny/paths-filter`):** saves a minute or two of CI on unrelated PRs, but adds a third-party action and logic that can skip a check by mistake. Both jobs take about a minute, so always running them is simpler.
- **One `CI` workflow with a `CI result` job that sums up all jobs:** the ruleset would only name one check, but the reviewer finds two workflows cleaner. Rejected in review of phase 3.
- **Request reviewers with an action or the PR tooling:** needs a token and runs after the PR is opened; CODEOWNERS is built in.
- **SHA pins in the workflow files:** replaced by the lockfile in review of phase 4 (also locks transitive actions, and Dependabot updates it).
- **Dependabot for actions and dependencies:** not part of this epic (see Open Questions).
- **Run ruff in its own job:** a separate Python setup for a check that takes a second; the `models` job already has Python and the requirements installed.

---

## Tech Specs

### `.github/pull_request_template.md`

The safenet template without the trailing `---` and `## CLA signature` section: a one or two line summary, then `### Context and Motivation`, `### Decisions and Tradeoffs`, `### Testing`, each with the safenet guidance comment, and the author checklist as an HTML comment at the end.

### `.github/CODEOWNERS`

```
# Every collaborator reviews every change. GitHub skips the PR's author.
* @rmeissner @rimeissner-ai @rimeissner-qa
```

### Workflows

`models.yml` and `webapp.yml` keep their steps, `permissions` and `concurrency`; only the triggers and names change:

```yaml
name: CI - Models

on:
  pull_request:
  push:
    branches: [main]
```

with the job's `name: CI - Models` (and the same for `CI - Webapp`). `workflows.yml` (phase 4) follows the same pattern.

### Ruff

```toml
# ruff.toml
target-version = "py313"

[lint]
select = ["E", "F", "W", "I", "B", "UP", "RUF"]
ignore = ["E501"]
```

Today's code has 6 auto-fixable findings (unsorted imports, unused `noqa`), one `B905` (`zip()` without `strict=`) and 7 files the formatter changes (~70 lines). The committed STLs must stay byte-identical (the existing `test_committed_stl_is_up_to_date` tests cover this).

### `README.md`

- A short **Contributing** section: PRs use the template, CODEOWNERS requests reviewers, the `CI - …` checks must pass.
- The **Generating models** section mentions `ruff check` and `ruff format` (phase 6).

### Repository settings (done by the owner, not in a PR)

After phase 3 is merged, a ruleset on `main` should:

- require a pull request (optionally with 1 approval and code owner review),
- require the status checks `CI - Models` and `CI - Webapp` (and `CI - Workflows` after phase 4),
- block force pushes and deletion.

---

## Implementation Phases

### Phase 1 — Plan

This file. No code.

### Phase 2 — PR template and CODEOWNERS

**Depends on:** 1 (merged plan). **Parallel:** yes, with phases 3 and 5.

- `.github/pull_request_template.md`, `.github/CODEOWNERS`.
- `README.md`: Contributing section (template and reviewers; the sentence about the checks is added in phase 3).

~50 lines, 3 files.

### Phase 3 — Always-running checks

**Depends on:** 1. **Parallel:** yes, with phases 2 and 5.

- `models.yml`, `webapp.yml`: drop the `paths` filters, rename the workflows and jobs to `CI - Models` and `CI - Webapp`.
- `README.md`: say that these checks must pass.

Both checks run on the PR itself, although it changes no code.

~30 lines, 4 files.

### Phase 4 — Harden the workflows

**Depends on:** 3. **Parallel:** yes, with phase 5.

- `models.yml`, `webapp.yml`: exact action tags, `permissions: {}` at the top and `contents: read` per job, `persist-credentials: false` on checkout.
- Add `.github/workflows/actions.lock` (generated with `gh actions-lock`).
- Add `workflows.yml` (`CI - Workflows`: `gh actions-lock --verify` and zizmor, pinned versions, hardened the same way).
- `README.md`: add `CI - Workflows` to the checks that must pass.
- Fix whatever zizmor reports.

~70 lines, 4 files.

### Phase 5 — Ruff config and cleanup

**Depends on:** 1. **Parallel:** yes, with phases 2, 3 and 4.

- Add `ruff.toml`, pin `ruff` in `tools/requirements.txt`.
- Run `ruff check --fix` and `ruff format` on `tools/` and `models/`; fix `B905` by hand (`strict=True` where the lengths must match).
- No behavior change: pytest passes and the committed STLs are unchanged.

~100 lines (mostly formatting), ~9 files.

### Phase 6 — Ruff in CI

**Depends on:** 4, 5. **Parallel:** no.

- `models.yml`: `ruff check` and `ruff format --check` steps in the `CI - Models` job.
- `README.md`: mention ruff in Generating models.

~15 lines, 2 files.

### Phase 7 — Remove the plan

**Depends on:** 2, 6. **Parallel:** no.

- Delete `epics/2026_11_08_repo_maintenance.md` after checking every phase is merged.

---

## Open Questions and Assumptions

- **"Request all contributors":** GitHub can't request "everyone with access" on its own and a personal repository has no teams, so CODEOWNERS lists today's three collaborators. If the repository moves to an organization, a team replaces the list.
- **Ruleset:** setting it up needs admin rights, so the owner does it on GitHub after phase 3 (see Repository settings). Until then, nothing changes for merging.
- **Dependabot:** not included. Without it, locked actions and ruff only change when someone bumps them by hand. A later PR can add `.github/dependabot.yml` (GitHub Actions, npm, pip).
- **Conflicts with open PRs:** phase 5 reformats Python files that open phases of other epics change (e.g. the 24-point star epic). Whichever PR merges second has to rebase; for a formatting-only conflict, re-running `ruff format` after the rebase resolves it. If the other epics are close to done, phase 5 can wait for them.
- **No merge queue:** the workflows don't listen to `merge_group`. If a merge queue is enabled later, add that trigger.
