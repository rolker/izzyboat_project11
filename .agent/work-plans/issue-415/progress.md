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
