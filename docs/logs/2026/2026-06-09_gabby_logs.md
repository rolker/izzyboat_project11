# Field log — gabby — 2026-06-09

**Host**: gabby
**Operator**: Roland + Claude Code Agent (Claude Opus 4.8, 1M context)
**Mode**: field (gitcloud origin)
**Deployment issue**: none (started without an issue, per operator)

Log started 2026-06-09 13:16 -04:00. Entries below are retrospective for
the session so far: timestamps from measured sources (bag filenames,
file mtimes, command output) are exact; derived/operator-reported times
are marked.

## 1. Pre-water stack health check

ROS stack up, 128 nodes. Verified before splash:

- **Nav2**: all lifecycle nodes `active` (controller, planner, behavior,
  smoother, BT navigator, waypoint follower, docking, both costmaps).
  `local_costmap/costmap_window` does not answer lifecycle queries
  (custom node, not lifecycle-managed) — expected.
- **SBG**: `imu_data` 25 Hz, `ekf_nav` 25 Hz. `/bizzy/odom` 10 Hz,
  `mavros/imu/data` 10 Hz.
- **FCU**: `mavros/state` connected=true, armed=false, mode MANUAL.
- **Serial ports** (gabby): ttyS0/COM1 → `sound_speed_bridge` (AML),
  ttyS1/COM2 → `sbg_device`, ttyS2/COM3 → `zda_serial_bridge`
  (ZDA-out to mercat). ttyS3 free.
- `/bizzy/sensors/sbg_device` lists twice in `ros2 node list` but is one
  process (pid 10790) — rmw_zenoh double-announce artifact, not a
  duplicate launch.

Expected-quiet-on-deck (not faults): `sound_speed` 0.0 (AML in air),
M3 silent (not in water), `velocity_smoother`/`cmd_vel_smoothed` silent
(disabled by design).

## 2. COM1 / AML sound velocity

