---
issue: 237
---

# Issue #237 — Add Garmin GCV-20 sidescan TF frames to BizzyBoat URDF

## Integrated Review
**Status**: complete
**When**: 2026-06-09 10:00 -0400
**By**: Claude Code Agent (Claude Opus 4.8 (1M context))

**PR**: #238 at `de97700`
**Sources**: 1 (Copilot @ `de97700`; no local review timeline existed for #237)
**Cross-source confirmations**: 0
**CI**: all-pass (only the Copilot reviewer check runs on this repo)

### Findings
- [ ] (valid, Copilot) Documentation inaccuracy — `bizzyboat.urdf.xacro:252` comment claims
  the driver stamps per-channel images with `bizzy/garmin_sidescan`, but
  `garmin_sidescan/node.py:757` builds `frame_id = f'{base}_{suffix}'`, yielding
  `bizzy/garmin_sidescan_down/_port/_starboard`. Also contradicts this PR's own
  `sidescan.xacro` header (lines 6-9), which is correct. — `bizzyboat_project11/urdf/bizzyboat.urdf.xacro`
- [ ] (style, Copilot) Channel joints use `${radians(...)}` and order `<origin>` before
  `<parent>`/`<child>`; sibling sensor macros (`camera_oak.xacro`, `sonar.xacro`) use `pi`
  math (`${-pi/2}`) and `parent`/`child`/`origin` order. Consistency-only; functionally inert.
  — `bizzyboat_project11/urdf/sensors/sidescan.xacro` (joints at lines 34/42/50)

### False positives
- (Copilot) Rationale "avoid relying on `radians()` being available in xacro" — `radians()`
  IS a xacro built-in (file builds, CI green), so that justification is wrong. The underlying
  style-consistency finding still stands and is retained above; only Copilot's reason is invalid.
