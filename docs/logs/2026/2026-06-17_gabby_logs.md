# 2026-06-17 — gabby log (BizzyBoat deployment)

Deployment issue: _pending — new survey day; issue to be created from a dev host and link stamped here_
Host: gabby
Side: field
Started: 2026-06-17 08:58 -04:00

## 2026-06-17

**2026-06-17 08:58 -04:00** — Stack up. Operator running a small in-water test.

**2026-06-17 08:58 -04:00** — Sidescan pinging started at operator request. `set_transmit data:true` → `success=True, message='transmitting'` (sound-speed interlock passed). Verified live: `sonar_image_port` publishing ~12.9 Hz, steady. `/bizzy/sonar_logger` up.

**2026-06-17 08:58 -04:00** — Checked FollowPath controller PID gains (`/bizzy/controller_server`): p=-13.0, i=-0.5, d=-1.2; i_clamp ±30; antiwindup=False, saturation=True; gain_ref_speed=1.8, gain_v_min=0.5, reset_threshold=1.0s. Read-only spot check, no changes.

**2026-06-17 09:02 -04:00** — Set `FollowPath.default_speed` 1.543→2.0578 m/s (4 kt) at operator request. Flagged that 4 kt is above the documented max (~1.9 m/s / 3.7 kt STW, full throttle per bizzyboat_hardware.md) and that with antiwindup=False the unreachable setpoint risks integral wind-up; operator accepted the risk and chose the literal 4 kt. Set verified via `param get` (=2.0578). Runtime-only — not durable across a nav2 relaunch.

**2026-06-17 09:03 -04:00** — Set `FollowPath.default_speed` 2.0578→0.5144 m/s (1 kt) at operator request. Verified via `param get` (=0.5144). Runtime-only.

**2026-06-17 09:04 -04:00** — Set `FollowPath.default_speed` 0.5144→1.5433 m/s (3 kt, cruise) at operator request. Verified via `param get` (=1.5433). Runtime-only.

**2026-06-17 09:05 -04:00** — Set `FollowPath.default_speed` 1.5433→0.7717 m/s (1.5 kt) at operator request. Verified via `param get` (=0.7717). Runtime-only.

**2026-06-17 09:06 -04:00** — Set `FollowPath.default_speed` 0.7717→0.5144 m/s (1 kt) at operator request. Verified via `param get` (=0.5144). Runtime-only.

**2026-06-17 09:06 -04:00** — Set `FollowPath.default_speed` 0.5144→0.7717 m/s (1.5 kt) at operator request. Verified (=0.7717). (Operator stepping speed setpoint up/down — apparent speed-response sweep.)

**2026-06-17 09:08 -04:00** — Set `FollowPath.default_speed` 0.7717→0.5144 m/s (1 kt) at operator request. Verified (=0.5144).

