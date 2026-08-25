---
issue: 458
---

# Issue #458 — Split rosbag recorders into their own launch file

## Issue Review
**Status**: complete
**When**: 2026-08-25 23:08 +00:00
**By**: Claude Code Agent (Claude Sonnet)

**Issue**: #458
**Comment**: (best-effort post follows this entry; not recorded inline)
**Scope verdict**: well-scoped

### Verification of issue claims

Checked against `bizzyboat_project11/launch/perception_launch.py` (current
tree, worktree `feature/issue-458`) and `config/bizzyboat.yaml`:

- `logger` and `sonar_logger` are `Node` actions nested in the same top-level
  `GroupAction` as the DeltaT, M3, and camera chains (lines 246-281). Ctrl-C
  on the `perception` tmux window does take all of them down together, as
  described.
- Both recorders load `config/bizzyboat.yaml` via an explicit
  `PathJoinSubstitution` in their own `parameters=` list, not the group's
  `SetParametersFromFile` — confirmed at lines 250-255 and 269-274.
- `/**/logger` and `/**/sonar_logger` in `config/bizzyboat.yaml` (lines
  655, 853) are double-wildcard node-name matches, independent of namespace
  path — moving the nodes to a new file's own `PushRosNamespace('bizzy')`
  keeps `/bizzy/logger` / `/bizzy/sonar_logger` resolving the same params.
  Recorded topics are all absolute (`/bizzy/...`, `/diagnostics`), so the
  namespace move doesn't touch what's captured.
- `datetime_str` (line 42) is shared as the default for both
  `log_subdirectory` and `sonar_log_subdirectory` — confirmed, and its
  per-launch-invocation freshness is what makes relaunch-without-crash work
  as claimed.
- `usb_camera_launch.py` documents itself as an earlier extraction from
  `perception_launch.py` for an analogous reason (letting a standalone test
  launch reuse it) — a working precedent for this kind of split in this
  same file, using the same `PushRosNamespace` pattern the issue proposes.
- `scripts/start_tmux_project11.bash` currently has 4 windows (`zenoh`,
  `core`, `perception`, `nav`); the `perception` window's inline comment
  reads "Perception: cameras, sonar, logging" (line 49) — accurate today,
  stale after the split.
- No test or CI file references `logger`/`sonar_logger` node names or
  `perception_launch.py`'s recorder section; the only other files that
  mention `perception_launch.py` (`usb_camera_launch.py`,
  `camera_test_launch.py`) do so for camera-namespace parity, unaffected by
  this change.

### Scope Assessment

**Well-scoped?** Yes — a mechanical move of two already-self-contained
nodes plus their five arguments into a new file, one tmux window added, one
existing launch file trimmed. Fits a single PR.

**Right repo?** Yes — `unh_echoboats_project11` is the project repo that
owns BizzyBoat's launch structure; this is domain-specific launch
reorganization, not generic workspace tooling.

**Dependencies**: None blocking. The issue cites `unh_marine_autonomy`
`docs/launch_manager.md` and `rolker/unh_marine_autonomy#327` (marked
complete) as motivating context only — this issue is explicitly scoped to
stand on its own regardless of whether that broader manager is ever built.

### Principle Alignment

| Principle | Status | Notes |
|---|---|---|
| Human control and transparency | OK | Independently start/stoppable logging directly serves operator control; new `logger:=`/`sonar_logger:=` args keep the split configurable. |
| Capture decisions, not just implementations | OK | Issue itself is a well-reasoned design record (cites the "clean cut" rationale, the `m3_all` sibling-dir workaround, and the upstream design doc). |
| A change includes its consequences | Watch | Scope item 3 covers adding the `logging` tmux window but doesn't mention updating the now-stale `# Perception: cameras, sonar, logging` comment on the existing `perception` window (`start_tmux_project11.bash:49`). Small, but it's a doc-drift instance of exactly this principle. |
| Only what's needed | OK | Verbatim node move, no speculative abstraction; explicitly declines to touch `core_launch.py` or `bizzyboat.yaml` reorganization (Non-goals section). |
| Improve incrementally | OK | Explicitly framed as "first concrete slice," useful standalone. |
| Test what breaks | Watch | Verification section is entirely manual (tmux + `ros2 node list` + `ros2 bag info` comparison). Reasonable for launch-file glue, but no automated regression check is proposed if this is meant to compose with the larger launch-manager effort later. |
| Workspace vs. project separation | OK | Correctly scoped to the project repo; no workspace-repo changes implied. |

### ADR Applicability

| ADR | Triggered | Notes |
|---|---|---|
| 0008 — Follow ROS 2 Official Conventions | Yes | New launch file; the proposed structure (args, `PushRosNamespace`, `GroupAction`) matches the conventions already used throughout this package, including the `usb_camera_launch.py` precedent for exactly this kind of extraction. No deviation flagged. |
| Others (0001-0007, 0009-0018) | No | No new agent-facing process, script, or workspace-repo change involved. |

### Consequences

- `scripts/start_tmux_project11.bash:49`'s `# Perception: cameras, sonar,
  logging` comment should be updated (drop "logging") alongside adding the
  new `logging` window's own comment, so the window map stays accurate —
  not called out explicitly in the issue's Scope section.
- No package README/API doc changes needed: topics, parameters, and
  behavior are unchanged, only file location and process boundary.

### Recommendations

- Update the `perception` window's inline comment in
  `start_tmux_project11.bash` when adding the `logging` window (see above).
- Consider echoing `usb_camera_launch.py`'s "extracted from
  perception_launch.py, edit here not there" style comment in the new
  `logging_launch.py`, for the same discoverability reason.

### Actions
- [ ] Update the stale `# Perception: cameras, sonar, logging` tmux-window comment when the `logging` window is added (start_tmux_project11.bash:49).
- [ ] Consider a short "moved from perception_launch.py" note in the new logging_launch.py for discoverability, mirroring usb_camera_launch.py's precedent.
