# Plan: Operator-side diagnostics — monitor nodes + /diagnostics recorder on salmon

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/97

## Context

Operator-side instrumentation is sparse compared to boat-side. The 2026-04-27 wedge revealed the gap: when `udp_bridge` stalled, the annunciator silently held the last-known OK state and an RTK degradation that fired properly boat-side never reached the operator UI. Class-prep priority for June 2026 hydrography.

The issue lists three actions. Audit on the current `jazzy` tip shows:

- **Action 1 (monitor nodes on salmon)** — **already done.** `bizzyboat_project11/launch/network_monitor_operator_launch.py` runs `mikrotik_monitor`, `teltonika_monitor`, `starlink_diagnostics`, and `ping_monitor` with op-side configs (`network_monitor_operator.yaml`, `teltonika_monitor_operator.yaml`, `ping_targets_operator.yaml`, plus inline starlink params for `192.168.100.1:9200`).
- **Action 3 (auto-launch monitors)** — **already done.** `operator_core_launch.py:75-83` includes `network_monitor_operator_launch.py`.
- **Action 2 (`/diagnostics` + operator-action recorder)** — **not done.** The only existing recorder is `bizzyboat_project11/scripts/record_camera_topics.sh` — boat-side, ad-hoc, shell-script-determined output dir (`~/data/logs/bizzy_images/bag_$(date +%Y-%m-%dT%H.%M.%S)_ffmpeg_seg`).

So the remaining work is just the recorder + wiring it into `operator_core_launch.py`.

## Approach

1. **New launch file `bag_recorder_operator_launch.py`** in `bizzyboat_project11/launch/`. Single `ExecuteProcess` action that runs `ros2 bag record` with topics + storage flags equivalent to `record_camera_topics.sh` but no shell wrapper. Output dir computed in Python at launch evaluation time:

   ```python
   from datetime import datetime
   import os

   now = datetime.now()
   day_dir = now.strftime('%Y-%m-%d')
   bag_name = now.strftime('diagnostics_%H.%M.%S')
   out_dir = os.path.expanduser(f'~/data/logs/operator/{day_dir}/{bag_name}')
   ```

   Per-day parent so multiple deployments in a day land grouped; per-launch bag dir inside. Path is `~/data/logs/operator/...` — generic enough to host non-diag operator-side bags later (camera, NMEA tap, etc.) without renaming.

2. **Topic list** (per issue body + scope-expansion comment + udp_bridge stats):
   - `/diagnostics` — picks up both boat-side diag forwarded over `udp_bridge` and salmon-local op-side diagnostics from the four monitor nodes.
   - `/bizzy/marine/command` — operator-originated CAMP commands (from `operator.yaml:18,32`).
   - `/bizzy/piloting_mode/manual/helm` — operator-originated joystick helm (from `operator.yaml:19,33`).
   - `/operator/udp_bridge/topic_statistics` — operator-side bridge top-level stats (per-topic byte/packet counters across all remotes).
   - `/operator/udp_bridge/bridge_info` — operator-side bridge config snapshot (latched; one message per launch, captures the connection topology).
   - `/operator/udp_bridge/remotes/bizzy/topic_statistics` — per-remote stats for the boat link (the one we actually care about during a wedge).
   - `/operator/udp_bridge/remotes/bizzy/bridge_info` — per-remote latched config snapshot.
   - `/rosout` — universal log; cheap; useful for op-side stack debugging.
   - `/tf`, `/tf_static` — usually empty on salmon, but recording adds zero cost if absent. Default to including so we don't have to revisit.

   The four udp_bridge topics are the wedge-investigation gold: when `udp_bridge#10` stalled, only inside-the-bridge stats can show the stall as it's happening. `/diagnostics` alone misses it because the bridge is *also* the transport that delivers boat-side diag — a stalled bridge silently freezes the diag stream.

3. **Storage profile**: `-s mcap --storage-preset-profile zstd_fast` (matches `record_camera_topics.sh`). Diagnostics is low-rate so compression fidelity doesn't matter, but consistency with the existing pattern eases later mcap tooling work.

4. **Lifecycle**: `ExecuteProcess` with `--disable-keyboard-controls` (rosbag2 puts the terminal in TTY mode otherwise — same gotcha the shell script documents). On launch shutdown, send SIGINT (not SIGTERM) so rosbag2 flushes the mcap cleanly. Set `sigterm_timeout='10'` and use the `on_exit` hook only to log; respawn should be **off** (one bag per launch, not auto-restart).

