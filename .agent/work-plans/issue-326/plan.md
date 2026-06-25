# Plan: Update bizzyboat_power.md with empirical speed→power/endurance/range characterization

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/326

## Context

`bizzyboat_power.md` currently states in **Drive efficiently**: *"Survey speed is already near
range-optimal (~3–3.5 kt)"*. Pooled data from three Massabesic lake surveys (2026-06-22/23/24,
~14 h of steady straight-line running, validated by the 06-23 full-discharge coulomb-count: 273.9 Ah
quad-model vs 273 Ah nameplate) shows the range plateau is actually **~2.0–2.9 kt (~27–28 nm on a
full pack)**. 3.5 kt — the historical cruise — is past the plateau, costing ~25 % range vs the
plateau.

The stale text also exists verbatim in `docs/analysis/2026-06-23/README.md` (line 14: *"Range-optimal
speed ~3–3.5 kt (today was already there)"*).

Analysis artifacts for 2026-06-24 are local at `~/data/logs/analysis/2026-06-24/`
(`2026-06-24_deployment.db`, `coulomb.py`, `speed_bins.py`, `speed_curve.py`,
`speed_endurance_range_curve.png`). No `docs/analysis/2026-06-24/` directory exists yet in the repo.
The 2026-06-23 directory pattern (`docs/analysis/2026-06-23/README.md` + committed plots) is the
template to follow.

## Approach

1. **Fix stale claim in `docs/analysis/2026-06-23/README.md`** — update line 14 to correct the
   "~3–3.5 kt range-optimal" text (this is the lowest-risk fix; do it first to avoid reader
   contradiction when the power doc is updated in the same PR).

2. **Create `docs/analysis/2026-06-24/` directory** — add `README.md` (regeneration notes: bag
   path, script names, method summary, caveats) and commit the `speed_endurance_range_curve.png`
   plot from `~/data/logs/analysis/2026-06-24/`. Match the 2026-06-23 pattern.

3. **Add "Speed → power, endurance, range (empirical)" subsection to `bizzyboat_power.md`** —
   insert between the *Validated full-discharge* section and the *Power model* section. Include:
   - The empirical table with **both nm and statute-mile** range columns (unit consistency with the
     rest of the doc which uses nm for distances), endurance, draw, mi/kWh columns.
   - Link to `docs/analysis/2026-06-24/speed_endurance_range_curve.png` (3-panel plot).
   - Decision framing: range-constrained → ~2.9 kt; endurance/loiter → 2.0 kt (~13.5 h, >2× the
     3.5 kt endurance); time-constrained → 3.5 kt (costs ~20 % range vs plateau, only worth it
     with margin).
   - Method summary: coulomb-quad pipeline, pooled 3-survey window, dock-departure/return GPS
     window used (boat dock-tied at lake, no tide interference); 06-23 full-discharge validates the
     model (273.9 Ah predicted vs 273 Ah actual pack).
   - Caveat paragraph: no current sensor (`BATT_MONITOR 3`); current/power modeled (quadratic PWM,
     ±~30 %); relative speed trade-offs are robust; absolute amps/watts carry the uncertainty band.
   - Cross-references: partially fills #88 (operational 2–4 kt band, not a controlled bench
     sweep); links to #315 (distance-aware reserve), #318 (SOC estimator), #196 (idle/charger).

4. **Revise "Drive efficiently" bullets in `bizzyboat_power.md`** — replace *"Survey speed is
   already near range-optimal (~3–3.5 kt)"* with the plateau finding (~2.9–3.0 kt) and add the
   range/time/endurance trade-off framing as a decision table or bullets.

## Files to Change

| File | Change |
|------|--------|
| `docs/analysis/2026-06-23/README.md` | Fix line 14: update stale "Range-optimal speed ~3–3.5 kt" to match new plateau finding or add cross-reference to #326 |
| `docs/analysis/2026-06-24/README.md` | **Create new** — regeneration notes, bag path, script names, caveats |
| `docs/analysis/2026-06-24/speed_endurance_range_curve.png` | **Copy from** `~/data/logs/analysis/2026-06-24/speed_endurance_range_curve.png` |
| `bizzyboat_project11/docs/bizzyboat_power.md` | Add "Speed → power, endurance, range (empirical)" subsection; revise "Drive efficiently" bullets |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| A change includes its consequences | Stale "~3–3.5 kt" text exists in two places; both updated in the same PR to avoid reader contradiction. |
| Only what's needed | Scope is purely documentation: one doc section added, one paragraph revised, one stale line fixed, one new analysis README — no code changes. |
| Capture decisions, not just implementations | The plan explicitly documents the ±30% caveat, the method (coulomb-quad pipeline), and the decision trade-offs so the "why" is recorded alongside the numbers. |
| Workspace vs. project separation | All changes are in `unh_echoboats_project11` — no workspace-level files touched. |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| ADR-0013 (progress.md vocabulary) | Yes | `## Plan Authored` entry appended to project-repo `progress.md` after this plan commit. |
| ADR-0001 (ADRs for architecture decisions) | No | This is a documentation update, not an architecture decision. |
| ADR-0002 (worktree isolation) | Yes (by dispatch) | Work is in the correct `feature/issue-326` worktree. |

## Consequences

| If we change... | Also update... | Included in plan? |
|---|---|---|
| "Drive efficiently" plateau claim in `bizzyboat_power.md` | `docs/analysis/2026-06-23/README.md` stale "~3–3.5 kt" line | Yes — step 1 |
| "Drive efficiently" guidance (operating point) | #315 (distance-aware reserve uses speed → range) | Cross-reference only; #315 is a separate issue |
| Empirical table introduces nm column | Table header and footer caveats must be self-consistent | Yes — handled in step 3 |

## Open Questions

- [ ] No open questions — plan is review-plan-ready.

## Estimated Scope

Single PR. Pure documentation: four files (two new, two modified).
