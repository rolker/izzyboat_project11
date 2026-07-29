---
issue: 396
---

# Issue #396 — bag recording: log AML sound-speed raw sentence topic in the main deployment bag

## Issue Review
**Status**: complete
**When**: 2026-07-29 08:03 -04:00
**By**: Claude Code Agent (Claude Sonnet)

**Issue**: #396
**Comment**: (best-effort post follows this entry; not recorded inline)
**Scope verdict**: well-scoped

### Actions
- [ ] Before merging, verify rolker/marine_tools#75 (PR #76) has actually merged and the `raw` topic is live on the driver — as of this review PR #76 is still **open** (not merged), so implementation should either wait for the merge or explicitly note the dependency ordering in the PR body.
- [ ] Confirm whether the raw sentence topic should also be added to `sonar_logger`'s record list (`bizzyboat_project11/config/bizzyboat.yaml` line ~685 already records the parsed `/bizzy/sensors/sound_speed/sound_speed` in *both* the main `logger` and `sonar_logger` sections for bathy sound-speed correction). The issue only asks for the main bag; confirm this is an intentional scope limit (raw bytes are a diagnostic-only artifact, not needed for the bathy correction pipeline) rather than an oversight, and note it explicitly in the PR if sonar_logger is deliberately excluded.

## Plan Authored
**Status**: complete
**When**: 2026-07-29 08:07 -04:00
**By**: Claude Code Agent (Claude Sonnet)

**Plan**: `.agent/work-plans/issue-396/plan.md` at `04c9a3a`
**Branch**: feature/issue-396 at `04c9a3a`
**Phases**: single

### Open questions
- [ ] No open questions — plan is review-plan-ready.
