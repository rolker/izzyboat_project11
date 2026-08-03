---
issue: 276
---

# Issue #276 — Nav-config forward fix: re-enable s57_layer + add bathymetry_layer (gated on #164)

## Issue Review
**Status**: complete
**When**: 2026-08-03 00:00 +00:00
**By**: Claude Code Agent (Claude Sonnet)

**Issue**: #276
**Comment**: (best-effort post follows this entry; not recorded inline)
**Scope verdict**: well-scoped

### Summary

Issue #276 is the **nav-config forward fix** for global planning at no-ENC inland sites (Lake Massabesic). It undoes the field-interim chart-layer disable (#263) by: (1) adding `bathymetry_layer` to both costmaps ordered after `s57_layer`, (2) re-enabling `s57_layer`, and (3) re-evaluating `allow_unknown` + global rolling window. Gated on the bathymetry layer plugin (#164) and store importer (#148). The #263 interim stays in force until those deps land.

### Scope Assessment

**Well-scoped?** Yes — config-only change in `bizzyboat_project11/config/nav2_overlay.yaml`, with a clear entry condition (after #164 + #148 land) and acceptance criteria (sim route across lake, no regression at ENC sites).

**Right repo?** Yes — config lives in `bizzyboat_project11` package inside `unh_echoboats_project11`.

**Dependencies**:
- #164 (bathymetry_layer plugin registration in nav2_params) — **hard block** on re-enabling s57 + adding bathy ordered after it
- #148 (store importer) — **hard block** on bathy prior being available
- #86 Phase-4 enablement parent — context tracking
- #96 (bizzy nav2 override structure) — coordinate on deep-merge layout
- Simulation harness: rolker/unh_marine_simulation#67 and #74 — needed for acceptance-criteria validation

**Note:** One commit already exists on this branch (`cb3d90a`) that re-enabled `bathymetry_layer` on both costmaps while keeping `chart_layer` (s57) commented out. This was a partial step (the bathymetry re-enable was unblocked independently); re-enabling s57 and ordering bathy after it are still pending #164/#148.

### Principle Alignment

| Principle | Status | Notes |
|---|---|---|
| Safety First | OK | Issue explicitly calls out footgun mitigation: GeoTIFF lake-outline masking prevents bathy from clearing charted non-bathy obstacles (docks/wrecks). The durable fix (#14) is also noted. |
| Simulation-First Validation | Watch | Acceptance criteria name two sim scenarios (Massabesic route across lake; no regression at ENC site). Confirm sim harness PRs (#67/#74 in unh_marine_simulation) are merged and stable before closing this issue. |
| Iterative, Validated Evolution | OK | The interim (#263) stays in force until deps (#164, #148) land — correct incremental posture. Partial commit on branch is appropriate. |
| Hardware Agnosticism | OK | N/A — pure config, no new hardware interface. |
| Modularity and Decoupling | OK | Layer ordering in the overlay (bathy after s57) is the right Nav2 deep-merge approach; no monolithic rework. |
| Standards Compliance | OK | Uses standard Nav2 costmap plugin list override patterns (deep-merge wholesale list replacement). |

### ADR Applicability

| ADR | Triggered | Notes |
|---|---|---|
| ADR-0001 (Adopt ADRs) | Watch | The ordering decision (bathy after s57) and the footgun-mitigation strategy (GeoTIFF masking interim, #14 as durable fix) are design decisions worth capturing — either in an ADR or a `docs/decisions/` note in the project repo. Not blocking, but the "why bathy ordered after s57" reasoning should survive this issue's close. |
| ADR-0002 (Worktree isolation) | OK | Worktree `issue-unh_echoboats_project11-276` exists. |
| ADR-0008 (ROS 2 conventions) | OK | Nav2 plugin ordering follows Nav2 deep-merge conventions. |
| ADR-0017 (Extend AGENTS.md to project repos) | Watch | If the project repo has an AGENTS.md, confirm it's up to date with the nav2 overlay pattern (especially the deep-merge wholesale-list behavior that's a gotcha for future maintainers). |

### Consequences

Per the consequences map:
- **Package parameters change** (nav2 costmap plugin list) → check if `bizzyboat_project11`'s `.agents/review-context.yaml` maps plugins; if so, update it in the same PR.
- **Config live at field sites** → the comment trail in `nav2_overlay.yaml` already documents each change with field dates and rationale (good practice); maintain this for the s57 re-enable commit too.
- The durable obstacle-split fix (#14) is flagged as follow-up in the issue — ensure that's tracked and not silently assumed done.

### Recommendations

- Before implementing the s57 re-enable, confirm #164 is merged into the base `nav2_params` and `bathymetry_layer` is a registered plugin — otherwise Nav2 will refuse to start.
- When writing the s57 re-enable commit, add a comment in `nav2_overlay.yaml` similar to the existing ones (date, issue reference, rationale) to maintain the file's documentation density.
- Validate `allow_unknown: false` on the global costmap in sim before field deployment — with bathy providing full coverage, unknown-space planning should no longer be needed, but confirm the sim run completes without the planner falling back to unknown traversal.
- Track the sim harness PRs (#67/#74) explicitly as a checklist item in this issue or a sub-task so they don't block the final acceptance check silently.

### Actions
- [ ] Confirm simulation harness PRs (unh_marine_simulation#67, #74) are merged before running acceptance validation.
- [ ] After #164 lands: re-enable `chart_layer` (s57_layer) in both costmap plugin lists in `nav2_overlay.yaml`, ordered before `bathymetry_layer`.
- [ ] Re-evaluate `allow_unknown` and global rolling-window config once bathy provides full global coverage — document the decision.
- [ ] Check and update `bizzyboat_project11` `.agents/review-context.yaml` if it maps costmap plugins.
- [ ] Consider capturing the layer-ordering rationale (bathy after s57 = surveyed depth overrides charted depth) in a short ADR or inline doc comment.

## Plan Authored
**Status**: complete
**When**: 2026-08-03 22:54 +00:00
**By**: Claude Code Agent (Claude Sonnet)

**Plan**: `.agent/work-plans/issue-276/plan.md` at `a33ae9e`
**Branch**: feature/issue-276 at `a33ae9e`
**Phases**: single

### Open questions
- [ ] confidence_gate value: `5.0` preserves cb3d90a-validated behavior (chart-prior cells trusted at keepout level); default `0.5` would use worst-case clearance for chart data — which is intended for production? 5.0 chosen for Delaware trip safety; revisit post-trip.
- [ ] allow_unknown override: should the bizzy overlay set `allow_unknown: false` in `planner_server`? With `unsurveyed_is_lethal: True` + chart prior, Massabesic should have no unknown cells — needs sim confirmation.
- [ ] rolling_window on global costmap: deferred — not needed for Delaware trip, non-trivial memory/perf tradeoff.

## Plan Review
**Status**: complete
**When**: 2026-08-03 23:00 +00:00
**By**: Claude Code Agent (Claude Opus)

**Plan**: `.agent/work-plans/issue-276/plan.md` at `a33ae9e`
**PR**: PR-less (`--issue 276`)
**Verdict**: changes-requested

Independent review: plan authored by Claude Sonnet; this review is a fresh-context
Claude Opus pass (different model, no shared reasoning) — treated as independent
despite the shared framework name.

### Findings
- [ ] (must-fix) `confidence_gate: 5.0` INVERTS the post-#276 trust-gate — it floods the lake LETHAL, the opposite of the plan's stated goal. In `bathymetry_layer.cpp` σ is *always* subtracted (`worst_case_clearance = clearance − σ`, L952) and `trusted = σ ≤ confidence_gate` (L953) only decides whether a below-`minimum_depth` cell is LETHAL (trusted) vs caution-capped (untrusted). With chart σ=5.0: gate 5.0 → trusted → LETHAL wherever depth<6 m (lake is ~1.5–7.6 m → mostly LETHAL, fails the "route across the lake" acceptance test). The cb3d90a "0% lethal" behavior is preserved by a gate BELOW σ (the 0.5 default → chart data untrusted → caution, never LETHAL). Plan copied the old `max_uncertainty: 5.0` straight across the rename — the exact trap the code's deprecation warning (L118-133) flags. Fix the value AND the prose: Context, Approach step 1 ("keepout governed by minimum_depth, not worst-case clearance" is false — L951-954), the ADR-0010 D7 row, and the inline-comment guidance all describe the model backwards. Resolve Open-Question #1 in favor of a low gate before implementing; do not defer. — `plan.md:31-36`, `plan.md:98-102`
- [ ] (suggestion) "chart before bathy so surveyed depth overrides charted (ADR-0010 D5)" likely doesn't hold: bathymetry_layer is raise-only max-combine (`bathymetry_layer.cpp:976`), so if s57_layer is too (standard Nav2; not checked out here to confirm), final cost = max(chart, bathy) regardless of order — ordering yields no override. The real surveyed-over-charted resolution is inside bathymetry_layer's max-over-reliable-samples (L926-934); charted shallow depth from s57 at ENC sites still raises cost where surveyed depth is deep — the deferred D10 obstacle-only split. Verify s57_layer's combination_method and soften the ordering rationale. — `plan.md:38-43`
- [ ] (suggestion) Ensure the deprecated `max_uncertainty` key is REMOVED from both costmap blocks (not left beside `confidence_gate`) — the plugin logs an error and ignores it (L118-133). — `plan.md:59`
- [ ] (note) Verified OK: base `chart_layer` block present for both costmaps (`nav2_params.base.yaml:117,168`); `allow_unknown: true` in base (L223), correctly held as an open question with the base unchanged; Documentation & Instruction Impact section present and non-silent (the `.agents/README.md` pitfall candidate must document the gate *direction* per the must-fix).
