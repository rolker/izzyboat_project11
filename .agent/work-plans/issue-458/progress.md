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
- [x] (must-fix) Recorders leave `record.disable_keyboard_controls` false with `emulate_tty=True`, so a stray SPACE in the now operator-facing logging window silently pauses a bag — `bizzyboat_project11/launch/logging_launch.py:116,141`
- [x] (must-fix) `.agents/README.md` still describes `perception_launch.py` as doing the logging; the agent-facing bring-up map does not know `logging_launch.py` exists — `.agents/README.md:82-84`
- [x] (suggestion) No pytest for `logging_launch.py`, though the package registers `test_core_launch.py` / `test_operator_core_launch.py` for exactly this wiring; the plan's claim that no launch-file test exists in this package is factually wrong — `bizzyboat_project11/CMakeLists.txt:33-52`
- [x] (suggestion) Neither recorder sets `output`, so the dedicated logging window shows nothing — not even a failed start — `bizzyboat_project11/launch/logging_launch.py:101,126`
- [x] (suggestion) Operator manual gains no "confirm recording is running" step, and the decoupling removes the old "perception up ⇒ bags recording" invariant — `docs/bizzyboat_operator_manual.md:293-297`
- [x] (suggestion) Shutdown step still says "Ctrl-C in each window" with no ordering; logging should be stopped last, and `stop_tmux_project11.bash` should be named — `docs/bizzyboat_operator_manual.md:107-109`
- [x] (suggestion) A mid-deployment `sonar_log_directory:=` relocation now leaves the M3 `.all` archive at the old root; the two-argument split is documented only in code comments — `bizzyboat_project11/launch/perception_launch.py:22-42`
- [x] (suggestion) The four removed perception launch args are now silently ignored if still passed (ros2launch does not validate top-level args), and `m3_all_directory` is undocumented outside the launch file — `bizzyboat_project11/launch/perception_launch.py:22-42`

## Implementation
**Status**: complete
**When**: 2026-08-25 23:46 +00:00
**By**: Claude Code Agent (Claude Opus)

**Branch**: feature/issue-458 at `177e03e`
**Addressed**: `## Local Review (Pre-Push)` (2026-08-25 23:38 +00:00, branch `feature/issue-458` at `7561482`) — 3 must-fix, 6 suggestions, all open
**Commits**: `ef81379`, `57061e8`, `6451ddf`, `d182e3c`, `a5e528a`, `a83e99a`, `e04db45`, `177e03e`

