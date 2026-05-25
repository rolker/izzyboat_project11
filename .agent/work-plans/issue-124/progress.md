---
issue: 124
---

# Issue #124 — Post-mission data review — 2026-05-01 BizzyBoat deployment

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-05-25 10:45
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))
**Verdict**: approved

**Branch**: feature/issue-124 at `249009e`
**Mode**: pre-push
**Depth**: Standard (reason: 699 LOC across 7 files incl. Python, project repo)
**Must-fix**: 0 | **Suggestions**: 6 (all addressed before push)

Covers §2 (Performance characterization). Two adversarial specialists
(Claude fresh-context + Copilot CLI v1.0.51) ran; the Claude subagent
independently re-ran both analysis scripts and confirmed every
per-deployment number reproduces exactly. No must-fix bugs; coordinate
conventions, circle-fit algebra, surge/decay slopes, and the
no-current-meter constraint all verified clean.

### Findings (all resolved)
- [x] (suggestion) accel gate admitted reverse-start transitions — tightened to near-idle start (`1470≤before≤1560`) — `dynamics.py`
- [x] (suggestion) no-arg run did 3 DBs but README said "all" — default now globs all 7 — `dynamics.py`
- [x] (suggestion) degenerate-window threshold too broad (10 min) — tightened to 2 min + comment — `dynamics.py`
- [x] (suggestion) cruise m/s↔kt pairing (1.5↔3.0 implies 1.54) — standardised to 1.52 m/s — `bizzyboat_performance.md`, `bizzyboat_hardware.md`
- [x] (suggestion) coast-down "~0.2 m/s²" was the max not median — restated ~0.15 (up to ~0.25) — `bizzyboat_performance.md`, `bizzyboat_hardware.md`
- [x] (suggestion) "fit quality tracks current" mis-attributed — reworded to heading-arc + speed steadiness; slack "≈0" → ~0.1 within fit noise — `bizzyboat_performance.md`, `README.md`

## Local Review (Pre-Push) — turning + yaw-cap round
**Status**: complete
**When**: 2026-05-25 12:10
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))
**Verdict**: approved (after fixes)

**Branch**: feature/issue-124 at `915571e`
**Mode**: pre-push
**Scope**: turn-radius item — turning.py, Turning section, max_yaw_speed 0.5→0.8 (behavior change)

Fresh-context review + user domain correction caught real defects, all fixed before push:
- [x] (must-fix) doc claimed "MANUAL turns didn't exceed clamp at cruise" — false; MANUAL is unclamped and hit 0.74 rad/s at cruise. Reworded.
- [x] (must-fix) "8.3% pinned at 0.5" was the 05-01 low end — now stated as 8%→39% across deployments (~21% pooled).
- [x] (must-fix) "0.5 is a placeholder / no tuning notes" — wrong; deployment log shows it was reduced 1.5→0.5 during an April steering-reversal debug. Reframed.
- [x] (user correction) steering is VECTORED THRUST, not a rudder → yaw authority scales with thrust (throttle), not boat speed. Re-did the steering-effectiveness analysis as a throttle×deflection grid; rewrote the physics framing.
- [x] (user correction) steering-reversal is a stationary controls-check artifact, orthogonal to max_yaw_speed → 0.8 bump cleared to proceed.

max_yaw_speed 0.5→0.8 is a behavior change: unvalidated for sustained GUIDED cruise turns → flagged for next-deployment validation (#88 controlled sweep).
