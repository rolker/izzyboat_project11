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
- [ ] (suggestion) Cleanup trap is EXIT-only; extend to `EXIT INT TERM` so a signal mid-copy doesn't orphan the staging temp — `scripts/deploy_datum_polygons.sh:101`
- [ ] (suggestion) Add regression tests for DEST-as-directory / symlink-DEST / unwritable DEST_DIR / empty source — `scripts/test_deploy_datum_polygons.sh`

Static analysis: shellcheck clean; test suite 26/26 pass; yamllint unavailable (ci.yml reviewed manually, valid). Local Adversarial skipped (Ollama unreachable); Copilot off (default). CI two-command `run: |` block verified safe (GH Actions default `bash -eo pipefail`).
