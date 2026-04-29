# BizzyBoat deployment log — gabby — 2026-04-29

**Host**: gabby
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Deployment**: #TBD (dev-side issue not yet opened)

## Scope

TBD as work proceeds.

## 1. Self-contained `perception_launch.py` log directory

2026-04-29T10:50-04:00 — Roland flagged that re-launching
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

2026-04-29T10:54-04:00 — Roland started ROS via
`start_tmux_project11.bash`. Both bag dirs created at the expected
launch-time UTC timestamp (shared between loggers, as designed):

- `/home/field/data/logs/bizzyboat/2026-04-29T14-54-18+00-00/2026-04-29T14-54-18+00-00_0.mcap`
- `/home/field/data/logs/bizzyboat_sonar/2026-04-29T14-54-18+00-00/2026-04-29T14-54-18+00-00_0.mcap`

2026-04-29T10:56-04:00 — 30 s sample on both mcap files confirmed
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

2026-04-29T11:14-04:00 — Roland flagged that fixes are landing for
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

2026-04-29T11:30-04:00 — Committed log §1 + §2 (`ee8867a`, later
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

2026-04-29T12:03-04:00 — Roland kicked off `start_tmux_project11.bash`.
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

2026-04-29T12:11-04:00 — After the chmod fix, core stayed up cleanly,
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

## Files touched

- `bizzyboat_project11/launch/perception_launch.py`
- `bizzyboat_project11/launch/core_launch.py`
- `bizzyboat_project11/scripts/start_tmux_project11.bash`
- `bizzyboat_project11/scripts/rtcm_relay_node.py` (mode change)
- `config/repos/core.repos`
- `docs/logs/2026/2026-04-29_gabby_logs.md` (this file)
