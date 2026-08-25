# Plan: Split rosbag recorders into their own launch file

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/458

## Context

`bizzyboat_project11/launch/perception_launch.py` nests `logger` and
`sonar_logger` (`rosbag2_transport recorder` nodes) inside the same
top-level `GroupAction` as the DeltaT, M3, and camera chains (lines 62-283).
The tmux `perception` window is the only handle to any of it, so stopping
recording means stopping cameras and sonar too.

Both recorders are already self-contained: they load
`config/bizzyboat.yaml` by explicit `PathJoinSubstitution` path in their
own `parameters=` list (not the group's `SetParametersFromFile`), and they
record absolute topic names, so a namespace push only affects node names.
`config/bizzyboat.yaml`'s `/**/logger` / `/**/sonar_logger` param overrides
are double-wildcard node-name matches, independent of namespace path — a
new file's own `PushRosNamespace('bizzy')` keeps `/bizzy/logger` and
`/bizzy/sonar_logger` resolving the same params. `usb_camera_launch.py` is
a working precedent in this same file for exactly this kind of extraction
(same `PushRosNamespace` pattern, same "edit here not there" framing).

## Approach

1. **Create `bizzyboat_project11/launch/logging_launch.py`** — new file,
   modeled on `usb_camera_launch.py`'s extraction-comment style:
   - Move the `namespace`, `log_directory`, `log_subdirectory`,
     `sonar_log_directory`, `sonar_log_subdirectory` argument
     declarations and the `datetime_str` computation verbatim from
     `perception_launch.py`.
   - Add two new booleans, `logger` and `sonar_logger`, both
     `default_value='true'`, via `DeclareLaunchArgument` +
     `IfCondition(PythonExpression(...))` (or `IfCondition(LaunchConfiguration(...))`
     — Jazzy's `IfCondition` accepts a launch-configuration substitution
     directly when its resolved value is `'true'`/`'false'`, matching the
     convention already used for other boolean args in this package; verify
     against an existing boolean-arg example in `core_launch.py` or
     `nav_launch.py` before implementing and reuse the same idiom).
   - Wrap the whole `GroupAction` in `PushRosNamespace(namespace)`, mirroring
     the top-level push in `perception_launch.py`.
   - Move both `Node(...)` blocks verbatim, gating `logger` with
     `condition=IfCondition(logger_enabled)` and `sonar_logger` with
     `condition=IfCondition(sonar_logger_enabled)`.
   - Add a short module comment (`usb_camera_launch.py` style) noting this
     was extracted from `perception_launch.py` so recording can be
     started/stopped independently of perception, per #458.

2. **Trim `perception_launch.py`** (revised after Plan Review — see
   "Plan Review response" below):
   - Remove the `log_directory`, `log_subdirectory`, `sonar_log_directory`,
     `sonar_log_subdirectory` `DeclareLaunchArgument`s, the `datetime_str`
     computation, and the now-unused `datetime` import.
   - Remove the two `Node(...)` blocks for `logger` and `sonar_logger`.
   - **Add a new `m3_all_directory` argument** for the M3 raw Kongsberg
     `.all` archive, which still consumes a directory here via
     `kongsberg_em_bridge.save_all_dir`. It defaults to
     `$P11_SONAR_LOG_DIR/m3_all` — the same path as before — so behaviour is
     unchanged, but the `.all` archive no longer shares an argument with the
     sonar bag across two launch files.
   - Correct the `save_all_dir` comment: it read as though the archive is
     always recording. `kongsberg_em_bridge`'s `record_on_start` defaults
     **false** (`node.py:202-205`, marine_tools#54), so the `.all` archive is
     opt-in and writes nothing until armed via the bridge's `set_recording`
     service. The comment now says so, and warns that any override must stay
     a *sibling* of the sonar bag directory.
   - Leave `namespace_arg` and everything else untouched — the namespace
     arg is still needed for the sensor/camera groups.

3. **Update `bizzyboat_project11/scripts/start_tmux_project11.bash`**:
   - Add a `logging` tmux window after `perception` (before `nav`), same
     env-sourcing pattern as the other windows, running
     `ros2 launch bizzyboat_project11 logging_launch.py`.
   - Update the `perception` window's inline comment from
     `# Perception: cameras, sonar, logging` to
     `# Perception: cameras, sonar` (drop "logging" — it now runs in its
     own window), and add a `# Logging: rosbag2 recorders (independently
     stop/restartable)` comment above the new window.

4. **Manual verification** (per issue's Verification section — no
   automated test exists for tmux/launch-file glue in this package today,
   consistent with how `usb_camera_launch.py`'s prior extraction was
   verified):
   - Boat bringup starts all four windows; `ros2 node list` shows
     `/bizzy/logger` and `/bizzy/sonar_logger`.
   - `ros2 bag info` on both bags shows the same topic sets as before the
     split.
   - Ctrl-C in `logging` stops both recorders, leaves `perception`/`core`/
     `nav` running; closed bags open cleanly.
   - Relaunching `logging` produces a new timestamped directory and
     records again.
   - `logger:=false` and `sonar_logger:=false` each independently disable
     their recorder while leaving the other running.

## Files to Change

| File | Change |
|------|--------|
| `bizzyboat_project11/launch/logging_launch.py` | New file: `logger` + `sonar_logger` nodes, their 5 args, `PushRosNamespace`, new `logger:=`/`sonar_logger:=` booleans. |
| `bizzyboat_project11/launch/perception_launch.py` | Remove the 2 recorder nodes and their 4 log-directory args + `datetime_str`. |
| `bizzyboat_project11/scripts/start_tmux_project11.bash` | Add `logging` window; update `perception` window's stale comment. |
| `docs/bizzyboat_operator_manual.md` | Bring-up list (line 291) becomes 5 steps: perception loses "logging", new **Logging** step documents the independent stop/restart and the `logger:=`/`sonar_logger:=` arguments. |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| Human control and transparency | Directly serves operator control — logging becomes stop/restartable without taking down perception; `logger:=`/`sonar_logger:=` give finer-grained control (e.g. stop sonar bags, keep diagnostics recording), matching the issue's stated example. |
| Only what's needed | Verbatim node move, no speculative abstraction beyond the two booleans the issue explicitly asks for. Explicitly does not touch `core_launch.py`, `bizzyboat.yaml`, or the M3 `.all` archive (issue's declared non-goals / known gap). |
| A change includes its consequences | Includes the `start_tmux_project11.bash` comment fix flagged by the Issue Review as missing from the issue's own Scope section. |
| Test what breaks | No automated launch-file test exists in this package; verification stays manual (tmux + `ros2 node list` + `ros2 bag info`), matching the issue's own Verification section and this package's existing practice for launch-file changes. |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| 0008 — Follow ROS 2 Official Conventions | Yes | New launch file follows the existing package convention (`DeclareLaunchArgument`, `PushRosNamespace`, `GroupAction`) and directly mirrors the `usb_camera_launch.py` extraction precedent already in this package. |
| Others | No | No workspace-repo or agent-process change involved; project-repo-local launch reorganization only. |

## Consequences

| If we change... | Also update... | Included in plan? |
|---|---|---|
| Recorder nodes move out of `perception_launch.py` | `start_tmux_project11.bash`'s stale `perception` window comment | Yes — step 3 |
| `perception_launch.py` loses 4 launch args | Any external caller passing `log_directory=`/`log_subdirectory=`/etc. to `perception_launch.py` | No known callers found (`usb_camera_launch.py`, `camera_test_launch.py` only include it for camera namespace parity, not recorder args) — no follow-up needed |
| New `logging_launch.py` exists | `logging_launch.py` itself needs a module docstring, not package docs | Yes — step 1's extraction comment |

## Documentation & Instruction Impact

- **Stale docs** (must land in this PR): `start_tmux_project11.bash`'s
  `# Perception: cameras, sonar, logging` inline comment (step 3) — this is
  the only doc the diff itself invalidates. No package README/API doc
  changes needed: topics, parameters, and node names are unchanged, only
  file location and process boundary (per Issue Review's Consequences
  section).
- **Agent-instruction candidates**: None — this is a mechanical,
  self-contained launch-file split with a clear in-package precedent
  (`usb_camera_launch.py`); it doesn't surface a new pattern or pitfall
  worth generalizing into `.agent/knowledge/` or `.agents/README.md`.

## Open Questions

*(none remaining)*

- ~~Which `IfCondition` idiom this package's Jazzy launch files use for
  boolean args~~ — **resolved**: `core_launch.py:490,:500` and
  `bag_recorder_operator_launch.py:98` both use
  `DeclareLaunchArgument(default_value='true')` +
  `IfCondition(LaunchConfiguration(...))`, no `PythonExpression`. Implemented
  that way.

## Plan Review response

The Plan Review (verdict: changes-requested) raised three must-fixes and two
suggestions. Resolution:

1. **`sonar_log_directory` still consumed by the `.all` archive** — real, and
   the fix is step 2's new `m3_all_directory` argument. Perception no longer
   references `sonar_log_directory` at all.
2. **Shared argument across two launch files breaks the sibling invariant** —
   dissolved rather than mitigated: the two launch files now own separate
   arguments, so there is nothing to diverge. Operator direction (2026-08-25)
   was that the `.all` archive is a debugging artifact, off by default, and
   should be handled separately from the sonar bag.
3. **`docs/bizzyboat_operator_manual.md:291` goes stale** — fixed; the
   bring-up list gains a Logging step.
4. *(suggestion)* **`bag_recorder_operator_launch.py` is the closer
   precedent** — adopted: both recorders now carry `sigterm_timeout='15'` /
   `sigkill_timeout='5'`, so mcap finalization completes after the SIGINT,
   matching the operator-side recorder. This bears directly on the issue's
   "Ctrl-C leaves a readable bag" goal.
5. *(suggestion)* **Close the `IfCondition` open question** — done, above.

**Correction carried into the implementation**: the issue body's "Known gap"
says stopping the logging group leaves the M3 `.all` archive "writing ~200 MB
segments". That is wrong — `record_on_start` defaults false, so the archive
writes nothing unless armed via `set_recording`. The stale comment in
`perception_launch.py` that implied otherwise is corrected in step 2, and the
issue body should be corrected too.

## Estimated Scope

Single PR.
