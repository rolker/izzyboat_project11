# BizzyBoat deployment log — gabby — 2026-05-22

**Host**: gabby
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7 (1M context))
**Mode**: field (gitcloud origin)
**Deployment**: git-bug `1e4fe7d` — *Deployment 2026-05-22: battery drain to LVD + perception #14 in-water + costmap-over-Starlink* (GitHub link added dev-side at wrap-up)

## Summary

*To be filled at wrap-up (user-curated).*

## Lessons Learned

*To be filled at wrap-up (user-curated).*

## 1. Session start — git-bug pull + field-side state confirmation

**2026-05-22T15:35-04:00** — Roland asked whether today's deployment
issue was visible. `git bug bug --label deployment --by edit` returned
only the 2026-05-21 entry (`7d5b52c`, still showing open locally); no
2026-05-22 entry yet. Same SSH_AUTH_SOCK gap as 2026-05-19 / 2026-05-21
sessions — `git bug pull` exits with
`Error: error creating SSH agent: "SSH agent requested but SSH_AUTH_SOCK not-specified"`.
The persistent fix (systemd user `ssh-agent.service` / keychain) noted
as follow-up after the last two deployments still hasn't landed.

**2026-05-22T15:36-04:00** — Roland confirmed: apply the same inline
workaround. Same recipe as 2026-05-21 §1:

```bash
eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519_gitcloud
git -C <repo> bug pull
ssh-agent -k
```

First pull "already up-to-date" — confirmed today's deployment issue
hadn't been published to gitcloud yet from dev side. Roland asked to
verify the local repo state before pulling again.

**2026-05-22T15:38-04:00** — `git status` on field-mode project repos
turned up two uncommitted changes from the morning's prep:

- `unh_echoboats_project11/bizzyboat_project11/config/bizzyboat.yaml` —
  restored `oak_aft_ffmpeg` to the VPN nodes list and `topics_list`;
  removed the explanatory comments about the 2026-05-19 uplink-budget
  drop. Roland: aft was re-added to see how it'd fare on the pier after
  the udp_bridge work; stable, commit it.
- `seafloor_echoboat_project11/echoboat_project11/config/nav2_params.yaml` —
  restored the full 4-instance `sea_surface_layer` list
  (port/starboard/aft); removed the 2026-05-21 forward-only workaround
  comments. Roland: `unh_marine_perception#6` is fixed, commit it.

