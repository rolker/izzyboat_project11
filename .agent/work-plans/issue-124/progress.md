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

## §2 completion — course-keeping (XTE)
**When**: 2026-05-25 13:30
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))

Added xte.py + Course-keeping section (PR #172). Track-holding ~0.13 m RMS
(consistent across 3 deployments, matches 04-24 "sub-meter"); XTE-vs-plan
~0.4–0.8 m. Self-reviewed (two bugs found+fixed during dev: pandas `.mode`
attribute shadowing, and plan-matching contamination → switched headline to
the robust line-fit-residual metric). §2 now complete (max-reverse + mid-PWM
curve spun to #88).

## External Review
**Status**: complete
**When**: 2026-05-25 16:25 -04:00
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))

**PR**: #172 at `da6ec14`
**Reviews**: 5 (all Copilot bot), 22 inline + 2 conversation (author's own — no action)
**CI**: no real CI (only copilot-pull-request-reviewer marker = success)
**Verdict**: 6 valid (all doc/tooling-accuracy, none touch analysis conclusions); 3 false-positive/addressed; several optional perf/robustness

### Actions
- [ ] (#1) "sub-decimeter" wording wrong for ~0.13 m RMS — fix performance.md:25 + hardware.md:303 ("decimeter-scale")
- [ ] (#2) turning.py:134 output prints stale "@0.8 rad/s" — change to 1.0 (the chosen cap)
- [ ] (#3) turning.py:4 docstring frames max_yaw_speed=0.5 as current — note 0.5-during-data → 1.0
- [ ] (#4) README:61/65 — turning.py (mavros/state) + xte.py (plan+odom) need the full deployment DB; not covered by the *_nav.db recipe/run examples
- [ ] (#5) narrow `except Exception: pass` (dynamics.py:178, dynamics_extra.py:99) to curve_fit RuntimeError/ValueError
- [ ] (#6) progress.md turning-round entry says 0.5→0.8 (final 1.0) — add correcting note
- [ ] (optional) perf/robustness: xte.py vectorization; dynamics_extra DB-existence guard/hardcoded names; turning.py velocity_body guard
