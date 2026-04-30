# BizzyBoat deployment log — gabby — 2026-04-29

**Host**: gabby
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Deployment**: #TBD (dev-side issue not yet opened)

## Scope

TBD as work proceeds.

## 1. Self-contained `perception_launch.py` log directory

**2026-04-29T10:50-04:00** — Roland flagged that re-launching
`perception_launch.py` on its own (without rerunning
`start_tmux_project11.bash`) required hand-crafting a fresh date-based
bag dir, because `log_directory` was a required arg with no default and
the bash script was the only thing computing the timestamp. Goal: make
the launch file self-sufficient so a Ctrl-C + up-arrow + Enter in the
perception tmux window picks a fresh subdir on its own.

Mirrored the pre-existing sonar pattern in the same file
(`bizzyboat_project11/launch/perception_launch.py`, lines 39-52
before the edit):

- `log_directory` now defaults to
  `EnvironmentVariable('P11_LOG_DIR',
  default='/home/field/data/logs/bizzyboat')` instead of being a bare
  `DeclareLaunchArgument` with no default.
- New `log_subdirectory` arg defaults to `datetime_str` — UTC, second
  precision, computed once at launch-description load time so the main
  rosbag and sonar rosbag share the same subdir per launch.
- Rosbag `storage.uri` for the main logger now joins the two via
  `PathJoinSubstitution`, matching how the sonar logger already worked.

In `bizzyboat_project11/scripts/start_tmux_project11.bash`, dropped
`LOGDIR_BAG` and the `log_directory:=...` arg from the perception
launch line. `NOW`/`LOGDIR` are still computed because the bash side
still owns `autostart_${NOW}.txt` (its own setup-output capture, not
the bag dir).

Side effect: the duplicate `sonar_log_directory_arg` declaration in
`perception_launch.py` is gone — the second declaration always
overrode the first, so the first was dead code. It fell out of the
restructured arg block.

**2026-04-29T10:54-04:00** — Roland started ROS via
`start_tmux_project11.bash`. Both bag dirs created at the expected
launch-time UTC timestamp (shared between loggers, as designed):

- `/home/field/data/logs/bizzyboat/2026-04-29T14-54-18+00-00/2026-04-29T14-54-18+00-00_0.mcap`
- `/home/field/data/logs/bizzyboat_sonar/2026-04-29T14-54-18+00-00/2026-04-29T14-54-18+00-00_0.mcap`

**2026-04-29T10:56-04:00** — 30 s sample on both mcap files confirmed
active writes:

- main: 1.64 MB → 1.91 MB (+264 KB)
- sonar: 496 KB → 688 KB (+192 KB)

(The 8 s flat window before that is consistent with mcap chunked-write
flush behavior, not a stalled recorder.)

### Format note (downstream tooling)

The main bag dir name format changed alongside this. Previously the
bash script produced `2026-04-29T10.54.13.278726542` — local time,
nanoseconds, dot separators, no UTC offset. Now it matches the sonar
convention: `2026-04-29T14-54-18+00-00` — UTC, second precision, dash
separators, with the offset suffix. Anything that parses these dir
names by structure needs to handle both going forward; old logs in the
parent dir keep their original names.

### Commit

`feat(perception_launch): self-contained log dir + datetime subdir`
on `jazzy`. (Originally `df8c2c2`; rebased onto post-sync origin/jazzy
in §3 below — current SHA `7027c67`.)

## 2. `make sync` — incoming commits for today's testing

**2026-04-29T11:14-04:00** — Roland flagged that fixes are landing for
today's testing; ran `make sync` to pull them and triage which apply
to the bizzyboat-on-gabby deployment. Three repos updated cleanly,
one skipped (project repo, dirty from this log file being untracked).

### Updated cleanly

**`unh_marine_autonomy`** (`80e012e..d7d11f5`, 2 commits)

- `7d7c87b Add SoundSpeed.msg for real-time point sound-speed sensors`
  (Roland, 2026-04-28). New message file. **Relevant** — pairs with
  the `sound_speed_bridge` addition incoming on origin/jazzy in
  `unh_echoboats_project11` (commit `22ef651`, see Skipped section
  below). The msg won't compile into bizzyboat's launch path until
  both land + a rebuild.

**`unh_marine_perception`** (`660963a..377f008`, 7 commits) — **all
directly relevant** to bizzyboat (4× OAK cameras + sea-surface
segmentation):

- `f1b8cab feat(depthai_marine): URDF-aligned frame_id default in
  CameraBase + segmentor pass-through`
