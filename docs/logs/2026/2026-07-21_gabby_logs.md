# 2026-07-21 — gabby log (BizzyBoat deployment — issue pending)

Deployment issue: pending (backfill from a dev host)
Host: gabby
Side: field
Started: 2026-07-21 13:30 -04:00

**2026-07-21 13:30 -04:00** — M3 multibeam pipeline: nodes all up and correctly wired (kongsberg_em_bridge → detections_to_pointcloud + sonar_logger → cube_bathymetry → coverage/tiles), but no data flowing. `ros2 topic hz` on /bizzy/sensors/m3/detections, /sonar_info, /cube_bathymetry/tiles and /coverage_tiles all produced zero messages over ~10 s. Bridge holds the publisher on /detections (1 pub, 2 subs) but was emitting nothing. Operator reports the M3 sonar software on the Windows machine is pinging and sending data — so the gap is on the capture side.

**2026-07-21 13:32 -04:00** — Operator restarted the perception launch group (perception_launch.py) to recover the M3 capture path. kongsberg_em_bridge came back as a fresh process (new PID). Recheck after relaunch: still no messages on /bizzy/sensors/m3/detections or /sonar_info over 12 s each. Capture path not yet flowing despite Windows-side pinging — needs further look (bridge network/connection config to the M3 host).

**2026-07-21 ~13:35 -04:00 (approx)** — M3 sonar path came back. That same 13:32 perception relaunch caught up rather than needing a further restart — the immediate post-relaunch recheck was just too early. Capture path flowing again from the same kongsberg_em_bridge process (no additional relaunch required).

**2026-07-22 — correction (from sonar-bag review)** — Reviewed the sonar_logger bags for 2026-07-21 (`~/data/logs/bizzyboat_sonar/`). The `/bizzy/sensors/m3/detections` stream was **continuous through the entire 13:30–13:35 window** — there was no capture-path outage in the recorded data. Detection receive-timestamps (local -04:00):

- `2026-07-21T14-09-43+00-00`: 10:19:22 → 13:26:28, no gap > 3 s
- `2026-07-21T17-26-41+00-00`: 13:26:42 → 13:50:17, no gap > 3 s
- `2026-07-21T17-50-39+00-00`: 13:50:40 → 14:04:17, no gap > 3 s

The only breaks in the whole stream are two recorder restarts between sessions (~14 s at 13:26:28→13:26:42, ~23 s at 13:50:17→13:50:40, the latter matching the 13:50:35 autostart) — not data stoppages. So the M3 bridge was publishing detections the whole time, and the recorder (an already-connected subscriber) captured them without interruption.

That means the 13:30 / 13:32 "no data flowing" reads were on the diagnostic `ros2 topic hz` subscriber only — a *fresh* subscriber that saw zero while the existing recorder subscriber had data. Consistent with the known rmw_zenoh new-subscriber discovery miss, not a capture-path failure. The 13:32 perception relaunch did not recover a stopped stream (the stream never stopped); the `hz` check simply started seeing the already-flowing data. The observations above are left as-recorded; this entry is the after-the-fact correction from the bag evidence.

## Issues encountered — coverage-tile updates (cube_bathymetry)

**2026-07-22 — code review of the live coverage-tile update path** — What actually
prompted the "is the sonar even flowing?" question yesterday: the live coverage
display was updating some tiles while others never updated, and often only **one**
tile updated when a ping's footprint clearly reached two or more. Detections were
flowing the whole time (see correction above), so this is a coverage-generation
issue, not a data-flow one. Read the `cube_bathymetry` ingest→dirty→publish path
(`sensors_ws/src/cube_bathymetry/cube_bathymetry`):

- **Ruled out — no "whole ping → one tile" assignment.** `GeoMapSheet::addSoundings`
  (`src/geo_map_sheet.cpp:77`) bounds all soundings in the batch, selects every grid
  overlapping that bounds, and marks each grid dirty individually when
  `GeoGrid::insert` returns true. Multiple tiles *can* be marked per ping.
- **Ruled out — no publish-side cap.** `publishDirtyTiles`
  (`src/cube_bathymetry_node.cpp:660`) iterates the whole publish-dirty set and emits
  one message per changed tile; it does not stop at one.
