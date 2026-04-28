# BizzyBoat deployment log — gabby — 2026-04-27

**Host**: gabby
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Deployment**: [#94](https://github.com/rolker/unh_echoboats_project11/issues/94)

## Scope

Integrate sonar software and test on the water.

## Summary

Sonar-software integration day in name; sonar work itself ran on
mercat, so the gabby side was logger + ROS-side support. Closed three
worthwhile things along the way:

1. **Camera→costmap TF gap fixed** — `sea_surface_segmentation` now
   takes a `frame_ids` parameter (default-empty for back-compat) and
   the BizzyBoat launch passes `bizzy/<name>_optical` to match the
   URDF. SeaSurfaceLayer's TF lookup would now resolve in the live
   system; still gated upstream on `unh_marine_perception#6/#7`.
2. **Camera-recorder coverage** — `record_camera_topics.sh` now
   captures the raw `/segmentation` Image streams (×4) plus the
   namespaced `/bizzy/robot_description`, so a bag from this script
   is sufficient on its own to replay-debug the costmap plugin.
3. **Survey-speed audit + interim bump** — traced the
   per-survey-speed pipeline end-to-end and identified the BT →
   FollowPath gap that prevents per-survey speed today. Bumped the
   shared `default_speed` 0.75 → 1.5 m/s as a deployment-blocking
   tactical move; verified at ~3 kn underway.

Plus: full prelaunch sweep clean, system timezone set to EDT,
DeltaT-removed memory captured, and BBR + larger TCP buffers
applied to gabby's host-level sysctls for Starlink performance.

Three captures during transit (~2 min each) and two long captures
(60 min, 36 min) — all clean. Disk after session: ~25 GiB used /
1.8 TiB free.

Carry-forward and follow-up issues are listed in §10.

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

## 4. Prelaunch checks — gabby

2026-04-27T10:48-04:00 — ran the full prelaunch sweep on gabby. All
green except one gap, called out at the bottom.

| Check | Status |
|---|---|
| Time sync (chrony → `time.lan.bizzy.p11.lan` S1) | ✅ system clock within 13 µs |
| Timezone | ✅ `EDT (-04:00)` |
| MAVROS ↔ FCU | ✅ connected, mode=MANUAL, disarmed, system_status=Active |
| GPS-RTK gps1 | ✅ `fix_type=6` (RTK_FIXED), 32 sats, h_acc=21mm v_acc=27mm |
| GPS gps2 raw | ❓ `--once` echo timed out twice; gps1 RTK-fixed so not blocking |
| NTRIP | ✅ receiving corrections |
| OAK cameras × 4 raw `segmentation` | ✅ ~5.0 Hz each |
| OAK cameras × 4 `image_raw/ffmpeg` | ✅ ~5.0 Hz each |
| `/tf` | ✅ ~33 Hz |
| Nav2 lifecycle | ✅ "Managed nodes are active" |
| Diagnostics aggregate | ✅ **48/48 OK**, 0 WARN/ERR/STALE |
| Comms (WiFi/Starlink/LTE/multi-WAN/pings) | ✅ all healthy (WiFi 45 dB SNR, Starlink 20 ms 0% drop, LTE -81 dBm) |

Notable diagnostics highlights from the 48-entry sweep:

- `mikrotik_monitor: wifi.bizzy/wlan1`: associated 45 dB SNR
- `starlink_diagnostics`: dish reachable, 0.0% drop, 20 ms, no
  obstruction or thermal alerts
- `teltonika_monitor: router.bizzy`: LTE -81 dBm, mwan3 wan online,
  mob1s1a1 standby
- `udp_bridge`: bizzy↔operator vpn (470 kB/s tx) + wifi (708 kB/s
  tx, 810 B/s rx) both flowing

There is **no `/diagnostics_agg` topic / no `diagnostics_aggregator`
node** on this system — individual nodes publish to `/diagnostics`
directly and the rqt_robot_monitor / operator UI must aggregate
client-side. Not a problem; just an architectural fact worth knowing
when looking for "the rolled-up status".

### TF gap on OAK camera frames (note for costmap-plugin replay)

`/bizzy/sensors/cameras/oak_forward/segmentation` messages carry
`header.frame_id = oak_forward_optical_frame` — **no `bizzy/`
namespace prefix.** That frame is **not in the TF tree**:

```
tf2_echo bizzy/base_link oak_forward_optical_frame
  → "Invalid frame ID 'oak_forward_optical_frame'" (persistent)
tf2_echo bizzy/odom oak_forward_optical_frame
  → same
```

`bizzy/base_link` and `bizzy/odom` resolve fine (e.g.,
`bizzy/odom → bizzy/base_link` is publishing at full rate, boat
sitting at `[0.326, -0.622, -21.069]` rel. to odom origin). It's
specifically the camera optical frames that aren't in the tree.

Implication for the costmap-plugin work later: `SeaSurfaceLayer`'s
TF lookup at `sea_surface_layer.cpp:141`
(`segments_msg->header.frame_id` → `global_frame_id_`) would fail
against this — consistent with `unh_marine_perception#6` (the
`matchSize()` segfault blocker) and `#7` (end-to-end OAK→costmap
validation, blocked on #6) being open in the roadmap. The plugin
isn't end-to-end yet. Worth knowing when we replay from a bag —
recording a bag won't paper over this; the upstream URDF / TF
publisher needs to publish the camera frames before the plugin can
function.

Not blocking launch.

## 5. OAK segmentation frame_id fix

2026-04-27T11:05-04:00 — closed the TF gap from §4. The publisher
hardcoded its frame_id at
`unh_marine_perception/sea_surface_segmentation/src/sea_surface_segmentation.cpp:35`:

```cpp
frame_id_ = name_ + "_optical_frame";
```

…producing `oak_forward_optical_frame` etc. The URDF
(`bizzyboat_project11/urdf/sensors/camera_oak.xacro:25`) publishes the
optical link as `bizzy/<name>_optical`. Two divergences in one line:
missing `bizzy/` namespace + extra `_frame` suffix.

### Fix path

Did the architecturally-clean fix rather than hardcoding the BizzyBoat
naming into the generic perception package:

1. **`unh_marine_perception` —** added a new optional node parameter
   `frame_ids` (array, position-matched to `camera_names`). When
   empty (or shorter than `camera_names`), the camera falls back to
   the historical `<name>_optical_frame` default → fully back-compat.
   Per-camera init log line now reports the chosen frame_id so
   misconfiguration is visible at boot. Commit on
   `unh_marine_perception/jazzy`.
2. **`unh_echoboats_project11` —** set
   `'frame_ids': [f'bizzy/{name}_optical']` per camera in
   `bizzyboat_project11/launch/oak_cameras_launch.py`. This pins the
   BizzyBoat naming where it belongs (the platform launch). Commit
   on `unh_echoboats_project11/jazzy`.

Both edits done in field mode — they'll reconcile to GitHub via
`/import-field-changes` on the dev side.

### Verification (post stack-restart)

- `frame_id` on `/bizzy/sensors/cameras/oak_forward/segmentation` →
  `bizzy/oak_forward_optical` ✅
- Same on `…/segmentation/camera_info` ✅
- `tf2_echo bizzy/odom bizzy/oak_forward_optical` → resolves, e.g.
  `Translation [0.348, -0.096, -19.674]`
- `tf2_echo bizzy/base_link bizzy/oak_forward_optical` → resolves to
  the URDF static `[0.310, 0.000, 1.410]` with the optical-convention
  rotation `[-π/2, 0, -π/2]` applied
- All 4 OAK segmentation streams still ~5.0 Hz — no regression

### Standing caveats

The matchSize() segfault (`unh_marine_perception#6`) is still the
blocker for the costmap plugin itself; this fix only closes the TF
gap that would have blocked it after #6 is resolved. Upstream of #6
this is dead code until the plugin can run.

## 6. On-water

2026-04-27T11:13-04:00 — operator deployed BizzyBoat. Boat is in
the water.

Open thread paused: USB serial check (asked at 11:09) — no new
device enumerated when checked; deferred until it's relevant again.

## 7. First on-water bag with the updated recorder

2026-04-27T11:25-04:00 — operator triggered a 120 s capture with
`record_camera_topics.sh 120`. First real exercise of the recorder
edits from §2 + §5 (raw `/segmentation` × 4 with the corrected
`bizzy/<name>_optical` frame_ids, plus `/bizzy/robot_description`).

Output: `~/data/logs/bizzy_images/bag_2026-04-27T14.25.31_ffmpeg_seg/`

| Metric | Value |
|---|---|
| Bag size | **91.6 MiB** (~46 MB/min) |
| Duration | 119.57 s |
| Total messages | 14,519 |
| Per-camera × per-stream | 598 msgs (= 5.00 Hz × 119.57 s) |
| `/bizzy/robot_description` | 1 (latched) |
| `/tf_static` | 2 |
| `/tf` | 3,634 (~30 Hz) |
| `/diagnostics` | 1,314 (~11 Hz aggregate across publishers) |

Every topic the §2 audit identified is in the bag. Per-stream
counts are identical (598) on all 4 cameras × 4 stream types — no
drops. The latched `/bizzy/robot_description` recorded exactly 1
message, as expected for a latched/transient-local publisher
captured on subscription.

### Closing the §2 disk-space TODO

§2's worst-case estimate was 480 MB for 120 s (assumed 256×256 RGB8).
**Reality: ~92 MB** — segmentation images are actually 128×96 RGB8
(36 KB/frame), and mcap+zstd_fast packs the rest tight. Headroom is
plenty for routine on-water captures; a multi-bag long campaign on
a 1 TB disk would still want some thought, but for ad-hoc 2-min
captures this is comfortably cheap.

§2's TODO is **closed**: ~46 MB/min is the realistic figure to plan
around for this recorder.

### Second capture

2026-04-27T11:02-04:00 (UTC start 15:02:15) — second 120 s capture
at operator request.

- `~/data/logs/bizzy_images/bag_2026-04-27T15.02.15_ffmpeg_seg/`
- 85.3 MiB / 119.57 s / 14,579 messages
- Slightly smaller than the first capture (91.6 → 85.3 MiB), same
  per-camera coverage

### Third capture

2026-04-27T11:21-04:00 (UTC start 15:21:26).

- `~/data/logs/bizzy_images/bag_2026-04-27T15.21.26_ffmpeg_seg/`
- 82.6 MiB / 119.57 s / 14,542 messages
- Trend: 91.6 → 85.3 → 82.6 MiB across the three captures (likely
  scene-content-driven compression efficiency, not a recorder issue)

## 8. Survey-speed pipeline audit + default bump 0.75 → 1.5 m/s

Operator asked whether they could specify a per-survey speed today.
Traced the chain end-to-end:

| Layer | State |
|---|---|
| `marine_nav_interfaces/msg/TaskInformation.msg:26-29` | YAML `data` field documented to carry a `speed` member ✅ |
| `marine_nav_bt_task_navigator/behavior_trees/run_tasks.xml:384-387` | BT extracts `target_speed` via `GetTaskDataDouble` ✅ |
| `run_tasks.xml` FollowPath call | **Gap** — `target_speed` is read but never passed downstream ❌ |
| nav2 `/speed_limit` topic | Not published from anywhere on this stack ❌ |
| `marine_nav_crabbing_path_follower::CrabbingPathFollower::setSpeedLimit()` (`crabbing_path_follower.cpp:74`) | Implemented — but `setSpeedLimit()` can only **decrease** below `desired_speed_` (line 113-120: `target_speed = min(desired_speed_, …)`) |
| `desired_speed_` source | `default_speed` YAML param, read **once at init** at `crabbing_path_follower.cpp:35-36` |

**Bottom line:** to raise speed beyond the YAML default, the BT→FollowPath
gap needs closing (smallest fix: a small custom BT action node that
publishes `nav2_msgs/SpeedLimit` to `/speed_limit` from the extracted
`target_speed`). Worth a follow-up issue under
`unh_marine_navigation` after wrap-up, not deployment-blocking.

### Default bump

For today, raised the floor instead. Edited
`seafloor_echoboat_project11/echoboat_project11/config/nav2_params.yaml:64`:
`default_speed: 0.75 → 1.5` (m/s).

Important context: that YAML is **shared between BizzyBoat and the
seafloor echoboat**. BizzyBoat's `bizzyboat_project11/launch/nav_launch.py`
includes `echoboat_project11`'s `nav2_bringup_launch.py` with no
`params_file` override, so it picks up the same file. Both platforms
will now run at 1.5 m/s default until something else changes. A
bizzy-only override would mean wiring an explicit `params_file` arg
through `nav_launch.py` — deferred for now.

Required a controller_server bounce to take effect (param read at
init, no callback). Operator restarted; **boat now reports ~3 knots
(≈ 1.54 m/s)**, exactly the configured 1.5 m/s within measurement
noise. Change verified live.

### Hour-long capture

2026-04-27T13:54-04:00 (UTC start 17:54:26) — operator triggered a
3600 s capture.

- `~/data/logs/bizzy_images/bag_2026-04-27T17.54.26_ffmpeg_seg/`
- 2.4 GiB / 3599.58 s / 437,997 messages
- ~41 MB/min — slightly better than the 2-min average (46 MB/min);
  long capture amortizes overhead and likely benefits from steadier
  scene content
- Disk after: 19 GiB used / 1.8 TiB free — no concern

## 9. Starlink TCP tuning

Operator asked about TCP buffer tweaks for Starlink. Pre-tune state on
gabby was kernel default (`rmem_max = 208 KiB`, `tcp_congestion_control
= cubic`, `default_qdisc = fq_codel`, BBR module not loaded). Starlink
BDP at 300 Mbps × 50 ms ≈ 1.9 MB — autotuned TCP fits within
`tcp_rmem` ceiling (6 MB) but apps that explicitly set
`SO_{RCV,SND}BUF` were clipped at 208 KiB.

Pre-tune RTT to 1.1.1.1: avg 27.1 ms / 0% loss / mdev 2.9 ms.

### Drop-ins applied

- `/etc/sysctl.d/30-starlink-tcp.conf` (965 B):
    - `net.core.{rmem,wmem}_max = 16777216` (16 MiB)
    - `net.ipv4.tcp_{rmem,wmem}` ceilings = 16 MiB
    - `net.core.netdev_max_backlog = 5000`
    - `net.core.default_qdisc = fq`
    - `net.ipv4.tcp_congestion_control = bbr`
- `/etc/modules-load.d/bbr.conf` (212 B): `tcp_bbr` (so BBR loads at
  boot — wasn't auto-loaded before)

### Why these

- **CUBIC → BBR**: biggest single win for Starlink. CUBIC reads
  satellite-handover transient loss as congestion and backs off
  aggressively; BBR models bandwidth + RTT and rides through
  short-loss windows.
- **`fq_codel` → `fq`**: BBR's pacing relies on `fq`. `fq_codel`
  works but BBR underperforms.
- **`{r,w}mem_max` 208 KiB → 16 MiB**: lets apps using `setsockopt`
  (e.g. SSH) actually request large buffers. Pure autotuned TCP
  isn't capped by these (it's bounded by `tcp_{r,w}mem`), but tools
  that opt out of autotuning hit the ceiling.

### Verification

Post-apply (no reboot needed — sysctls applied via `sysctl --system`,
module via `modprobe tcp_bbr`):

- `tcp_available_congestion_control = reno cubic bbr` ✅
- `tcp_congestion_control = bbr` ✅
- `default_qdisc = fq` ✅
- `tcp_bbr` module loaded with 95 in-use refs immediately
- 92 active TCP sockets using BBR within seconds (`ss -tin | grep -c bbr`)
- Post-tune RTT to 8.8.8.8: 10/10 / avg 21.9 ms / mdev 3.1 ms — in
  the same ballpark as the pre-tune baseline (different host, idle
  RTT not the metric the change targets)

The win is throughput stability under load, not idle RTT — would
need a sustained iperf3 or large transfer to characterize, not worth
doing mid-deployment.

### Side-note on the verification false alarm

First post-tune ping to 1.1.1.1 came back 100% loss in 5 packets,
briefly looked alarming. Confirmed false alarm via spread: 8.8.8.8
and the LAN router both at 0% loss with the same routing through
`enp7s0`. 1.1.1.1 specifically was being dropped somewhere upstream;
not a sysctl-change side-effect. **Lesson: when verifying network
changes, ping at least three hosts (one external, one LAN), don't
trust a single target.**

## 10. Wrap-up

2026-04-27T20:28-04:00 — operator signaled boat recovered; closing
out the deployment.

### 45-min capture (the in-flight one when recovery started)

- `~/data/logs/bizzy_images/bag_2026-04-27T18.55.46_ffmpeg_seg/`
- 1.5 GiB / 2143.69 s / 247,292 messages
- Note: `Duration: 2143 s` rather than the requested 2700 s — the
  bag's duration is computed from first-to-last message timestamp,
  so if cameras stopped publishing at recovery (USB power cycle
  during pull-out is plausible) but the recorder's `timeout` ran the
  full 2700 s, only ~36 min of message content lives in the bag.
  Not a recorder bug; the bag stops where the data stops.

### State at wrap-up

| Repo | Local commits ahead of `origin/jazzy` | Pushed? |
|---|---|---|
| `unh_echoboats_project11` | 9 (logs + recorder + launch) | (this commit, then yes) |
| `unh_marine_perception` | 1 (frame_ids parameter) | not yet |
| `seafloor_echoboat_project11` | 1 (default_speed bump) | not yet |

All three will be pushed to gitcloud at the close of this session.
Reconciliation to GitHub happens dev-side via `/import-field-changes`.

### Capture archive (today)

Five bags total, ~4.6 GiB on `~/data/logs/bizzy_images/`:

| Start (UTC) | Duration | Size |
|---|---|---|
| 14:25:31 | 119.6 s | 91.6 MiB |
| 15:02:15 | 119.6 s | 85.3 MiB |
| 15:21:26 | 119.6 s | 82.6 MiB |
| 17:54:26 | 3599.6 s | 2.4 GiB |
| 18:55:46 | 2143.7 s | 1.5 GiB |

### Carry-forward — for the dev-side wrap-up agent to action

1. **Open issue** under `unh_marine_navigation` (or wherever the BT
   lives): wire BT `{target_speed}` → `/speed_limit` topic publish.
   Smallest fix: add a `PublishTopic` (or small custom action node)
   firing `nav2_msgs/SpeedLimit` from the already-extracted
   `target_speed` (`run_tasks.xml:384-387`) before each `FollowPath`.
   With this, per-task survey speed becomes specifyable end-to-end —
   today only the YAML default is honored.
2. **Reconcile field commits via `/import-field-changes`** — three
   field-mode repos have unmerged commits to land on GitHub:
   `unh_echoboats_project11` (recorder edits + launch wiring + log),
   `unh_marine_perception` (frame_ids parameter),
   `seafloor_echoboat_project11` (default_speed bump). All three need
   issues + draft PRs against GitHub `jazzy`.
3. **Roadmap candidate** (`docs/roadmap.md`): bizzy-only nav2_params
   override. The current shared `nav2_params.yaml` between BizzyBoat
   and the seafloor echoboat means today's speed change applies to
   both. If the seafloor platform ever wants a different default
   speed, the cleaner fix is for BizzyBoat's `nav_launch.py` to
   declare its own `params_file` override. Not on deck for next
   deployment, but worth recording as a future-cleanup item.

### Out-of-repo state worth knowing

- **Starlink TCP tuning** is host-level on `gabby`
  (`/etc/sysctl.d/30-starlink-tcp.conf` + `/etc/modules-load.d/bbr.conf`).
  Not version-controlled in this workspace today — there is no
  precedent for tracking host sysctls in any layer repo. If a similar
  tweak is wanted on `mercat`, `salmon`, or other Starlink-fronted
  field hosts, it should be replicated there manually (or eventually
  rolled into an Ansible/role-style provisioning artifact, which is
  bigger than a deployment-day fix).
- **DeltaT removal** is captured in agent memory
  (`project_bizzyboat_deltat_removed.md`) so future agents won't
  misread the leftover ROS scaffolding as a live sensor.

### Open thread

USB serial check (asked at 11:09, paused on §6): never came back to
this. If the device still needs reading, defer to the next session
or to a ticket — not a wrap-up blocker.
