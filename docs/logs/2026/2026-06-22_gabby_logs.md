# 2026-06-22 — gabby log (BizzyBoat deployment — issue pending)

Deployment issue: pending (backfill from a dev host)
Host: gabby
Side: field
Started: 2026-06-22 09:48 -04:00

## 2026-06-22

**2026-06-22 09:48 -04:00** — Deployment mode activated on gabby (field side) via `/start-deployment`. Issue-less start (#533): no deployment issue yet; a dev host backfills the issue link later (it finds this log by date). TODO (dev): create + link the deployment issue, stamp `- [gabby log](docs/logs/2026/2026-06-22_gabby_logs.md)` under its `## Logs` section, and clear the `pending` marker above.

**2026-06-22 ~09:40 -04:00** — SBG INS confirmed healthy after power-on. Driver recovered on its own after an initial `SBG_TIME_OUT` (device was off at first check) — "valid UTC log detected"; no restart needed. `status_general` all green (power/imu/gps/settings/temp/datalogger/cpu); `status_aiding` GPS1 pos/vel/hdt/utc + mag + air_data received (GPS2 not received — single-antenna config, not a fault); `imu_data` accel bits all true and in range. Note: `ros2 topic hz` on the high-rate `imu_data` topic kept timing out with no rate (rmw_zenoh fresh-subscriber discovery race) — `echo --once` returns current data every time, so not a data problem.

**2026-06-22 09:47 -04:00** — Enabled sidescan transmit at operator request: `set_transmit data:true` on `/bizzy/sensors/sidescan/garmin_sidescan/set_transmit` (std_srvs/SetBool) → `success=True, message='transmitting'`. Verified `/garmin_sidescan/transmitting` flipped false → true.

**2026-06-22 09:52 -04:00** — Health sweep at operator request (operator sees images/heartbeat/sidescan). 128 nodes up, no ERROR logs in last 10 min. Full nav2 stack active: controller_server, planner_server, bt_task_navigator, behavior_server, smoother_server, velocity_smoother, waypoint_follower, local+global costmaps all [active]. SBG healthy (earlier). Did not verify RTK fix quality this pass.

**2026-06-22 10:09 -04:00** — RTK fix verified: /bizzy/sensors/sbg/gps_pos status=0 (SOL_COMPUTED), type=7 (RTK_INT, ~2cm fixed-integer) — best possible fix. 32/44 SVs used. RTK_INT implies NTRIP/RTCM base corrections are flowing and being applied.

**2026-06-22 10:12 -04:00** — Started 10-min (600s) camera capture at operator request via record_camera_topics.sh → ~/data/logs/bizzy_images/bag_2026-06-22T10.11.35_ffmpeg_seg (mcap/zstd_fast). 24 topics: 4 OAK cams (ffmpeg + raw/compressed segmentation + camera_info), /tf, /tf_static, /diagnostics, /bizzy/robot_description, /bizzy/local_costmap/costmap. Recorder confirmed subscribed + Recording.

**2026-06-22 10:20 -04:00** — Set sidescan range at operator request: param set /bizzy/sensors/sidescan/garmin_sidescan range_m 45.0 (was 0.0/auto; bounds min 1 / max 60). Set returned successful; verified via param get = 45.0 (zenoh set confirmed, not silently dropped).

**2026-06-22 10:21 -04:00** — 10-min camera capture complete (exit 0, clean SIGINT — 'Recording stopped', metadata.yaml written). Bag: ~/data/logs/bizzy_images/bag_2026-06-22T10.11.35_ffmpeg_seg/ — 458M mcap + 28K metadata.

**2026-06-22 10:25 -04:00** — Halved CA box widths at operator request on /bizzy/ca_safety (custom collision-avoidance node, not stock nav2 collision_monitor): stop_width 4.0->2.0 m, slowdown_width 6.0->3.0 m. Lengths unchanged (stop_length 5, slowdown 5-20). Both sets returned successful + verified via param get. RUNTIME ONLY — not durable across ca_safety relaunch; push to YAML if it should persist.

**2026-06-22 10:28 -04:00** — Set controller avoidance weight at operator request: /bizzy/controller_server FollowPath.obstacle_avoidance_weight 0.5->1.0. Set returned successful + verified via param get = 1.0. RUNTIME ONLY — not durable across controller_server relaunch; push to YAML if it should persist.

**2026-06-22 10:30 -04:00** — Set sidescan range at operator request: /bizzy/sensors/sidescan/garmin_sidescan range_m 45.0->60.0 m (= range_max_m bound). Set returned successful + verified via param get = 60.0.

**2026-06-22 10:37 -04:00** — Operator query: sidescan ping rate + coverage per 480 pings. Measured ping rate ~8.86 pings/s (delta of cumulative status ping count: 277 pings / 31.3 s) at 60 m range (physical ceiling 2*60/1500 = 12.5 pings/s). 480 pings = 54.2 s. SOG snapshot 1.82 m/s (3.54 kn) from SBG gps_vel (N -1.34, E 1.235). -> along-track coverage in 480 pings ~99 m (0.053 nm). SOG is a snapshot; ping rate tied to current 60 m range.

**2026-06-22 14:33 -04:00** — Set controller lookahead at operator request: /bizzy/controller_server FollowPath.lookahead_time 0.0->3.0 s (lookahead_distance still 0.0, min 1.0 m). Set successful + verified via param get = 3.0. RUNTIME ONLY — not durable across controller_server relaunch; push to YAML if it should persist.

**2026-06-22 14:34 -04:00** — Reverted controller lookahead at operator request: /bizzy/controller_server FollowPath.lookahead_time 3.0->0.0 s (back to min-distance floor 1.0 m; lookahead_distance still 0.0). Set successful + verified via param get = 0.0. RUNTIME ONLY.

**2026-06-22 14:37 -04:00** — ANOMALY: operator reported 'Bizzy is going crazy, not sure what she is doing... seems to be back online now' immediately after I set FollowPath.lookahead_time 0.0->3.0. Mitigate-before-diagnose: reverted lookahead_time 3.0->0.0 (verified) to restore the prior known-good state. Temporal correlation with the 0->3 change is strong but NOT confirmed as cause. Controller_server lifecycle re-checked after revert. RCA deferred to wrap-up: investigate whether lookahead_time=3 (velocity*3s lookahead) drove the erratic path-following at survey speed.

**2026-06-22 14:41 -04:00** — Started 20-min (1200s) camera capture at operator request via record_camera_topics.sh (operator notes it is raining at Bizzy's location) -> ~/data/logs/bizzy_images/bag_2026-06-22T14.40.28_ffmpeg_seg (mcap/zstd_fast, same 24 topics: 4 OAK cams ffmpeg+raw/compressed segmentation+camera_info, TF, diagnostics, robot_description, local_costmap). Recorder confirmed Recording.

**2026-06-22 15:06 -04:00** — 20-min rain camera capture complete (exit 0, clean SIGINT — 'Recording stopped', metadata.yaml written). Bag: ~/data/logs/bizzy_images/bag_2026-06-22T14.40.28_ffmpeg_seg/ — 804M mcap + 28K metadata.

**2026-06-22 15:07 -04:00** — Started 30-min (1800s) camera capture at operator request via record_camera_topics.sh -> ~/data/logs/bizzy_images/bag_2026-06-22T15.06.41_ffmpeg_seg (mcap/zstd_fast, same 24 topics). Recorder confirmed Recording.

**2026-06-22 17:00 -04:00** — 30-min camera capture complete (exit 0, clean — metadata.yaml written). Bag: ~/data/logs/bizzy_images/bag_2026-06-22T15.06.41_ffmpeg_seg/ — 1.3G mcap + 28K metadata. Today's captures: 458M + 804M + 1.3G ~= 2.6G total in ~/data/logs/bizzy_images/.

**2026-06-22 17:01 -04:00** — Stopped sidescan transmit at operator request (boat at the dock): set_transmit data:false -> success=True, message='transmit off'. Verified /garmin_sidescan/transmitting = false.

**2026-06-22 17:05 -04:00** — Session end — boat at the dock, sidescan transmit off. Operator requested wrap-up; gabby is field side (gitcloud origin) so full /wrap-up-deployment runs dev-side only. Committing + pushing this gabby log to gitcloud so a dev host can collect it for wrap-up (issue close, PR, RCA). Open items for dev wrap-up: (1) issue-less start — create + link the deployment issue dated 2026-06-22; (2) RCA: erratic boat behavior immediately after FollowPath.lookahead_time 0->3, reverted to 0 (controller_server stayed active); (3) all runtime param changes today were NOT persisted to YAML (sidescan range, CA stop/slowdown widths halved, controller obstacle_avoidance_weight 0.5->1.0) — decide which to make durable.

**2026-06-22 17:08 -04:00** — Baked runtime tunes into YAML at operator request (durable across relaunch): bizzyboat_project11/config/nav2_overlay.yaml — ca_safety slowdown_width 6.0->3.0, stop_width 4.0->2.0 (CA boxes half width); controller_server FollowPath.obstacle_avoidance_weight 0.5->1.0. Updated inline comments with dated 2026-06-22 tune notes. NOT baking lookahead_time (that change misbehaved and was reverted to 0). Field-mode commit to jazzy + push to gitcloud.

**2026-06-22 17:17 -04:00** — Final field-side closeout: project repo working tree clean and in sync with origin/jazzy (gabby log + nav2_overlay.yaml tune both committed and pushed to gitcloud). Workspace .claude/settings.local.json edit (dlog.sh allowlist) is gitignored — intentionally not committed. Nothing else edited locally. Deployment handed off for dev-side /wrap-up-deployment (issue creation/close, dev-log consolidation + operator interview, wrap-up PR, RCA).
