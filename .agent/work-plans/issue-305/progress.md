---
issue: 305
---

# Issue #305 — sidescan grazing_deg default 62.5° → 35° (field-measured)

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-06-21 16:51 +00:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: changes-requested

**Branch**: feature/issue-305 at `aa202a2`
**Mode**: pre-push
**Depth**: Light (reason: single-file xacro default + rationale-comment change, 27 lines, non-security, non-cross-layer)
**Must-fix**: 1 | **Suggestions**: 0
**Round**: 1 | **Ship**: continue — one mechanical comment-only must-fix remains; otherwise shippable

### Findings
- [ ] (must-fix) Stale "Manual TF check" expected value: still cites old default `[0, 0.462, -0.887]` / "62.5 deg depression"; with new 35° default the check yields `[0, 0.819, -0.574]` / 35°. Cross-confirmed (lead + adversarial Lens A). — `bizzyboat_project11/urdf/sensors/sidescan.xacro:83`
