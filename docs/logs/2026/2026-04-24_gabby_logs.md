# Field log — gabby — 2026-04-24

**Host**: gabby
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)

## Summary

Session covered new OAK camera topic capture, per-camera H.265 bitrate
tuning, and two TF-frame fixes in the tide-estimation / MRU-transform
stack. One helper script added. Two source edits staged for rebuild.

## 1. Camera topic capture

New topics published by the `sea_surface_segmentation` nodes:

- `/bizzy/sensors/cameras/oak_<dir>/image_raw/ffmpeg` (H.265 via `ffmpeg_image_transport_msgs/FFMPEGPacket`)
- `/bizzy/sensors/cameras/oak_<dir>/segmentation/compressed` (`sensor_msgs/CompressedImage`)

for `<dir>` ∈ {`forward`, `starboard`, `aft`, `port`}. Neither is in the
persistent logger config (`bizzyboat.yaml` `/**/logger:`); past image
bags under `~/data/logs/bizzy_images/` contained `segmentation/compressed`
but no ffmpeg topics.

### Ad-hoc 2-minute capture

Ran an ad-hoc `ros2 bag record` (not a logger-config edit) covering the
4 ffmpeg + 4 segmentation/compressed topics plus `/diagnostics`, `/tf`,
`/tf_static`. Output:

- `~/data/logs/bizzy_images/bag_2026-04-24T14.42.24_ffmpeg_seg/` — 67.3 MiB, 119.6 s, 8736 msgs
- Per-camera rates ≈ 5 Hz on each stream, as expected

## 2. `record_camera_topics.sh` helper

New helper:
`bizzyboat_project11/scripts/record_camera_topics.sh [duration_secs]`
(default 120 s). Writes mcap/zstd bag under `~/data/logs/bizzy_images/`.

Matches the `test_cmd_vel.sh` pattern in the same dir — executable
bash, not added to `CMakeLists.txt install(PROGRAMS ...)` (run from the
source tree, same as `test_cmd_vel.sh`).

### Process-group / SIGTTOU pitfall (diagnosed + fixed)

First version used `timeout --signal=INT 120 ros2 bag record ...` — worked
when I invoked it inline (stdin not a TTY), but deadlocked when run
interactively from a shell. `ros2 bag record` enables TTY raw mode for its
"Press SPACE for pause/resume" feature; `timeout` had placed it in a
separate process group, so the kernel sent SIGTTOU and stopped the
recorder (`ps STAT=Tl`). The pending SIGINT from `timeout`'s deadline
then sat undelivered because the process was SIGSTOP'd.

Fix: pass `--disable-keyboard-controls` to `ros2 bag record` (the
purpose-built flag). No TTY mode change → no SIGTTOU → timeout works
normally. Verified end-to-end with a 10 s run.

## 3. OAK camera H.265 bitrate tuning

Edited `bizzyboat_project11/launch/oak_cameras_launch.py` per-camera
`h265_bitrate_kbps`:

| Camera | Before | After | Field adjust |
|---|---|---|---|
| `oak_forward` | 1000 | 1000 | 1000 |
| `oak_starboard` | 1000 | 800 | 800 |
| `oak_port` | 1000 | 800 | 800 |
| `oak_aft` | 1000 | 500 | **800** (bumped — 500 was looking blocky) |

Total per-camera target: initial ~3.1 Mbps, post field-adjust ~3.4 Mbps.
The
`sea_surface_segmentation` node does no validation beyond
`bitrate_kbps > 0`; anything positive is passed straight to
`dai::node::VideoEncoder::setBitrateKbps`. The hardware VideoEncoder on
the OAK Myriad X is the effective limit, not the node.

Installed launch file is a symlink to source (workspace built with
`--symlink-install`), so no rebuild needed. **Requires
`perception_launch` restart** — OAK pipelines read the param only at
init; neither `respawn=True` nor `ros2 param set` re-pushes a new
bitrate to a running camera.

## 4. Sea-surface / tide-estimator frame-prefix fixes

### Problem