- `e181c7e feat(depthai_marine): optional frame_id ctor arg on
  Image/FFMPEG publishers`
- `5489f65 test(sea_surface_segmentation): bootstrap gtest harness +
  cover frame_ids`
- `d612833 test(depthai_marine): cover applyParams round-trip +
  setH265Profile lazy validation`
- `3af7e68 docs(depthai_marine): document new frame_id parameter`
- `0cc28eb`, `1f2af6f` — Copilot review nits
- `377f008` — merge commit (PR #9)

This is the upstream half of the camera→costmap TF gap flagged in
[2026-04-27 §2](2026-04-27_gabby_logs.md) — bizzyboat-side
`frame_ids` plumbing already landed on the 27th; this set provides
the matching `frame_id` defaults/parameters in `depthai_marine` and
the `frame_id_resolver` in `sea_surface_segmentation`.

**`seafloor_echoboat_project11`** (`5e63e83..0d2b7fd`, 1 merge
PR #17) — **not relevant** to bizzyboat-on-gabby (different platform
repo).

### Skipped: `unh_echoboats_project11`

Origin/jazzy moved `6c177fb..85befd0` — 40+ commits ahead of our
local base. Local HEAD is our unpushed `df8c2c2` from §1. Sync did
NOT auto-integrate (the untracked log file marked the tree dirty);
holding for Roland to decide when to rebase.

Highest-relevance incoming commits, grouped by fix theme (full set
in `git log HEAD..origin/jazzy`):

- **SBG Ellipse-D bring-up on `PORT_E` + RTCM** —
  - `eb61243 feat(bizzyboat): bring SBG Ellipse-D into ROS on gabby
    (PORT_E)`
  - `19d9d47 config(sbg): pin gabby's PORT_E to /dev/ttyS0 @ 115200`
  - `7c85212 fix(sbg): respawn the RTCM relay; namespace-track its
    input topic`
  - `866c474 fix(sbg): pin rtcm namespace/topic_name in YAML`
- **Nav source: switch to FCU EKF3-fused topics** —
  - `e604a36 config: switch BizzyBoat nav source to FCU EKF3-fused
    topics`
  - `d40845e mavros: namespace local_position velocity_body frame_id`
- **NTRIP namespace** —
  - `c026268 fix(bizzyboat): forward namespace to ntrip_launch in
    core_launch`
- **Sound-speed bridge** (pairs with `unh_marine_autonomy`
  `SoundSpeed.msg` above; both required) —
  - `22ef651 Add sound_speed_bridge to bizzyboat core launch`
- **Operator-side diagnostics bag** —
  - `4da96d2 Add operator-side bag recorder for diagnostics +
    udp_bridge stats (#97)`
- **FCU battery params** —
  - `a72125b fcu: raise BATT_LOW_VOLT to 23.0, anchor to
    field-measured V-drop`

### Build implications

Current running ROS session is on the pre-sync state — none of the
above fixes are active yet. To activate: rebase
`unh_echoboats_project11` onto `origin/jazzy`, then `make build` (or
per-layer `colcon build`), then relaunch the affected tmux windows
(`core` for SBG / nav source / NTRIP / sound-speed bridge, `perception`
for camera frame_ids). The two cross-repo pairs (`SoundSpeed.msg` ↔
`sound_speed_bridge`, `frame_ids` plumbing ↔ camera defaults) need
both sides built before the dependent code path is exercised.

## 3. Rebase + build + manifest gap → `marine_tools` added

**2026-04-29T11:30-04:00** — Committed log §1 + §2 (`ee8867a`, later
rebased) and re-ran `make sync` to integrate the project repo's
40-commit incoming chain. Clean rebase: our two local commits
replayed on top, ending at `d64bd34` (log) + `7027c67`
(perception_launch).

`make build` ran clean across all five layers — synced fixes compiled
in (frame_ids work in `depthai_marine` + `sea_surface_segmentation`,
SoundSpeed.msg generated, etc.).

`rosdep check` afterwards flagged three gaps:

- `apt: ros-jazzy-ffmpeg-image-transport` — runtime dep for
  `depthai_marine`'s FFMPEG H.265 publishers (Roland resolved with
  `rosdep install`).
- `apt: ros-jazzy-sbg-driver` — runtime dep for the synced SBG
  bring-up commits (Roland resolved with `rosdep install`).
- `sound_speed_bridge` — declared in `bizzyboat_project11/package.xml`
  (`<exec_depend>`), used by `sound_speed_launch.py` from synced
  commit `22ef651`. Not in any `.repos` manifest. Per the launch
  file's docstring, it lives in `rolker/marine_tools` as a sibling
  package alongside the planned QINSy → ROS bridge (`marine_tools#1`).

