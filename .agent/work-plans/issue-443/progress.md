---
issue: 443
---

# Issue #443 — Repoint boat config to the world store root: store_path + draft_dir (uma#310 follow-up)

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-08-20 19:40 -04:00
**By**: Claude Code Agent (Claude Fable 5)
**Verdict**: approved

**Branch**: feature/issue-443 at `0b00dbe`
**Mode**: pre-push
**Depth**: Light (reason: config repoint, but boat-safety-relevant — adversarial pass targeted at the draft_dir semantics)
**Must-fix**: 1 | **Suggestions**: 3
**Round**: 1 | **Ship**: recommended — must-fix and both in-repo suggestions fixed in-session; upstream design note filed as cube#135

### Findings
- [x] (must-fix, Claude Adversarial) draft_dir mapped one level too deep: the node treats it as a store ROOT (<draft_dir>/draft/), and the costmap's flat-layout loader skips subdirs — costmap would be silently blind to live tiles. Fixed: draft_dir = /home/field/data/world/depths — `bizzyboat_project11/config/bizzyboat.yaml`
- [x] (suggestion, Claude Adversarial) rebuild-day trap: legacy cube_draft survey/ tiles must NOT auto-migrate to processed/ (live-node flyers would outrank fresh draft) — recorded in the config comment + PR body for the rebuild-day script — `bizzyboat_project11/config/bizzyboat.yaml`
- [x] (suggestion, Claude Adversarial) scripts/build_bathy_store.sh defaults still targeted the retired root — repointed (BATHY_STORE → world/depths, BS_STORE → world/imagery/backscatter) — `scripts/build_bathy_store.sh:71-72`
- [x] (suggestion, Claude Adversarial) live-writer vs costmap-reader non-atomic tile write race, activated by this unification — upstream, filed as rolker/cube_bathymetry#135

### False positives
- (none)