User observed not-all-`bizzy/`-prefixed TF frames in `core_launch`, plus
`tf2_buffer` timeout errors from `mru_transform_node`.

### 4a. `sea_surface_estimator` — config-only fix

`mru_transform/nodes/sea_surface_estimator.cpp` declares three
TF-frame parameters, all defaulting to un-prefixed names:

- `sea_surface_frame` — default `map_tide` (child of the tide TF broadcast)
- `chart_datum_frame` — default `chart_datum` (lookup for MLLW range check)
- `mhhw_frame` — default `chart_datum_mhhw` (lookup for MHHW range check)

`bizzyboat.yaml` previously only overrode `/**/chart_datum:` (the
*publisher* side — `chart_datum_node` publishes
`bizzy/chart_datum` / `bizzy/chart_datum_mhhw`). The estimator was
running on defaults, with two consequences:

1. Broadcast tide transform `bizzy/odom → map_tide` — child orphaned from
   the `bizzy/*` TF subtree.
2. `is_out_of_range()` looked up `chart_datum` / `chart_datum_mhhw`
   (un-prefixed); those frames don't exist, so `lookupTransform` threw,
   the `catch` returned `false`, and tide-range validation **silently
   never fired**.

**Fix** (added to `bizzyboat_project11/config/bizzyboat.yaml`, just
after the `/**/chart_datum:` block):

```yaml
/**/sea_surface_estimator:
  ros__parameters:
    sea_surface_frame: bizzy/map_tide
    chart_datum_frame: bizzy/chart_datum
    mhhw_frame: bizzy/chart_datum_mhhw
```

Config-only; installed yaml is symlinked; no rebuild needed.

### 4b. `mru_transform_node` tf2_buffer timeout error — source fix

Symptom in `core_launch` logs (repeating):

```
[mru_transform_node-1] [ERROR] [...] [tf2_buffer]: Do not call canTransform or
lookupTransform with a timeout unless you are using another thread for populating
data. Without a dedicated thread it will always timeout...
```

Root cause: `mru_transform/src/mru_transform.cpp` velocity callback used
the 4-arg `lookupTransform` overload — timestamp + **0.1 s timeout**:

```cpp
tf = tf_buffer_->lookupTransform(
  base_frame_, velocity.header.frame_id,
  rclcpp::Time(velocity.header.stamp),
  rclcpp::Duration::from_seconds(0.1));
```

The node spins single-threaded, so while `lookupTransform` blocks, the
same thread cannot service incoming `/tf` messages — the wait always
times out. Every other TF call in the same file uses
`tf2::TimePointZero` (no timeout); the position callback even documents
the rationale: *"assuming static sensor to base_link transform, so any
time is ok"*.

**Fix** (`mru_transform/src/mru_transform.cpp:258-259`):

```cpp
tf = tf_buffer_->lookupTransform(
  base_frame_, velocity.header.frame_id, tf2::TimePointZero);
```

Matches the convention used by every other TF lookup in the package.
Requires rebuild of `mru_transform` + restart of `core_launch`.

### 4c. mavros plugin frame-id overrides

After the 4b rebuild, the tf2_buffer threading error went away but
exposed real disconnected-TF-tree warnings:

```
velocity:   TF 'map' -> 'bizzy/base_link'       ... unconnected trees
orientation: TF 'base_link' -> 'bizzy/base_link' ... unconnected trees
```

`base_frame_` and `map_frame_` in `mru_transform_node` were already
correct (`bizzy/base_link`, `bizzy/map`) — but the incoming message
`header.frame_id`s were flat `map` / `base_link`, published by the
mavros plugins with their stock defaults from
`/opt/ros/jazzy/share/mavros/launch/apm_config.yaml`.

The project's existing `echoboat_project11/config/mavros.yaml` only
overrode `setpoint_velocity.mav_frame` + `time.timesync_rate`, not the
frame_ids.