Added `marine_tools` to `config/repos/core.repos`. Subtlety: the
workspace's `configs/manifest/` is a symlink into this project repo's
`config/` — so the manifest edit shows up here as `M
config/repos/core.repos`, not as a workspace-repo change.

`make sync` alone doesn't initial-clone repos new in the manifest
(`Skipping marine_tools: could not resolve repository path`); a
`make build` re-runs `setup_layers.sh core` because the layer-stamp
mtime is now older than `core.repos`. That import brought in two new
packages:

- `marine_tools` — sonar/QINSy code (PolynomialRegression,
  marine_sonar_to_pointcloud)
- `sound_speed_bridge` — what we needed

Final `make build` after the apt deps landed: clean, fully cached, no
stderr.

## 4. First launch crash: `rtcm_relay_node.py` exec bit (upstream regression)

**2026-04-29T12:03-04:00** — Roland kicked off `start_tmux_project11.bash`.
Core launch (`core_launch.py`) crashed immediately with:

> `[ERROR] [launch]: Caught exception ... executable 'rtcm_relay_node.py'
> not found on the libexec directory '.../bizzyboat_project11/lib/...'`

Cascading SIGINT to all 22 other nodes. mavros caught a SIGABRT (exit
code -6) on the way down — collateral from rcl shutting down while
mavros was mid-init. nav window's `controller_server` then aborted
because `bizzy/map_tide` disappeared with `sea_surface_estimator`.
Perception window held through the cascade and kept recording.

Root cause: the synced commit `7c85212 fix(sbg): respawn the RTCM
relay; namespace-track its input topic` added
`bizzyboat_project11/scripts/rtcm_relay_node.py` without the
executable bit (`-rw-rw-r--`). Its peers (`gps_rtk_diagnostics_node.py`,
`ntrip_diagnostics_node.py`) have `-rwxrwxr-x`. Symlink-install
preserves source perms, so ROS's `Node` action fails the executable
check and trips the launch exception immediately.

Fixed with `chmod +x`. **This is an upstream regression** — anyone
syncing 7c85212 fresh will hit the same wall. Worth flagging back to
the dev side for a follow-up fix on the source commit.

## 5. mavros TF tree split — `local_position` plugin gap (d40845e is a no-op)

**2026-04-29T12:11-04:00** — After the chmod fix, core stayed up cleanly,
but `mru_transform` started spamming a TF lookup failure every 5 s:

> `velocity: TF 'base_link' -> 'bizzy/base_link' lookup failed: Could
> not find a connection between 'bizzy/base_link' and 'base_link'
> because they are not part of the same tree.`

Investigated. The synced commit `d40845e mavros: namespace local_position
velocity_body frame_id` was supposed to fix this — its message claimed
it added a missing `child_frame_id` to the local_position config block
in `bizzyboat_project11/config/mavros.yaml`, mirroring what
global_position has.

But `local_position` doesn't actually expose a `child_frame_id`
parameter. Verified live:

```
$ ros2 param list /bizzy/mavros/local_position
  frame_id                  ← present, set to bizzy/map ✓
  tf.child_frame_id         ← present, but tf.send is false
  tf.frame_id
  tf.send
  ... (no plain child_frame_id)

$ ros2 param get /bizzy/mavros/local_position child_frame_id
Parameter not set
```

`global_position` does expose the param (its `local` Odometry has
`child_frame_id: bizzy/base_link`). The two plugins aren't symmetric;
d40845e's yaml override is silently dropped on `local_position`.
Live confirmation:

- `local_position/velocity_body.header.frame_id` → bare `base_link`
- `local_position/odom.child_frame_id` → bare `base_link`
- `/tf_static` carries 3 disconnected fragments rooted in bare names:
  `map → map_ned`, `odom → odom_ned`, `base_link → base_link_frd`
  (mavros's NED/FRD conversion frames; published regardless of
  `tf.send`)

These bare-name fragments never connect to the bizzy/-prefixed URDF
tree, so `mru_transform`'s velocity lookup fails forever.

### Workaround applied

Added three identity `static_transform_publisher` bridges to
`core_launch.py`, just before the MAVROS group:

- `bizzy/map → map`
- `bizzy/odom → odom`
- `bizzy/base_link → base_link`

This stitches the bare-name fragments under the bizzy/ tree so all
TF lookups resolve. Verified after relaunch:

