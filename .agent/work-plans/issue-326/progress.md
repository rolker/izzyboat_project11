---
issue: 326
---

# Issue #326 — Update bizzyboat_power.md with empirical speed→power/endurance/range characterization

## Issue Review
**Status**: complete
**When**: 2026-06-24 00:00 +00:00
**By**: Claude Code Agent (Claude Sonnet)

**Issue**: #326
**Comment**: (best-effort post follows this entry; not recorded inline)
**Scope verdict**: well-scoped

### Actions
- [ ] When revising the power doc, also update `docs/analysis/2026-06-23/README.md` line 13 (currently reads "Range-optimal speed ~3–3.5 kt") — this will conflict with the revised guidance once the power doc is updated. Update it or add a forward reference to avoid reader confusion.
- [ ] Confirm that the analysis plot lands in the top-level `docs/analysis/2026-06-24/` (consistent with `docs/analysis/2026-06-23/` pattern), not under `bizzyboat_project11/docs/analysis/`.
- [ ] Add a regeneration note in `docs/analysis/2026-06-24/README.md` (bag path + script names) since `coulomb.py`, `speed_bins.py`, `speed_curve.py` are local-only — reproduce path: `~/data/logs/gabby/logs/bizzyboat/2026-06-24T12-11-05+00-00`.

## Plan Authored
**Status**: complete
**When**: 2026-06-24 10:30 +00:00
**By**: Claude Code Agent (Claude Sonnet)

**Plan**: `.agent/work-plans/issue-326/plan.md` at `968fc54`
**Branch**: feature/issue-326 at `968fc54`
**Phases**: single

### Open questions
- [ ] No open questions — plan is review-plan-ready.

## Plan Review
**Status**: complete
**When**: 2026-06-24 23:29 +00:00
**By**: Claude Code Agent (Claude Opus)
<!-- Independent fresh-context review. Plan author was a Sonnet-model agent; the
     shared workspace AGENT_NAME is not, by itself, evidence of self-review, so no
     self-review annotation is applied. -->

**Plan**: `.agent/work-plans/issue-326/plan.md` at `968fc54`
**PR**: PR-less (--issue mode; gh not authenticated on host)
**Verdict**: approve-with-suggestions

### Findings
- [ ] (risk) Source artifacts `~/data/logs/analysis/2026-06-24/` (incl. `speed_endurance_range_curve.png`) absent on this host — confirm implementer can reach them or run implementation where the data lives — `plan.md:19,61`
- [ ] (suggestion) Stale "Range-optimal speed ~3–3.5 kt" is on line 13 of `docs/analysis/2026-06-23/README.md`, not line 14 — target by text, not line number — `plan.md:59`
- [ ] (suggestion) Insert new subsection after `#### SOC ↔ voltage reference` (`bizzyboat_power.md:76`), just before `## Power model` — avoids splitting that subsection — `plan.md:35`

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-06-25 00:07 +00:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: changes-requested

**Branch**: feature/issue-326 at `afb62c5`
**Mode**: pre-push
**Depth**: Standard (reason: safety-relevant operational guidance with quantitative range/endurance claims)
**Must-fix**: 2 | **Suggestions**: 3
**Round**: 1 | **Ship**: continue — 2 must-fix, one a genuine range-planning gap; dispatch address-findings then re-review

### Findings
- [ ] (must-fix) Range figures (~27–28 nm plateau, ~24 nm @3.1kt) are straight-line-idealized; only measured full-discharge (06-23) got ~19.2 nm @3.1kt mean SOG (drew ~44A ≈ 3.5kt bin due to turns) — add real-survey derate + surface "straight-line" at the table — `bizzyboat_project11/docs/bizzyboat_power.md:102-123`
- [ ] (must-fix) 06-23 quad-coulomb anchor self-contradicts: 273.9 Ah (new README) vs 272.6 Ah (power doc, twice) — reconcile — `docs/analysis/2026-06-24/README.md:38` ↔ `bizzyboat_project11/docs/bizzyboat_power.md:67,156`
- [ ] (suggestion) 06-23 avg draw 42 A (lines 72,208) vs 44 A (line 139); 44 A matches 273Ah/6.16h — reconcile — `bizzyboat_project11/docs/bizzyboat_power.md:72,139,208`
- [ ] (suggestion) "drag step at ~3.2 kt" implies discontinuity but quadratic model I=8+59r² is smooth — reword to "climbs steeply" — `bizzyboat_project11/docs/bizzyboat_power.md:121`
- [ ] (suggestion) "~2.9–3.0 kt" sweet spot has no 3.0kt table row and 2.0–2.9 plateau vs "best=2.9kt" reads ambiguously — clarify or add row — `bizzyboat_project11/docs/bizzyboat_power.md:111-134`
