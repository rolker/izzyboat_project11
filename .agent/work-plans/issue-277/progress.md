---
issue: 277
---

# Issue #277 — BizzyBoat deployment (2026-06-15 Lake Massabesic)

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-06-16 01:20 +00:00
**By**: Claude Code Agent (Claude Opus 4.8)
**Verdict**: approved

**Branch**: feature/issue-277 at `573f703`
**Mode**: pre-push
**Depth**: Deep (reason: 14 files ≥ 10 and 807 lines ≥ 200)
**Must-fix**: 0 | **Suggestions**: 6

Deep-tier review of a field-deployment import (changes already ran live during the
2026-06-15 survey). Two disjoint-lens fresh-context adversarial passes + static
analysis (shellcheck, ruff + py_compile on launch files, YAML parse). Verified: USB
camera launch extraction preserves node placement (`<ns>/sensors/cameras/usb/usb_camera`,
matching the udp_bridge config) bar the documented 640×360→480 black-buffer fix;
`record_diagnostics` plumbing correct (declared → passed → consumed via `IfCondition` in
bag_recorder_operator_launch.py); included launches (oak_cameras, usb_camera, udp_bridge)
all resolve; CMakeLists install targets exist; YAML period changes consistent with their
comments. gh offline so issue title unresolvable; diffed against local origin/jazzy.

### Findings
- [ ] (suggestion) camera_test script swallows its has-session guard/warning into the logfile — operator re-running interactively sees no terminal feedback (cross-confirmed Lens A+B) — `bizzyboat_project11/scripts/start_tmux_camera_test.bash:21,39-44`
- [ ] (suggestion) bench scripts start their own rmw_zenohd (default port 7447) with only a prose "don't run alongside" guard; add a `pgrep rmw_zenohd` precheck — `bizzyboat_project11/scripts/start_tmux_camera_test.bash:51`, `start_tmux_operator_bridge.bash:41`
- [ ] (suggestion) new `lake_datum: 52.3` has no consumer in this repo; confirm the external chart_datum node reads that exact param name (rclcpp silently ignores a misspelled param); value is provisional per the field log — `bizzyboat_project11/config/bizzyboat.yaml:477`
- [ ] (suggestion) all four OAK segmentation streams moved to full rate on the constrained VPN link (the link the day's log calls saturated); intentional operator scheme but confirm measured bitrate before treating as stable — `bizzyboat_project11/config/bizzyboat.yaml` (VPN block ~267-279)
- [ ] (suggestion) operator_bridge documents `tmux kill-session` (hard kill) vs camera_test's graceful `stop_tmux_project11.bash`; unify on the parameterized stop script; operator_bridge also writes no logfile — `bizzyboat_project11/scripts/start_tmux_operator_bridge.bash:10-11`
- [ ] (suggestion) `oak_starboard_ffmpeg`/`oak_port_ffmpeg` remain in the VPN topics_list while now `period: -1.0` (disabled); drop for clarity — `bizzyboat_project11/config/bizzyboat.yaml:213,217`

Static analysis clean: ruff + py_compile OK (4 launch files), YAML parses, shellcheck
clean except SC2054 on `pull_boat_logs.sh:200` (false positive — comma is rsync flag
syntax inside one bash array element) and SC2034 on untouched lines (out of scope).

No project PRINCIPLES.md/ADRs and no work plan — Plan Drift skipped; governance minimal
(project field-deployment code, no workspace consequence-map triggers).