Committed with agent identity (`-c user.name=... -c user.email=...` per
[AGENTS.md](../../../../../../../../AGENTS.md) — env-var script doesn't
propagate across each Bash invocation's fresh subshell):

- `unh_echoboats_project11` `a83b416` — *bizzyboat.yaml: restore
  oak_aft_ffmpeg to VPN*
- `seafloor_echoboat_project11` `bf4da10` — *nav2_params.yaml: restore
  full 4-layer sea_surface_layer list*

**2026-05-22T15:40-04:00** — Push to gitcloud rejected on
`unh_echoboats_project11` — salmon agent had pushed
`85585e5 docs/logs: 2026-05-21 salmon deployment log` in the meantime.
No file conflict (different paths). Rebased local commit onto
`origin/jazzy`; new SHA `ac77860`. Push succeeded for both repos:

- `unh_echoboats_project11`: `ac77860` → `origin/jazzy`
- `seafloor_echoboat_project11`: `bf4da10` → `origin/jazzy`

**2026-05-22T15:42-04:00** — Ran `make sync` from the workspace root
(with ssh-agent inline). All repos up-to-date; `ros2_network_monitor`
picked up an update. No other workspace movement.

**2026-05-22T15:44-04:00** — Second `git bug pull` after sync surfaced
the day's deployment issue: `1e4fe7d` — *Deployment 2026-05-22: battery
drain to LVD + perception #14 in-water + costmap-over-Starlink*.
Reviewed in full; this log header references it. Per
[[feedback_deployment_issue_readonly]] the issue is read-only from
gabby — all observations land here.

### Field-side reconciliation note for wrap-up PRs

Two of the three "field A/B" items called out in the deployment issue
are already on `origin/jazzy` (gitcloud) as of `ac77860` and `bf4da10`:

- `seafloor_echoboat_project11` `#21` workaround revert — `bf4da10`.
- `unh_echoboats_project11` `bizzyboat.yaml` `oak_aft_ffmpeg` VPN
  restore — `ac77860`.

The third — the 4:3 preview+video A/B on `oak_cameras_launch.py` — has
not been applied yet (pending operator go-ahead during pre-launch).

## 2. ROS bring-up verification

**2026-05-22T16:15-04:00** — Roland started ROS bring-up. Asked to
verify the launch is OK before further activity. Snapshot after
graph settled:

| Check | Result |
|---|---|
| Nodes / topics | 120 nodes / 297 topics |
| `controller_server` lifecycle | `active [3]` |
| `lifecycle_manager_navigation/is_active` | `True` |
| `local_costmap` plugins | `chart_layer`, `sea_surface_layer_forward`, `..._port`, `..._starboard`, `..._aft`, `inflation_layer` |
| `/bizzy/tide_estimate` rate | ~10 Hz steady |
| TF `map → odom → map_tide` | broadcast at ~10.2 Hz |
| TF `map → chart_datum`, `map → chart_datum_mhhw` | present (PR #153 datum chain) |

**Multi-instance `sea_surface_layer` bench validation — PASS.** All
four instances loaded into `local_costmap` and `controller_server`
reached `active [3]` (lifecycle state 3 = PRIMARY_STATE_ACTIVE). The
`unh_marine_perception#6` / `#14` segfault on activation does not
reproduce with the merged fix in place. This is the in-water
prerequisite from the deployment-issue Block 1 plan — bench passes;
in-water validation still pending.

**`map_tide` TF startup race did not bite.** Memory
[[project_mru_global_startup_race]] notes Nav2 lifecycle can lose a
startup race for `map_tide` TF after the `mavros/global_position/global`
switch; this launch produced a steady-state chain on the first try. No
relaunch needed.

**Deltat frame in TF tree.** `bizzy/base_link → bizzy/deltat` is
present but this is a static URDF TF; per
[[project_bizzyboat_deltat_removed]] the Imagenex 837 driver is not
installed and the sensor is off. Frame presence does not imply data
flow.

**#157 activation-race: did NOT bite today (single-attempt success).**
Initially thought the messages were lost to terminal-only output, but
the per-node rclcpp logs are written to `~/.ros/log/<node>_<pid>_<ts>.log`
(distinct from the launch-subdirectory `launch.log`, which only
captures `process started with pid` lines). From
`/home/field/.ros/log/lifecycle_manager_23149_1779480587936.log`:

| Event | Timestamp | Source |
|---|---|---|
| `Activating controller_server` | `1779480589.085` (16:09:49 EDT) | `bizzy.lifecycle_manager_navigation` |
| `Server controller_server connected with bond.` | `1779480595.241` (16:09:55 EDT) | `bizzy.lifecycle_manager_navigation` |

**Δ activation = 6.16 s, no `Retry attempt N/4` messages.** Per
[#157](https://github.com/rolker/unh_echoboats_project11/issues/157)
decision criteria: single attempt → activation race avoided this run.
Recording in the dev log so the cross-deployment trend can be tracked.

**Lookup tip for future agents**: when reconstructing lifecycle
timings, the path is `~/.ros/log/<lifecycle_manager_node>_<pid>_<ts>.log`,
not the launch-subdir. The launch.log is shallower than it looks.

## 3. 4:3 OAK preview+video A/B applied

**2026-05-22T16:25-04:00** — Per the deployment-issue Block 1 plan and
the comment-thread spec, applied the 4:3 size params to
`bizzyboat_project11/launch/oak_cameras_launch.py`. Single uniform
block in `_oak_camera_node()` (not per-camera in `CAMERAS`) since the
A/B is global; revert is a one-block deletion. Four keys added:
`video_width`/`video_height`/`preview_width`/`preview_height` = 1280×960.

**Bitrate decision**: Roland chose to **leave `h265_bitrate_kbps` at
800** (declined the proposed 800 → 1066 bump). Keeps the A/B clean —
size change isolated from bitrate. Accepts the ~25% bits-per-pixel
drop at the larger pixel count; if image quality degrades visibly
during the field-test, the bitrate tweak is the obvious follow-on.

Commit: `8b32cc4` *oak_cameras_launch.py: 4:3 preview+video A/B
(field-test 2026-05-22)*.

**Open**: OAK camera nodes are still running with the pre-edit (16:9)
params — `ros2 launch` evaluates the launch description once at
startup, so the running nodes don't pick up the file change until the
group is re-launched. Per [[feedback_dont_kill_launched_nodes]], will
ask Roland to re-launch the oak_cameras group rather than killing
individual nodes (their `respawn=True` would just bring them back with
the old in-memory params).

**Parent launch**: `oak_cameras_launch.py` is included by
`bizzyboat_project11/launch/perception_launch.py` — that's the group
to Ctrl-C and re-launch (terminal pts/4 here). `core_launch.py` and
`nav_launch.py` don't include it; leave them alone.

### 3a. First relaunch (16:26 EDT) — params loaded, slow OAK reconnect

**2026-05-22T16:27-04:00** — Roland relaunched `perception_launch.py`.
New oak node PIDs 27180–27183 (was 22989–22992) — fresh launch.
Verified params on **all four** cameras (`oak_forward`, `oak_starboard`,
`oak_aft`, `oak_port`):

```
video_width  = 1280   preview_width  = 1280
video_height = 960    preview_height = 960
h265_bitrate_kbps = 800   (per operator decision — bump declined)
```

Param load confirmed correct. `unh_marine_perception#10` 4:3 A/B is in
effect at the param layer.

**Slow PoE OAK reconnect on `oak_starboard`.** Per the per-node log
`~/.ros/log/sea_surface_segmentation_27181_*.log`:

- 1779481608 — Initializing
- 1779481666 — Failed: `Device already closed or disconnected: I/O error`
  (retry 1/5)
- 1779481669 — Failed: `Cannot find any device with given deviceInfo`
  (retry 2/5)
- 1779481671 — Failed: same (retry 3/5)
- 1779481695 — Connected (DeviceInfo 192.168.20.12) — **~87 s
  after initialization began**

These are PoE (Ethernet) OAK cameras with `X_LINK_TCP_IP` link type.
The previous process's TCP session needs to time out on the device
side before the new process can re-establish — quick-cycle relaunches
hit this retry path. The other three came up quickly (no IP-stack
contention).

**3b. Frame-flow verification incomplete.** Within the ~7 min the
relaunch was up, ran `ros2 topic hz` on `image_raw/ffmpeg` and
`segmentation` for all 4 cameras with 5-10 s windows — saw no
messages. Could be:
- Cameras still in pipeline-warmup phase post-connect (oak_starboard
  only finished connecting ~80 s before the topic-hz attempts started).
- Pipeline/encoder issue triggered by the new params.
- DepthAI internals slow to start emitting after `Camera::setSize`
  reconfiguration.

`Publisher count: 0` on `/image_raw/ffmpeg` for oak_forward at one
sampling point — so it wasn't a subscriber-only issue, the publisher
hadn't created the topic yet (or had already torn down). Insufficient
data to distinguish.

**16:34 EDT** — Roland Ctrl-C'd `perception_launch.py` to let the OAK
TCP sessions fully release before the next relaunch (avoids
repeating the 87 s `oak_starboard` retry cycle). Plan: relaunch after
a settling period and re-verify frame flow with a longer hz window.

**Lookup tip for future agents**: when verifying OAK camera startup,
budget at least 30-60 s after the per-node log shows `Connected to
device:` before declaring "no frames" — the DepthAI pipeline + h.265
encoder warm-up is observed (but not yet quantified) to take longer
than typical ROS-node startup.

### 3c. Second relaunch (16:38 EDT) — both streams 4:3 still 0 fps

**2026-05-22T16:38-04:00** — Roland Ctrl-C'd and relaunched again,
this time waiting longer for OAK PoE TCP sessions to fully release.
All four cameras connected cleanly on the first attempt. Per-node logs
showed the same `Connected to device → FFMPEGPublisher init` sequence,
then silence.

**Operator observation**: rqt_camera_grid on the operator station
showed segmentation images *present but not updating* — last frame
from before the stall was cached/latched (TRANSIENT_LOCAL QoS), giving
the false impression of partial success. **Lesson for live ops:
"segmentation image visible" ≠ "frames flowing"; verify with topic
hz**, per [[feedback_node_list_vs_data_flow]].

`ros2 topic hz` confirmed: **zero msg/s on all 12 topic/camera
combinations** (`image_raw/ffmpeg`, `segmentation`,
`segmentation/compressed` × 4 cameras). `topic info` confirmed
publishers exist (`Publisher count: 1`), so the issue isn't a missing
publisher — it's a stalled depthai pipeline producing no data.

### 3d. Split A/B (16:45 EDT) — preview default, video 4:3 → still 0 fps

**2026-05-22T16:45-04:00** — On Roland's call, applied a split test
instead of full revert: dropped `preview_*` keys, kept
`video_{width,height}=1280×960`. Hypothesis: maybe the preview-side
ISP reconfig was the fragile bit, and video-side `setSize(1280×960)`
works independently. Commit `d555d45`.

Relaunched perception_launch. All 4 cameras connected cleanly within
~13 s; `oak_starboard` was last at 1779482740.56 (no retry storm —
prior wait had let its TCP session clear). 116 s after the last
connect: **still 0 frames** on all 4 cams × both topic families.
Identical "connect → FFMPEGPublisher init → silence" signature in
per-node logs.

### 3e. Full revert (16:48 EDT) → frame flow restored

**Finding for [unh_marine_perception#10](https://github.com/rolker/unh_marine_perception/issues/10)
follow-up**: `video_{width,height}=1280×960` alone (preview at the
1280×720 default) is enough to stall the depthai pipeline on all 4
PoE OAK cameras. The "flip both 4:3 together to sidestep
`setPreviewSize` / `setSize` independence concerns" hypothesis from
the deployment-issue comment is invalid — the issue is in the
video-side `setSize` itself, not in mixing aspect ratios. The
sea_surface_segmentation driver / depthai version on gabby today
**cannot serve a 1280×960 video stream**.

Caveats on this finding:
- Single resolution tested (1280×960). A different 4:3 resolution
  (e.g. 1920×1440, or a non-IMX378-native 4:3 ratio) might behave
  differently — not tested.
- depthai version not captured in this log (recommend documenting in
  the #10 follow-up issue alongside this finding).
- "Stall" is unexplained — no error/warning in the per-node log
  beyond the routine connect + FFMPEGPublisher init lines.

Reverted by dropping both `video_*` keys back out — restoring the
pre-2026-05-22 state. Commit `a5d9e22`. Roland relaunched.

**Frame-flow verification post-revert**:

| Camera | `image_raw/ffmpeg` | `segmentation/compressed` |
|---|---|---|
| `oak_forward` | 5.001 Hz | 5.001 Hz |
| `oak_starboard` | 4.998 Hz | 5.003 Hz |
| `oak_aft` | 4.999 Hz | 4.995 Hz |
| `oak_port` | 5.009 Hz | 5.000 Hz |

All four cameras at the expected ~5 fps on both topic families. The
in-water portion is no longer blocked. Three relaunch cycles burned
(~25 min wall time) for the A/B + diagnostic + revert — worth it for
the durable #10 finding.

**Carry-forward for wrap-up**: the 4:3 A/B reconciliation PR called
out in the deployment-issue Block 3 plan becomes a "field-tested,
reverted, follow-up filed against #10" entry rather than a config
change to merge. The bench-A/B-on-different-resolutions path proposed
during the diagnostic is the natural next step for the #10 thread —
not a deployment-blocking concern today.

## 4. Block 1 quick-verify sweep

**2026-05-22T16:51-04:00** — Ran the remaining gabby-side pre-launch
checks from the deployment-issue Block 1 plan in a single pass.
Findings below.

### 4a. Battery voltage

`/bizzy/mavros/battery.voltage = 25.024 V` (current 0.01 A, percentage
−0.01 — FCU has no full-cell calibration). Matches the deployment
issue's prep estimate of "currently at ~25.25 V"; we're slightly
below, well above the LVD floor. No concern.

### 4b. PR #153 datum topics — publish OK, but logger wasn't recording them

| Topic | Hz | Sample value | Type |
|---|---|---|---|
| `/bizzy/tide_estimate` | 9.9 | −21.94 | `std_msgs/Float64` |
| `/bizzy/mllw_offset` | 1.0 | −28.01 | `std_msgs/Float64` |
| `/bizzy/mhhw_offset` | 1.0 | −25.15 | `std_msgs/Float64` |

Topics publish at expected cadence. But `ros2 node info /bizzy/logger`
did **not** list any of the three in its subscriptions — they would
not have landed in today's bag.

**Root cause**: PR [#153](https://github.com/rolker/unh_echoboats_project11/pull/153)
added the publishers (in `chart_datum_node`) but the corresponding
entries in the boat-side logger's `record.topics:` list in
`bizzyboat_project11/config/bizzyboat.yaml` were missed. (The install
file is symlinked to src, so this isn't a build-staleness issue —
the lines were simply never added.)

**Fix**: appended three lines to the `/**/logger` block's
`record.topics:` list, just below
`/bizzy/sensors/sound_speed/sound_speed`, with a comment noting the
#153 follow-up. Commit `7b6d8f3`.

```yaml
      - /bizzy/sensors/sound_speed/sound_speed
      # Tide estimator + chart-datum offsets (PR #153 follow-up — the
      # publishers landed but the logger subscriptions were missed).
      - /bizzy/tide_estimate
      - /bizzy/mllw_offset
      - /bizzy/mhhw_offset
      - /bizzy/udp_bridge/bridge_info
```

Roland Ctrl-C'd `perception_launch.py` on pts/4 (logger's parent) and
re-launched. Post-restart `ros2 node info /bizzy/logger` confirms all
three subscriptions live. Cameras came back at ~5 Hz on both
topic families on the same relaunch — and noticeably faster than the
earlier cycles: `oak_starboard` reconnected ~27 s after the other
three, vs the 87 s retry storm seen at 16:27. **Empirically, a
~5-minute settle between relaunches mostly eliminates the slow
reconnect.** Worth carrying into the convention if it holds across
future deployments.

**Tide-value sanity**: the −21.94 m on `tide_estimate` looks wrong at
first glance vs the NOAA forecast (we're between L 10:36 −0.09 m and
H 17:02 +2.68 m, so the actual tide should be approaching +2.5 m
MLLW). But the topic is `std_msgs/Float64` with no frame_id, and
`mllw_offset` / `mhhw_offset` differ by ~2.9 m which roughly matches
the local tidal range — so these are likely heights in some
ellipsoid / chart-datum reference frame, not literal MLLW metres.
Flagging for the wrap-up dev-side review rather than treating as a
problem now. PR #153 follow-up should also document the reference
frame for these topics so future agents don't trip on this.

### 4c. AML SVS dry sanity — silent on /dev/ttyS0 (expected out of water)

`/bizzy/sensors/sound_speed/sound_speed_bridge` log shows clean
startup:

```
sound_speed_bridge started: device=/dev/ttyS0 baud=9600
  parser=regex udp_targets=[('mercat', 20003, 'valeport')]
Opened serial /dev/ttyS0 @ 9600
```

…then silence. `ros2 topic hz /bizzy/sensors/sound_speed/sound_speed`
shows zero messages. Per Roland: **expected** — the AML probe is
dry, and the regex parser only publishes on successful parse (so no
"placeholder 0.0" stream out of water). The deployment issue's "0.0
m/s placeholder is expected" prediction is wrong for the current
firmware/parser combination; the actual out-of-water behavior is full
silence. **Defer the real verification to in-water phase** — bag will
then need to show non-zero values per the verify-before-June-4 item.

### 4d. costmap rate — deferred to under-thrust

`/bizzy/local_costmap/costmap` and `/bizzy/local_costmap/published_footprint`
both timed out on `topic hz` from a still boat. Nav2's costmap
publish is event-driven (updates_only after the initial transient_local
emit). Without thrust + motion the local costmap doesn't tick. Will
re-verify naturally once the boat is moving in Phase 1.

### 4e. Items NOT done from gabby (operator-side or other-host)

- **Mercat NTP verify** — requires SSH to the Windows host and
  `ntpq.exe -pn` against `time.bizzy.p11.lan`. Operator-driven.
- **Operator-side bring-up on salmon** — not a gabby task.
- **Activation-race observation** — already captured in §2 above
  (single-attempt success today; #157 didn't bite).

## Files touched (this session, gabby-side, so far)

| Commit | Path | Why |
|---|---|---|
| `a83b416` (→ rebased `ac77860`) | `bizzyboat_project11/config/bizzyboat.yaml` | Restore `oak_aft_ffmpeg` to vpn topics |
| `bf4da10` | `echoboat_project11/config/nav2_params.yaml` (seafloor_echoboat) | Restore 4-instance sea_surface_layer |
| `8968ed0` | `docs/logs/2026/2026-05-22_gabby_logs.md` | Initial log file |
| `8b32cc4` | `bizzyboat_project11/launch/oak_cameras_launch.py` | 4:3 A/B (added 4 keys) |
| `d555d45` | same | Split test — preview reverted, video stays 4:3 |
| `a5d9e22` | same | Full revert — both back to defaults |
| `7b6d8f3` | `bizzyboat_project11/config/bizzyboat.yaml` | Add tide/datum topics to logger |
