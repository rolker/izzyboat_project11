---
issue: 415
---

# Issue #415 — bizzyboat nav2: ADR-0010 D10 depth-authority split (depth_costs:false + re-enable bathymetry_layer)


## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-08-05 15:17 +00:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: approved

**Branch**: feature/issue-415 at `7e87b30`
**Mode**: pre-push
**Depth**: Standard (reason: 53 changed lines; single safety-relevant nav config, no Deep trigger)
**Must-fix**: 0 | **Suggestions**: 1
**Round**: 1 | **Ship**: recommended — no Must-fix; both Claude adversarial lenses clean, D10 config verified against s57_layer + base + bathymetry_layer

### Findings
- [ ] (suggestion) In D10 mode (`depth_costs: false`) a store-absent no-op leaves zero depth authority, not a chart-depth fallback; the "(safe)" comment now understates that — tighten to flag store presence as a hard pre-launch check — `bizzyboat_project11/config/nav2_overlay.yaml:129`

## Integrated Review
**Status**: complete
**When**: 2026-08-05 11:39 -04:00
**By**: Claude Code Agent (Claude Opus)

**PR**: #416 at `3b7cf5a`
**Sources**: 3 (Copilot R1 @ `3b7cf5a` — 0 comments; Local Review (Pre-Push) @ `7e87b30` — 1 suggestion; CI rollup @ `3b7cf5a`)
**Cross-source confirmations**: 0
**CI**: all-pass (build-and-test success, copilot-pull-request-reviewer success)

### Findings
- [ ] (suggestion, integrator) `bathymetry_layer.unsurveyed_is_lethal: True` is re-enabled with its rationale comment still reading "Closed lake basin: the chart prior is masked to the lake outline, so no-data cells are land" — Massabesic-specific and stale now that the layer runs at an open-coast site whose store holds only survey-track coverage (the Lewes chart prior import is still owed, uma#289). Out-of-coverage cells then read LETHAL, the same blanket that forced the 2026-08-03 field disable. The issue body scopes the semantics decision to the #408 RCA; the cheap in-scope fix is a comment cross-reference to #408 so the stale lake rationale doesn't read as current justification — `bizzyboat_project11/config/nav2_overlay.yaml:149-151,196`

### Resolved since prior round
- (Local Review (Pre-Push) @ `7e87b30`, suggestion) "store-absent no-op leaves zero depth authority, not a chart-depth fallback" — fixed in `3b7cf5a`: the store_path comment now states the no-op leaves NO depth authority and that store presence is a hard pre-launch check, not soft degradation (`nav2_overlay.yaml:129-135`).

### False positives
- none — Copilot R1 reviewed both changed files and generated no comments.

### Verification performed
- Deep-merge safety: `param_compose.deep_merge` (seafloor_echoboat_project11) merges dicts key-by-key, so the overlay's `chart_layer:` block carrying only `depth_costs: false` inherits `plugin: s57_layer::S57Layer` and the depth/tide params from `nav2_params.base.yaml` (lines 117-118 local, 168-169 global) — no risk of blanking the plugin type.
- Upstream dependency satisfied: `depth_costs` is declared and honored in `s57_layer.cpp:57-58,99,172,520`; rolker/s57_tools#31 merged 2026-08-05 14:47Z (issue #30 closed). Deploy note stands — gabby must pull + rebuild core_ws s57_tools for the flip to take effect; older binaries ignore the key (degrades to chart depth + raise-only bathy — over-conservative, not unsafe).
- Plugin ordering (`chart_layer` before `bathymetry_layer`) preserved in both costmaps; global list restates the base list plus bathymetry_layer, as deep-merge replaces lists wholesale.
