---
issue: 289
---

# Issue #289 — BizzyBoat deployment 2026-06-16 (Lake Massabesic standard survey)

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-06-17 10:38 +00:00
**By**: Claude Code Agent (Claude Opus 4.8)
**Verdict**: changes-requested

**Branch**: feature/issue-289 at `d80a2b0`
**Mode**: pre-push
**Depth**: Deep (reason: 635 changed lines ≥ 200; safety-relevant controller PID + field SV feed to the M3 sonar)
**Must-fix**: 1 | **Suggestions**: 9

### Findings
- [ ] (must-fix) Stale temperature used indefinitely — only warns, never reverts to `--fallback`/stops; silent bad-SV feed to M3 if Garmin dies mid-survey (already a wrap-up item; mitigated this run — survey attended + complete) — `bizzyboat_project11/scripts/temp_sound_speed.py:81-94`
- [ ] (suggestion) No guard against double-feed hazard (both scripts / live bridge → same UDP mercat:20003) — `bizzyboat_project11/scripts/static_sound_speed.py` + `temp_sound_speed.py`
- [ ] (suggestion) Non-positive `--rate` silently falls back to 1 Hz instead of erroring — `static_sound_speed.py:56`, `temp_sound_speed.py:69`
- [ ] (suggestion) Temp sanity gate (-5..50 °C) admits values outside Marczak's valid 0–95 °C range — `temp_sound_speed.py:77`
- [ ] (suggestion) No SIGTERM handling — `pkill`/systemd stop bypasses socket + rclpy cleanup — `static_sound_speed.py`, `temp_sound_speed.py`
- [ ] (suggestion) Default `--value 1493.3` is the uncorrected initial value; same-day calibration concludes 1492.3 — `static_sound_speed.py:16`
- [ ] (suggestion) `valeport_frame()` raises on out-of-range `--value` even under `--no-udp` where the frame is unused — `static_sound_speed.py:57`
- [ ] (suggestion) ament_flake8/pep257 D301: use `r"""` for backslash docstrings (×4) — `static_sound_speed.py:2,36`, `temp_sound_speed.py:2,50`
- [ ] (suggestion) ament_flake8 I100: import order — `marine_interfaces` before `sensor_msgs` — `temp_sound_speed.py:40`
- [ ] (suggestion) No unit tests for pure functions `marczak_freshwater` / `valeport_frame` (Test-what-breaks) — `temp_sound_speed.py`, `static_sound_speed.py`

### Notes
- Verified clean (not findings): Marczak 1997 polynomial + offset reproduce the logged numbers; Valeport frame byte-exact to bridge `format_valeport`; topic/type/units assumptions hold; `nav2_overlay.yaml` FollowPath.pid override is complete (all base keys present, only p −20→−13 / d −0.6→−1.2 changed) and deep-merges safely against `nav2_params.base.yaml`; M3 bridge `respawn=True` opens a fresh timestamped `.all` (no truncation); UDP send errors logged, not swallowed.
- shellcheck findings (SC2034/SC2054 in `scripts/pull_boat_logs.sh`) dropped — on pre-existing lines untouched by this diff.
- No work plan (deployment issue); Plan Drift specialist skipped. Copilot Adversarial off (not opted in).
