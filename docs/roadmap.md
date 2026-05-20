# BizzyBoat / hydrography roadmap

What we're aiming for, and what's deferred. Scope is BizzyBoat plus the
sensor payload (M3 sonar, SBG, SVS) bound for the June 2026 field
hydrography class.

This document is the **carry-over mechanism between deployments**.
Items here are durable direction; specific bounded work belongs in
GitHub task issues (referenced from here when relevant).

## End goal

**Fully autonomous survey round-trips.** Plan a survey from the
operator station; boat transits to the area, runs survey lines, returns
to the pier — all without user intervention.

## Forcing function

**Summer Hydro 2026 — class + real lake survey.**
- **June 4**: Class starts. Roland teaches boat operation; students learn
  survey-component integration in parallel. Heavy development should be
  **done by this date** — switch to maintenance mode thereafter.
- **June 15 → ~June 29**: Two-week real survey at Lake Massabesic, NH.
  10 students rotate in 3 daily groups (3–4 students/day) plus engineer
  / intern helpers.

This is a real survey for a real customer, not a class exercise — the
system must work, not just demonstrate. Hydrographic-quality output is
the educational goal even though the operational bar is lower. The
system must support multi-operator handoff across daily cohorts.

## Active threads (have task issues)

Cross-references — the roadmap is not the source of truth for any
specific task; the linked issue is. Listed here so the threads are
visible from one place.

### Sensor payload integration (M3 + SBG + SVS on mercat)

