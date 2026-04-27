# BizzyBoat deployment log — gabby — 2026-04-27

**Host**: gabby
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Deployment**: #TBD (dev-side issue not yet opened)

## Scope

Integrate sonar software and test on the water.

## Summary

_To be filled in at end of session._

## 1. Session start

2026-04-27T10:02-04:00 — `make sync` + `make build` clean on gabby. Sync
pulled in the new `docs/logs/README.md` deployment-logging convention
(7 files, +1273 lines on `unh_echoboats_project11`). Build report: 5
layers, 45 packages, all green.

2026-04-27T10:02-04:00 — system timezone was `Etc/UTC`; set to
`America/New_York` (`timedatectl set-timezone America/New_York`). Local
time now reads `EDT (-0400)` so log timestamps match the on-site clock.

## 2. Camera-recorder coverage for SeaSurfaceLayer replay-debug

2026-04-27T10:18-04:00 — audited
`bizzyboat_project11/scripts/record_camera_topics.sh` against what the
nav2 costmap plugin
`sea_surface_layer::SeaSurfaceLayer` (in
`unh_marine_perception/sea_surface_segmentation/src/sea_surface_layer.cpp`)
actually consumes. Found one critical gap.

Plugin subscriptions (`sea_surface_layer.cpp:38-48`):

- `segmentation_topic` as **raw `sensor_msgs::msg::Image`** (default
  `segmentation`) — NOT `CompressedImage`
- `camera_info_topic` as `sensor_msgs::msg::CameraInfo` (default
  `camera_info`)
- TF lookup at `sea_surface_layer.cpp:141`:
  `segments_msg->header.frame_id` → costmap global frame, 1 s timeout

Pre-edit, the recorder captured `/segmentation/compressed` (×4) +
`/segmentation/camera_info` (×4) but **not** the raw `/segmentation`
Image topic that the plugin subscribes to. Replaying that bag against
the plugin would never trigger the callback unless an image-transport
republisher were chained in.

The bizzyboat persistent-logger config
(`bizzyboat_project11/config/bizzyboat.yaml:78,82,86,90,116,120,124,128`)
already lists `oak_segmentation_<dir>_raw` →
`sensors/cameras/oak_<dir>/segmentation` with `period: -1.0`, so the
system is aware of those raw topics and explicitly opts out of
always-on logging — confirming the topics exist and just need to be
added to the ad-hoc recorder.

### Edit

Added to `record_camera_topics.sh`:

- 4× `/bizzy/sensors/cameras/oak_<dir>/segmentation` (raw Image —
  what the plugin subscribes to)
- `/robot_description` (latched URDF — lets RViz render the boat
  from the bag with no live system)

Kept everything that was there: `/tf`, `/tf_static`, `/diagnostics`,
the H.265 `image_raw/ffmpeg` streams (visual context for humans),
the segmentation compressed variants and segmentation camera_info,
plus the raw-camera `camera_info` (not used by SeaSurfaceLayer but
useful if other downstream consumers ever need it).

Header comment was tightened to state that the resulting bag is
sufficient to replay-debug SeaSurfaceLayer offline.

### Disk-space note (TODO)

Raw segmentation Images are small (DepthAI NN output, likely ~128×96
to ~256×256 RGB8 — `sea_surface_segmentation.cpp:38` calls
`calibrationToCameraInfo(..., 128, 96)`). Worst-case order-of-magnitude
estimate at 256×256 RGB8 × 5 Hz × 4 cams ≈ 4 MB/s, ≈ 480 MB for the
default 120 s capture. Should be fine, but **measure on first run**
before relying on this in the field.

## 3. Pre-launch system bring-up

2026-04-27T10:34-04:00 — operator ran
`~/start_tmux_project11.bash` (symlink to the project11 install-tree
copy). `tmux ls` shows the `project11` session (4 windows) up.
`ros2 node list` shows the full nav2 stack
(`/bizzy/local_costmap/local_costmap`,
`/bizzy/global_costmap/global_costmap`, `behavior_server`,
`controller_server`, etc.), all four OAK cameras
(`/bizzy/sensors/cameras/oak_{forward,starboard,aft,port}`), MAVROS,
`deltat` + `cube_bathymetry`, and `sonar_logger`.

### Recorder fix: `/robot_description` is namespaced

Verified topic publication while the system was up; caught a typo in
my own commit `cc7e7fe`. The recorder edit added bare
`/robot_description`, but on this system the URDF is published as
`/bizzy/robot_description` — under the `bizzy` namespace, like every
other platform-side topic. (Cross-system topics `/diagnostics`, `/tf`,
`/tf_static` are correctly un-namespaced and the script already had
those right.)

Fixed in the script — entry now reads `/bizzy/robot_description`.
Lesson noted for future bag-recorder edits: **verify topic names
against a live system before trusting documentation or assumed
conventions** rather than just the namespacing pattern of nearby
entries.

### Inventory correction: DeltaT is not live

Operator clarified that the section-3 inventory misrepresented the
sonar state. The **DeltaT (Imagenex 837) sensor is physically removed
from BizzyBoat.** The `/bizzy/sensors/deltat/deltat` node, the
`cube_bathymetry` node, and the `sonar_logger` shown in
`ros2 node list` are leftover lifecycle/launch scaffolding plus
udp_bridge listeners waiting on UDP packets that no longer arrive.
Verified post-hoc with `ros2 topic hz`:

- `/bizzy/sensors/deltat/soundings` — no messages in 2 s
- `/bizzy/sensors/deltat/cube_bathymetry` — no messages in 2 s

Lesson: **a node appearing in `ros2 node list` does not mean its
underlying sensor is live.** Always confirm with `ros2 topic hz`
on a known output topic before treating a node as a live data
source. Same caveat for any udp_bridge-fronted sensor on this
platform — the ROS-side topic exists whether or not bytes are
flowing across the bridge.