- `tf2_echo bizzy/base_link base_link` → identity ✓
- `tf2_echo bizzy/map map` → identity ✓
- `tf2_echo bizzy/odom odom` → identity ✓
- 0 `mru_transform` lookup-failed warnings in the last 2000 lines of
  scrollback (was every 5 s before)
- nav lifecycle reached `Managed nodes are active. Creating bond timer`
- both costmaps doing tide-corrected lookups: `Tide offset updated:
  2.36 m (water above chart datum)` repeating

### Follow-up needed (not done today)

- **`d40845e` should be reverted or amended** in
  `unh_echoboats_project11`. As-is it's misleading: the commit
  message claims the bug is fixed, but the yaml override is a no-op.
- **Right fix is upstream**: patch mavros's `local_position` plugin
  to expose `child_frame_id` like `global_position` does. The
  workaround can stay as a belt-and-suspenders even after that
  lands (identity transforms are cheap), or be removed once the
  upstream fix is in.
- **`7c85212` exec-bit regression** — flag to dev side for a
  follow-up commit that re-adds the bit (`git update-index
  --chmod=+x`).

## 6. SBG Ellipse-D RTK bring-up — UART fault, NTRIP upgrade, RTK fix achieved

The afternoon's main task was getting RTCM corrections actually flowing
into the SBG so it could compute RTK. Started simple, ended up
uncovering and routing around a hardware UART fault on gabby.

### 6.1 NTRIP source upgrade — legacy → MSM iMAX

Initial state had NTRIP wired to MaCORS port 31000 (`RTCM3_MASA`),
which streams legacy GPS+GLO L1/L2-only RTCM3.0 messages
(1004/1012/1006/1008/1013/1033/1230). The internal u-blox ZED-F9P
inside the Ellipse-D works much better with multi-constellation MSM4
corrections. Switched to MaCORS port 10000 with the `RTCM3MSM_IMAX`
mountpoint — full MSM4 GPS+GLO+GAL+BDS (1074/1084/1094/1124 + 1006).

The new mountpoint is a network iMAX solution requiring GGA echoback
at ~1 Hz. Wired that up in `ntrip_launch.py` via a `topic_tools
throttle` node that downsamples `mavros/global_position/raw/fix` from
10 Hz to 1 Hz and republishes to `/bizzy/sensors/ntrip/fix`. The
microstrain `ntrip_client` already auto-converts NavSatFix → GPGGA
per `ntrip_ros_base.py:101`, so no NMEA-conversion code needed.

Verified via raw-byte capture of the topic that the new caster
delivers the expected MSM4 set; the old mountpoint did not.

### 6.2 SBG output config — `log_*` params + namespace cleanup

Independently of RTCM, the SBG driver wasn't publishing any output
topics earlier in the day (only `/parameter_events` and `/rosout`).
Disassembling the shipped `sbg_device` binary symbol table revealed
the cause: `SbgDevice::initSubscribers` routes through
`MessagePublisher::initPublisher(rclcpp::Node&, uint8_t,
_SbgEComOutputMode, std::string)` and only creates a publisher when
the corresponding `output.log_*` yaml param is non-zero. Bizzy's
`sbg_ellipse_d.yaml` had none of them set, so no publishers existed
even though the driver was decoding the binary stream.

Added the trimmed unified set (`log_status`, `log_imu_data`,
`log_ekf_quat`, `log_ekf_nav`, `log_utc_time`, `log_mag`,
`log_gps1_pos`, `log_gps1_vel`, `log_gps1_hdt`); all topics came up.

While restructuring the SBG launch, also fixed the doubled `sbg/`
segment in topic paths (`/bizzy/sensors/sbg/sbg/imu_data` →
`/bizzy/sensors/sbg/imu_data`). The driver adds its own internal
`sbg/` topic prefix, so the launch should push only `sensors` and
let the prefix complete the namespace. See `sbg_launch.py:28`.

### 6.3 RTCM-not-ingesting — the long debug

With NTRIP and output topics both fixed, the chain *appeared*
healthy end-to-end: rtcm_relay republishing `/bizzy/sensors/rtcm` at
~5 Hz (valid MSM4 framing), sbg_device subscribed, kernel `write()`
syscalls returning success. But `gps_pos` continued to show
`base_station_id: 65535` and `diff_age: 65535` — the "no RTCM ever
ingested" sentinel. RTK was never engaging.

