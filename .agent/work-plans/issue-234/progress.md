---
issue: 234
---

# Issue #234 — Wire Garmin GCV-20 sidescan into BizzyBoat (launch wrapper + recording)

## Integrated Review
**Status**: complete
**When**: 2026-06-07 22:04 -0400
**By**: Claude Code Agent (Claude Opus 4.8 (1M context))

**PR**: #236 at `942606d`
**Sources**: 2 Copilot reviews (@ `361c834`, @ `942606d`)
**Cross-source confirmations**: 0
**CI**: copilot check pass (no build gate — config/launch repo)

### Findings
- [x] (must-fix, Copilot) debug_raw passed as LaunchConfiguration (string) but node declares it bool -> node fails on startup; crash-loops now that sidescan is on-by-default — wrap in ParameterValue(value_type=bool) — `bizzyboat_project11/launch/sidescan_launch.py`
- [x] (should-fix, Copilot) sound_speed_topic hard-coded /bizzy/...; add a namespace arg, derive the SV topic from it, pass namespace from core_launch — `sidescan_launch.py`, `core_launch.py`
- [x] (doc, Copilot) PR #236 body still says it vendors mercat/* scripts; they were de-vendored to marine_tools — update the PR description
- [x] (defensive, Copilot) install_proxy_service.ps1 NSSM single-string args -> tracked in marine_tools#22 (merged code, needs Windows verification)

### False positives
- (Copilot x3) sidescan default 'true' / "on by default" comments contradict issue's opt-in — superseded by explicit user instruction to make sidescan on by default; code + comments are consistent and correct.
