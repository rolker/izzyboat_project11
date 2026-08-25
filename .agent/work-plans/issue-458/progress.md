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

## Plan Authored
**Status**: complete
**When**: 2026-08-25 23:10 +00:00
**By**: Claude Code Agent (Claude Sonnet)

**Plan**: `.agent/work-plans/issue-458/plan.md` at `bfb8606`
**Branch**: feature/issue-458 at `bfb8606`
**Phases**: single

### Open questions
- [ ] Which `IfCondition` idiom this package's Jazzy launch files use for boolean args — confirm against an existing example (e.g. `core_launch.py`/`nav_launch.py`) during implementation.

## Plan Review
**Status**: complete
**When**: 2026-08-25 23:13 +00:00
**By**: Claude Code Agent (Claude Opus)

**Plan**: `.agent/work-plans/issue-458/plan.md` at `bfb8606`
**PR**: PR-less (`--issue 458`, fresh-context sub-agent in worktree `feature/issue-458`)
**Verdict**: changes-requested

**Independence**: independent. The `## Plan Authored` entry's agent-name portion
("Claude Code Agent") matches `$AGENT_NAME`, which the skill's name-based
heuristic would read as an author self-review — but this is a separate
fresh-context dispatch on a different model (Sonnet authored, Opus reviewed),
so the annotation is deliberately omitted. Every agent in this workspace shares
one `$AGENT_NAME`, so that heuristic cannot discriminate here.

**Note**: `gh` is unauthenticated in this worktree, so the issue body and any
`review-issue` comment could not be re-fetched from GitHub. The review used the
`## Issue Review` entry above (which records the issue's claims and findings in
detail) plus direct verification against the working tree.

### Findings
- [ ] (must-fix) Removing `sonar_log_directory` breaks the M3 `.all` archive — `kongsberg_em_bridge.save_all_dir` still consumes it at `perception_launch.py:124-126` — `plan.md:52-54`
- [ ] (must-fix) `sonar_log_directory` becomes shared across two launch files; the `<base>/m3_all` collision-free-sibling invariant (`perception_launch.py:114-123`) silently breaks if only one launch gets an override — not in the Consequences table — `plan.md:110-114`
- [ ] (must-fix) `docs/bizzyboat_operator_manual.md:291` ("Perception ... cameras, sonar logging") and its 4-step boat bring-up list go stale; plan asserts the tmux comment is the only invalidated doc — `plan.md:118-123`
- [ ] (suggestion) `bag_recorder_operator_launch.py` is the closer in-repo precedent than `usb_camera_launch.py` — carries the rosbag2 SIGTTOU / clean-flush lessons (`--disable-keyboard-controls`, `sigterm_timeout=15`) that bear directly on #458's "Ctrl-C leaves a readable bag" goal — `plan.md:28-30`
- [ ] (suggestion) Close the Open Question now: `core_launch.py:117-130` + `:456,:500` and `bag_recorder_operator_launch.py:98` both use `DeclareLaunchArgument(default_value='true')` + `IfCondition(LaunchConfiguration(...))` — no `PythonExpression` needed — `plan.md:129-136`

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-08-25 23:38 +00:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: changes-requested

**Branch**: feature/issue-458 at `7561482`
**Mode**: pre-push
**Depth**: Deep (reason: 289 changed lines in code/docs, 619 including the plan docs — over the 200-line Deep threshold)
**Must-fix**: 3 | **Suggestions**: 6
**Round**: 1 | **Ship**: continue — two of the three must-fixes are shutdown-path data-integrity risks on the boat's data of record, both flagged independently by two adversarial passes.

**Note**: `git fetch origin` failed (host key verification / offline); the diff is against the local `origin/jazzy` ref, which may be stale. No `.agents/review-context.yaml` exists in this repo, so the review used `.agents/README.md` only.

### Findings
- [x] (must-fix) `stop_tmux_project11.bash` SHUTDOWN_TIMEOUT=10 s is now shorter than the recorders' new 15+5 s shutdown grace, so `kill-session` can SIGHUP a finalizing mcap — `bizzyboat_project11/scripts/stop_tmux_project11.bash:11`
- [ ] (must-fix) Recorders leave `record.disable_keyboard_controls` false with `emulate_tty=True`, so a stray SPACE in the now operator-facing logging window silently pauses a bag — `bizzyboat_project11/launch/logging_launch.py:116,141`
- [ ] (must-fix) `.agents/README.md` still describes `perception_launch.py` as doing the logging; the agent-facing bring-up map does not know `logging_launch.py` exists — `.agents/README.md:82-84`
- [ ] (suggestion) No pytest for `logging_launch.py`, though the package registers `test_core_launch.py` / `test_operator_core_launch.py` for exactly this wiring; the plan's claim that no launch-file test exists in this package is factually wrong — `bizzyboat_project11/CMakeLists.txt:33-52`
- [ ] (suggestion) Neither recorder sets `output`, so the dedicated logging window shows nothing — not even a failed start — `bizzyboat_project11/launch/logging_launch.py:101,126`
- [ ] (suggestion) Operator manual gains no "confirm recording is running" step, and the decoupling removes the old "perception up ⇒ bags recording" invariant — `docs/bizzyboat_operator_manual.md:293-297`
- [ ] (suggestion) Shutdown step still says "Ctrl-C in each window" with no ordering; logging should be stopped last, and `stop_tmux_project11.bash` should be named — `docs/bizzyboat_operator_manual.md:107-109`
- [ ] (suggestion) A mid-deployment `sonar_log_directory:=` relocation now leaves the M3 `.all` archive at the old root; the two-argument split is documented only in code comments — `bizzyboat_project11/launch/perception_launch.py:22-42`
- [ ] (suggestion) The four removed perception launch args are now silently ignored if still passed (ros2launch does not validate top-level args), and `m3_all_directory` is undocumented outside the launch file — `bizzyboat_project11/launch/perception_launch.py:22-42`