5. **Launch arg `record_diagnostics`** (default `'true'`) gating the `ExecuteProcess` via `IfCondition`. Lets devs disable recording during sim/dev without editing the launch file.

6. **Wire into `operator_core_launch.py`**: add `IncludeLaunchDescription` for `bag_recorder_operator_launch.py` outside the `operator` namespace group (matching how `network_monitor_operator_launch.py` is included). The recorder records absolute topic paths so namespacing is irrelevant.

## Files to Change

| File | Change |
|------|--------|
| `bizzyboat_project11/launch/bag_recorder_operator_launch.py` | **New.** ExecuteProcess running `ros2 bag record` with launch-computed date-stamped output dir, mcap+zstd_fast storage, the seven topics, SIGINT shutdown, `record_diagnostics` arg gate. |
| `bizzyboat_project11/launch/operator_core_launch.py` | Add `IncludeLaunchDescription` for the new recorder launch, sibling to the existing `network_monitor_operator_launch.py` include at lines 75-83. |
| `bizzyboat_project11/CMakeLists.txt` | No change — verified `install(DIRECTORY launch DESTINATION ...)` already covers the new file. |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| **A change includes its consequences** | Recorder is the third leg of a deployment artifact set (boat-side bags, dev logs, op-side bags). Wiring it into the auto-launched stack — not leaving it as an opt-in script — closes the loop. |
| **Test what breaks** | No unit test for a launch file is meaningful. The relevant test is field-side: run `operator_core_launch.py`, confirm a bag appears at the expected path with non-zero diag traffic. Plan flags this as a manual smoke step in the test plan; no fake unit tests. |
| **Only what's needed** | Resisting two temptations: (a) "make the recorder configurable per-deployment with a YAML topic list" — not yet, the topic set is small and stable; YAML adds a moving part for no current benefit. (b) "auto-rotate bags by size/duration" — rosbag2 supports this natively via `--max-bag-size` / `--max-bag-duration` if needed later; default unbounded for now since deployments are bounded by operator runtime. |
| **Capture decisions, not just implementations** | This plan + PR description should call out *why* the date-dir is computed in Python rather than via a shell wrapper: parity with the rest of the `bizzyboat_project11` launch surface (everything else is `.launch.py`, no shell wrappers in the auto-bringup path), and so `operator_core_launch.py` can include it via the standard `IncludeLaunchDescription` mechanism. |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| **ADR-0008 follow-ros2-official-conventions** | Yes | Use `ros2 bag record` (the official tool), `mcap` storage (the ROS 2 default in Jazzy), `ExecuteProcess` (the official launch action for non-Node processes), and standard launch-arg conventions. |
| **ADR-0003 workspace-infrastructure-is-project-agnostic** | Borderline | The recorder launch is project-specific (BizzyBoat operator stack), so it lives in `bizzyboat_project11`, not in workspace infrastructure. ADR is not violated; flag this so future "extract to a shared launch helper" temptation is intentional, not accidental. |

## Consequences

| If we change... | Also update... | Included in plan? |
|---|---|---|
| Recorder topic list | This plan, the launch file's docstring, the dev log entry. | Yes — all three sit in this PR. |
| `operator.yaml` udp_bridge topics | Recorder topic list (so post-incident bags can answer "did the operator send X?"). | **Out of scope here** — call this out in the PR body so future udp_bridge config edits remember to revisit. |
| `~/data/logs/operator/` path convention | The shell script `record_camera_topics.sh` uses `~/data/logs/bizzy_images/`; document this divergence in the recorder launch's module docstring and the dev log so the two patterns don't drift further. | Yes — call out the convention boundary in the docstring. |

## Open Questions

(Resolved by user during plan review — kept here for audit trail.)

- ~~Path: `operator_diag/` vs `operator/`~~ → `operator/` (generic root for all op-side bags, not just diag).
- ~~Include `/tf`/`/tf_static`?~~ → Yes (zero cost when absent).
- ~~Per-day parent dir or flat?~~ → Per-day grouped: `~/data/logs/operator/<YYYY-MM-DD>/diagnostics_<HH.MM.SS>/`.
- ~~Add udp_bridge stats topics?~~ → Yes — added the four `/operator/udp_bridge/...` topics to the list. These are the wedge-investigation core.
- ~~`record_diagnostics` default~~ → `'true'` (record by default during deployment launches).

## Estimated Scope

Single PR. ~80 lines of new launch code, ~5 lines of include in `operator_core_launch.py`, one CMake-spot-check, one dev-log paragraph. No new packages, no new dependencies. Field-test gated (acceptance bullet 4 won't be checkable until next deployment).