**2026-06-17 09:09 -04:00** — Operator reported instability at 1 kt. Diagnosed: FollowPath plugin is `marine_nav_crabbing_path_follower`, which speed-schedules the cross-track PID output by `gain_ref_speed / max(v, gain_v_min)` (#76). With gain_ref_speed=1.8, gain_v_min=0.5, the effective cross-track gain is ~3.5× at 1 kt (v=0.514, on the v_min floor) vs ~1.17× at 3 kt — schedule over-compensates near minimum steerage → oscillation. Matches the sweep (stable at 3/1.5 kt, unstable at 1 kt). Mitigations offered (run ≥1.5 kt / raise gain_v_min→1.0 / lower gain_ref_speed); none applied yet pending operator choice.

**2026-06-17 09:12 -04:00** — Set CA stop zone to ~off at operator request (controlled test): `ca_safety` `stop_length` 5.0→0.01 m, `stop_width` 4.0→0.01 m. Slowdown zone left intact (slowdown_max_length=20, slowdown_width=6). Effect: no hard-stop CA response until obstacle ~1 cm off bow; slowdown braking still active. Both verified via `param get`. Runtime-only. **Restore stop_length=5.0 / stop_width=4.0 before normal autonomous ops.**

**2026-06-17 09:15 -04:00** — Applied 1-kt instability mitigation (option 2): `FollowPath.pid.gain_v_min` 0.5→1.0. Cuts the low-speed cross-track gain boost at 1 kt from 3.5× to 1.8× (scale=1.8/max(0.514,1.0)=1.8); cruise (≥1.8 m/s) unaffected. Verified via `param get` (=1.0). Runtime-only. Awaiting operator re-test at 1 kt.

**2026-06-17 09:16 -04:00** — Disabled the slowdown zone too at operator request ("disable both ca ranges"): `ca_safety` slowdown_min_length 5.0→0.01, slowdown_max_length 20.0→0.01, slowdown_width 6.0→0.01. Combined with the earlier stop-zone disable, **CA is now fully off** — no slow or stop response to obstacles; obstacle avoidance is entirely manual/operator. All five zone params verified at 0.01. Runtime-only. **Restore before normal autonomous ops: stop_length=5.0, stop_width=4.0, slowdown_min_length=5.0, slowdown_max_length=20.0, slowdown_width=6.0.**

**2026-06-17 09:18 -04:00** — Also disabled the FollowPath controller's obstacle-avoidance term at operator request: `FollowPath.obstacle_avoidance_weight` 0.5→0.0 (avoid_speed already 0.0). Verified (=0.0). Combined with both ca_safety zones off, **the boat now has zero automatic obstacle handling** — controller follows the path through costmap obstacles, no reactive slow/stop. Runtime-only. **Restore obstacle_avoidance_weight=0.5 before normal autonomous ops.**

**2026-06-17 09:19 -04:00** — Set `FollowPath.default_speed` →0.5144 m/s (1 kt) at operator request. Verified (=0.5144). This is the re-test at 1 kt after the gain_v_min→1.0 mitigation (09:15).

**2026-06-17 09:20 -04:00** — Set `FollowPath.default_speed` →0.2572 m/s (0.5 kt) at operator request. Verified (=0.2572). Note: below the gain_v_min=1.0 floor, so cross-track gain boost stays capped at 1.8× (1.8/max(0.257,1.0)); steerage authority marginal at this speed.

**2026-06-17 09:20 -04:00** — Set `FollowPath.default_speed` →1.8006 m/s (3.5 kt) at operator request. Verified (=1.8006). Near the ~3.7 kt max; at the gain-schedule reference (1.8), so cross-track gain ≈1.0× (nominal).

**2026-06-17 09:22 -04:00** — Baked the gain_v_min tune into config: `nav2_overlay.yaml` FollowPath `pid.gain_v_min` 0.5→1.0 (with rationale comment). Committed field-mode on `jazzy` as `4bb736d` (agent identity, pre-commit hooks passed). Only the YAML committed — deployment log left uncommitted (still appending; batch at wrap-up). NOT pushed — gabby has no SSH agent for gitcloud (`git bug pull origin` failed earlier the same way); reconcile via `/import-field-changes` from a dev host or push when connectivity allows. Note: this banks ONLY the PID floor; the live CA-disable params (stop/slowdown=0.01, obstacle_avoidance_weight=0) were NOT baked — they remain runtime-only and revert on relaunch (intended).

**2026-06-17 09:26 -04:00** — Stopped sidescan pinging at operator request: `set_transmit data:false` → `success=True, message='transmit off'`. Verified: `sonar_image_port` produced no messages in a 4 s hz window (was ~12.9 Hz). Transmit off.

**2026-06-17 09:27 -04:00** — Restored CA at operator request. `ca_safety`: stop_length→5.0, stop_width→4.0, slowdown_min_length→5.0, slowdown_max_length→20.0, slowdown_width→6.0; `controller_server` FollowPath.obstacle_avoidance_weight→0.5. First batch rejected slowdown_min_length=5.0 (ordering: min must be ≤ max, and max was still 0.01 at that instant); re-set after max was back to 20.0. All six verified at their original values. **CA fully re-enabled.**

**2026-06-17 09:34 -04:00** — Boat recovered (operator-reported), transiting to a second lake site for another survey today. End of the first-site session. State at recovery: sidescan transmit off; CA fully restored (zones 5/4/5/20/6, obstacle_avoidance_weight 0.5); `FollowPath.default_speed` left at 1.8006 m/s (3.5 kt, runtime-only); baked PID fix `gain_v_min=1.0` committed (`4bb736d`, unpushed). Runtime-only params (default_speed, CA zones) reset to YAML defaults on the next nav/ca_safety relaunch at the new site; the baked gain_v_min persists.

**2026-06-17 10:32 -04:00** — ⚠️ Clock discontinuity: host clock advanced ~58 min between the 09:34 entry above and this one with no real elapsed gap (likely NTP resync when the boat reconnected to a network around recovery/transit). Entries timestamped ≤09:34 are on the pre-sync clock; ≥10:32 on the post-sync clock. Bag/file timestamps below use the post-sync clock.

**2026-06-17 10:32 -04:00** — Started 30 min (1800 s) camera capture at operator request via `record_camera_topics.sh 1800` (background id bsjwy68r8). Recording 4 OAK cameras (ffmpeg + segmentation raw/compressed + camera_info), TF, diagnostics, robot_description, local costmap → mcap at `~/data/logs/bizzy_images/bag_2026-06-17T10.31.57_ffmpeg_seg/`. All 24 topics had live publishers (camera stack up post-recovery). Auto-stops + flushes at ~11:02.

**2026-06-17 11:02 -04:00** — 30 min camera capture completed cleanly (exit 0, full 1800 s). Bag closed/flushed OK (metadata.yaml present): `bag_2026-06-17T10.31.57_ffmpeg_seg_0.mcap` = 2.0 GB at `~/data/logs/bizzy_images/`.

**2026-06-17 11:03 -04:00** — Started 20 min (1200 s) camera capture at operator request via `record_camera_topics.sh 1200` (background id bcl5u9qf9). Same topic set; → `~/data/logs/bizzy_images/bag_2026-06-17T11.03.00_ffmpeg_seg/`. All 24 topics subscribed, recording. Auto-stops ~11:23.

**2026-06-17 11:23 -04:00** — 20 min camera capture completed cleanly (exit 0, full 1200 s: ts 1781708580→1781709780). Bag flushed OK (metadata.yaml present): `bag_2026-06-17T11.03.00_ffmpeg_seg_0.mcap` = 1.4 GB at `~/data/logs/bizzy_images/`.

**2026-06-17 11:43 -04:00** — Cell-link / udp_bridge status check (operator query, boat in transit). Cell link UP: Teltonika RUTX11, LTE @ -92 dBm RSRP / -62 RSSI (fair), connection reachable; router mwan3 showed cellular SIM "Standby" + wan "disconnecting" (failover churn, modem interface Up). udp_bridge over cell actively flowing: tx ~44 KB/s, rx ~14 KB/s to operator. Stress flagged: resend give-ups bursting to ~75/s ("exceeds error threshold", cumulative 363362), fluctuating to 0 — bursty cell-link loss/saturation, the failure mode in the open udp_bridge audit issue (gitcloud 405770, queue_size/fail-fresh under saturation). wifi transport dead (no rx 2193 s, expected in transit); vpn tx failures/drops. No action taken — read-only status, link functional.

**2026-06-17 11:46 -04:00** — Started 1 h (3600 s) camera capture at operator request via `record_camera_topics.sh 3600` (background id b7i2lmfng). Same topic set; → `~/data/logs/bizzy_images/bag_2026-06-17T11.45.56_ffmpeg_seg/`. All 24 topics subscribed, recording. Auto-stops ~12:46 (~4 GB expected).

**2026-06-17 11:47 -04:00** — Started sidescan pinging (second site) at operator request: `set_transmit data:true` → `success=True, message='transmitting'`. Verified: `sonar_image_port` ~11.9 Hz steady (cf. ~12.9 Hz at first site — minor, likely range/auto-range difference). Sidescan data captured by the auto-running `/bizzy/sonar_logger` (separate sonar bag under `~/data/logs/bizzyboat_sonar/<session>`).

**2026-06-17 11:59 -04:00** — Advertised USB camera over udp_bridge vpn channel at operator request (0.5 Hz). `remote_advertise` (srv udp_bridge_interfaces/srv/Subscribe): remote=operator, connection_id=vpn, source=`/bizzy/sensors/cameras/usb/image_raw/compressed` (JPEG — self-contained frames; raw/ffmpeg unsuitable at 1-of-2s), period=2.0, queue_size=1 (fail-fresh). Service accepted (empty response = ok). NOTE: operator chose vpn despite it being down — vpn host empty / port 0, diagnostics show `vpn: tx failures/drops`, so frames hold/drop until the VPN endpoint comes up; nothing reaches operator until then. Runtime-only (lost on bridge relaunch). Cell channel was the working alternative (declined).

**2026-06-17 11:59 -04:00** — Set sidescan `range_m` →30.0 m at operator request (valid 1–60). Verified (=30.0). Runtime param on `garmin_sidescan`.

**2026-06-17 12:27 -04:00** — Started 30 min (1800 s) camera capture at operator request (`record_camera_topics.sh 1800`, id btwkdtziy) → `bag_2026-06-17T12.27.32_ffmpeg_seg/`. Auto-stops ~12:57. NOTE: overlaps the still-running 1 h capture (b7i2lmfng, ends ~12:46) — two recorders on the same camera topics 12:27–12:46 (duplicate data in two bags). Flagged to operator; both left running pending their call.

**2026-06-17 12:28 -04:00** — Halved CA stop zone at operator request: `ca_safety` stop_length 5.0→2.5 m, stop_width 4.0→2.0 m. Both verified. Stop zone still active (not disabled); slowdown zone (5/20/6) and obstacle_avoidance_weight (0.5) unchanged — CA remains on, smaller hard-stop box. Runtime-only.

**2026-06-17 12:39 -04:00** — Collapsed both ca_safety zones to ~zero (0.01) at operator request — **reason: too many false positives** tripping the reactive stop/slowdown (surface clutter at this site). stop_length/stop_width/slowdown_min_length/slowdown_max_length/slowdown_width all →0.01 (verified; set min before max for the ordering constraint). Reactive ca_safety layer now effectively off. Controller costmap avoidance `obstacle_avoidance_weight` left at 0.5 (operator named only the zones) — flagged as the next knob if false-positive path-steering persists. Runtime-only. Restore zones to 5/4/5/20/6 before normal autonomous ops.

**2026-06-17 12:40 -04:00** — Zeroed `FollowPath.obstacle_avoidance_weight` 0.5→0.0 at operator request (follow-on to the false-positive zone disable). Verified (=0.0). **All obstacle handling now off** (reactive ca_safety zones ~0 + controller costmap avoidance 0). Runtime-only. Restore obstacle_avoidance_weight=0.5 before normal autonomous ops.

**2026-06-17 12:45 -04:00** — 1 h camera capture (b7i2lmfng) completed cleanly (exit 0, full 3600 s). Bag flushed OK: `bag_2026-06-17T11.45.56_ffmpeg_seg_0.mcap` = 2.7 GB. The overlapping 30 min capture (btwkdtziy) still running to ~12:57.

**2026-06-17 12:57 -04:00** — 30 min camera capture (btwkdtziy) completed cleanly (exit 0, full 1800 s). Bag flushed OK: `bag_2026-06-17T12.27.32_ffmpeg_seg_0.mcap` = 1.3 GB. No camera captures now running.

**2026-06-17 13:13 -04:00** — Set sidescan `range_m` 30→50.0 m at operator request (valid 1–60). Verified (=50.0). Still pinging.

**2026-06-17 13:14 -04:00** — Sidescan ping rate at range=50 m: ~8.4 Hz (period ~0.118 s, steady) on sonar_image_port. Ping rate scales inversely with range (two-way travel time): ~12.9 Hz first site, ~11.9 Hz earlier here, 8.4 Hz at 50 m.

**2026-06-17 14:25 -04:00** — Operator: "looks like we are not getting sound speed again." Confirmed: `/bizzy/sensors/sound_speed/sound_speed` not publishing (no msgs in 5 s window) — AML SVS / sound_speed_bridge feed dropped. Sidescan still tx=ON using fallback `sound_speed=1500.0` (driver default, not live); pings accumulating (port=119839). Implications: (1) sonar logged against default 1500 m/s — freshwater actual ~1480, affects range/depth scaling + the recorded sound_speed used for post-proc correction; (2) if the interlock has a source-timeout, transmit could drop later if dropout persists (hasn't so far). "again" = recurring. No troubleshooting yet per live-ops contract — awaiting operator direction.

**2026-06-17 14:27 -04:00** — Operator noted yesterday's (2026-06-16) recurring SVS dropout was worked around with stopgap scripts the prior agent wrote: `bizzyboat_project11/scripts/temp_sound_speed.py` (committed 697e390) — subscribes Garmin `water_temperature`, computes SV = Marczak1997(T) + 0.96 (yesterday's bag-measured SVS−Marczak offset at Massabesic), publishes ROS `SoundSpeed` on `/bizzy/sensors/sound_speed/sound_speed` + M3 Valeport UDP (mercat:20003) @1 Hz; args `--offset/--rate/--fallback 1492.3/--host/--port/--no-ros/--no-udp`; ⚠️ must be stopped on real SVS restore; supersedes `static_sound_speed.py` (don't run both). Located but NOT run — see next.

**2026-06-17 14:30 -04:00** — Operator: "sound speed came back, stand down on the scripts." SVS recovered on its own; no stopgap run. Confirmed: `/bizzy/sensors/sound_speed/sound_speed` publishing again ~25 Hz. ⚠️ Observation: sidescan status still `sound_speed=1500.0` (fallback) with ping count climbing (122433) — did NOT auto re-sync to the recovered live value; would likely need a `set_transmit` false→true re-toggle to re-latch. Flagged to operator, no action taken (stand-down). Caveat for any future reuse: the +0.96 offset in temp_sound_speed.py is site-specific to yesterday's lake — re-derive if used at today's site.

**2026-06-17 14:31 -04:00** — Set sidescan `range_m` 50→20.0 m at operator request (valid 1–60). Verified (=20.0).

**2026-06-17 14:36 -04:00** — Set sidescan `range_m` 20→50.0 m at operator request (valid 1–60). Verified (=50.0).

**2026-06-17 14:39 -04:00** — Operator: "sound speed seems to be spotty." Confirmed intermittent: feed recovered ~14:30 (25 Hz briefly) then dropped again ~14:33; `sound_speed` published nothing in a 10 s window now; `sound_speed_bridge` diagnostic "No reading for 355.1s" (~6 min). Pattern = cutting in/out, matches yesterday's root cause (loose wire at SVS connector — intermittent contact, immune to power-cycle; was "being fixed" 2026-06-16 15:37). Impact: sidescan unaffected (still on 1500 fallback, decoupled); M3 holds last-good SV between gaps. Offered the temp_sound_speed.py steady-feed stopgap (built for exactly this yesterday) vs reseating the connector hardware-side; awaiting operator. No commands fired.

**2026-06-17 15:07 -04:00** — Re-enabled CA + avoidance at operator request (reverting the false-positive workaround). `ca_safety`: stop_length→5.0, stop_width→4.0, slowdown_min_length→5.0, slowdown_max_length→20.0, slowdown_width→6.0 (set max before min for ordering); `controller_server` FollowPath.obstacle_avoidance_weight→0.5. All six verified at original values. CA fully ON again — false-positive slow/stops may return if surface clutter persists. Runtime-only.

**2026-06-17 15:19 -04:00** — Operator: boat drifting, should be starting its next line. Localized (not CA, not helm): `collision_monitor_state` action_type=0 (DEACTIVATED — CA not stopping it); autonomy WAS commanding forward `piloting_mode/autonomous/cmd_vel` linear.x=1.8006 m/s (= 3.5 kt default_speed). So controller had a velocity but boat wasn't progressing onto the next line → **line-to-line transition didn't auto-sequence** (coverage/BT navigator not advancing). **Operator resolved by issuing a goto override — resumed normal line-following once it reached the goto.** Not CA / not thrust. WRAP-UP RCA candidate: why the survey line transition stalled (manda_coverage / bt_task_navigator sequencing). No autonomy commands fired by agent.

**2026-06-17 15:55 -04:00** — Set sidescan `range_m` 50→25.0 m at operator request (valid 1–60). Verified (=25.0).

**2026-06-17 16:01 -04:00** — Set sidescan `range_m` 25→15.0 m at operator request (valid 1–60). Verified (=15.0).

**2026-06-17 16:16 -04:00** — Set sidescan `range_m` 15→25.0 m at operator request (valid 1–60). Verified (=25.0).

**2026-06-17 16:32 -04:00** — Disabled CA + avoidance again at operator request: `ca_safety` all five zone params →0.01 (stop + slowdown), `controller_server` FollowPath.obstacle_avoidance_weight →0.0. All verified. All obstacle handling off again. Runtime-only. Restore: zones 5/4/5/20/6, obstacle_avoidance_weight 0.5.

**2026-06-17 16:35 -04:00** — Set sidescan `range_m` 25→15.0 m at operator request (valid 1–60). Verified (=15.0).

**2026-06-17 16:45 -04:00** — Set sidescan `range_m` 15→25.0 m at operator request (valid 1–60). Verified (=25.0).

**2026-06-17 16:46 -04:00** — Set sidescan `range_m` 25→35.0 m at operator request (valid 1–60). Verified (=35.0).

**2026-06-17 17:04 -04:00** — Stopped sidescan pinging at operator request: `set_transmit data:false` → `success=True, message='transmit off'`. Verified: `sonar_image_port` silent in a 4 s window. Transmit off.

**2026-06-17 17:05 -04:00** — Boat at the dock (operator-reported). Second-site survey done. Runtime state at dock: sidescan transmit OFF; CA + avoidance disabled (ca_safety zones 0.01, obstacle_avoidance_weight 0); default_speed 1.8006 m/s (3.5 kt); USB-cam-on-vpn advertise still registered (vpn endpoint was down). All runtime-only → revert on relaunch. SVS feed was intermittent late session (loose connector, yesterday's recurring issue). Durable change today: nav2_overlay gain_v_min 1.0 (commit 4bb736d, unpushed field-mode on jazzy).

**2026-06-17 17:24 -04:00** — Baked USB-cam-on-vpn into config at operator request. `bizzyboat.yaml` udp_bridge operator/vpn connection: added `usb_camera` to topics_list + `usb_camera: {source: sensors/cameras/usb/image_raw/compressed, period: 2.0, queue_size: 1}` to topics dict (mirrors the in-session remote_advertise; relative source, 0.5 Hz, fail-fresh). Committed field-mode on jazzy as `462edba` (agent identity, hooks passed). Verified installed config is a SYMLINK to source (install/.../config/bizzyboat.yaml → src), so effective on next udp_bridge relaunch with NO rebuild — same applies to the earlier nav2_overlay PID bake (also symlinked → relaunch-durable confirmed). Both commits (4bb736d, 462edba) unpushed (no SSH agent on gabby for gitcloud) — reconcile via /import-field-changes from a dev host.
