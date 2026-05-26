# Plan: Configure nav2 Collision Monitor for BizzyBoat (reflex safety layer)

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/170

## Context

The Collision Monitor scaffolding **already exists** on BizzyBoat's
autonomous `cmd_vel` path. The shared `echoboat_project11/config/nav2_params.yaml`
(`seafloor_echoboat_project11`, used by bizzy *and* izzy — bizzy's
`nav_launch.py` passes no params override) defines `collision_monitor:` with
`cmd_vel_in_topic: cmd_vel_smoothed` → `cmd_vel_out_topic:
piloting_mode/autonomous/cmd_vel`, i.e. it gates autonomous commands ahead of
`mavros/setpoint_velocity/cmd_vel` — exactly #170's intent. **But** its only
`observation_sources` is a `scan` (LaserScan) topic BizzyBoat does not publish,
so the monitor is **blind today**.

What #170 actually needs: feed the monitor the reflex PointCloud2 from
`unh_marine_perception#17`'s `segments_to_pointcloud` (reflex mode:
`target_frame=bizzy/base_link_level`, publishes `~/pointcloud`), and tune the
polygons for boat momentum. BizzyBoat does not launch `segments_to_pointcloud`
at all yet — only the four OAK segmentation-image nodes run
(`oak_cameras_launch.py`).

**Hard dependency**: perception#17 (draft PR #18) provides the reflex
`target_frame`/`~/pointcloud` surface. Phase A cannot deploy until it merges to
`jazzy`; it can be sim-tested in-workspace from the perception#17 worktree.

## Approach

Phased per discussion (user-confirmed). **Phase A** is this PR.

### Phase A — publish + record + bridge the reflex cloud (this PR)

1. **Launch a forward-OAK reflex instance** in
   `bizzyboat_project11/launch/perception_launch.py` (already uses
   `GroupAction`/`PushRosNamespace`/`IncludeLaunchDescription`). Include
   `sea_surface_segmentation/launch/segments_to_pointcloud_launch.py` with
   `name=segments_to_pointcloud_reflex`, `target_frame=bizzy/base_link_level`,
   wrapped in a `GroupAction` whose `SetRemap`s wire the node to the forward
   camera and to the **canonical** observation topic:
   - `segmentation` → `sensors/cameras/oak_forward/segmentation`
   - `segmentation/camera_info` → `sensors/cameras/oak_forward/segmentation/camera_info`
   - `~/pointcloud` → `/bizzy/collision_monitor/pointcloud` (absolute dst to
     avoid private-namespace remap ambiguity)

   **Activation risk to verify**: the node is a `LifecycleNode` and won't
   publish until configured+activated. `segments_to_pointcloud_launch.py`
   computes its `LifecycleTransition` target name from
   `LaunchConfiguration('ros_namespace')`, which `PushRosNamespace` does **not**
   set — so under a pushed namespace the transition may target the wrong FQN
   and never fire. Verify activation in sim; if it misfires, pass `ros_namespace`
   explicitly or launch the reflex node directly (with its own transition)
   rather than via the include. This is the load-bearing check for Phase A —
   no activation means no cloud to record/bridge.

2. **Record it.** Add `/bizzy/collision_monitor/pointcloud` to the explicit
   `logger.topics` allowlist in `bizzyboat_project11/config/bizzyboat.yaml`.

3. **Bridge it on both links.** Add a `collision_pointcloud` entry
   (`source: collision_monitor/pointcloud`) to the WiFi *and* VPN topic lists
   in `bizzyboat.yaml`. **Measured** size is tiny — 128×96 mask, ≤~53 projecting
   `PointXYZI` points across the real 2026-05-22 obstacle-approach window,
   <2 KB/msg, <0.1 Mbps @10 Hz — so VPN inclusion is safe (unlike the costmap
   dropped in #68 for size). Start at `period: 1.0` (operator SA/debug; the
   monitor consumes it on-boat); tunable.

### Phase B — wire + tune the monitor (follow-up sub-issue, own plan)