- **Confirmed correct — per-grid spreading.** `GeoGrid::insert` (`src/geo_grid.cpp:45`)
  clips each sounding's influence radius to its own grid via `index_`, so a selected
  neighbor grid correctly picks up its side of a boundary-spanning sounding.
- **Leading suspect — grid *selection* is under-margined.** `boundsForSoundings`
  (`src/geo_map_sheet.cpp:40-56`) pads the sounding bounding box by only **one cell**
  (`grid_level.cellAngularSpan()`), but each sounding spreads over an influence
  radius of *many* cells (`radius`/`max_radius`, `src/geo_grid.cpp:56-68`, up to
  `CONF_99PC·√(horizontal_error)`). A neighbor grid the soundings don't physically
  enter (±1 cell) is never selected, so its spillover cells are never written or
  marked dirty. Reproduces both symptoms: near a boundary only the home tile updates,
  and a tile reached *only* by spillover never updates.
- **Not yet confirmed.** Whether a genuine beam-straddle (soundings in two grids) can
  also drop a tile depends on `gggs::GridAreaIterator`/`gridIndex` in the external
  GGGS lib (not yet read).

**Discriminator (open next step):** the bags recorded `~/tiles` (GridMap) and
`~/coverage_tiles`; replay and list the actual grid indices emitted per ping to
separate selection-margin from iterator behavior. No issue opened yet (pending that
confirmation).

## Issues encountered — path following degraded, manual recovery

**2026-07-21 — boat strayed off course, did not recover across a full
stack restart** — Operator account: the boat behaved fine for most of the deployment,
then **toward the end started straying off course**. Operator restarted the full
stack; it **still failed to follow a path** after the restart. Operator had to
**drive back to the boat ramp manually**.