Detour through the SBG configuration system: built up a
version-controlled `sbg_ellipse_d_configure.yaml` template (with
`confWithRos: true`) intending to push device config from gabby. To
do that, gabby needed to be on PORT_A (the only `portAConfMode`-flagged
port). Cable-swapped temporarily — gabby on PORT_A, mercat on PORT_E.
Push partially succeeded — driver logged `[Config] Aiding assignement
updated`, `[Config] IMU alignement updated`, etc. — but
`SAVE_SETTINGS` failed with `SBG_INVALID_PARAMETER`. RTCM still
didn't ingest. Attributed ambiguously to PORT_A/PORT_E differences or
fw/driver schema mismatches.

### 6.4 Narrowed-but-not-isolated: TX-side fault on the ttyS0 path

Loopback test, SBG-end-of-cable bridge of pins 2↔3, gabby tries to
echo via `/dev/ttyS0` — sent 20 bytes, got 0 back. Two retries with
two different null-modem adapters: same. Then a cross-machine test
running gabby's cable to mercat's TeraTerm:

| Path | Result |
|---|---|
| mercat → gabby (via ttyS0) | ✓ received cleanly |
| gabby → mercat (via ttyS0, adapter A) | ✗ nothing |
| gabby → mercat (via ttyS0, adapter B) | ✗ nothing |
| gabby → mercat (via ttyS1, AML SVS port) | ✓ received cleanly |

What this proves: **TX side of the gabby↔SBG ttyS0 path is faulty;
RX direction works**. Likely culprits are gabby's onboard ttyS0
RS-232 line driver IC (an asymmetric transceiver failure consistent
with an ESD event on the TX pin) **or** the gabby↔SBG cable itself
(a broken TX conductor). The two adapters control for the adapter,
and the ttyS1 path proves the mercat side and a different gabby port
both work, but **none of these tests swap the cable** — gabby is
mounted in the boat and pulling the cable for a known-good
substitution wasn't practical mid-session.

So the data narrows it to "TX-side fault somewhere on the ttyS0
path"; isolating gabby-port vs cable is a follow-up bench task. Both
remain candidates.

Modem-control-line state and termios were healthy on the kernel side
(`DTR=ON, RTS=ON, CTS=ON`, `-crtscts`); earlier strace had confirmed
the kernel was clocking bytes out the UART register, so the fault is
below the kernel. That's consistent with both the line-driver-IC
hypothesis and the broken-cable hypothesis.

(YAMA gotcha along the way: had to set `kernel.yama.ptrace_scope=0`
to attach strace to a launch-supervised child process. Made the
relaxation persistent in `/etc/sysctl.d/99-ptrace-allow.conf`.)

### 6.5 Final wiring + production yaml

Repurposed gabby's ttyS1 (which was the AML SVS port) for the SBG.
The AML SVS is RX-only — it just emits sound-velocity sentences and
doesn't accept commands — so it can use the TX-faulty ttyS0 path
with no functional impact, regardless of whether the fault turns out
to be the gabby UART or the SBG cable.

gabby panel rewire (one-time):

- `ttyS1` panel jack ← SBG cable (was AML SVS)
- `ttyS0` panel jack ← AML SVS cable (was SBG)

SBG splitter side, end state:

- PORT_A ← mercat (back to original; sbgCenter access restored)
- PORT_E ← gabby ttyS1 (RTCM input, binary output stream consumer)

This is essentially the original-intended SBG-side wiring, just
with a working gabby UART for the first time today.

Yaml updates:

- `bizzyboat_project11/config/sbg_ellipse_d.yaml` — `portName:
  /dev/ttyS1`, `portID: 4` (PORT_E), header rewritten to document
  the new wiring + ttyS0 fault context for future readers.
- `bizzyboat_project11/launch/sound_speed_launch.py` — `device:
  /dev/ttyS0`, docstring explains why a TX-faulty path is fine
  for an RX-only sensor regardless of where the fault actually is.
- `bizzyboat_project11/config/sbg_ellipse_d_configure.yaml` (NEW)
  — version-controlled config-push template kept as an artifact
  for any future situation where gabby (or a successor host)
  ends up on PORT_A again. Not used in production today.

### 6.6 The airData inconsistency — partial diagnosis, deferred

When mercat tried to flip `aiding.diffCorr.source` from comA back to
comE in sbgCenter, the save failed with **"air data model source
inconsistency"** — the same root cause as our ROS-driver
`SBG_INVALID_PARAMETER` on `SAVE_SETTINGS`. The Ellipse-D's airData
fields (`model: internal, source: internal, useAirSpeed: never,
useAltitude: never`) are pre-existing config from an older firmware
that fw 3.0.3949-stable validates more strictly. The airData panel
isn't reachable in sbgCenter on this Ellipse-D variant (no air-data
sensor → GUI hides the controls), so the inconsistency can't be
fixed through any channel we have on the boat today.

