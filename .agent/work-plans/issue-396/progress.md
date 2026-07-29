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

## Plan Review
**Status**: complete
**When**: 2026-07-29 08:45 -04:00
**By**: Claude Code Agent (Claude Opus)

**Plan**: `.agent/work-plans/issue-396/plan.md` at `04c9a3a`
**PR**: PR-less (`--issue` mode; branch `feature/issue-396`)
**Verdict**: approve-with-suggestions

Both Issue Review actions are discharged by the plan: the marine_tools#75 /
PR #76 dependency ordering is stated (plan.md:16-20, PR-body requirement at
plan.md:47-49), and the `sonar_logger` exclusion is confirmed deliberate and
recorded in the consequences table (plan.md:41-43, 76). Independently
verified against source: `bizzyboat.yaml:571` (main `logger`) and `:685`
(`sonar_logger`) are the correct anchors; marine_tools PR #76 publishes an
**always-on, unconditional** bare-relative `raw` from `_handle_reading()` for
**both** the `aml` and `regex` parsers — so BizzyBoat's `parser: 'regex'`
config (`launch/sound_speed_launch.py`) is covered and the plan's "no launch
changes" claim holds. Precedent check confirms the consequences table: #270
(commit `8accf34`) added the Garmin scalars as a config-only 6-line change
with no doc updates, and no bag-contents inventory exists in `docs/`.
izzyboat has no sound-speed probe, so there is no platform-parity
consequence; the sim launch does not run the recorder.

### Findings
- [ ] (suggestion) Consequences table omits the deployment/rebuild row — the config only takes effect after gabby pulls **and rebuilds** `bizzyboat_project11` (ament `install(DIRECTORY config/)` copies YAML; symlink-install does not propagate data files), and the topic only exists after marine_tools#76 merges **and** `sound_speed_bridge` is rebuilt on gabby. Add a row so the field-side action isn't lost — `plan.md:74-77`
- [ ] (suggestion) Have the added YAML comment name the driver-version dependency, not just the issue numbers — until #76 lands and gabby rebuilds, the entry records silently nothing, and a field reader seeing an empty topic should not mistake it for a probe/driver fault. In-file precedent for annotating a topic that records nothing: the commented-out `/bizzy/sensors/deltat/soundings` at `bizzyboat.yaml:648-649` — `plan.md:34-39`
- [ ] (suggestion) Verification is under-specified ("live/bag smoke check") — state a checkable acceptance criterion instead: after the gabby rebuild, `ros2 bag info` on a new main bag shows `/bizzy/sensors/sound_speed/raw` (`std_msgs/UInt8MultiArray`) with a nonzero message count while the probe is streaming — `plan.md:64`
- [ ] (suggestion) Note in the plan that izzyboat needs no parity change (no sound-speed probe; `izzyboat.yaml` has `logger`/`sonar_logger` blocks but no `sound_speed` entry) so the omission reads as verified rather than unconsidered — `plan.md:74-77`
- [ ] (note, no action) `std_msgs/UInt8MultiArray` carries no header/stamp, so raw-vs-parsed correlation relies on rosbag2 receive time. Settled driver-side in marine_tools#76; out of scope here.
- [ ] (note) The skill's author-self-review heuristic compares only the agent-name portion of `## Plan Authored` (`Claude Code Agent`), which every agent in this workspace shares. This review is a fresh-context sub-agent on a different model (Opus vs. the planner's Sonnet), so no self-review annotation was applied.
