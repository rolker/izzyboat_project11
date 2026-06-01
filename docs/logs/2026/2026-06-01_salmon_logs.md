# 2026-06-01 — salmon log (BizzyBoat deployment f1fb95e)

Deployment issue: git-bug `f1fb95e` — "Deployment 2026-06-01: clean survey run — override/resume (#52) + turning limits + cross-track"
Host: salmon
Side: field
Started: 2026-06-01 13:20 -04:00

> **Note for next dev-side `/start-deployment`:** stamp a link to this
> file under the deployment issue's `## Logs` section
> (`docs/logs/2026/2026-06-01_salmon_logs.md`). Field side is read-only
> on the issue, so it could not add the link itself.

**2026-06-01 13:24 -04:00** — stack up; salmon sees 17 nodes via DDS: `/operator/camp` + `/operator/udp_bridge` running, bizzy command_bridge_sender/joy/helm chain, network monitors (mikrotik/teltonika/starlink/ping) + rosbag2_recorder. Boat autonomy graph (gabby) not visible from salmon by design (arrives via UDP bridge). Operator side + bridge nominal.

**2026-06-01 13:25 -04:00** — CAMP not showing costmap. Probe on salmon: `/bizzy/local_costmap/published_footprint` arrives but `/bizzy/local_costmap/costmap` (OccupancyGrid) does NOT. Footprint present ⇒ costmap node alive on gabby + bridge link up; grid topic simply not forwarded across UDP bridge. Operator side auto-receives, so send-side (gabby) udp_bridge forwarded-topic set is the suspect, not a throttle (absent ≠ 0.5 Hz). Next: confirm gabby udp_bridge forwards local_costmap/costmap.

**2026-06-01 13:30 -04:00** — costmap now working in CAMP. Operator: "I forgot I had to do a hack" — resolves the 13:25 costmap-not-bridged finding. The grid topic crossing the bridge required a manual workaround the operator applied (specifics not captured live). ⚠️ **WRAP-UP TODO:** capture exactly what the hack was and where it lives, so the costmap-over-bridge step is either documented or made permanent (the bridge config gap from 13:25 is real — the hack is the current stopgap).

**2026-06-01 13:31 -04:00** — controls checks done, getting ready to launch.

**2026-06-01 13:46 -04:00** — CAMP (operator station app on salmon) crashed and was restarted by operator. Back up. ⚠️ **WRAP-UP TODO:** check for a CAMP crash dump / stderr on salmon to capture the cause (no live diagnosis — operator restarted to keep going).

**2026-06-01 13:50 -04:00** — CAMP crashed AGAIN; boat has been in the water a few minutes by now. Now a repeating crash, not a one-off. Could not capture a crash signature live: `~/.ros/log` has only stale `operator-camp-*-stdout.log` from prior sessions — CAMP isn't logging to the ROS tree this session (likely launched from a terminal/tmux), and per ops policy did not poke the operator's console. Impact is operator situational-awareness only — autonomy + control run on gabby, unaffected by a salmon display crash. ⚠️ **WRAP-UP TODO:** get CAMP's actual stderr/fault (relaunch from a terminal to capture, or find where its console output goes); repeating crash on the operator station needs a real root-cause.

**2026-06-01 14:01 -04:00** — ROOT CAUSE CONFIRMED (CAMP crash loop). 7 crashes in `~/.ros/log/2026-06-01-13-18-21-991976-salmon-224573/launch.log`, all `exit code -6` (SIGABRT), all the same: uncaught `tf2::BackwardExtrapolationException`, transform `[bizzy/map]→[earth]`, requested time ~56–66 s older than the oldest entry in CAMP's TF cache. (The `NavSource::trySubscribe` lines before each abort are just 1 Hz timer noise — NavSource takes lat/lon directly, no TF.)
- **Crash site:** `Platform::pathCallback` (`camp/src/camp/platform_manager/platform.cpp:241`) subscribes to a `nav_msgs/msg/Path` and transforms **each pose at its own header stamp** via `getGeoCoordinate` → `transform_buffer_->transform(ps, "earth", 1.5s)` in `camp/src/camp/ros/ros_widget.cpp:19` — **no try/catch**. A Path whose poses carry stale planning stamps (older than the map→earth cache) throws → terminate → abort.
- **Trigger (operator-reported):** new nav-stack visualizations this run — the followed-path / survey-line-avoidance overlay (`unh_marine_navigation` #30/#51 + #199/#200, all merged 2026-06-01). `platform.cpp` itself took a 1-line change in today's sync (jazzy `031fc86`). The Path poses arrive over the bridge stamped in the past → backward-extrapolation.
- **Contrast:** CAMP's `markers`/`collision_monitor` paths use a tf2 message_filter that *drops* stale frames gracefully ("Message Filter dropping message … earlier than all the data in the transform cache"). The Path path has no such guard.
- **Impact:** operator-display SA only; autonomy + control on gabby unaffected.
- **Immediate mitigation:** stop the new Path overlay (turn off the followed-path/survey-avoidance publisher on the nav stack — it's display-only) → removes the trigger, no rebuild.
- **Permanent fix:** guard `getGeoCoordinate`'s transform (catch tf2 exception → fall back to latest-tf `TimePointZero` or skip the pose, mirroring the message_filter drop). Field-mode repo on salmon; needs camp rebuild + operator relaunch. → WRAP-UP / fix candidate.

**2026-06-01 14:06 -04:00** — FIX APPLIED (operator chose patch-now). Guarded `ROSWidget::getGeoCoordinate` in `camp/src/camp/ros/ros_widget.cpp`: empty-frame_id early-out + try/catch on `tf2::TransformException`; on a stale/extrapolation throw it retries the transform at latest-TF (stamp 0, map→earth is quasi-static) so the Path point still renders, and only drops the point (throttled WARN) if even that fails. Mirrors the already-safe `Grid::getGeoCoordinate` pattern (that's why the costmap/grid path never crashed). Built camp into `ui_ws/install` (colcon, --symlink-install, 20 s, clean). camp is field mode (`git@gitcloud:field/camp.git`), on `jazzy`. Operator to relaunch CAMP from the `ui` tmux window to pick up the new binary. ⚠️ **NOT yet committed** — working-tree edit only; commit to camp `jazzy` (field mode) at a breakpoint. ⚠️ **WRAP-UP TODO:** (1) commit + push the camp fix; (2) upstream question — why are the new nav-stack Path overlay poses stamped ~56 s in the past (bridge latency vs planner stamping nominal-line poses with old times)? The guard stops the crash but stale stamps may still mean the overlay lags; worth fixing at the source. (3) confirm post-relaunch the followed-path/survey-avoidance overlay renders correctly.

**2026-06-01 14:15 -04:00** — CAMP stable after relaunch on the patched build; operator: "camp seems ok now." Crash loop resolved (was every ~1–2 min, none since relaunch ~14:06). Fix confirmed working on water. Overlay-render correctness (wrap-up TODO #3) not yet explicitly checked — CAMP is up and not crashing, which is the headline.

**2026-06-01 16:37 -04:00** — boat recovered; on-water portion of the run complete. Natural breakpoint — moving toward wrap-up. Open items: camp tf-guard fix still uncommitted (working-tree edit on camp `jazzy`, field mode); upstream stale-stamp question; overlay-render confirmation; and the costmap-over-bridge "hack" specifics from 13:30.