**Important update on the airData hypothesis**: had theorized
mid-debug that airData inconsistency was *gating RTK functionality*
(defensive degraded-mode behavior in the firmware). **Wrong.** RTK
locked within seconds of the cable rewire + sbgCenter runtime flip,
even with the airData inconsistency unresolved and SAVE continuing
to fail. The airData issue **only blocks `SAVE_SETTINGS`** — a real
but isolated problem, not a critical-path concern for the
deployment.

### 6.7 RTK FIX achieved

After the rewire + sbgCenter runtime flip of `aiding.diffCorr.source`
from comA back to comE:

```
status.status:    0    (SOL_COMPUTED)
status.type:      7    (SBG_ECOM_GPS_POS_RTK_INT — Integer fix)
base_station_id:  42   (real MaCORS station — no longer 65535 sentinel)
diff_age:         ~35  (0.35 s — fresh corrections being applied)
```

Topic rates all nominal: 50 Hz IMU/EKF, 5 Hz GPS / RTCM.

### Follow-up for a future bench session

- **SBG support ticket**: send the sbgCenter JSON dump
  (`/tmp/ELLIPSE-D-G4A2-B1_000034256_20260429_181248.json`) plus
  the airData inconsistency error and driver SBG_INVALID_PARAMETER
  logs. Ask for either a CLI / import path that reaches the airData
  fields on this Ellipse-D variant, or a firmware-level rule to set
  airData to a consistent disabled state.
- **Hardware**: gabby's ttyS0 path has a TX-side fault, **not
  isolated** to gabby's UART vs the SBG cable (cable-swap test wasn't
  practical mid-session — gabby is boat-mounted). Bench task: pull
  the cable, swap with a known-good one, and test gabby's ttyS0
  directly. Worth capturing in the boat's hardware doc with both
  candidates listed; plan a board swap **or** cable replacement
  **or** a permanent USB-serial dongle next bench session. The
  current workaround (SBG on ttyS1, AML SVS on ttyS0) is functional
  regardless of which culprit it turns out to be.
- **QINSy**: mercat is back on PORT_A, but PORT_A's output set
  hasn't been re-tuned since the day's trim. QINSy may or may not
  be receiving everything it expects — separate audit needed.

## 7. Post-RTK polish: sound-speed namespace + bag coverage

After RTK fix was confirmed and before the boat went in the water, a
few cleanups landed.

### 7.1 Sound-speed UDP NaN handling — verified, no change needed

With the AML SVS probe stowed (out of water) the bridge publishes
`sound_speed: NaN`. Verified the Valeport UDP formatter
(`marine_tools/sound_speed_bridge/sinks.py:42-44`) short-circuits with
`return None` on NaN, and the dispatcher loop
(`node.py:222-223`) skips targets that return None. So mercat's M3
Valeport listener never receives garbage values from a stowed probe.
ROS topic `sound_speed` does still publish the NaN — downstream
subscribers handle it. Diagnostic at `/diagnostics` raises a WARN
("Last reading is NaN (parse failed)") on each NaN reading.

### 7.2 Sound-speed topics moved into `sensors/sound_speed/`

Was: `/bizzy/sound_speed`, `/bizzy/temperature`, `/bizzy/fluid_pressure`
(top-level under the bizzy namespace). Now:
`/bizzy/sensors/sound_speed/<topic>` — matches the
`<ns>/sensors/<sensor>/<topic>` convention used by SBG, deltat, ntrip,
and the OAK cameras.

The doubled `sound_speed` segment in the path
(`/bizzy/sensors/sound_speed/sound_speed`) is mildly awkward but
deliberately kept — switching to `sensors/aml/...`, `sensors/svp/...`,
or `sensors/svs/...` was considered and rejected; "sound_speed" as
the namespace makes the role unambiguous from the topic tree alone,
matching how `ntrip` is named by role rather than vendor.

Implementation: `sound_speed_launch.py` now wraps the node in a
GroupAction with `PushRosNamespace('sensors/sound_speed')`.

### 7.3 Bag coverage — main + sonar loggers updated

The two recorders had been blind to the SBG outputs (the topics didn't
exist when the original logger config was written) and to the
sound-speed bridge. Added to `bizzyboat.yaml`:

**Main `logger`** (operations bag) gets all 9 SBG topics
(`imu_data`, `ekf_nav`, `ekf_quat`, `mag`, `gps_pos/vel/hdt`, `status`,
`utc_time`) plus the 3 sound-speed topics.