COM1 (`/dev/ttyS0`) confirmed receiving AML SVM sentences
(`$AML,SVM,0.000,SN,205937`) at 9600 baud, consumed by
`sound_speed_bridge` → `/bizzy/sensors/sound_speed/sound_speed` at
25 Hz. Read 0.0 m/s in air; later 1495.x m/s once submerged (valid,
within the sidescan's 1400–1600 SV window).

## 3. RTK status (pre-splash)

RTK **fixed**: SBG `gps_pos.status.type 7` (RTK_INT), 32 SVs used of 43
tracked, `ekf_nav.solution_mode 4` (NAV_POSITION). Position 43.0721,
−70.7115 (dock). Correction chain sustained: `/bizzy/sensors/rtcm`
~6 Hz, `/bizzy/sensors/ntrip/fix` ~1 Hz.

## 4. Garmin sidescan bring-up

GCV20 at 192.168.20.8 reachable (0.7 ms) via iface 192.168.20.5; driver
`garmin_sidescan` connected (registered a down ping, reported standby).
Held off transmit on deck by safety interlocks: `safety=on`,
`require_sv=True` with `sv=0.0` (AML in air), `tx=OFF`.

Once SV read valid (1495 m/s, in-window) after splash, started transmit:

- Command: publish to `…/garmin_sidescan/change_state`
  (`marine_radar_control_msgs/RadarControlValue`)
  `{key: status, value: transmit}` — the `status` control's enums are
  `standby` / `transmit`.
- Result: `transmitting=true`, `tx=ON`, ping counts climbing on all
  channels (0/0/1 → 555/556/557 within seconds), `sonar_image_port`
  ~10.6 Hz. All three channels (port/stbd/down) producing imagery.

## 5. Automatic sonar logging — confirmed

`/bizzy/sonar_logger` is actively recording this session to
`~/data/logs/bizzyboat_sonar/2026-06-09T14-41-36+00-00/` (UTC-named dir,
started 10:41 local). Records the processed sidescan:
`sonar_image_{port,starboard,down}` + `state` + `status` +
`debug/raw_status` (plus sound_speed, SBG, odom). **Does NOT record** the
full raw byte stream (`debug/raw`) or `debug/raw_config`.

Corroboration: 5-minute segments held ~3.4 MB while transmit was off,
jumped to ~44–63 MB from segment `_21` (mtime 12:31) when the sidescan
began transmitting — the imagery landing in the auto-log. Storage is mcap
with zstd chunk compression.

## 6. record_sidescan_debug.sh helper (new)

Added `bizzyboat_project11/scripts/record_sidescan_debug.sh [duration_secs]`
(default 60), committed to `jazzy` (50783f7), **not pushed**. Fills the
gap the auto-logger leaves: records ALL `garmin_sidescan` node topics +
`/diagnostics`, and toggles the driver's `debug_raw` param on for the
capture then restores it to false on exit (verified per the rmw_zenoh
silent-drop caveat). Modeled on `record_camera_topics.sh`
(timeout --signal=INT, --disable-keyboard-controls, zstd_fast mcap).

Captures taken to `~/data/logs/bizzy_sidescan/`:

- `bag_2026-06-09T11.22.54_sidescan_raw` — earlier 34 s debug+diagnostics
  capture (manual, pre-transmit; debug/raw + diagnostics, no imagery yet).
- `bag_2026-06-09T12.30.06_sidescan_raw` — 60 s via the new script during
  live transmit: 18,443 msgs (debug/raw 15,623; sonar_image_* ~630 each;
  diagnostics 894), 11.2 MiB.

## 7. Disk space

`/home` (`/dev/sda1`, holds `~/data/logs`): 1.9 TB total, **~1.7 TB free**
(5% used; logs dir 74 G). At the sidescan-transmitting rate (~0.7 GB/hr
for sonar) runway is on the order of weeks — disk is not a constraint
this deployment.

## 8. False-positive emergency stops (collision avoidance)

**2026-06-09 14:03 -04:00** — Operator reports the boat is *often*
emergency-stopping on false positives.

Confirmed path: `/bizzy/ca_safety` (the collision monitor) stops on
points in `/bizzy/collision_monitor/pointcloud`, which is the camera
sea-surface-segmentation **reflex** pointcloud
(`segments_to_pointcloud_reflex`, oak_forward), projected onto the
`z=0.0` water plane. Per `[[project_ca_independent_of_seasurfacelayer]]`
this is independent of the costmap / SeaSurfaceLayer.

Root mechanism: **no `min_points` / persistence filter and no confidence
threshold** is exposed on either `ca_safety` or the reflex source. So a
*single* spurious segmentation point landing in the stop polygon
(`stop_length 5.0 m × stop_width 4.0 m` ahead of base_link) trips a full
stop. Glint / wake / foam mis-segmented → one projected point in that
5×4 m box → e-stop.

Current geometry: stop 5.0×4.0 m, ttc_time_constant 4.0, slowdown
5–20 m × 6 m, source_timeout 1.0, source_loss_behavior passthrough.

Only runtime lever is the stop-polygon **geometry** (shrinking it trades
away reaction distance to real obstacles — operator risk call). The
durable fix (fewer false segmentations, or adding a points-persistence
filter) is upstream model/code work → wrap-up. **Awaiting operator
decision; no CA params changed.**

**2026-06-09 14:14 -04:00** — Operator authorized shrinking the stop box.
Set on `/bizzy/ca_safety` (verified via `param get`, both took):

- `stop_length` 5.0 → **3.0 m**
- `stop_width`  4.0 → **3.0 m**

Slowdown zone unchanged (5–20 m × 6 m). Mitigation only — fewer false
trips at the cost of shorter hard-stop reaction distance to real
returns. Runtime-only: **not durable across a nav/ca relaunch**; push to
YAML for permanence at wrap-up. Watch whether false e-stops drop without
real obstacles being missed.

## 9. M3 pipeline — soundings flowing, grid not producing

**2026-06-09 14:25 -04:00** — Operator asked whether M3 data is going
through the pipeline and producing a grid. Traced each stage:

- `m3/detections` ✓ **10 Hz** (`kongsberg_em_bridge` reading the M3)
- `m3/soundings` ✓ **9 Hz** (`detections_to_pointcloud`, active),
  frame_id `bizzy/m3`
- `m3/grid` ✗ — `cube_bathymetry` is **active**, publisher count 1,
  topic VOLATILE, **0 messages in 10 s**, 0 subscribers.

Ruled out the usual suspects:
- **Lifecycle**: `detections_to_pointcloud` and `cube_bathymetry` both
  `active`. (`kongsberg_em_bridge` not lifecycle, but clearly producing.)
- **TF**: `bizzy/map → bizzy/m3` resolves (~[154, 116, −26.8],
  updating ~1 Hz) — so it's not the `map`/`map_tide` startup race from
  `[[project_mru_global_startup_race]]`.

So the break is **inside the gridding stage**: `cube_bathymetry` has
active state, 9 Hz sounding input, and valid TF, but publishes no grid.
Not yet diagnosed (time-boxed). Candidate next steps: read its rosout
for gridding warnings, check publish-trigger/accumulation params, or
confirm whether it needs survey motion before the first grid. **No
changes made.**

## 10. M3 soundings are NOT being recorded (logger config gap)

**2026-06-09 14:47 -04:00** — Operator asked whether the soundings are
getting recorded. They are **not**, on the ROS side:

- `/bizzy/sonar_logger` subscribes only to `/bizzy/sensors/deltat/soundings`
  — the **DeltaT** sonar, decommissioned on BizzyBoat
  (`[[project_bizzyboat_deltat_removed]]`). Not subscribed to
  `m3/soundings`, `m3/detections`, or `m3/grid`.
- `/bizzy/logger` records none of them.

So the live M3 pipeline (detections 10 Hz, soundings 9 Hz) is **not being
bagged on gabby** — the logger config still points at the
removed sonar's topic. Likely the logger YAML (`bizzyboat.yaml`
`/**/sonar_logger:`) was never re-pointed from DeltaT to M3.

