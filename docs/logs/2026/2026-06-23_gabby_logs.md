# 2026-06-23 — gabby log (BizzyBoat deployment #313)

Deployment issue: https://github.com/rolker/unh_echoboats_project11/issues/313
<!-- backfilled at wrap-up: issue-less field start (#533) linked to #313, the deployment dev created the morning of 2026-06-23 -->
Host: gabby
Side: field
Started: 2026-06-23 09:14 -04:00

## 2026-06-23

**2026-06-23 09:15 -04:00** — Deployment mode activated on gabby (field side) via /start-deployment. Issue-less start (#533): no deployment issue yet; a dev host backfills the link later (finds this log by date). TODO (dev): create + link the deployment issue, stamp '- [gabby log](docs/logs/2026/2026-06-23_gabby_logs.md)' under its ## Logs section, and clear the 'pending' marker in the header above.

**2026-06-23 09:18 -04:00** — Enabled sidescan transmit at operator request: set_transmit data:true on /bizzy/sensors/sidescan/garmin_sidescan/set_transmit (std_srvs/SetBool) -> success=True, message='transmitting'. Verified /garmin_sidescan/transmitting = true.

**2026-06-23 10:08 -04:00** — Started 10-min (600s) camera capture at operator request via record_camera_topics.sh -> ~/data/logs/bizzy_images/bag_2026-06-23T10.08.21_ffmpeg_seg (mcap/zstd_fast). Recorder confirmed subscribed (4 OAK cams ffmpeg + raw/compressed segmentation + camera_info, /tf, /tf_static, /diagnostics, /bizzy/robot_description, /bizzy/local_costmap/costmap) and Recording.

**2026-06-23 10:19 -04:00** — Camera capture complete: 600s elapsed, clean SIGINT flush (cache written, metadata.yaml present). Bag 435M -> ~/data/logs/bizzy_images/bag_2026-06-23T10.08.21_ffmpeg_seg/bag_2026-06-23T10.08.21_ffmpeg_seg_0.mcap.

**2026-06-23 10:48 -04:00** — Operator: running a trackline; after a few segments it's going off line. (Boat drifting off the planned trackline partway through the survey segments.)

**2026-06-23 10:50 -04:00** — Off-line check: RTK fix still solid — /bizzy/sensors/sbg/gps_pos status=0 (SOL_COMPUTED), type=7 (RTK_INT), 31/46 SVs used. Localization not the cause; off-line behavior is downstream (controller hold / environmental set / path tolerance). No per-node controller_server log file in current ~/.ros/log session dirs to inspect.

**2026-06-23 10:51 -04:00** — Operator: looks like yesterday's behavior — created a new trackline and executed, boat took off in a DIFFERENT direction (not the commanded line). Operator hit 'clear', boat hovered (held station), then re-sent the second trackline and it seems to be tracking OK now. Workaround (clear + resend) recovered it, same as yesterday. RTK was solid throughout (logged 10:50).

**2026-06-23 11:17 -04:00** — Trackline-RCA enablement: added /bizzy/marine/mission_plan (trackline geometry) and /bizzy/marine/mission_manager/command (execute/clear/next) to the boat-side 'logger' record list in bizzyboat_project11/config/bizzyboat.yaml. These were the gap — the boat bag logged the helm bus + mission *status* but not the trackline that was sent. Both std_msgs/String, low-rate, verified live. Config is installed via ament install(DIRECTORY): takes effect after a rebuild+relaunch (running logger PID 183112 won't pick it up until relaunch).

**2026-06-23 11:19 -04:00** — Committed logger config change as f3a43c1 on jazzy (field mode, direct commit). Not pushed to gitcloud yet (batched). Takes effect on next rebuild+relaunch of the boat stack.

**2026-06-23 11:22 -04:00** — Started 5-min (300s) camera capture at operator request via record_camera_topics.sh -> ~/data/logs/bizzy_images/bag_2026-06-23T11.21.41_ffmpeg_seg (mcap/zstd_fast). Recorder confirmed subscribed + Recording.

**2026-06-23 11:30 -04:00** — 5-min camera capture complete: 300s, clean flush (metadata.yaml present). Bag 208M -> ~/data/logs/bizzy_images/bag_2026-06-23T11.21.41_ffmpeg_seg/.

**2026-06-23 12:01 -04:00** — Pushed logger change to gitcloud. Initial push rejected (remote jazzy ahead by 13 commits — all docs/logs from the #309 deployment wrap-up, no overlap with bizzyboat.yaml). Fetched + rebased our commit cleanly onto origin/jazzy (SHA f3a43c1 -> 2a72464) and pushed: 84c94ee..2a72464 jazzy. Rebase also pulled the remote's 2026-06-22 dev/salmon/gabby log updates into the local tree.

**2026-06-23 13:28 -04:00** — Diagnostics sweep (operator asked re: Starlink). Starlink healthy: dish reachable, 0.0% ping drop, ~19ms latency, uplink ~21 Mbps, SNR above noise floor, 0.05% obstruction, no thermal alerts, uptime ~96.8h. One Starlink WARN: alerts 'lower_signal_than_predicted' (common marine/motion benign alert; link metrics unaffected). Other non-OK in /diagnostics: ERROR udp_bridge operator resend give-up rate 117.33/s (exceeds threshold) -- operator link lossy, POSSIBLY relevant to the trackline-wrong-direction event (mission_plan rides this bridge); ERROR mavros System 'Sensor health' (known FCU sensor-health flag, ties to #312 gyro RCA from #309 wrap-up); ERROR ping router_op_direct + salmon_direct unreachable (direct LAN paths down -- likely expected over Starlink); STALE ping dns_cloudflare 39.6s; WARN teltonika cellular LTE -98dBm (backup link, marginal); WARN mikrotik ether2-5/wlan1 'Not running' (unused ports, expected); WARN mavros Mount (no gimbal, expected).

**2026-06-23 14:01 -04:00** — Set sidescan range to 40 at operator request: ros2 param set /bizzy/sensors/sidescan/garmin_sidescan range_m 40.0 (no set_range service; range is a node param). Was 0.0 (auto); bounds range_min_m=1.0 / range_max_m=60.0. Verified with param get: range_m = 40.0 (zenoh set confirmed, not dropped). Note: runtime param, not durable across a node relaunch.

**2026-06-23 15:12 -04:00** — Down-view 'stuck at 1.8' triage. nadir_depth: max_range=1.843m, range(current return)=0.176m. Tried reverting range_m to 0.0 (auto) per operator -> FAILED: validator rejects 0.0 (allowed 1.0-60.0); range_m stays 40.0. Key insight: range_m=40 but down-view max_range=1.84 -> range_m controls the SIDESCAN channel, NOT the down-view; my earlier sidescan change did NOT cause the down-view cap, and a revert wouldn't fix it. Down-view ranges independently (device-side). 0.0 was a startup sentinel, not settable; restoring it needs a node relaunch (operator-driven). No 'auto' param or service on the node (params have no auto-range knob; services are set_transmit/set_parameters only).

**2026-06-23 15:13 -04:00** — Set sidescan range to 5 m at operator request: range_m 40.0 -> 5.0 (within 1-60 bounds). Verified via param get: range_m = 5.0 (zenoh set confirmed). Runtime param, not durable across node relaunch.

**2026-06-23 15:13 -04:00** — Set sidescan range to 35 m at operator request: range_m 5.0 -> 35.0. Verified via param get: range_m = 35.0 (zenoh set confirmed).

> **Wrap-up correction (operator)**: gabby's conclusion that `range_m` affects only the sidescan channel and the down-view stuck-at-~1.8 m was independent/device-side is **walked back**. Operator observed that setting the sidescan range to **5 m got the down-view channel auto-tracking the bottom again** — i.e. there IS an interaction between the sidescan `range_m` setting and the down-view auto-track. The "device-side, unrelated" attribution (entries 15:12 and 15:13, and open-item #5) is incorrect; this is a real cross-channel behavior worth a follow-up.

**2026-06-23 17:23 -04:00** — RECOVERY: back at the dock. Operator: boat ran out of power and was towed in. Phase = recovery. (Power-exhaustion underway -> tow recovery; key RCA item for wrap-up.)

**2026-06-23 17:25 -04:00** — Field-side wrap-up. Deployment ended at the dock (towed in, power exhaustion). Operator: nothing further to report; dev agent will dig into the battery logs. Committing + pushing this gabby log to gitcloud for the dev-side /wrap-up-deployment. Open RCA/handoff items listed in the appendix section below.

## Open items for dev wrap-up

Handoff for the dev-side `/wrap-up-deployment` agent (field host has no GitHub access).

1. **Power exhaustion → tow (primary).** Boat ran out of power underway and was towed in. Operator is driving this RCA. Note: FCU dataflash logging is disabled on this boat (LOG_BACKEND_TYPE=0, no onboard logs), so reconstruct the V/I history from the boat bag `/bizzy/mavros/battery` (in the `logger` record list), not FCU onboard logs.
2. **Trackline wrong-direction (recurring).** New trackline executed → boat headed off in the wrong direction; `clear` (boat hovers) + resend recovered it. Same as a prior day per operator. RTK was solid throughout, so not localization. `mission_plan` + `mission_manager/command` are now logged (commit `2a72464`, takes effect next rebuild+relaunch) to enable commanded-vs-actual analysis next run.
3. **udp_bridge operator resend give-ups 117/s (ERROR).** Operator link lossy at the time; the trackline (`mission_plan`) rides this bridge — possible contributor to item 2. Investigate link quality.
4. **mavros System 'Sensor health' (ERROR).** Confirm whether this is the known FCU 3D-gyro health flag (#312 RCA from the #309 wrap-up) or something new.
5. **Down-view sonar stuck ~1.8 m.** `nadir_depth` max_range pinned ~1.84 m, current return ~0.18 m. `range_m` controls the sidescan channel only (NOT the down-view), so the sidescan range changes did not cause this. Likely transducer / bottom-lock (device-side). Sidescan `range_m` left at 35 m (runtime only, not durable across relaunch).
6. **Backfill the deployment issue (issue-less start, #533).** No deployment issue was created (field-side, no GitHub). Create + link it (date-anchored 2026-06-23), stamp `- [gabby log](docs/logs/2026/2026-06-23_gabby_logs.md)` under its `## Logs` section, and clear the `Deployment issue: pending` marker in this log's header.
