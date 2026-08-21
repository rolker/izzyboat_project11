---
issue: 445
---

# Issue #445 — Materialize datum user polygons into ~/data/world/datum/user/

Work item 5 of [unh_marine_autonomy#288](https://github.com/rolker/unh_marine_autonomy/issues/288).
The settled design lives in that repo's `.agent/work-plans/issue-288/plan.md`
(item 5) and the ADR-0010 D3 amendment (2026-08-20); this issue implements the
boat-host deploy step only.

## Implementation
**Status**: complete
**When**: 2026-08-20 21:30 -04:00
**By**: Claude Code Agent (Claude Opus)
**Branch**: feature/issue-445
**Commit**: `fc35c4a`

### What was built
A boat-host deploy step that copies the git-reviewed
`bizzyboat_project11/config/massabesic_datum_polygons.yaml` into
`~/data/world/datum/user/` — the discovery surface for the
`marine_vertical_datum` precedence chain (ADR-0010 D3 amendment).

- **`scripts/deploy_datum_polygons.sh`** — the deploy step.
  - Follows the existing repo idiom (`scripts/build_bathy_store.sh`, the other
    "materialize into `~/data/world/…`" host tool): repo-root `scripts/`,
    `set -euo pipefail`, `err/die` + `usage()`-via-sed, env-overridable
    `SRC`/`DEST_DIR`, `--dry-run`. No new mechanism invented.
  - **Idempotent**: creates `~/data/world/datum/user/` if absent; no-op ("up to
    date") when the copy already matches git; installs **atomically**
    (stage-then-rename) so a discovering consumer never reads a half-written
    file.
  - **Git stays source of truth** (ADR-0010 D1 exception): source is the
    in-tree checkout (resolved `SCRIPT_DIR`-relative, no ROS dependency), and
    the script **overwrites in-place edits back to git** on every deploy,
    enforcing "never hand-edited in place". Destination keeps the git basename
    (the ADR's exact `massabesic_datum_polygons.yaml` example).
  - **Loud failure** if the source file is missing (no silent skip).
- **`scripts/test_deploy_datum_polygons.sh`** — 26-check self-contained
  regression suite (no ROS runtime; `SRC`/`DEST_DIR` redirected to a temp
  tree). Covers dry-run (install/update variants) changing nothing, real
  install, git-content match, idempotent re-run, in-place-edit correction (D1
  invariant), basename preservation, atomic temp-file cleanup, missing-source
  failure, arg validation, `--help`, and that the default `SRC` resolves to the
  real in-tree config.
- **`.github/workflows/ci.yml`** — added the new test to the "Test scripts"
  step (alongside `test_build_bathy_store.sh`).
- **`docs/datum_polygon_deploy.md`** + README link — documents the mechanism,
  the **ADR-0010 D1 regenerable-from-git exception**, and the **explicit CAMP
  (operator-station) provisioning deferral** (boat host only; D6 CAMP consumer
  out of scope).

### Design decisions verified against source
- Consumer convention: `chart_datum_node` reads an explicit `datum_config_path`
  (default `""`, no directory scan) — confirmed in
  `mru_transform/nodes/chart_datum_node.cpp:105-153` and
  `bizzyboat_project11/launch/core_launch.py:123-126`. So `world/datum/user/`
  is a discovery surface, not the runtime read path, and preserving the git
  basename is correct.
- Destination + git-exception wording cross-checked against the ADR-0010 D3
  amendment (`unh_marine_autonomy/docs/decisions/0010-geospatial-world-model.md`,
  lines ~183-207) and `marine_vertical_datum/README.md` (`~/data/world/datum/…`
  canonical location).

### Verification evidence
- `shellcheck scripts/deploy_datum_polygons.sh scripts/test_deploy_datum_polygons.sh`
  → clean.
- `bash scripts/test_deploy_datum_polygons.sh` → **26 passed, 0 failed**.
- Manual smoke test: dry-run creates nothing; real deploy creates the dir and
  matches git; re-run is a no-op; a tampered copy is restored to git content;
  missing source exits non-zero with a loud message; no leftover temp files.
- `pre-commit run` over the changed files → all hooks Passed; committed with
  hooks active (no `--no-verify`).

### Not in scope (deferred / other items)
- Operator-station (CAMP) datum provisioning — explicitly deferred (documented).
- `datum/geoid/` + `datum/vdatum/` grid provisioning — separate queued
  `s57_tools` follow-on (#288 items 2/6), not this deploy step.
- No push, no GitHub interaction (host performs pushes).

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-08-21 00:00 +00:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: changes-requested

**Branch**: feature/issue-445 at `2cf7ad9`
**Mode**: pre-push
**Depth**: Deep (reason: 364 lines ≥200; ci.yml CI override-trigger)
**Must-fix**: 1 | **Suggestions**: 2
**Round**: 1 | **Ship**: continue — one must-fix (silent failed-deploy when DEST pre-exists as a directory); mechanical one-line guard, re-review after fix

### Findings
- [x] (must-fix) DEST pre-existing as a directory -> `mv` orphans temp inside it, prints "deployed", exits 0 (silent failed deploy); add regular-file type guard on `$DEST` (also closes symlink-on-DEST) — `scripts/deploy_datum_polygons.sh:81,104`
- [x] (suggestion) Cleanup trap is EXIT-only; extend to `EXIT INT TERM` so a signal mid-copy doesn't orphan the staging temp — `scripts/deploy_datum_polygons.sh:101`
- [x] (suggestion) Add regression tests for DEST-as-directory / symlink-DEST / unwritable DEST_DIR / empty source — `scripts/test_deploy_datum_polygons.sh`

Static analysis: shellcheck clean; test suite 26/26 pass; yamllint unavailable (ci.yml reviewed manually, valid). Local Adversarial skipped (Ollama unreachable); Copilot off (default). CI two-command `run: |` block verified safe (GH Actions default `bash -eo pipefail`).

## Implementation
**Status**: complete
**When**: 2026-08-21 00:06 +00:00
**By**: Claude Code Agent (Claude Opus)

**Branch**: feature/issue-445 at `48921b0`
**Addressed**: Local Review (Pre-Push) — 2026-08-21 00:00 +00:00, branch `feature/issue-445` at `2cf7ad9`
**Commits**: `11f9ea9`, `7a40b7b`, `48921b0`

Addressed all three open findings from the pre-push review (1 must-fix, 2
suggestions). shellcheck clean on both scripts; regression suite grew 26 → 38
checks, all passing. No push (host performs pushes).

### Actions
- [x] (must-fix) DEST-as-directory/symlink silently misfires the atomic `mv` — added a `[[ -L "$DEST" || ( -e "$DEST" && ! -f "$DEST" ) ]]` guard that dies loudly ("not a regular file") before the idempotent check, so a directory/symlink at DEST is refused instead of reported as a phantom "deployed". — `scripts/deploy_datum_polygons.sh:80` (commit `11f9ea9`)
- [x] (suggestion) Cleanup trap EXIT-only — added `trap 'exit 130' INT` / `trap 'exit 143' TERM` alongside the existing EXIT cleanup (and cleared all three after the successful `mv`). A signal mid-copy now becomes an ordinary exit that fires the EXIT trap, so the staging temp is never orphaned. — `scripts/deploy_datum_polygons.sh:101` (commit `7a40b7b`)
- [x] (suggestion) Missing edge-case regression tests — added four cases (DEST-as-directory, symlink-DEST, unwritable DEST_DIR [skipped as root], empty source), +12 checks. The empty-source case is a genuine failure because I also added a `[[ -s "$SRC" ]]` non-empty-source guard (consistent with the script's existing loud-failure-on-bad-source philosophy; a zero-byte safety-relevant datum config is refused rather than silently deployed). — `scripts/test_deploy_datum_polygons.sh`, `scripts/deploy_datum_polygons.sh:78` (commit `48921b0`)

### Next step
Re-review the fixes (Implementation → review-code). Dispatch a fresh-context
sub-agent: `.agent/scripts/dispatch_subagent.sh --mode in-process --issue 445 --skill review-code`.

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-08-21 00:11 +00:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: approved

**Branch**: feature/issue-445 at `4efb70e`
**Mode**: pre-push
**Depth**: Deep (reason: >200 lines; ci.yml CI override-trigger)
**Must-fix**: 0 | **Suggestions**: 0
**Round**: 2 | **Ship**: recommended — Round-1 must-fix + both suggestions addressed and independently re-verified; static clean, 38/38 tests, both Deep adversarial lenses clean

### Findings
- [ ] No issues found. LGTM.

Round-2 re-review after the Round-1 changes-requested entry. Verified: DEST non-regular-file guard closes the silent failed-deploy (must-fix); trap extended to EXIT INT TERM; empty-source `[[ -s ]]` guard added; regression suite 26 -> 38 checks, all pass. shellcheck clean; yamllint unavailable (ci.yml reviewed manually, valid). Two fresh-context Claude Adversarial passes (Lens A logic + Lens B systemic) both clean; the mktemp->trap window Lens B raised was dropped as non-actionable (unhittable two-statement window; harmless ignored dotfile; matches the repo's own build_bathy_store.sh idiom). Local Adversarial skipped (Ollama unreachable); Copilot off (default).

## Implementation
**Status**: complete
**When**: 2026-08-21 00:18 +00:00
**By**: Claude Code Agent (Claude Opus)

**PR**: #448 at `1690c61`
**Addressed**: host-validated Copilot comment on PR #448 (drift dry-run test case captured output but never asserted exit 0)
**Commits**: `1690c61`

Single trivial finding from the PR review. The drift dry-run block ("in-place
edit is corrected back to git") captured `out` but, unlike every other dry-run
block in the file (lines 49-50, 69-70), never captured `rc` or asserted the
script exited 0. Added `; rc=$?` to the invocation and a `check "exits 0"`
assertion ahead of the "would update" content check, matching the file's
existing idiom (exit-code assertion first, then output-content assertion).

### Actions
- [x] Drift dry-run test asserts exit 0 — `scripts/test_deploy_datum_polygons.sh:75` (commit `1690c61`)

### Verification
- `shellcheck scripts/test_deploy_datum_polygons.sh` → clean.
- `bash scripts/test_deploy_datum_polygons.sh` → **39 passed, 0 failed** (was 38; +1 new assertion).
- Committed with pre-commit hooks active (no `--no-verify`). No push (host performs pushes).

### Next step
Re-review the fix (Implementation → review-code). Dispatch a fresh-context
sub-agent: `.agent/scripts/dispatch_subagent.sh --mode in-process --issue 445 --skill review-code`.