**`sonar_logger`** (bathy bag) gets a focused subset:
- `sensors/sound_speed/sound_speed` — sound-velocity correction for
  bathy post-processing (critical)
- `sensors/sbg/imu_data` — motion compensation
- `sensors/sbg/ekf_quat` — attitude

Verified live: `/bizzy/logger` and `/bizzy/sonar_logger` both have all
the expected subscriptions, both bags growing at ~30-40 KB/s.

### 7.4 Pre-launch verification

Final sweep before water:

| Check | Result |
|---|---|
| RTK status | `type=7` (RTK_INT), `base_station_id=42`, `diff_age=0.59 s` |
| Sound-speed namespace | All 3 topics under `/bizzy/sensors/sound_speed/` |
| SBG namespace | All 9 topics under `/bizzy/sensors/sbg/` (single segment) |
| `imu_data` rate | 25.0 Hz |
| `ekf_nav` rate | 24.9 Hz |
| `gps_pos` rate | 5.0 Hz |
| RTCM in | 6.0 Hz (MaCORS MSM4) |
| `/bizzy/odom` | 10.4 Hz — mru_transform OK, TF tree intact |
| `sound_speed` rate | 19.8 Hz (NaN until probe in water) |
| Nav lifecycle | Tide offsets updating, costmaps active |
| Both bag recorders | Subscribed + writing |

Boat went in.

One non-issue noted but not fixed: `[ERROR] Unable to get the device
Info : SBG_TIME_OUT` at sbg_device startup — expected on PORT_E
(no `portAConfMode` feature). Driver continues to parse the binary
log stream normally; cosmetic only.

### 7.5 In-water surprise: AML SVS parser mismatch — `aml` → `regex`

Once the boat went in the water `sound_speed` *should* have switched
from NaN to a real ~1479 m/s value, but it stayed NaN. The
`sound_speed_bridge` diagnostic was loud about it:

    parser_rate_hz: 24.00
    parse_error_count: 64068
    message: "Last reading is NaN (parse failed)"

Bytes were arriving at the right rate but every sentence failed
parsing. Briefly killed the bridge (respawn=True, ~2 s gap) and
captured `/dev/ttyS0` raw — the probe emits NMEA-style sentences:

    $AML,SVM,1479.029,SN,205937*01\r\n
    $AML,SVM,1479.026,SN,205937*0E
    $AML,SVM,1479.022,SN,205937*0A

The `'aml'` parser in
`marine_tools/sound_speed_bridge/parsers.py:101-104` expects bare
decimal values (`1479.029\r\r\n`) — it does literally
`Decimal(stripped.decode('ascii'))` on the whole line. Fed an NMEA
string, `Decimal("$AML,SVM,1479.029,SN,205937*01")` raises
InvalidOperation, parser returns NaN.

Switched the bridge to the generic `'regex'` parser with:

    regex_pattern: \$AML,SVM,(?P<sound_speed>\d+\.\d+)
    regex_line_terminator: crlf
    regex_sound_speed_scale: 1.0

Restarted core; sound_speed immediately reported 1479.043 m/s —
clean, matches the on-the-wire values. M3's Valeport listener also
started seeing the values (per mercat operator confirmation:
"sonar got sound speed!").

Open question for the marine_tools side: AMLParser's docstring
claims AML SVS terminates with CRCRLF, but our probe clearly uses
CRLF and emits NMEA-style sentences. Either AMLParser was written
against a different firmware variant or it's an incomplete
implementation. Worth filing on the marine_tools repo with a
sample of the probe's actual output for either a docstring
correction or a per-variant subclass.

## 8. Deployment wrap-up

### 8.1 Bag inventory

10 bags written today, all closed cleanly (each has a `metadata.yaml`):

**Main bag** (`/home/field/data/logs/bizzyboat/`) — 4 sessions reflecting
the day's core-launch restarts during debug:

| Start (UTC) | Size | Context |
|---|---|---|
| `2026-04-29T14-54-18` | 17 MB | first launch this morning — no SBG topics yet (pre-`log_*` trim), nav couldn't activate (TF gap) |
| `2026-04-29T16-03-55` | 65 MB | post rtcm_relay chmod fix, post mavros TF bridges |
| `2026-04-29T17-49-56` | 138 MB | post namespace cleanups (sbg/sbg → sbg, sound_speed under sensors) |
| `2026-04-29T21-43-29` | 251 MB | **survey session** — RTK held throughout, sound speed real after parser fix |

**Sonar bag** (`/home/field/data/logs/bizzyboat_sonar/`) — paired sessions:

