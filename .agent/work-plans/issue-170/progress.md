---
issue: 170
---

# Issue #170 — Configure nav2 Collision Monitor for BizzyBoat (reflex safety layer)

## Plan Authored
**Status**: complete
**When**: 2026-05-26 09:20 -04:00
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))

**Plan**: `.agent/work-plans/issue-170/plan.md` at `3345331`
**PR**: https://github.com/rolker/unh_echoboats_project11/pull/178 (`[PLAN]` prefix)
**Phases**: 3 (A = launch reflex node + record + bridge [this PR]; B = swap collision_monitor source + tune polygons; C = offline trigger cataloging)

### Open questions
- [ ] Bridge `period` for `collision_pointcloud` — plan assumes `1.0` on both links; confirm or set unthrottled.
- [ ] Phase A merge gating — open-now-hold-ready (sim-test vs perception#17 worktree) vs wait for perception#17 to land first.