Bag-derived timing anchors (main bags `~/data/logs/bizzyboat/`, `/bizzy/piloting_mode/manual/helm` msg counts as the who's-driving tell; local -04:00):

- `2026-07-21T14-09-43+00-00` (10:09:43 → 13:26:29): 3,580 helm msgs, sparse over ~3.3 h — manual transit out + autonomous survey.
- `2026-07-21T17-26-41+00-00` (13:26:41 → 13:50:17): **234 helm msgs (near-zero)** — autonomous survey; this window contains the straying.
- `2026-07-21T17-50-39+00-00` (13:50:39 → 14:04:17): **14,106 helm msgs (~17 Hz, continuous)** — the manual drive back to the ramp.
- Stack restart pinned to the **autostart marker at 13:50:35** (`autostart_2026-07-21T13.50.35…txt`), sitting exactly between the autonomous session 2 and the all-manual session 3.

So the path-follow failure was **autonomous**, inside 13:26–13:50; the restart at 13:50:35 did not restore path-following; manual takeover ran 13:50:39 → 14:04:17. **Root cause not yet determined** — onset within 13:26–13:50 still to be pinned (cross-track error `/bizzy/plan` vs `/bizzy/odom`), and the failure mode to be read from `/bizzy/behavior_tree_log`, `/bizzy/collision_monitor_state`, `/bizzy/cmd_vel_nav` vs `/bizzy/mavros/setpoint_velocity/cmd_vel`, and `/bizzy/FollowPath/pid/pid_state`. No cause attributed yet.

**Additional operator observation — command latency:** while the boat was straying,
**sending commands to it got very laggy**. This spanned command sending generally (it
persisted into the manual drive-back, which was still recoverable but sluggish), so it
points at the **transport/compute layer** rather than controller logic: correct
commands arriving late/dropped rather than wrong commands computed. Consistent with the
rmw_zenoh drop mode already seen on the M3 `hz` probe earlier the same day, and also
with onboard overload (CPU/memory pressure or zenoh-router slowdown) degrading
everything at once. This makes **command-chain latency/rate over time** a first-class
thing to measure in the bag review — inter-message gaps and end-to-end lag along
`cmd_vel_nav → autonomous/cmd_vel → mavros/setpoint_velocity/cmd_vel`, plus any rate
collapse on `/bizzy/odom` and the mavros feedback topics — not just message presence.
`/rosout` warnings across 13:26–14:04 to be scanned for overload/zenoh signatures.

### Root-cause analysis (bag review, 2026-07-22)

Analyzed the main bags `2026-07-21T17-26-41+00-00` (session 2, autonomous, 13:26:41→13:50:17)
and `2026-07-21T17-50-39+00-00` (session 3, manual drive-back, 13:50:39→14:04:17). Not a
single clean fault — three layers, and the "restart didn't fix it" now has a concrete cause.

**Command flow (rate/gap analysis, receive-time):** the *upstream* autonomy pipeline stayed
healthy the whole of session 2 — `cmd_vel_nav` ~5 Hz, `autonomous/cmd_vel` and
`cmd_vel_smoothed` steady 10 Hz, `odom` + all mavros feedback steady 10 Hz, no meaningful
gaps. The break was on **`/bizzy/mavros/setpoint_velocity/cmd_vel`** (what actually reaches
the FCU): **15.7 s gap at 13:46:49** and **22.8 s gap at 13:47:45** while everything upstream
kept flowing. Setpoint twist at the gap edges: `vx=1.74 →[15.7 s]→ -0.70`, then
`vx=1.55 →[22.8 s]→ 0.00`.

**Chronic degradation (present the entire session, from 13:26:42):**
- `controller_server: Control loop missed its desired rate` — **119×**, 13:26:42→13:50:03. The
  FollowPath control loop was under-running throughout, not just at the end.
- `ca_safety: obstacle source lost — passing commands through` — **58×**, 13:26:42→13:50:16,
  driven by the OAK cameras repeatedly failing to connect (`oak_forward/aft/port/starboard:
  Failed to connect to device`) + TF `Lookup would require extrapolation into the future` on
  SeaSurfaceLayer / reflex pointcloud. CA **failed open** (passed commands through), so it did
  not itself stop the boat — but perception was degraded the whole run.
- `detections_to_pointcloud: No recent odometry; vessel_speed = NaN` — despite `/bizzy/odom`
  publishing at a steady 10 Hz, i.e. messages arriving **stale** to that node (a latency, not a
  data-absence, signature).

**Acute failure (13:42–13:47):**
- **13:42:29–13:45:36** — `bt_task_navigator: [run_tasks] Aborting handle` ×10,
  `controller_server: Failed to make progress`, `Failed to get result for follow_path in node
  halt` → the navigation task aborted repeatedly.
- **13:43:42** — FollowPath PID `|error|` jumped from ~3 to **171**, then stayed **130–250**
  through the end of the session (`FollowPath/pid/pid_state`).
- **13:46:49 & 13:47:45** — the setpoint-to-FCU dropouts above.
- **13:46:52 & 13:47:48** — `mavros.sys: FCU: target not received last N secs, stopping` →
  **ArduPilot GUIDED-mode failsafe stopped the vehicle**. This is the direct mechanism of the
  straying: with no velocity setpoint arriving, the FCU times out and stops, and the boat drifts
  off the line under wind/current.

**Persistent comms-link fault — why the 13:50:35 restart did not restore control:**
- `udp_bridge: Received next packet number that is less than previous one` — **17× in session 2**
  (13:27:30–13:36:44) and **102× continuously through session 3** (13:51:12→14:04:16, the entire
  manual drive-back). Out-of-order / regressing sequence numbers on the topside↔boat UDP link:
  this is the operator's "laggy commands," and it **spanned the restart** — it did not clear.
- Post-restart (session 3) the `controller_server` missed-rate spam is **gone** (compute
  recovered), but the `udp_bridge` regression persisted, so the return was flown on **manual
  helm** (`manual/helm` ~19 Hz, bursty; setpoint tracked helm) — laggy but workable.
- Session-3 startup transients (normal, ignore): `guided_target: PositionTargetGlobal failed
  because no origin` ×45 at 13:50:41–45 (EKF origin not yet set), OAK camera connect failures,
  `mavros VER service timeout` — all cleared within seconds of the restart.

**Motion signature — "straight line off-path, then a sudden turn, then straight again"
(operator observation, confirmed in the track):** this is a **controller-oscillation**
signature, NOT the setpoint dropouts. Setpoint delivery was actually at-rate for almost all
of 13:40–13:50 (only two >10 s gaps, at 13:46:49 and 13:47:45; 5,494 sub-0.3 s intervals
otherwise), so sparse delivery does not explain the repeated straight/turn pattern. The
commanded-vs-actual yaw rate does:
- During the bad legs the autonomy (`cmd_vel_nav`) was **oscillating its yaw-rate command hard**
  — swinging the full range (e.g. `±0.75` at 13:45:10–20, **`±3.0` rad/s** within a single 10 s
  window at 13:45:30 and 13:46:30) — while the **actual** boat yaw rate (`/bizzy/odom`) stayed
  small (≈±0.05) and lagged. The boat's slow yaw dynamics **average an oscillating command to
  near-zero net turn → straight-line travel**; a sustained command breaks through as the
  **sudden turn**. That reproduces the observed signature exactly.
- Downstream attenuation compounds it: the `±3` rad/s demands reached the FCU
  clamped/smoothed to ≈`±1` rad/s (setpoint yaw magnitudes are consistently smaller than
  `cmd_vel_nav`'s), so even sustained corrections were capped. (Note: this shows
  `/bizzy/cmd_vel_smoothed` was **active** at 10 Hz — contrary to an earlier assumption that the
  velocity smoother was disabled; trust the bag.)
- On the clean legs (e.g. 13:44:00–13:45:00) commanded yaw ≈ 0 and actual ≈ 0 — a genuine
  straight survey line — so the oscillation was intermittent, not constant.
- Likely driver: the chronic control-loop rate misses (119×) + stale pose feedback
  (`No recent odometry`) → irregular `dt` / stale state → the controller oscillates rather than
  tracks. *Caveat:* the PID `|error|` numbers above are per-60 s **max**, so they may overstate
  how sustained the tracking error was; the yaw command/response evidence is the solid part.

**Synthesis (evidence-based; candidate roots flagged, not concluded):**
- *Cause of the straight-off-path-then-sudden-turn motion:* an **unstable/oscillating autonomy
  yaw command** (controller instability) that the boat's dynamics smear into straight segments
  with occasional jerks, capped by a downstream ≈±1 rad/s yaw clamp — driven by the degraded
  control-loop rate and stale feedback. This is the bulk of the "straying."
- *Separate, later event:* autonomous velocity setpoints stopped reaching the FCU (two gaps,
  13:46:49 + 13:47:45) → ArduPilot failsafe stop → ~90 s of chaotic COG swings (13:46:50–13:48:20),
  on top of a FollowPath controller already failing to make progress and aborting the task
  (13:42–13:45).
- *Why a restart didn't recover it:* a persistent topside↔boat **UDP link degradation**
  (`udp_bridge` sequence regression) that survived the restart — a link/RF problem, not a
  software wedge. This also explains the "laggy commands."
- *Not provable from these bags* (no CPU/mem/thermal/RF-RSSI recorded): whether the chronic
  controller rate-misses and the setpoint stall share a common onboard resource/compute
  saturation, and whether the UDP-link degradation correlates with the boat ranging out.

**Candidate follow-ups (no issues opened yet — pending operator go-ahead):**
1. Topside↔boat UDP link health (`udp_bridge` sequence regression): check RF link margin / range
   / antenna; this is the thread that persisted across the restart and forced manual recovery.
2. `controller_server` chronic "missed desired rate" (119× over one session): is the FollowPath
   loop rate over-specified for the onboard compute, or was the CPU saturated? Needs system
   metrics that these bags don't carry. **Directly implicated in the oscillation** — an
   irregular/slow loop with stale feedback is the likely driver of the chattering yaw command.
2b. FollowPath **controller stability / tuning**: the autonomy commanded oscillating ±3 rad/s
   yaw during the straying, smeared to straight-line by boat dynamics. Review controller gains /
   goal+progress checkers / feedback freshness, and the downstream ≈±1 rad/s yaw clamp (which
   node applies it, and whether it's masking or worsening the instability).
3. Setpoint-to-FCU stall (15–23 s gaps on `setpoint_velocity/cmd_vel` while upstream flowed):
   identify the stalling node in the `cmd_vel → mavros setpoint` bridge (echo_helm / mavros
   setpoint plugin) and why it blocked.
4. OAK camera connect flakiness feeding CA/perception (failed open, so not causal here, but a
   reliability gap): USB/hardware reliability.