**First attempt: inline dict on mavros_node — didn't work.** Appended
a `{'global_position.frame_id': [frame_prefix, 'map'], ...}` dict at
the end of the mavros Node `parameters=[...]` list. After restart, the
warnings continued and `ros2 param get /bizzy/mavros/global_position
frame_id` still returned `"map"`.

**Why it failed**: each mavros plugin is its own ROS 2 node
(`/bizzy/mavros/global_position`, `/bizzy/mavros/imu`,
`/bizzy/mavros/local_position`, …), with plain `frame_id` parameters.
Inline dicts on the mavros_node Node action bind to the *main*
`mavros_node` — they never reach the plugin sub-nodes. Only the
`/**/plugin_name: ros__parameters:` yaml pattern walks into them.

**Second attempt (works): new `bizzyboat_project11/config/mavros.yaml`**,
appended as the last entry in the mavros Node `parameters=[...]` list:

```yaml
/**/global_position:
  ros__parameters:
    frame_id: "bizzy/map"
    child_frame_id: "bizzy/base_link"

/**/imu:
  ros__parameters:
    frame_id: "bizzy/base_link"

/**/local_position:
  ros__parameters:
    frame_id: "bizzy/map"
```

Loaded after `mavros/apm_config.yaml` and
`echoboat_project11/config/mavros.yaml`, so these values win. The
`bizzy/` prefix is hardcoded — yaml can't accept the
`frame_prefix` LaunchConfiguration. File header comment flags this for
future maintainers.

`tf.send: false` is the default for each plugin in `apm_config.yaml`,
so the `tf.frame_id` / `tf.child_frame_id` parameters don't need to be
overridden — mavros isn't broadcasting TF anyway.

**Rebuild needed**: the new `mavros.yaml` didn't exist when the package
was last installed, so `--symlink-install` hasn't linked it into the
install tree. `colcon build --packages-select bizzyboat_project11` (or
the workspace build script) is required before `core_launch` restart
can resolve the file path.

## 5. Known-but-deferred: `sea_surface_segmentation` frame_id hardcoding

The segmentation node publishes messages tagged
`frame_id = "<camera_name>_optical_frame"` — hardcoded at
`sea_surface_segmentation.cpp:35`. Two mismatches with the URDF
(`urdf/sensors/camera_oak.xacro`):

| | URDF frame | Node `frame_id` |
|---|---|---|
| Prefix | `bizzy/…` | *(none)* |
| Suffix | `…_optical` | `…_optical_frame` |

No parameter exists to override it. A sibling node
(`depthai_marine/src/measure_timing.cpp:184-186`) already exposes a
`frame_id` parameter; the segmentation node could copy that pattern.
**Deferred** — needs its own issue in `unh_marine_perception` and a C++
change + rebuild. Not fixed today.

## Pending on operator

- Restart `perception_launch` → picks up new per-camera H.265 bitrates.
- Rebuild `bizzyboat_project11` (data-only; needed so the new
  `config/mavros.yaml` gets linked into the install tree).
- Rebuild `mru_transform` (`colcon build --symlink-install
  --packages-select bizzyboat_project11 mru_transform` from
  `layers/main/platforms_ws/` covers both in one shot).
- Restart `core_launch` → picks up the rebuilt `mru_transform_node`,
  the new `/**/sea_surface_estimator:` yaml block, and the new
  `bizzyboat_project11/config/mavros.yaml` plugin frame overrides.

## Files touched

**`unh_echoboats_project11`** (field, gitcloud):

- `bizzyboat_project11/scripts/record_camera_topics.sh` (new)
- `bizzyboat_project11/launch/oak_cameras_launch.py` (bitrates)
- `bizzyboat_project11/launch/core_launch.py` (load new mavros.yaml)
- `bizzyboat_project11/config/mavros.yaml` (new — plugin frame-id overrides)
- `bizzyboat_project11/config/bizzyboat.yaml` (+ `/**/sea_surface_estimator:` block)
- `docs/logs/2026/2026-04-24_gabby_logs.md` (this log)

**`mru_transform`**:

- `mru_transform/src/mru_transform.cpp` (velocity lookupTransform → `TimePointZero`)