- Shared `nav2_params.yaml`: switch `observation_sources` from `scan` to a
  `pointcloud` source on the **canonical** topic `collision_monitor/pointcloud`
  (relative; namespaced per boat). Each boat remaps its reflex cloud to that
  topic; izzy opts in later (it currently has `publish_pointcloud: false`, so the
  switch is a no-op for izzy until then). Spans `seafloor_echoboat_project11`
  (params) + bizzy launch (remap, done in Phase A).
- Tune polygons for momentum: passive coast-down is ~10–15 m from ~1.5 m/s cruise
  (#124 §2 / PR #172), so the slowdown/limit zone must extend well beyond ~15 m,
  or the monitor must command reverse rather than zero throttle. Favor
  slowdown/limit over hard stop; forward-arc only. Keep the polygon block shared
  unless bizzy/izzy tuning must differ.
- Sim-verify before field.

### Phase C — offline trigger cataloging (validation; likely under #169)

Replay logged forward segmentation (`~/data/logs/bizzy_images/`, 2026-04-21…05-22)
through adapter + monitor, catalog every slow/stop trigger vs. track/speed
(`/bizzy/odom`) to separate true positives from false positives for polygon
tuning — no field time. Per the #170 issue comment.

## Files to Change (Phase A)

| File | Change |
|------|--------|
| `bizzyboat_project11/launch/perception_launch.py` | Add a `GroupAction` (SetRemap + include of `segments_to_pointcloud_launch.py`) launching the forward-OAK reflex instance → `/bizzy/collision_monitor/pointcloud` |
| `bizzyboat_project11/config/bizzyboat.yaml` | Add the canonical topic to `logger.topics`; add `collision_pointcloud` entries to WiFi + VPN udp_bridge lists |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| A change includes its consequences | Phase A keeps node + record + bridge together so the cloud is observable end-to-end; merge-order dependency on perception#17 stated. |
| Capture decisions, not just implementations | Canonical-topic-over-edit-shared-params and phasing decisions recorded; "measured, not heavy" recorded against #68 precedent. |
| Test what breaks | Lifecycle-activation-under-namespace is the failure mode that yields a silent empty topic; called out as the sim check gating Phase A. |
| Only what's needed | Phase A is launch + two config edits; monitor wiring/tuning deferred to B with its own review. |
| Robustness (boat on open water) | Safety reflex is Phase B; Phase A first makes the feed recordable/visible so B is tuned against real data, not guesses. |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| 0002 — Worktree isolation | Yes | `layers/worktrees/issue-unh_echoboats_project11-170`. |
| 0008 — ROS 2 conventions | Yes | snake_case params; reuse upstream launch via include + SetRemap; sensor_msgs/PointCloud2 unchanged. |
| 0013 — progress.md vocabulary | Yes | `## Plan Authored` entry appended. |

## Consequences

| If we change... | Also update... | Included? |
|---|---|---|
| Launch reflex node (new `/bizzy/collision_monitor/pointcloud`) | bag `logger.topics` + udp_bridge (wifi+vpn) | Yes (Phase A) |
| Canonical observation topic name | Phase B `nav2_params.yaml` `observation_sources` + per-boat remap | Phase B (own plan) |
| Depend on perception#17 surface | Merge perception#17 to `jazzy` before Phase A deploys | Stated; merge-order note |
| (gap) no `.agents/README.md` in echoboats | Author one as a dedicated task | Out of scope — noted, not fixed here |

## Open Questions

- [ ] **Bridge period** for `collision_pointcloud` — plan assumes `period: 1.0`
  on both links (it's operator SA/debug; monitor consumes on-boat). Confirm or
  set unthrottled.
- [ ] **Phase A merge gating** — open this PR now (sim-tested against the
  perception#17 worktree) and hold for perception#17 merge, or wait until
  perception#17 lands first? Plan assumes open-now-hold-ready.

## Estimated Scope

Phase A: single small PR (one launch addition + two config edits), gated on
perception#17. Phases B and C are separate PRs/sub-issues with their own plans.
