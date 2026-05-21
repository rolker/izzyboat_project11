---
issue: 140
---

# Issue #140 — Remove stale bencloud ping target from operator-side ping_monitor (doesn't reflect WG link health)

## External Review
**Status**: complete
**When**: 2026-05-21 09:00
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))

**PR**: #148 — 1 review (Copilot, no inline comments), 2 conversation comments, 1 valid, 0 false positives
**CI**: all pass (copilot-pull-request-reviewer success)

### Actions
- [ ] Decide doc path for `bizzyboat_project11/docs/operator_annunciator_design.md` L59–75 "What we deliberately don't include: `Ping: ping.op: bencloud`" section. Sub-agent review (PR comment #4504056328) flags it as incoherent once the active target is removed. Two options:
  - **A (inline, bundle)**: add a 2-line note to the section saying it was removed entirely in #140; section retained as historical context. Keeps doc honest at near-zero cost.
  - **B (defer)**: file a follow-up issue that explicitly names this file and section (not a handwave at "docs").
