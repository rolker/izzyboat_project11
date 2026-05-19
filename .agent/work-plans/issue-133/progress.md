---
issue: 133
---

# Issue #133 — OAK cameras: coprime keyframe intervals to decorrelate IDR peaks for Starlink-only ops

## External Review
**Status**: complete
**When**: 2026-05-19 09:55
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))

**PR**: #134 — 1 Copilot review, 1 inline comment, 0 valid, 1 false positive.
**CI**: copilot-pull-request-reviewer success (single check).

### Actions
- [ ] (Optional) Dismiss the Copilot review on #134 — the single inline
  comment asks for redundant WHAT documentation that conflicts with the
  workspace's "WHY-not-WHAT" comment rule (CLAUDE.md). The per-camera
  mapping is authoritative in the dict literal at
  `bizzyboat_project11/launch/oak_cameras_launch.py:19–32`; duplicating
  it in the rationale comment would create a drift-prone second source
  of truth.
- [ ] Merge #134 once approved; remove worktree with
  `.agent/scripts/worktree_remove.sh --issue 133`.
- [ ] Bench-verify the new keyframe cadences on a dev OAK before
  field deployment (test plan in PR body).