- [`unh_echoboats_project11#76`](https://github.com/rolker/unh_echoboats_project11/issues/76) — mercat bring-up + data flow + NTRIP strategy + NTP. *Software pipeline live end-to-end as of 2026-04-27 (#94); first surveys recorded. M3 1PPS time-sync chain completed 2026-05-01 (#121) — after discovering that the M3 software's Device Properties → Time Sync Mode dropdown was the real gating switch, not the cable / SBG / pulse parameters that occupied most of the morning. QINSy SBG hookup live (position + attitude + heading + heave + GPS QC).*
- [`unh_echoboats_project11#77`](https://github.com/rolker/unh_echoboats_project11/issues/77) — physical install, offsets, URDF, SVG diagram
- [`rolker/marine_tools#1`](https://github.com/rolker/marine_tools/issues/1) — QINSy → ROS bridge for coverage / sounding feedback
- [`unh_echoboats_project11#137`](https://github.com/rolker/unh_echoboats_project11/issues/137) — *(2026-05-19)* M3 sonar: investigate intermittent missing pings (suspected ping-rate × depth correlation). Historical observation — 2026-05-19 was the first time the M3 software's log window was open during ops and the explicit error messages were visible. **Load-bearing for the June 2026 class** if missing pings scale up at the ping-rate × depth combos used for survey grids.

### Camera obstacle avoidance

- [`rolker/unh_marine_perception#6`](https://github.com/rolker/unh_marine_perception/issues/6) — `SeaSurfaceLayer::matchSize()` segfault (blocker)
- [`rolker/unh_marine_perception#7`](https://github.com/rolker/unh_marine_perception/issues/7) — end-to-end OAK→costmap validation (blocked on #6); per-camera `frame_ids` parameter + URDF-aligned `<label>_optical_frame` default across all `CameraBase` publisher paths landed via [PR #9](https://github.com/rolker/unh_marine_perception/pull/9) (merged 2026-04-28)

### Navigation reliability

- [`rolker/unh_marine_navigation#23`](https://github.com/rolker/unh_marine_navigation/issues/23) — TF extrapolation on multi-line survey goals
- [`rolker/unh_marine_navigation#24`](https://github.com/rolker/unh_marine_navigation/issues/24) — wire BT `target_speed` → nav2 `/speed_limit` (per-task survey speed); deployment 2026-04-27 worked around with shared `default_speed` bump
- [`unh_echoboats_project11#96`](https://github.com/rolker/unh_echoboats_project11/issues/96) — BizzyBoat-specific nav2 params override (decouple from seafloor echoboat defaults)

### Both nav systems report at base_link *(theme — 2026-04-29; major progress 2026-05-01)*

The 2026-04-29 in-water bag exposed that neither the SBG nor the FCU was reporting position at `base_link` — each published at its own GNSS antenna (0.64 m fore-aft body-frame offset between them). The URDF didn't model the SBG IMU/antennas, and the EKF3-fused mavros streams weren't being recorded, so cross-checks had to fall back to downstream `/bizzy/odom`. These three issues are a unit: pick a contract, model the geometry, and capture the streams that prove it's working.

- [`unh_echoboats_project11#110`](https://github.com/rolker/unh_echoboats_project11/issues/110) — model SBG INS, GNSS antenna(s), and IMU mounting alignment on bizzyboat (URDF gap). **Still open** — today's fixes addressed the *config* side; the URDF gap (no SBG body / Trimble antennas modeled) remains.
- [`unh_echoboats_project11#111`](https://github.com/rolker/unh_echoboats_project11/issues/111) — define lever-arm/base_link contract for SBG and mavros position streams. **Resolved live 2026-05-01** — the SBG sbgCenter Output Location was the missing config; with it set, both SBG and FCU now report at `base_link`. gabby agent confirmed agreement live; quantitative verification is post-mission ([#124](https://github.com/rolker/unh_echoboats_project11/issues/124)).
- [`unh_echoboats_project11#112`](https://github.com/rolker/unh_echoboats_project11/issues/112) — record `mavros/global_position/global` + EKF3-fused `local_position/*` + `altitude`. **Fixed in [#123](https://github.com/rolker/unh_echoboats_project11/pull/123)**, awaiting merge.
- [`unh_echoboats_project11#138`](https://github.com/rolker/unh_echoboats_project11/issues/138) — *(2026-05-19)* `mru_transform`: choose durable nav-input source after the ellipsoidal-vs-EKF discovery that aborted the nav stack mid-deployment. Field-side revert to `mavros/global_position/raw/fix` (commit `c36acfa`, cherry-picked onto PR #136 as `ece31dc`) is mission-enabling but a workaround; the proper design choice (mavros raw vs SBG vs mavros + geoid compensation) hooks into `#110` lever-arm work.

### Class-ready operator UI

- [`rolker/rqt_operator_tools#2`](https://github.com/rolker/rqt_operator_tools/issues/2) — operator logbook (Phase 1 landed, not field-tested)
- [`rolker/rqt_operator_tools#29`](https://github.com/rolker/rqt_operator_tools/issues/29) — pre-launch checklist (form factor TBD)
- [`rolker/rqt_operator_tools#31`](https://github.com/rolker/rqt_operator_tools/issues/31) — rqt_camera_grid: harden destructor↔callback sync + audit `currentText()` reads
- [`rolker/rqt_operator_tools#32`](https://github.com/rolker/rqt_operator_tools/issues/32) — rqt_camera_grid: `populate_topic_combo` Refresh re-leaks display label
- [`unh_echoboats_project11#18`](https://github.com/rolker/unh_echoboats_project11/issues/18) — student-facing operating documentation

### Class-day operator observability *(new theme — 2026-04-27; major expansion 2026-05-19)*

The 2026-04-27 deployment surfaced an asymmetry: boat-side instrumentation is rich, operator-side is sparse. The annunciator silently kept showing OK during an RTK loss because the udp_bridge wedge had stalled `/diagnostics`. Class operators need real-time visibility into the operator-side network + a way to know when the diagnostic stream itself is stale.

The 2026-05-19 deployment surfaced three more silent-failure shapes from one session: (a) Nav2 lifecycle bringup aborted with no operator alert until a goal was rejected, (b) operator-side `mikrotik_monitor` + `teltonika_monitor` crashed at startup with no alert (just showed STALE in the aggregator), (c) operator-side udp_bridge stats publication stalled for ≈1h17m while data plane stayed healthy. All three share the same gap: the operator finds out by accident or by failed user action, not by an alert. The brainstorm response settled on a defense-in-depth approach using existing ROS 2 primitives (`DiagnosticStatus`, `~/transition_event`, built-in `topic_statistics`) rather than a new lifecycle manager.

- [`unh_echoboats_project11#97`](https://github.com/rolker/unh_echoboats_project11/issues/97) — run network monitor nodes on salmon + record salmon-side `/diagnostics` during deployments
- [`rolker/ros2launch_session#5`](https://github.com/rolker/ros2launch_session/issues/5) — *(2026-05-19)* add observability mode: emit `DiagnosticStatus` for tracked processes and lifecycle nodes (`~/transition_event` subscription + process-death detection + `ros2launch_session run` CLI for per-host adoption). **Main vehicle** for closing the silent-failure gap; should ship before the June 2026 class.
- [`rolker/ros2_network_monitor#23`](https://github.com/rolker/ros2_network_monitor/issues/23) — *(2026-05-19)* `mikrotik_monitor` + `teltonika_monitor` crash silently on startup if initial connect fails — needs try/except + backoff. Symptom that would have shown up via `ros2launch_session#5` even before the underlying try/except fix.
- [`unh_echoboats_project11#141`](https://github.com/rolker/unh_echoboats_project11/issues/141) — *(2026-05-19)* `/Operator/*` diagnostics aggregator buckets STALE because publishers live under `/Other/*` (config drift). Aggregator-config cleanup.
- [`unh_echoboats_project11#142`](https://github.com/rolker/unh_echoboats_project11/issues/142) — *(2026-05-19)* host thermals as `DiagnosticStatus` (lm-sensors + NVMe SMART). Investigate-and-integrate (likely off-the-shelf package available).
- [`unh_echoboats_project11#139`](https://github.com/rolker/unh_echoboats_project11/issues/139) — *(2026-05-19)* replace `output='screen'` with `output='both'` in BizzyBoat launches — multiplies the value of any of the above by making crash output recoverable post-mission.
- [`unh_echoboats_project11#140`](https://github.com/rolker/unh_echoboats_project11/issues/140) — *(2026-05-19)* remove stale `bencloud` ping target (doesn't reflect WG link). Small but contributes to "toplevel ERROR is always lit" noise.
- *(future)* annunciator stale-stream indicator on `rqt_operator_tools` — distinguish "everything OK" from "stream wedged, last value stale"
- *(future)* topic-staleness layer using built-in ROS 2 `topic_statistics` + aggregator analyzers — sibling concern to `ros2launch_session#5`; addresses the udp_bridge stats-stall failure shape. Most natural home `unh_marine_autonomy`; deferred to its own session.

### Network reliability under load *(new theme — 2026-04-27)*

Multiple network-layer issues surfaced during the same long deployment day: udp_bridge wedges (4×), post-recovery multi-device cycle, op-router forwarding asymmetry, gabby DNS wedge. Themes converge on (a) fix specific bugs, (b) better instrumentation (overlaps with observability theme above).

- [`rolker/udp_bridge#10`](https://github.com/rolker/udp_bridge/issues/10) — bridge wedges (reader thread blocked, Recv-Q backup) when remote subscriber dies
- [`rolker/udp_bridge#9`](https://github.com/rolker/udp_bridge/issues/9) — resend loop amplifies traffic (earlier related)
- [`rolker/udp_bridge#16`](https://github.com/rolker/udp_bridge/pull/16) — *(2026-05-01)* forwarding-throughput regression from PR #12 + `rmw_zenoh_cpp` 0.2.9 BEST_AVAILABLE keyexpr workaround
- [`rolker/camp#51`](https://github.com/rolker/camp/pull/51) — *(2026-05-01)* operator-side QoS fix complementing the bridge default change
- [`rolker/udp_bridge#20`](https://github.com/rolker/udp_bridge/issues/20) — *(2026-05-19)* operator-side stats-timer publication stalls during Starlink-only ops while data-republish keeps working (≈1h17m blind on operator panels). Specific to stats path — video, costmap, heartbeat unaffected.
- [`rolker/udp_bridge#21`](https://github.com/rolker/udp_bridge/issues/21) — *(2026-05-19)* resend-give-up "after N attempts" value varies 5/6/1 across the session — meaningful or counter glitch?
- *(future)* End-of-day network pathology root-cause work — open once we have more signal from a future deployment with op-side diagnostics in place

### Over-horizon operations capability *(new theme — 2026-05-01; update 2026-05-19)*

The 2026-05-01 deployment ran the boat past visual range with the new comms stack and surfaced the saturation envelope. Even on Starlink-only at moderate distance, the current ROS topic stack saturates the link, producing 30–60 s latency episodes. Asymmetric resilience worked: control commands and SSH stayed reliable through saturation; situational awareness did not. RC failsafe stack now configured for over-horizon use (`FS_THR_ENABLE = 0`, `FS_GCS_ENABLE = 0`, GUIDED stale-setpoint HOLD).

**2026-05-19 update**: Phase 1 (operator-side WiFi disabled, Starlink-only at close range) and a partial Phase 2 (Starlink-only autonomous trackline + initial survey pattern, cut short on time, in-harbor) both completed without losing control — the post-2026-05-01 fixes ([#134](https://github.com/rolker/unh_echoboats_project11/pull/134) coprime keyframe stagger, [`rolker/udp_bridge#16`](https://github.com/rolker/udp_bridge/pull/16) throughput regression fix, [`rolker/camp#51`](https://github.com/rolker/camp/pull/51) NavSource QoS workaround) held under load. The data-path half of Phase 2's intent is validated. **The literal OOL element + a completed survey are still pending** — tracked in [`#130`](https://github.com/rolker/unh_echoboats_project11/issues/130) (Field validation: over-horizon Starlink-only operation), which stays open. New observability findings from 2026-05-19 ([`rolker/udp_bridge#20`](https://github.com/rolker/udp_bridge/issues/20) stats-timer stall masked operator-side bridge health throughout, [`rolker/udp_bridge#21`](https://github.com/rolker/udp_bridge/issues/21) resend-N interpretation question) are the kind of thing a future OOL attempt needs better instrumentation for — see the observability theme below.

- **Topic-budget cull** — required, not optional. Identify which topics dominate the link, cull or rate-limit accordingly.
- **VPN-path indicator** (Starlink vs. cellular vs. WiFi) — operator awareness gap; today we lost significant diagnostic time guessing which path was carrying traffic. See [#124](https://github.com/rolker/unh_echoboats_project11/issues/124).
- **Bench stress-test rig** — synth topics + mininet + CAMP-stub harness so the next saturation question can be answered at the desk, not on the water. See [#124](https://github.com/rolker/unh_echoboats_project11/issues/124).
- **RC mode-switch fringe-range hardening** — pin to AUTO/GUIDED, disable channel via FCU params, or power off RC entirely during autonomous runs. See memory `project_bizzyboat_rc_mode_switch_at_fringe_range.md`.
- **Low-bandwidth status fallback** — text/heartbeat/minimal-telemetry path that survives when the full topic stream doesn't (today's gabby SSH access bridged the gap manually).

### Autonomy robustness *(new theme — 2026-05-01)*

2026-05-01 deployment surfaced a real BT design issue and validated the GUIDED stale-setpoint failsafe.

- **BT `SkipUnknownTaskType` catchall masks execution failures** — top-level `ReactiveFallback` can't distinguish "no script condition matched" from "matching subtree's execution failed", so the catchall fires on action ABORTs and silently marks tracklines done. Forensic match for the 2026-05-01 15:09 HOLD episode (FollowPath ABORTED → SurveyLineTask sequence failed → catchall fired → trackline marked done → `done_hover` activated). Needs a new task issue against the BT / mission_manager. See gabby log §11.
- **GUIDED stale-setpoint HOLD verified working** — when `cmd_vel` publication stops, FCU correctly enters HOLD. Confirmed Nav2-crash failsafe behaves as intended.

### Perception → costmap *(new theme — 2026-05-01)*

The 2026-05-01 mooring ball near-miss made this concrete: cameras can see surface obstacles, but segmentation output is not feeding the Nav2 costmap, so the autonomy planner has no awareness. This is a real survey-readiness blocker — any autonomous survey will be in waters with mooring balls, debris, and other vessels.

Existing tracker: [`rolker/unh_marine_perception#7`](https://github.com/rolker/unh_marine_perception/issues/7) (end-to-end OAK → costmap validation). Currently blocked on [`unh_marine_perception#6`](https://github.com/rolker/unh_marine_perception/issues/6) (`SeaSurfaceLayer::matchSize()` segfault). Today reinforces the priority — without this, autonomous survey requires constant manual override for surface-obstacle avoidance.

**Companion concern**: [`rolker/unh_marine_autonomy#127`](https://github.com/rolker/unh_marine_autonomy/issues/127) — *(2026-05-19)* operator-side local costmap display: characterize transmission cost + design path to CAMP. 2026-05-19 measured ~78% loss on `/bizzy/local_costmap/costmap` over WiFi (small fragmented topics fine, large multi-fragment topic punishing). Becomes operationally critical the moment perception→costmap fusion lands — operator needs to see the obstacles the boat is reasoning about, especially for OOL ops where direct visual is impossible.

## Deferred / lower priority — no current issue

These items are explicitly not on deck. Promote to a task issue when
they become relevant.

### Navigation polish

- **Hover v5** (range-aware taper for faster excursion recovery) —
  v4 is sufficient for current use; revisit only if v4's behavior
  becomes a real ergonomics problem
- **Hover vectored-thrust parameter** — works well enough with v4 cliff

### Networking

- **DNS-over-HTTPS on RUTX11** — exploration item, not urgent
- **WiFi bridge: static routes → default gateway approach** — current
  static-route setup works; cleaner default-gateway redesign deferred
- **IzzyBoat WireGuard return path fix** — IzzyBoat is parked, fix
  this before next IzzyBoat deployment

### Testing

- **Formal WiFi range test** — 2026-04-21 field data shows graceful
  degradation well past the old "300 m limit" and range comparable to
  or better than 2025 IzzyBoat (see memory `project_wifi_range.md`).
  A dedicated controlled range test is out of class-prep scope.

### Hardware oddities

- **Forward USB camera** publishes a black image — root cause unknown,
  USB camera has not been needed for any field work. Revisit if it
  becomes load-bearing.
- **Duplicate `/bizzy/sensors/sbg_device` graph entry** *(observed 2026-05-19, gabby log §2)* — one real PID, second name registration is a graph-level ghost from a prior lifecycle (likely RMW/Zenoh discovery-state quirk after kill-and-restart cycles). Data flow is fine; service-call routing to `sbg_device` could be ambiguous in theory. Not deploy-blocking; no clean fix path right now. Watch for recurrence; promote to an issue if it ever causes a real failure.

## What's not on this roadmap

- Specific bug fixes — those are task issues
- Specific deployments — those get their own deployment issues
- Anything that's on deck for the **next** deployment — that goes in
  the next deployment issue's body, not here

## How this roadmap stays useful

- At deployment start: planner reads this + open task issues → picks
  the next deployment's scope
- At deployment wrap-up: items that came up but aren't bounded enough
  for a task issue and aren't going to be done next time → land here
- Periodically: if "deferred" items have been sitting more than a
  couple of months without any pull toward them, they're probably
  dropped, not deferred. Edit them out.

This document was seeded from the milestone content of
[`unh_echoboats_project11#57`](https://github.com/rolker/unh_echoboats_project11/issues/57)
(BizzyBoat field ops umbrella) when that issue was closed in favor of
the per-deployment convention. See
[`unh_echoboats_project11#92`](https://github.com/rolker/unh_echoboats_project11/issues/92)
for the close-out rationale.
