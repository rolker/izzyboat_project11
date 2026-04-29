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

`df8c2c2 feat(perception_launch): self-contained log dir + datetime
subdir` on `jazzy`. Local only — Roland asked to hold the push.

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

## Files touched

- `bizzyboat_project11/launch/perception_launch.py`
- `bizzyboat_project11/scripts/start_tmux_project11.bash`
- `docs/logs/2026/2026-04-29_gabby_logs.md` (this file)
