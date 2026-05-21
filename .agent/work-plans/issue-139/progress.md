---
issue: 139
---

# Issue #139 — Replace output='screen' with output='both' in BizzyBoat launch files (loses crash output today)

## External Review
**Status**: complete
**When**: 2026-05-21 09:25
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))

**PR**: #147 — 1 review (Copilot, 0 inline comments), 2 conversation comments (both informational from `rolker`); 0 valid issues, 0 false positives
**CI**: copilot-pull-request-reviewer = success

### Actions
- [ ] (Optional) Confirm #120 (IzzyBoat parity tracker) lists the remaining `output='screen'` sites in `izzyboat_project11/launch/360_camera_launch.py:129` and `oak_launch.py:39`; add if missing
- [ ] Merge PR #147 — no blockers; mechanical `output='screen'` → `output='both'` substitution across 4 BizzyBoat launch files; sub-agent LGTM stands and CI is green
