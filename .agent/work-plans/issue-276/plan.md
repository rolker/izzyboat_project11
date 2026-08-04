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

**Deprecated key since cb3d90a** (uma#276 merged post-session): `max_uncertainty` was
renamed to `confidence_gate` with **changed semantics** — no longer a reject filter but a
trust gate: a sample is TRUSTED (keepout-eligible) only when σ ≤ gate; untrusted samples are
capped at caution and can never be LETHAL (`bathymetry_layer.cpp` computeCost). The old
`max_uncertainty: 5.0` in the overlay is **deprecated and ignored** at runtime (one-shot
warning); the default `confidence_gate: 0.5` m applies instead. Net current behavior: chart-
prior cells (σ=5.0) are untrusted → caution-only, which matches the cb3d90a-validated
"0% lethal + caution ramp" intent (with a stronger ramp, since worst-case clearance =
depth − σ). The config must drop the dead key and set the gate deliberately — NOT copy 5.0
across the rename, which would *trust* σ=5.0 chart data and flood the ~1.5–7.6 m lake
LETHAL wherever depth − 5.0 < minimum_depth 1.0 (i.e. depth < 6 m).

**Timeline driver**: Delaware (UDel/Lewes) trip — ENC-covered site, so "no regression at
ENC sites" is the operative acceptance criterion.

## Approach

1. **Replace `max_uncertainty: 5.0` with `confidence_gate: 0.5`** (the plugin default,
   stated explicitly) in both costmap `bathymetry_layer` blocks, and **remove the deprecated
   key outright** (the plugin logs an error and ignores it). Semantics (ADR-0010 D7):
   trusted = σ ≤ gate, and only trusted data may keep a cell out. Gate 0.5 keeps chart-prior
   cells (σ=5.0) untrusted → caution-only (preserves the cb3d90a-validated no-lethal-flood
   behavior), while M3 survey cells (σ typically < 0.5) stay keepout-capable for real shoals.
   Inline comment documents the trust direction and the copy-5.0-across-the-rename trap.

2. **Re-enable `chart_layer` in both costmap plugin lists**, ordered BEFORE
   `bathymetry_layer` — **required, not stylistic**: `s57_layer::updateCosts` OVERWRITES the
   master grid where chart data exists (`s57_layer.cpp:474-476`) and stomps NO_INFORMATION
   over not-yet-loaded tiles (`:480-489`), so running it after bathy would clobber the bathy
   prior. With s57 first, bathymetry_layer max-combines on top (raise-only, skips
   NO_INFORMATION) → final = max(chart, bathy). Note this means surveyed-deep can NOT lower
   charted-shallow — that resolution lives in the store query and the deferred D10
   obstacle-only split, not in layer ordering.
   - Local costmap: `["chart_layer", "sea_surface_layer", "bathymetry_layer", "inflation_layer"]`
   - Global costmap: `["chart_layer", "sea_surface_relay", "bathymetry_layer", "inflation_layer"]`
   At Massabesic the s57 source is uncharted-complete and `allow_uncharted` defaults true
   (`s57_layer.h:119`, base config doesn't override) → master grid untouched, harmless; at
   ENC sites it carries charted obstacles — correct everywhere, not lake-only.

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
| `bizzyboat_project11/config/nav2_overlay.yaml` | Remove deprecated `max_uncertainty`, set `confidence_gate: 0.5` (both costmap blocks); re-enable `chart_layer` ordered before `bathymetry_layer` in both plugin lists |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| Safety First | chart_layer re-enable with bathy ordered after (ordering required — s57 overwrites, bathy raise-only combines on top; final = max(chart, bathy), never lowered). ENC-site regression validated in sim before close. Footgun mitigation: s57 at Massabesic is uncharted-complete + allow_uncharted → grid untouched, no false lethal. confidence_gate 0.5 keeps high-σ chart data caution-only; keepout reserved for trusted survey data (ADR-0010 D7). |
| Simulation-First Validation | Two acceptance sim runs required (Massabesic route + ENC-site no-regression). Sim harness already merged. |
| Iterative, Validated Evolution | cb3d90a partial work preserved; this PR completes the forward fix. Rolling-window re-evaluation deferred — behavior unchanged from base. |
| Documentation Accuracy | All comments reference actual parameter names and semantics post-uma#276. |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| uma ADR-0010 D5 | Yes | Layer ordering: bathy after s57 (required — s57 overwrites the master grid; bathy max-combines on top). Surveyed-over-charted resolution happens in the store query / deferred D10 split, not ordering |
| uma ADR-0010 D7 | Yes | Deprecated `max_uncertainty` removed; `confidence_gate: 0.5` (default, explicit) — chart σ=5.0 untrusted → caution-only, survey σ<0.5 trusted → keepout-capable |
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

- **confidence_gate value — RESOLVED (plan review must-fix)**: low gate (`0.5`, the
  default, stated explicitly). A 5.0 gate would *trust* σ=5.0 chart cells and turn most of
  the 1.5–7.6 m lake LETHAL (worst-case clearance = depth − σ < minimum_depth wherever
  depth < 6 m) — failing the route-across-lake acceptance test and inverting ADR-0010 D7
  (keepout only on trusted data). The low gate reproduces the cb3d90a-validated caution-only
  chart behavior and keeps keepout for trusted survey data.
- **allow_unknown override**: Should the bizzy overlay set `allow_unknown: false` in
  `planner_server`? With `unsurveyed_is_lethal: True` + chart prior, Massabesic should have
  no unknown cells → `false` enables stricter planning. Needs sim confirmation.
- **rolling_window on global costmap**: Base sets `rolling_window: true` on the global
  costmap. With a static bathy prior, a static global costmap (`rolling_window: false`) would
  enable true long-range planning. Deferred — not needed for Delaware trip, non-trivial
  memory/perf tradeoff at 1 m resolution.

## Estimated Scope

Single PR on `feature/issue-276`.
