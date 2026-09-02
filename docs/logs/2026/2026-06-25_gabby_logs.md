# 2026-06-25 — gabby log (BizzyBoat deployment)

Deployment issue: https://github.com/rolker/unh_echoboats_project11/issues/331
Host: gabby
Side: field
Started: 2026-06-25 10:33 -04:00 (deployment-mode activated late; boat already on the water this session)

**2026-06-25 10:34 -04:00** — Deployment mode activated late this session (boat already on the water). Issue-less field start; backfill the deployment-issue link from a dev host.

**2026-06-25 10:34 -04:00** — udp_bridge: added mavros rc/in, rc/out, state, setpoint_velocity/cmd_vel + sound_speed on all 3 operator connections (wifi/vpn/cell), and water_temperature on cell. Applied live via remote_advertise (verified against bridge_info) and persisted to bizzyboat.yaml. NOTE: dev side had independently landed the same mavros/sound_speed set via PR #325 (72d9dd9); committed+pushed only the unique cell water_temperature add (1037595).

**2026-06-25 10:34 -04:00** — controller_server FollowPath.obstacle_avoidance_weight set 1.0 -> 0.0 LIVE ONLY (operator: false-positive obstacles bending survey lines). line_following_weight stays 1.0; reflex Collision Monitor unaffected. Not persisted to nav2_overlay.yaml per operator — a nav relaunch reverts to 1.0. Revert: ros2 param set /bizzy/controller_server FollowPath.obstacle_avoidance_weight 1.0

**2026-06-25 10:38 -04:00** — ca_safety zones effectively disabled per operator: slowdown_min/max_length, slowdown_width, stop_length, stop_width all set 0.01 LIVE (verified). Prior: slowdown 5-20m len x 3.0w, stop 5.0x2.0. Live-only, not persisted — nav relaunch restores config. Revert: re-set to those values or relaunch nav.

**2026-06-25 10:39 -04:00** — Started 10-min (600s) camera bag via record_camera_topics.sh -> ~/data/logs/bizzy_images/bag_2026-06-25T10.39.25_ffmpeg_seg. All 4 OAK ffmpeg+segmentation, TF, /bizzy/local_costmap/costmap. Recording during CA-disabled run. Ends ~10:49.

**2026-06-25 10:49 -04:00** — 10-min camera bag complete (clean SIGINT flush, exit 0): bag_2026-06-25T10.39.25_ffmpeg_seg, 438M mcap + metadata.yaml in ~/data/logs/bizzy_images/.

**2026-06-25 11:09 -04:00** — Restored CA + path avoidance to config values (verified live): ca_safety slowdown 5-20m len x 3.0w, stop 5.0x2.0; controller_server FollowPath.obstacle_avoidance_weight 1.0. CA-disabled / avoidance-off window closed.