Note: raw M3 bathymetry may still be captured by **QINSy on mercat**
(per the sonar architecture) — not verified from gabby, and separate
from the ROS-side `m3/soundings` product.

Mitigation options (not yet actioned): (a) ad-hoc `ros2 bag record` of
`m3/soundings` + `m3/detections` + TF + odom now (one-off, like the
sidescan debug capture); (b) re-point the `sonar_logger` YAML
DeltaT→M3 + relaunch — durable but disruptive, → wrap-up. **No changes
made; awaiting operator.**

**2026-06-09 15:54 -04:00** — Operator: log M3 detections durably (they
are first in the pipeline — confirmed `kongsberg_em_bridge` →
`detections` → `soundings` → grid), and record ad-hoc for now. Both done:

- **Ad-hoc (mitigate-now):** background `ros2 bag record` (mcap/zstd_fast)
  to `~/data/logs/bizzy_m3/bag_2026-06-09T14.51.50_m3_detections/`,
  capturing `m3/detections` + `m3/soundings` + `/tf` + `/tf_static` +
  `/bizzy/odom` + `sound_speed`. Confirmed writing (~0.44 MB/3 s).
  Runs until stopped.
- **Durable:** edited `bizzyboat_project11/config/bizzyboat.yaml`
  `/**/sonar_logger:` topics — added `/bizzy/sensors/m3/detections`
  (YAML validated). **Not yet active**: the running logger uses the
  installed copy, and config is `install(DIRECTORY)`-copied, so this
  needs a **rebuild + sonar_logger relaunch** to take effect — deferred
  (disruptive mid-op). The ad-hoc bag bridges until then. Left the dead
  `deltat/soundings` line in place, flagged for wrap-up cleanup.

Uncommitted on `jazzy`: this log + the `bizzyboat.yaml` edit (batched
per urgency contract; commit at a breakpoint).

## 11. Can't send mission / change autonomy mode — command link down

**2026-06-09 16:01 -04:00** — Operator reports unable to send mission or
change autonomy mode. Checked boat-side command path:

- All command-path **nodes alive**: `command_bridge_receiver`,
  `helm_manager`, `mission_manager`, `udp_bridge`, `platform_sender`,
  `echo_helm`, `ca_safety`.
- But the **entire marine command channel is silent**, incl. the
  normally-always-on heartbeat: `marine/heartbeat`,
  `marine/status/mission_manager`, `marine/command`, `marine/response`
  all silent over 3 s.
- `command_bridge_receiver` listens on `/bizzy/marine/command` (silent).
- `udp_bridge` (port 4200) has **no connected peer** (`remotes host: ''`,
  `port: 0`) — normally it learns the topside address on connect.

Conclusion: break is the **boat↔topside UDP command link** — topside
isn't connected/sending, so commands never reach `command_bridge_receiver`
→ helm/mission managers. Boat-side autonomy is healthy and would act if
commands arrived. **Not caused by this session's changes** (sidescan
transmit, CA stop-box params, read-only ad-hoc recorder, source-only
config edits — none touch the marine channel / udp_bridge).

Handed to operator to check topside command app + radio link (operator
has ground truth on comms; no boat-side hardware/network commands fired
on inference). No changes made.

## 12. Correction — boat recovered, stack down intentionally

**2026-06-09 16:49 -04:00** — Operator clarified: **the boat has been
recovered and the ROS stack is down by design.** Re-frames §11 and the
follow-on investigation:

- The silent marine command channel (§11), the node list dropping to 1,
  the data plane stopping, and "no zenoh router running" are **all the
  intended post-recovery shutdown — not a fault.** I over-investigated a
  non-issue instead of asking; phase had moved prep/launch/underway →
  **recovery** and I didn't catch the cue. (`[[feedback_track_deployment_phase]]`,
  `[[feedback_scribe_not_detective]]`.)
- **mercat = 192.168.20.8 runs a proxy to reach the Garmin** — so the
  earlier "mercat resolves to the GCV's IP" is the **proxy architecture,
  not an IP collision.** No conflict.
- Ad-hoc M3 bag (§11) stopped + finalized cleanly: 346 MB, metadata
  written, ~14:51–16:49 in-water `m3/detections`+`soundings`+TF+odom.

Phase: **recovered**. Awaiting operator on wrap-up.