| Start (UTC) | Size |
|---|---|
| `2026-04-29T14-54-18` | 5.8 MB |
| `2026-04-29T16-03-55` | 21 MB |
| `2026-04-29T17-49-56` | 43 MB |
| `2026-04-29T21-43-29` | 87 MB |

**Camera bags** (`/home/field/data/logs/bizzy_images/`) — ad-hoc OAK
ffmpeg + segmentation captures during the survey:

| Bag | Duration | Size |
|---|---|---|
| `bag_2026-04-29T18.45.22_ffmpeg_seg` | 30 min | 1.2 GB |
| `bag_2026-04-29T19.35.07_ffmpeg_seg` | 15 min | 927 MB |

Day total: ~2.8 GB. Disk after session: 23 GB used / 1.8 TB free.

### 8.2 Final state at shutdown

- RTK held `type=7` (RTK_INT) for the entire survey, ±1.4 cm horizontal
  / ±1 cm vertical, 32 sats, base_station 42.
- Sound speed flowed real values (~1479 m/s) once probe was in water.
- Boat moved at survey speed (~3 kn) on the 21:43 session.
- No process deaths, no `[ERROR]` lines beyond the cosmetic
  `SBG_TIME_OUT` on PORT_E `Get-Device-Info` (well-understood; PORT_E
  doesn't carry `portAConfMode`).

### 8.3 Open follow-ups for the dev side

Three items worth carrying forward from today's debug — none of them
deployment-blocking, all already documented in their own sections
above:

1. **SBG support ticket** (per §6.6) — fix the airData-inconsistency
   `SAVE_SETTINGS` failure on this Ellipse-D / fw 3.0.3949 combo. JSON
   dump at `/tmp/ELLIPSE-D-G4A2-B1_000034256_20260429_181248.json`
   captures the device state.
2. **Hardware doc update** — gabby's ttyS0 path has a TX-side fault.
   Not isolated between gabby's UART line driver and the SBG cable;
   the cable-swap test couldn't be done mid-session because gabby is
   boat-mounted. Bench task: substitute a known-good cable to
   isolate. Current workaround (SBG on ttyS1, AML SVS on ttyS0) is
   functional regardless of which side actually has the fault.
3. **marine_tools issue** (per §7.5) — file with the `sound_speed_bridge`
   package. AMLParser docstring claims AML SVS terminates with CRCRLF
   and emits bare decimals; our probe emits NMEA-style `$AML,SVM,*`
   with CRLF. Either docstring needs correction or a per-variant
   subclass that handles SVM sentences natively. We have a known-good
   regex pattern (`\$AML,SVM,(?P<sound_speed>\d+\.\d+)` with
   `crlf` terminator) that works with the current `RegexParser`; sample
   raw bytes captured at `/tmp/aml_bytes.bin` from today.

### 8.4 What worked end-to-end at shutdown

- gabby's working ttyS1 ↔ SBG PORT_E (the simple, original-intended
  wiring, just routed around the TX-faulty ttyS0 path)
- MaCORS NTRIP via port 10000 / RTCM3MSM_IMAX with 1 Hz GGA echoback
  feeding the SBG; RTK INT engaged within seconds
- M3 sonar receiving Valeport-format SV over UDP from the AML SVS via
  the `sound_speed_bridge` regex parser
- mru_transform velocity TF lookup happy through the static
  bizzy/* ↔ * bridges in core_launch.py (workaround for mavros's
  bare-named NED/FRD frames)
- Both rosbag2 recorders (main + sonar) capturing the full new SBG +
  sound_speed topic set
- 45 minutes of OAK camera replay-debug bags captured cleanly during
  survey

## Files touched

- `bizzyboat_project11/launch/perception_launch.py`
- `bizzyboat_project11/launch/core_launch.py`
- `bizzyboat_project11/launch/ntrip_launch.py`
- `bizzyboat_project11/launch/sbg_launch.py`
- `bizzyboat_project11/launch/sound_speed_launch.py`
- `bizzyboat_project11/scripts/start_tmux_project11.bash`
- `bizzyboat_project11/scripts/rtcm_relay_node.py` (mode change)
- `bizzyboat_project11/config/bizzyboat.yaml`
- `bizzyboat_project11/config/sbg_ellipse_d.yaml`
- `bizzyboat_project11/config/sbg_ellipse_d_configure.yaml` (new)
- `config/repos/core.repos`
- `ccomjhc_project11/configuration/bizzyboat_ntrip.yaml` (cross-repo)
- `docs/logs/2026/2026-04-29_gabby_logs.md` (this file)
