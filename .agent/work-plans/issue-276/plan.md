# Plan: Nav-config forward fix — re-enable s57_layer + fix confidence_gate (#276)

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/276

## Context

The Jun-26 field interim (#263) disabled `chart_layer` on both costmaps at Lake
Massabesic (no ENC coverage). All blocking deps are now resolved:
- uma#164 (bathymetry_layer plugin) — CLOSED
- uma#148 (store importer) — CLOSED
- Sim harness rolker/unh_marine_simulation#67 and #74 — MERGED

**Existing partial work** (commit `cb3d90a` on branch): `bathymetry_layer` re-enabled
on both costmaps and sim-validated (0% lethal, caution ramp for shallow areas). `chart_layer`
(s57_layer) is still commented out.

**Silent regression since cb3d90a** (uma#276 merged post-session): `max_uncertainty` was
renamed to `confidence_gate` with inverted semantics. The old `max_uncertainty: 5.0` in the
overlay is **deprecated and ignored** at runtime; the default `confidence_gate: 0.5` m now
applies. With σ=5.0 m chart-prior data and worst-case clearance = depth − σ, cells shallower
than 6 m (= min_depth 1.0 + σ 5.0) become LETHAL — a behavioral change from what cb3d90a
validated. This must be fixed before trusting any sim results.

**Timeline driver**: Delaware (UDel/Lewes) trip — ENC-covered site, so "no regression at
ENC sites" is the operative acceptance criterion.

## Approach

1. **Fix `max_uncertainty` → `confidence_gate`** in both costmap `bathymetry_layer` blocks.
   Set `confidence_gate: 5.0` to match the chart-prior import uncertainty and preserve the
   cb3d90a sim-validated behavior (all lake cells with σ=5.0 m treated as trusted; keepout
   governed by `minimum_depth: 1.0` m, not worst-case clearance). Remove the now-stale
   comment that references `max_uncertainty`. Update inline comment to explain the coupling
   to the chart-prior σ and reference ADR-0010 D7.

2. **Re-enable `chart_layer` in both costmap plugin lists**, ordered BEFORE
   `bathymetry_layer` so surveyed M3 depth overrides charted depth (ADR-0010 D5).
   - Local costmap: `["chart_layer", "sea_surface_layer", "bathymetry_layer", "inflation_layer"]`
   - Global costmap: `["chart_layer", "sea_surface_relay", "bathymetry_layer", "inflation_layer"]`
   At Massabesic the s57 source is empty and harmless; at ENC sites it carries charted
   obstacles while bathy overrides depth — correct everywhere, not lake-only.

3. **Re-evaluate `allow_unknown`** (currently `true` in `planner_server` in the base).
   With `unsurveyed_is_lethal: True` + full-lake chart prior, Massabesic should have no
   unknown cells — `allow_unknown: false` may be appropriate for the overlay. Hold as an
   open question pending sim run; do not change the base.

4. **Sim validate** both acceptance scenarios before marking complete:
   - bizzyboat_massabesic_launch: global planner routes across the lake (not just local window)
   - ENC-covered site check: charted non-bathy obstacles (docks, wrecks) remain lethal
     even where surveyed depth underneath is deep.

## Files to Change

| File | Change |
|------|--------|
| `bizzyboat_project11/config/nav2_overlay.yaml` | Fix `max_uncertainty` → `confidence_gate: 5.0` (both costmap blocks); re-enable `chart_layer` ordered before `bathymetry_layer` in both plugin lists |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| Safety First | chart_layer re-enable with bathy ordered after = surveyed depth overrides charted (ADR-0010 D5). ENC-site regression validated in sim before close. Footgun mitigation: s57 at Massabesic is empty → no false lethal from charted depth. |
| Simulation-First Validation | Two acceptance sim runs required (Massabesic route + ENC-site no-regression). Sim harness already merged. |
| Iterative, Validated Evolution | cb3d90a partial work preserved; this PR completes the forward fix. Rolling-window re-evaluation deferred — behavior unchanged from base. |
| Documentation Accuracy | All comments reference actual parameter names and semantics post-uma#276. |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| uma ADR-0010 D5 | Yes | Layer ordering: bathy after s57, so surveyed depth overrides charted |
| uma ADR-0010 D7 | Yes | `max_uncertainty` renamed to `confidence_gate`; value 5.0 m preserves chart-prior trust semantics |
| uma ADR-0010 D10 | Follow-up | s57 obstacle-only split (suppress depth output from s57_layer) deferred; referenced as the durable post-276 step |
| Workspace ADR-0008 (ROS 2 conventions) | OK | Nav2 deep-merge wholesale list replacement — plugin lists restated in full |

## Consequences

| If we change... | Also update... | Included? |
|---|---|---|
| `plugins:` list (both costmaps) | `chart_layer` block must exist in base — confirmed present | Yes |
| `max_uncertainty` → `confidence_gate` | Both local + global costmap bathy blocks | Yes |
| Plugin ordering (chart before bathy) | No other config references ordering | Yes |
| `allow_unknown` (if changed) | Planner behavior at non-Massabesic sites | No — open question |

## Documentation & Instruction Impact

- **Stale docs**: None — no external README references these parameters.
- **Agent-instruction candidates**: The `max_uncertainty`→`confidence_gate` rename + semantic
  change (reject-filter → trust-gate, default 0.5 m) should be noted in the overlay inline
  comments (done by this PR) and in `.agents/README.md` under "nav2 overlay pitfalls" so
  future agents don't re-introduce the deprecated key.

## Open Questions

- **confidence_gate value**: Setting `5.0` preserves the cb3d90a-validated behavior
  (chart-prior cells trusted at keepout level, keepout = minimum_depth 1.0 m). The new
  ADR-0010 D7 worst-case-clearance model (default gate 0.5 m) would treat chart cells as
  go-slow rather than keepout. Which is intended for production? The `5.0` choice is
  conservative-safe for the Delaware trip; revisit after the trip.
- **allow_unknown override**: Should the bizzy overlay set `allow_unknown: false` in
  `planner_server`? With `unsurveyed_is_lethal: True` + chart prior, Massabesic should have
  no unknown cells → `false` enables stricter planning. Needs sim confirmation.
- **rolling_window on global costmap**: Base sets `rolling_window: true` on the global
  costmap. With a static bathy prior, a static global costmap (`rolling_window: false`) would
  enable true long-range planning. Deferred — not needed for Delaware trip, non-trivial
  memory/perf tradeoff at 1 m resolution.

## Estimated Scope

Single PR on `feature/issue-276`.