### Actions
- [x] (must-fix) `SHUTDOWN_TIMEOUT` 10 s → 25 s, with a comment tying it to the recorders' `sigterm_timeout=15` + `sigkill_timeout=5` — `bizzyboat_project11/scripts/stop_tmux_project11.bash:11-17` (`ef81379`)
- [x] (must-fix) Both recorders now set `record.disable_keyboard_controls: True`, so a stray SPACE in the operator-facing logging window cannot pause a bag — `bizzyboat_project11/launch/logging_launch.py:105-123,138-149` (`57061e8`)
- [x] (must-fix) `.agents/README.md` bring-up chain now names `logging_launch.py` as the recorders' home and says explicitly that they are *not* in `perception_launch.py` — `.agents/README.md:82-90` (`6451ddf`)
- [x] (suggestion) Added `test/test_logging_launch.py` (18 tests, registered in `CMakeLists.txt`) covering both-recorders-by-default, independent disable, keyboard-pause disabled, `output='both'`, per-recorder output dirs, distinct bag dirs, the shared config file, the `m3_all` sibling invariant, the moved-argument guard, and the stop-script-outwaits-the-grace cross-file invariant; corrected the plan's wrong "no automated launch-file test exists in this package" claim in both the step-4 note and the Test-what-breaks row — `bizzyboat_project11/test/test_logging_launch.py`, `bizzyboat_project11/CMakeLists.txt:52-57`, `.agent/work-plans/issue-458/plan.md:81-90,113` (`d182e3c`, `177e03e`)
- [x] (suggestion) Both recorders set `output='both'`, so the dedicated logging window shows start-up and failures instead of nothing — `bizzyboat_project11/launch/logging_launch.py:124-131,150-158` (`a5e528a`)
- [x] (suggestion) New **Confirming recording is running** section in the operator manual: check the `logging` window, `ros2 node list | grep -E '/bizzy/(sonar_)?logger'`, confirm a fresh bag dir is growing, and how to restart recording mid-deployment — it states outright that the split removed the "perception up ⇒ bags recording" invariant — `docs/bizzyboat_operator_manual.md:320-351` (`a83e99a`)
- [x] (suggestion) Shutdown step now names `~/stop_tmux_project11.bash` and, for a manual shutdown, says to stop `logging` **last** and why (~20 s of mcap finalization) — `docs/bizzyboat_operator_manual.md:105-115` (`e04db45`)
- [x] (suggestion) New **Sending the data somewhere else** subsection documents the two-launch-file split as a table (bag dirs vs `m3_all_directory`), warns that restarting `logging` with `sonar_log_directory:=` moves the bag but not the still-running `.all` archive, and states the sibling-directory rule outside code comments — `docs/bizzyboat_operator_manual.md:352-378` (`177e03e`)
- [x] (suggestion) `perception_launch.py` now rejects the four moved recorder arguments with an `OpaqueFunction` preflight (same idiom as `core_launch.py`'s `check_ellipsoidal_fix_available`) that names `logging_launch.py` and shows the corrected command line, rather than letting `ros2 launch` silently ignore them; `m3_all_directory` is now documented in both `.agents/README.md` and the operator manual — `bizzyboat_project11/launch/perception_launch.py:18-63,66-71`, `.agents/README.md:82-95` (`177e03e`)

### Deferred actions
None — all nine findings were actioned.

### Verification
- `pytest test/test_logging_launch.py` — 18 passed.
- `pytest test/` — 241 passed, 8 failed; all 8 failures are in `test_operator_core_launch.py` and reproduce on a clean stash of this branch (they need the package installed / a specific hostname). Untouched by this pass.
- `bash -n scripts/stop_tmux_project11.bash` — clean.
- `flake8` on the three changed Python files — only the `D1xx`/`I1xx`/`Q003` classes this package already carries in its sibling launch files and tests; no new class of warning introduced. (The package registers no `ament_flake8` test.)
- Pre-commit hooks ran on every commit; none bypassed.

### Not verified here
On-boat behaviour still needs the hardware: that the `logging` tmux window comes up and prints recorder start-up, that `ros2 bag info` shows the same topic sets as before the split, and that a Ctrl-C in `logging` leaves the other windows running. That was already the plan's manual-verification list and is unchanged by this pass.

### Next step
`review-code` (re-review) — hand off to a fresh-context sub-agent:

    .agent/scripts/dispatch_subagent.sh --mode in-process --issue 458 --skill review-code


## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-08-25 23:56 +00:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: changes-requested

**Branch**: feature/issue-458 at `93daa76`
**Mode**: pre-push
**Depth**: Deep (reason: 981 changed lines / 10 files — over both the 200-line and 10-file thresholds; `.agents/README.md` is also a project-repo override trigger)
**Must-fix**: 2 | **Suggestions**: 14
**Round**: 2 | **Ship**: recommended — must-fix is flat at 2 (down from 3), both are precise mechanical fixes (a test that checks the wrong node, a stale count in a README); no specialist found a correctness defect in the shipped launch/script code this round.

**Specialists**: Static Analysis, Governance, Plan Drift, Claude Adversarial x2 (Lens A + Lens B). Copilot and Local Adversarial off (default).
**Note**: `git fetch origin` failed (host key verification / offline); diff is against the local `origin/jazzy` ref, which may be stale. No `.agents/review-context.yaml` exists in this repo, so the review used `.agents/README.md` only.

### Findings
- [x] (must-fix) `test_the_stop_script_outwaits_the_recorder_shutdown_grace` reads the grace from `logger` only, though its docstring says "the recorders" and it is the sole guard on the cross-file SHUTDOWN_TIMEOUT invariant; mutation-verified (sonar_logger sigterm_timeout='60' leaves all 18 tests green) — `bizzyboat_project11/test/test_logging_launch.py:207-218`
- [x] (must-fix) `.agents/README.md` still says "Six pytest suites, all registered in CMakeLists.txt" — this PR registers a seventh (6 bullets vs 7 `ament_add_pytest_test` calls) — `.agents/README.md:141`
- [x] (suggestion) Nothing pins `PushRosNamespace(namespace)`; mutation-verified — deleting it leaves all 18 tests green while the recorders would come up as `/logger` / `/sonar_logger`, breaking the manual's own verification grep — `bizzyboat_project11/launch/logging_launch.py:98`
- [x] (suggestion) The moved-argument guard is one-directional: `m3_all_directory:=` passed to `logging_launch.py` (the natural mistake from the new three-row relocation table) is silently ignored and the `.all` archive stays on the internal disk — cross-pass confirmed (Lens A + Lens B) — `bizzyboat_project11/launch/logging_launch.py`, `docs/bizzyboat_operator_manual.md:369-371`
- [x] (suggestion) Both subdirectory defaults share one `datetime_str`, so pointing `P11_LOG_DIR` and `P11_SONAR_LOG_DIR` at one disk (which the manual newly invites) gives both recorders an identical `storage.uri` and one dies at start; pre-existing but newly advertised — cross-pass confirmed — `bizzyboat_project11/launch/logging_launch.py:74-85`
- [x] (suggestion) The confirm-recording step cannot detect the double-start the split newly makes cheap: it says "only one means the other died" and never that more than one of each halves the disk budget into two half-authoritative datasets — `docs/bizzyboat_operator_manual.md:347-352`
- [x] (suggestion) Tests resolve `P11_LOG_DIR` / `P11_SONAR_LOG_DIR` / `OVERRIDE_LAUNCH_PROCESS_OUTPUT` from the ambient environment; verified both failure modes locally — isolate with `monkeypatch.delenv` — `bizzyboat_project11/test/test_logging_launch.py:47-71,135`
- [x] (suggestion) `SHUTDOWN_TIMEOUT` is a per-window sequential budget (worst case ~50s → ~150s though only `logging` needs 20+s), and on expiry the script warns then `kill-session`s anyway, so the truncation the new comment says it prevents still happens 15s later — 3-way confirmed — `bizzyboat_project11/scripts/stop_tmux_project11.bash:17,37-56,82`
- [x] (suggestion) The manual says the stop script "Ctrl-Cs every window in order" then says to stop `logging` last, but the script Ctrl-Cs every non-zenoh window in one loop — cross-pass confirmed — `docs/bizzyboat_operator_manual.md:107,112-115`
- [x] (suggestion) `_ExecuteLocal__output` / `__sigterm_timeout` / `__sigkill_timeout` / `__emulate_tty` all have public properties (verified against the installed `launch`); only `_Node__node_name` needs the mangled form — `bizzyboat_project11/test/test_logging_launch.py:126,135,212-213`
- [x] (suggestion) Neither recorder sets `respawn`, and `storage.uri` frozen at launch time forecloses it (a respawn would crash-loop on "Bag directory already exists") — recovery needs a per-process subdirectory — `bizzyboat_project11/launch/logging_launch.py:101-160`
- [x] (suggestion) The moved-arg guard trips on presence in `launch_configurations`, not on the arg being user-supplied, so an including bring-up that declares `log_directory` would abort the whole boat — `bizzyboat_project11/launch/perception_launch.py:43-44`
- [x] (suggestion) The "parent directory would race the bag" rule is not real — rosbag2 aborts only on the exact `storage.uri` pre-existing — so `assert all_dir != sonar_uri.parent` will fail CI for a legitimate future config — `bizzyboat_project11/launch/perception_launch.py:157-165`, `bizzyboat_project11/test/test_logging_launch.py:177`
- [x] (suggestion) Plan's Documentation & Instruction Impact still says the tmux comment is "the only doc the diff invalidates" and "Agent-instruction candidates: None"; Files to Change omits the four files added since Round 1 — `.agent/work-plans/issue-458/plan.md:103-110,136-148`
- [x] (suggestion) Five launch args carry no `description=`, though four are now the documented operator handle for relocating the boat's data of record — `bizzyboat_project11/launch/logging_launch.py:47,65,74,85,90`
- [x] (suggestion) "Pass `log_subdirectory:=/sonar_log_subdirectory:=` to override" reads as one path-like token; it means two separate arguments — `bizzyboat_project11/launch/logging_launch.py:31`

### Instruction-update candidate (proposal only — not applied)
- [x] (deferred: targets `.agent/knowledge/` in the workspace repo, outside this worktree; recorded in the plan's Documentation & Instruction Impact for the host to apply) "Moving a launch argument between launch files fails silently" → `.agent/knowledge/ros2_development_patterns.md`. `ros2 launch` does not validate top-level `name:=value`, so a stale habit or runbook line gives a clean bring-up with the wrong behaviour and no message anywhere. Leave a preflight `OpaqueFunction` in the old file that inspects `context.launch_configurations` and raises, naming the new file. Reference implementation: `perception_launch.py:18-63`, tested at `test_logging_launch.py:178-201`. Verified absent from the knowledge docs today.

### Pre-merge (not a code finding)
- [x] (deferred: `ci_local.sh` needs docker, which is not available in this worktree — the host must run the full-scope attestation before merge) ADR-0018: no `git notes --ref=ci-local` attestation on HEAD; full-scope local CI verification required before merge.

## Implementation
**Status**: complete
**When**: 2026-08-26 00:09 +00:00
**By**: Claude Code Agent (Claude Opus)

**Branch**: feature/issue-458 at `bf17d48`
**Addressed**: `## Local Review (Pre-Push)` (2026-08-25 23:56 +00:00, branch `feature/issue-458` at `93daa76`) — 2 must-fix, 14 suggestions, plus an instruction-update candidate and the ADR-0018 pre-merge item; all 18 open
**Commits**: `4631637`, `1a6820a`, `f366062`, `874258f`, `2d8245b`, `0059c7f`, `2f19eb5`, `124c4ff`, `e3dade8`, `65b6974`, `f8c0b6c`, `f01c54a`, `e8ebd38`, `409f927`, `bf17d48`

### Actions
- [x] (must-fix) The stop-script grace test is now parametrized over both recorders, so `sonar_logger`'s `sigterm_timeout` is covered too; re-running the review's mutation (`sonar_logger sigterm_timeout='60'`) now fails — `bizzyboat_project11/test/test_logging_launch.py:317-334` (`4631637`)
- [x] (must-fix) `.agents/README.md` says **Seven** pytest suites and lists `test_logging_launch.py` alongside the other six; bullet count now matches the seven `ament_add_pytest_test` calls — `.agents/README.md:141,174-181` (`1a6820a`)
- [x] (suggestion) Two tests pin `PushRosNamespace`: the recorders come up under `bizzy` by default and follow `namespace:=`. Mutation-verified — deleting the push now fails 2 of 27 — `bizzyboat_project11/test/test_logging_launch.py:105-131,232-243` (`f366062`)
- [x] (suggestion) `logging_launch.py` now rejects `m3_all_directory:=` with the mirror image of perception's guard, naming `perception_launch.py` and listing the arguments that do live here; the manual's relocation note now states the error is hard in **both** directions — `bizzyboat_project11/launch/logging_launch.py:17-56`, `docs/bizzyboat_operator_manual.md:406-411` (`874258f`)
- [x] (suggestion) A preflight `OpaqueFunction` resolves both `storage.uri`s and refuses to start if they are equal, naming `sonar_log_subdirectory:=` as the way out — so pointing `P11_LOG_DIR` and `P11_SONAR_LOG_DIR` at one disk fails at launch instead of killing whichever recorder starts second. The manual's relocation section says so too — `bizzyboat_project11/launch/logging_launch.py:59-95,205-207`, `docs/bizzyboat_operator_manual.md:396-402` (`2d8245b`)
- [x] (suggestion) The confirm-recording step now asks for **exactly one of each** and explains the double-start: two `logging` instances both record, nothing errors, the disk fills twice as fast and each directory looks plausible — `docs/bizzyboat_operator_manual.md:352-366` (`0059c7f`)
- [x] (suggestion) An autouse fixture `monkeypatch.delenv`s `P11_LOG_DIR` / `P11_SONAR_LOG_DIR` / `OVERRIDE_LAUNCH_PROCESS_OUTPUT`; verified the failure it prevents (with the two P11_* vars set to one path, `test_the_two_bags_never_share_a_directory` failed before the fix, passes after) — `bizzyboat_project11/test/test_logging_launch.py:31-49` (`2f19eb5`)
- [x] (suggestion) `stop_tmux_project11.bash` now spends one shared wall-clock budget on the non-zenoh windows (they are all Ctrl-C'd before the wait starts) instead of `SHUTDOWN_TIMEOUT` per window, and both the comment and the expiry warning say plainly that the timeout is a grace, not a guarantee — on expiry the session is killed and anything still writing may be truncated — `bizzyboat_project11/scripts/stop_tmux_project11.bash:11-23,35-57,63-64` (`124c4ff`)
- [x] (suggestion) The manual's shutdown step now describes what the script does (Ctrl-Cs everything at once, zenoh last, waits up to 25 s), tells the operator to watch for the `still running` warning, and notes the manual `logging`-last ordering is for hand shutdowns only — `docs/bizzyboat_operator_manual.md:105-119` (`e3dade8`)
- [x] (suggestion) Tests use `entity.output` / `.sigterm_timeout` / `.sigkill_timeout` / `.emulate_tty`; only `_Node__node_name` stays mangled, with a comment saying why (the public property raises until the node executes) — `bizzyboat_project11/test/test_logging_launch.py:80-84,159,168,330-331` (`65b6974`)
- [x] (suggestion) Why the recorders do not respawn is now written down in both places it matters: the launch file (`storage.uri` is frozen at launch and rosbag2 refuses an existing directory, so a respawn would crash-loop; real recovery needs a per-respawn subdirectory and a decision about a run split across directories) and the manual (`a recorder that dies stays dead`, which is why the check is worth repeating during a long deployment) — `bizzyboat_project11/launch/logging_launch.py:125-133`, `docs/bizzyboat_operator_manual.md:373-377` (`f8c0b6c`)
- [x] (suggestion) Both guards now key on `context.argv` — the command-line `name:=value` pairs `ros2 launch` seeds — via a shared `command_line_argument_names` helper, so an including bring-up that declares `log_directory` for its own purposes no longer aborts the whole boat; a test pins that inherited configurations are ignored — `bizzyboat_project11/launch/perception_launch.py:28-42`, `bizzyboat_project11/launch/logging_launch.py:31-45`, `bizzyboat_project11/test/test_logging_launch.py:299-314` (`f01c54a`)
- [x] (suggestion) The "parent directory races the bag" claim is gone — rosbag2 objects only to its own exact target — so `assert all_dir != sonar_uri.parent` is dropped and the launch comment, the guard's error message and the manual now say "off the bag directory itself", with the sibling default presented as the chosen tidy layout rather than a hard constraint — `bizzyboat_project11/launch/perception_launch.py:69-72,171-182`, `bizzyboat_project11/test/test_logging_launch.py:258-276`, `docs/bizzyboat_operator_manual.md:403-407` (`e8ebd38`)
- [x] (suggestion) The plan's Documentation & Instruction Impact is rewritten: the "only doc the diff invalidates" claim is corrected (`.agents/README.md` and the operator manual are listed), and the "Agent-instruction candidates: None" line now carries the Round-2 candidate. Files to Change gains the four files added since Round 1 — `.agent/work-plans/issue-458/plan.md:107-111,140-166` (`bf17d48`)
- [x] (suggestion) All five `DeclareLaunchArgument`s now carry a `description=`, including what the two base directories are for and that the sonar one must not collide with the general one — `bizzyboat_project11/launch/logging_launch.py:140-190` (`409f927`)
- [x] (suggestion) The header comment now reads "Override with `log_subdirectory:=<name>` and, separately, `sonar_log_subdirectory:=<name>` -- two arguments, one per bag" — `bizzyboat_project11/launch/logging_launch.py:123-124` (`409f927`)

### Deferred actions
- [x] (deferred: targets `.agent/knowledge/ros2_development_patterns.md` in the **workspace** repo, which is outside this issue's worktree — the review itself marked it "proposal only — not applied") Instruction-update candidate: "moving a launch argument between launch files fails silently". Recorded in this issue's plan under Documentation & Instruction Impact so the host has it in hand; the reference implementation it cites is in this PR, now on both launch files and keyed on `context.argv`.
- [x] (deferred: no container runtime in this worktree — `docker` is not on PATH and there is no daemon socket, and `ci_local.sh` exits early without it) ADR-0018 pre-merge attestation. HEAD still carries no `refs/notes/ci-local` record; the full-scope run must happen on a host with docker before merge. Local sanity checks are in Verification below and are **not** a substitute for it.

### Verification
- `pytest test/test_logging_launch.py` — 27 passed (was 18; +9 from this pass).
- `pytest test/` — 250 passed, 8 failed; all 8 are the same pre-existing `test_operator_core_launch.py` failures the previous round recorded (they need the package installed / a specific hostname) and are untouched here.
- Mutation checks re-run for the two tests this pass added or repaired: deleting `PushRosNamespace(namespace)` now fails 2 tests (it failed none before), and exporting `P11_LOG_DIR`/`P11_SONAR_LOG_DIR` at one path no longer changes the suite's result.
- `bash -n` and `shellcheck` on `stop_tmux_project11.bash` — both clean.
- `flake8 --select=E,W,F` on `logging_launch.py` and `test_logging_launch.py` — clean; `perception_launch.py`'s remaining E501s are all pre-existing lines this pass did not touch.
- Pre-commit hooks ran on all 15 commits; none bypassed.

### Not verified here
Unchanged from the previous pass: on-boat behaviour still needs the hardware (the `logging` window coming up and printing recorder start-up, `ros2 bag info` topic sets matching pre-split, Ctrl-C in `logging` leaving the other windows running). New this pass and also hardware-only: that the collision guard's error is what an operator actually sees when both `P11_*` variables point at one disk, and that a duplicate `logging` window shows as repeated `ros2 node list` lines.

### Next step
`review-code` (re-review) — hand off to a fresh-context sub-agent:

    .agent/scripts/dispatch_subagent.sh --mode in-process --issue 458 --skill review-code

## Integrated Review
**Status**: complete
**When**: 2026-08-25 21:09 -04:00
**By**: Claude Code Agent (Claude Opus)

**PR**: #461 at `27a7147`
**Sources**: 3 (Copilot R1 @ `27a7147`, Local Review (Pre-Push) R2 @ `93daa76`, CI rollup)
**Cross-source confirmations**: 0
**CI**: all-pass (`build-and-test` success, `copilot-pull-request-reviewer` success)

### Findings
- [ ] (must-fix, Copilot @ `27a7147`) The shared-deadline shutdown wait warns on the clock alone: once the budget is consumed by an earlier window, each later window's `while [ $SECONDS -lt $SHUTDOWN_TIMEOUT ]` is false on entry so the window is never probed, and the post-loop `if [ $SECONDS -ge $SHUTDOWN_TIMEOUT ]` prints `WARNING: <window> still running` for windows that exited long ago. This PR deliberately made that warning the operator's data-integrity signal (`docs/bizzyboat_operator_manual.md:110-112` and the script's own comment at :19-22 tell the operator to distrust a run's bags when they see it), so a warning that cries wolf trains the operator to ignore the one line that flags a truncated mcap. Fix: track whether each window's loop exited by `break`, and after the loop do one final `pane_pid` / `pgrep -P` probe, warning only when a child is still running — which also correctly reports a window that was never waited on because the budget was already gone but is genuinely still writing — `bizzyboat_project11/scripts/stop_tmux_project11.bash:41-63`

### Lineage (not a same-SHA cross-confirmation)
- This is a regression introduced by the Round-2 fix `124c4ff`, which converted the per-window budget into one shared deadline in answer to Local Review R2 finding #8 (3-way confirmed that round). The shared deadline is correct; only the warning's condition was left keyed to the clock. Copilot reviewed the current head (`commit_id` == `head_sha`), so the finding is fresh.

### False positives
None — the single Copilot comment is valid.

### Test coverage note (not a finding)
`test_logging_launch.py:347-358` only greps `SHUTDOWN_TIMEOUT=` out of the script text; nothing exercises the wait loop's warning logic, which is why 27 green tests did not catch this. A pure-bash behaviour test is out of proportion here — re-check the fix with `bash -n` / `shellcheck` plus a two-window tmux smoke where the first window is slow to exit.

### Pre-merge (carried forward, not a code finding)
- [ ] (deferred: no docker in this worktree) ADR-0018 — HEAD still carries no `refs/notes/ci-local` full-scope attestation; the host must run `.agent/scripts/ci_local.sh` before merge.

### Next step
`address-findings` — one open must-fix. Hand off to a fresh-context sub-agent:

    .agent/scripts/dispatch_subagent.sh --mode in-process --issue 458 --skill address-findings
