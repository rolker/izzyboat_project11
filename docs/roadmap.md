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

**Verify before June 4:**
- AML SVS bridge — believed complete (gabby-side); confirm data is
  actually being captured in deployment bag files. Some past
  deployments used the mercat-side PowerShell stand-in
  (`aml_bridge.ps1`); class cohort handoff shouldn't depend on that.
- Mercat NTP — believed configured. Promote verification (`ntpq.exe -pn`)
  to in-class teaching content for students.

**Open decision (decide before June 4):**
- Sidescan imagery option — install Garmin sidescan (colleague has
  headless protocol implementation) vs run M3 in imagery mode. Tradeoff
  is install effort vs imagery quality. *(Needs an issue.)*

**Student-led / deferred:**
- [`unh_echoboats_project11#137`](https://github.com/rolker/unh_echoboats_project11/issues/137) — M3 sonar intermittent missing pings. Basics work; tuning is in-class student work, not a class-blocker.
- [`rolker/marine_tools#1`](https://github.com/rolker/marine_tools/issues/1) — QINSy → ROS bridge. Nice-to-have, not class-critical. Students can use QINSy's native display for survey planning.

**Track:**
- [`unh_echoboats_project11#77`](https://github.com/rolker/unh_echoboats_project11/issues/77) — physical install / offsets / URDF / SVG diagram. Cross-references the URDF gap in [`#110`](https://github.com/rolker/unh_echoboats_project11/issues/110) (both-nav-at-base_link theme).

**Done:**
- [`unh_echoboats_project11#76`](https://github.com/rolker/unh_echoboats_project11/issues/76) — mercat bring-up. Software pipeline live 2026-04-27 (#94); M3 1PPS time-sync chain completed 2026-05-01 (#121); QINSy SBG hookup live.
- NTRIP — MassDOT source tested at Lake Massabesic; works with current configuration.

### Surface-obstacle awareness — camera + costmap

The 2026-05-01 mooring-ball near-miss made this concrete: cameras see
surface obstacles, but segmentation output is not feeding the Nav2
costmap, so the autonomy planner has no awareness. With student
operators driving the boat at Lake Massabesic — where the obstacle set
is recreational boats and kayaks (no swimmers; the lake is a
drinking-water reservoir) and drifting debris — the operational gap
matters.

**Two-tier delivery — display first, planning second.** The display
path has a lower bar because it doesn't have to be perfect to be useful
— an operator looking at a noisy costmap still gets situational
awareness value. The planning path is much higher bar: the autonomous
planner needs the costmap to be trustworthy before it'll improve
autonomy quality.

**Priority for June 4** (display path):
- [`rolker/unh_marine_perception#6`](https://github.com/rolker/unh_marine_perception/issues/6) — `SeaSurfaceLayer::matchSize()` segfault. **Status (2026-05-21)**: [`PR #11`](https://github.com/rolker/unh_marine_perception/pull/11) shipped and fixes single-instance, but **multi-instance still segfaults** — discovered live during 2026-05-21 bring-up when [`seafloor_echoboat_project11#19`](https://github.com/rolker/seafloor_echoboat_project11/pull/19)'s 4-camera config triggered the crash on `controller_server` activation. Active field workaround: forward-only via [`seafloor_echoboat_project11#21`](https://github.com/rolker/seafloor_echoboat_project11/pull/21). Multi-instance root-cause pending — may need #6 reopened or a new issue against `unh_marine_perception`.
- [`rolker/unh_marine_perception#7`](https://github.com/rolker/unh_marine_perception/issues/7) — end-to-end OAK → costmap validation. Blocked on #6. End state for display-first: "a costmap is being published, populated by segmentation, and the operator can see it."
- [`rolker/unh_marine_autonomy#127`](https://github.com/rolker/unh_marine_autonomy/issues/127) — operator-side local costmap display. Becomes critical-to-have once #6 / #7 ship. 2026-05-19 measured ~78% loss on the wifi path for the costmap topic; bandwidth budget needs to fit.
- Per-camera `frame_ids` + URDF-aligned `<label>_optical_frame` default via [PR #9](https://github.com/rolker/unh_marine_perception/pull/9) (2026-04-28). *(Done.)*

**Defer past June 4** (planning path):
- Using the costmap for autonomous planning. Requires costmap quality
  to be much higher than the display-only bar. Maintenance-mode work.

**Fallback plan if the display path doesn't ship in time:**
- Vigilant camera-watching — current SOP. Multi-operator station means
  multiple eyes (you + 3–4 students + engineer helpers).
- Pre-plan exclusion zones around docks, traffic lanes, shoreline.
- Manual override / RC takeover drilled with student operators before
  going autonomous.
- (See also Navigation reliability — [`unh_marine_navigation#24`](https://github.com/rolker/unh_marine_navigation/issues/24)
  lets the operator drop survey speed on demand for any reason,
  including obstacle reaction time.)

### Navigation reliability

**Must finish before June 4:**
- [`rolker/unh_marine_navigation#24`](https://github.com/rolker/unh_marine_navigation/issues/24) — wire BT `target_speed` → `/speed_limit`. High priority operational item — per-task speed from a CAMP-sent mission is needed for normal operations (different survey speeds for different segments / line types), not just as a safety fallback. Current `default_speed` bump workaround from deployment 2026-04-27 doesn't support per-task variation.
- [`rolker/unh_marine_navigation#23`](https://github.com/rolker/unh_marine_navigation/issues/23) — TF extrapolation on multi-line survey goals. No fix landed; 2026-05-19 deployment logs likely still show TF-lookup-out-of-time errors. Survey patterns at the lake will repeatedly trigger this. Verify still occurring, then fix.

**Investigate before June 4:**
- [`rolker/unh_marine_navigation#19`](https://github.com/rolker/unh_marine_navigation/issues/19) — costmap-update timeout too aggressive at 1.0s. Open and currently unscheduled. Likely matters once the costmap is populated (Surface-obstacle awareness theme). Check if it's a real bottleneck under realistic load before deciding to fix vs defer.
- **Boat-side bathy costmap** *(placeholder — needs issue or existing
  agent-branch link)*. Lake Massabesic has no S57 ENC coverage, so the
  Nav2 costmap won't have any depth-derived "don't go here" data unless
  external bathymetry is ingested. Likely consumes NHGranIT contours via
  [`unh_marine_autonomy#86`](https://github.com/rolker/unh_marine_autonomy/issues/86)'s GGGS data store as a Processed source. Roland recalls
  possible work on this from another computer — confirm location, then
  either link existing issue/branch or open new. Borrowable code in
  `s57_tools`/`marine_charts` for the depth-data → costmap layer
  plumbing.

**Defer past June 4:**
- [`unh_echoboats_project11#96`](https://github.com/rolker/unh_echoboats_project11/issues/96) — BizzyBoat-specific nav2 params override (decouple from seafloor echoboat defaults). Not critical for single-boat ops; promote when joint Bizzy + Izzy ops come into scope.

### Both nav systems report at base_link *(theme — 2026-04-29; major progress 2026-05-01; FCU side outstanding)*

The 2026-04-29 in-water bag exposed that neither the SBG nor the FCU
was reporting position at `base_link` — each published at its own GNSS
antenna (0.64 m fore-aft body-frame offset). 2026-05-01 closed the SBG
side via sbgCenter Output Location. The mavros side and the durable
EKF Z reference both remain — and both can land via a single FCU
reconfiguration.

**Why getting this right matters operationally**: tide / water-level
estimation depends on it. The 2026-05-19 nav-stack abort was driven
exactly by this chain — mavros `/global` Z was wrong (baro tracking
weather pressure, not GPS altitude), so `sea_surface_estimator`
produced implausible water-level estimates, so `map → map_tide` was
never broadcast, so `local_costmap` couldn't activate, so
`bt_task_navigator` rejected goals. A correct base_link reference and
correct Z source are not just lever-arm hygiene — they're a prerequisite
for the tide / water-level / chart-datum chain to function. (For Lake
Massabesic that chain becomes a "lake-level / chart-datum" chain;
mathematically the same, no tidal variation but reference geometry
still load-bearing for sonar processing.)

**Must finish before June 4:**
- [`unh_echoboats_project11#138`](https://github.com/rolker/unh_echoboats_project11/issues/138) — `mru_transform` durable nav-input choice + FCU reconfig. **Substantive FCU change is only `EK3_SRC1_POSZ = 3`** (GPS), so the FCU EKF Z stops tracking atmospheric pressure. (Earlier brief drafts also called for an `EK3_GPS_OFFS_*` family — those params don't exist on ArduPilot Rover; the GPS antenna lever-arm goes through `GPS_POS1_*` only, which was already at the right values from #91.) Field-side revert to `mavros/global_position/raw/fix` is a workaround; FCU reconfig is the durable answer. **Status (2026-05-21)**: bench-side validation passed — `/global` altitude back in chart-datum band, `tide_estimate` plausible, suppression warnings gone — and `mru_transform` switched back from `raw/fix` → `/global` in field commit `f348f66`. In-water trackline validation didn't run (nav stack unhealthy — see [`#150`](https://github.com/rolker/unh_echoboats_project11/issues/150) topic 6); offline bag analysis pending in [`#150 topic 1`](https://github.com/rolker/unh_echoboats_project11/issues/150). **Caveat pending bag review**: gabby agent's in-water cross-check found a likely lever-arm double-count in the downstream `mru_transform`/`sea_surface_estimator` chain (1.78 m systematic bias = 2 × \|GPS_POS1_Z\|; sign-flipped result is within 24 cm of NOAA forecast). Not deploy-blocking — plausibility band still passes — but downgrades #138's closure from "delivered" to "FCU side delivered, downstream lever-arm regression pending bag review".

**Wrap-up / housekeeping:**
- [`unh_echoboats_project11#111`](https://github.com/rolker/unh_echoboats_project11/issues/111) — lever-arm / base_link contract. SBG half resolved live 2026-05-01; FCU half folds into #138's reconfig. Plan: fold the remaining FCU-side scope into #138's body, then close #111 with a pointer.

**Defer past June 4:**
- [`unh_echoboats_project11#110`](https://github.com/rolker/unh_echoboats_project11/issues/110) — URDF gap (SBG INS + GNSS antennas + IMU mounting). Becomes load-bearing when the camera-image → costmap pipeline ships (need accurate geometric placement for segmentation projection), but it's not on the critical path for the tide / chart-datum chain — which uses the position+altitude topics directly. Until then, documentation-correctness work that can live in maintenance mode.

**Done:**
- [`unh_echoboats_project11#112`](https://github.com/rolker/unh_echoboats_project11/issues/112) — record EKF3 streams. **CLOSED** ([PR #123](https://github.com/rolker/unh_echoboats_project11/pull/123) merged 2026-05-18).

### Class-ready operator UI

The interactive surface (logbook, checklist, camera grid) is in
good-enough shape — Phase-1 plugins exist or the current config works,
and students can fall back to text editor / paper for the recording
parts. Documentation for student operators is the only must-finish.

**Must finish before June 4:**
- [`unh_echoboats_project11#18`](https://github.com/rolker/unh_echoboats_project11/issues/18) — student-facing deployment guide. Students operate without an expert next to them. Draft from the BizzyBoat deployment logs.

**Nice-to-have / acceptable workaround:**
- [`rolker/rqt_operator_tools#2`](https://github.com/rolker/rqt_operator_tools/issues/2) — operator logbook Phase 1. Field-untested but acceptable. Students can use a text editor for shift logs if the plugin isn't yet trusted.
- [`rolker/rqt_operator_tools#29`](https://github.com/rolker/rqt_operator_tools/issues/29) — pre-launch checklist. Paper or text-file checklist is acceptable for the class. Promote to active dev if capacity opens up; otherwise capture the checklist content in #18.
- [`rolker/rqt_operator_tools#31`](https://github.com/rolker/rqt_operator_tools/issues/31) / [`#32`](https://github.com/rolker/rqt_operator_tools/issues/32) — rqt_camera_grid hardening. Current grid configuration is working and not being reconfigured; the bugs only manifest under reconfiguration. Don't touch unless reconfiguration becomes necessary.

**Operator-side background map** *(from background-data theme split)*:
- Students will find a suitable background map (NHGranIT contours,
  aerial imagery, etc.) before June 15 as part of their integration
  work. No developer-side starter needed.
- *(See companion: [`unh_marine_autonomy#127`](https://github.com/rolker/unh_marine_autonomy/issues/127) operator-side local costmap display — only matters once camera→costmap fusion ships.)*

**Design thread — defer past June 4** *(surfaced 2026-05-21 from
deployment debrief)*:

Platform-aware speed override + on-the-fly trackline editing. From the
2026-05-21 collision incident: when the boat is following a trackline
and an obstacle appears, the operator's current options are *(a)* slow
the boat manually via RC / USB controller, *(b)* full manual override
+ steer around + re-engage autonomy (the path that caused today's
collision — cross-track-error correction pulled the boat through the
obstacle when the manual override was disengaged with the boat beside,
not past, the obstacle). Two CAMP-side enhancements could give the
operator gentler intermediate options:

- **Platform-aware speed override**: have the platform message that
  tells CAMP about the boat also carry `default_speed` and `max_speed`,
  and surface a slider (or similar) for instant override of the
  current commanded speed. Multi-piece scope: (a) message-schema
  addition, (b) CAMP UI control, (c) FCU / autonomy plumbing for the
  override path.
- **On-the-fly trackline editing**: let the operator drag a trackline
  waypoint past an obstacle instead of taking the helm. Removes the
  "reposition fully past the obstacle before re-engaging" procedural
  trap entirely. May become moot once a planner can do obstacle-aware
  trackline modification itself, but that's a much further-out
  capability; this is a near-term UI addition that works alongside the
  current by-design collision-avoidance-free trackline model.

Not promoted to issues yet — both pieces want scoping conversations
about where the message-schema change lands and what CAMP's plugin
surface for these controls looks like.

### Class-day operator observability *(new theme — 2026-04-27; major expansion 2026-05-19)*

Student operators won't intuit silent failures the way an expert does.
The 2026-05-19 deployment surfaced three silent-failure shapes —
Nav2 lifecycle bringup aborted without alert, network monitors crashed
silently at startup, bridge stats publication stalled for 1h17m —
sharing the same gap: operator finds out by accident, not by alert.

**Architecture decision**: the diagnostic aggregator is not in the
operator UI path — the annunciator subscribes to `/diagnostics`
directly. Aggregator output has no user-facing consumer; the rqt
aggregator view plugin caused problems and isn't used. Direction is
"publishers → /diagnostics → annunciator," no aggregator middleman.

**Must finish before June 4 — small easy wins, do these first:**
- [`unh_echoboats_project11#141`](https://github.com/rolker/unh_echoboats_project11/issues/141) reframed — **remove** the `diagnostic_aggregator` from operator launches. Strip the Node from `operator_core_launch.py` + delete the unused aggregator config in `diagnostics.yaml`. Eliminates the "STALE bucket / config drift" misdirection 2026-05-19 surfaced.
- [`unh_echoboats_project11#139`](https://github.com/rolker/unh_echoboats_project11/issues/139) — `output='screen'` → `output='both'` in BizzyBoat launches. One-line change. Crash output recoverable post-mission.
- [`unh_echoboats_project11#140`](https://github.com/rolker/unh_echoboats_project11/issues/140) — remove stale `bencloud` ping target. Trivial. Reduces the chronic alert-fatigue noise.
- [`rolker/ros2_network_monitor#23`](https://github.com/rolker/ros2_network_monitor/issues/23) — try/except + backoff for `mikrotik_monitor` / `teltonika_monitor`. Small fix; prevents the silent-startup-crash failure shape directly (without needing ros2launch_session#5 to catch it as a generalization).
- [`unh_echoboats_project11#97`](https://github.com/rolker/unh_echoboats_project11/issues/97) — run network monitor nodes on salmon + record salmon-side `/diagnostics` during deployments. Already in the deployment process intent; confirm it's actually wired up and recording.

**Desirable, defer if needed:**
- [`rolker/ros2launch_session#5`](https://github.com/rolker/ros2launch_session/issues/5) — observability mode. Substantial implementation. Catches the lifecycle-abort + silent-process-death failure shapes as a general mechanism. Would close the biggest remaining observability hole, but the rest of the easy wins above already deliver most operator-visible value. Treat as stretch goal — if it ships before June 4 great, otherwise the workaround is documented manual checks at launch time + students drilled to recognize "I queued a goal and nothing happened" as a system problem requiring expert help.
- [`unh_echoboats_project11#142`](https://github.com/rolker/unh_echoboats_project11/issues/142) — host thermals as `DiagnosticStatus` (lm-sensors + NVMe SMART). Off-the-shelf package available; do if quick, defer if not.

**Future:**
- annunciator stale-stream indicator on `rqt_operator_tools`.
- topic-staleness layer via `topic_statistics` + aggregator analyzers (the analyzer module — doesn't require running the aggregator node).

### Network reliability under load *(new theme — 2026-04-27)*

2026-05-19 cross-deployment analysis ([`#144`](https://github.com/rolker/unh_echoboats_project11/issues/144) + [`udp_bridge#22`](https://github.com/rolker/udp_bridge/issues/22) comment thread) showed the bridge is in good operational shape: resend storms on wifi loss are by-design behavior, milder than 2026-05-01's worst, and stay within configured rate limits. The remaining items here are real but not class-critical — defer to maintenance mode unless one of them recurs during class prep.

**Track during class prep:**
- [`rolker/udp_bridge#10`](https://github.com/rolker/udp_bridge/issues/10) — bridge wedges when remote subscriber dies. Real bug; not observed during 2026-05-01 or 2026-05-19. If it surfaces during student-led ops it could be operationally bad, but track rather than promote unless it recurs.

**Maintenance mode after June 4:**
- [`rolker/udp_bridge#23`](https://github.com/rolker/udp_bridge/issues/23) — restrict resend response to requesting connection. Wire-format change (`connection_id` field). Modest impl, reduces resend amplification under loss. Filed 2026-05-20; `[PLAN]` PR [`#25`](https://github.com/rolker/udp_bridge/pull/25) merged 2026-05-21 (plan document only — implementation still pending).
- [`rolker/udp_bridge#20`](https://github.com/rolker/udp_bridge/issues/20) — stats-timer publication stalls. Made operator panels blind for 1h17m during 2026-05-19 (data plane unaffected). Stats are observability — not data path. Less urgent than the observability theme's main vehicle.
- [`rolker/udp_bridge#21`](https://github.com/rolker/udp_bridge/issues/21) — "after N attempts" value varies 5/6/1. Counter interpretation question. Investigate when convenient.

**Future (post-June-4):**
- [`unh_echoboats_project11#145`](https://github.com/rolker/unh_echoboats_project11/issues/145) — concurrent Starlink + cell with safety-critical traffic pinned to cell. Today's RUTX11-failover model causes a brief outage at every Starlink↔cell switch, blinding the operator before they can react. udp_bridge already supports per-topic-per-connection assignment, so this is primarily a network setup question — router config, possibly a second VPN endpoint for the cell-side path. Pin heartbeat / position / command to a cell-backed connection; let video / costmap / etc. stay on Starlink.

**Done:**
- [`rolker/udp_bridge#9`](https://github.com/rolker/udp_bridge/issues/9) — resend loop amplification. **CLOSED** via the #13 resend-logic work (exponential backoff + TTL alignment + debounce).
- [`rolker/udp_bridge#16`](https://github.com/rolker/udp_bridge/pull/16) — forwarding-throughput regression. **MERGED** 2026-05-01.
- [`rolker/camp#51`](https://github.com/rolker/camp/pull/51) — operator-side QoS fix complementing the bridge default change. **MERGED** 2026-05-18.
- [`rolker/udp_bridge#22`](https://github.com/rolker/udp_bridge/issues/22) — "Giving up on resend" WARN log too loud. **CLOSED** via [`udp_bridge#24`](https://github.com/rolker/udp_bridge/pull/24) (merged 2026-05-21). End-to-end evidence from 2026-05-21: operator bag 99 MB vs 296 MB on 2026-05-19 over similar duration; give-up rate held 1.8/s background through the mission.

### Over-horizon operations capability *(new theme — 2026-05-01; updates 2026-05-19, 2026-05-20)*

The 2026-05-01 deployment ran the boat past direct-comms range with the
new comms stack and surfaced the saturation envelope. Even on
Starlink-only at moderate distance, the current ROS topic stack
saturates the link, producing 30–60 s latency episodes. Asymmetric
resilience worked: control commands and SSH stayed reliable through
saturation; situational awareness did not. RC failsafe stack now
configured for OTH ops (`FS_THR_ENABLE = 0`, `FS_GCS_ENABLE = 0`,
GUIDED stale-setpoint HOLD).

**2026-05-19 update**: Phase 1 (operator-side WiFi disabled,
Starlink-only at close range) and a partial Phase 2 (Starlink-only
autonomous trackline + initial survey pattern, cut short on time,
in-harbor) both completed without losing control — the post-2026-05-01
fixes ([`#134`](https://github.com/rolker/unh_echoboats_project11/pull/134)
coprime keyframe stagger,
[`udp_bridge#16`](https://github.com/rolker/udp_bridge/pull/16)
throughput regression fix,
[`camp#51`](https://github.com/rolker/camp/pull/51) NavSource QoS
workaround) held under load. The data-path half of Phase 2's intent is
validated. The literal OTH element + a completed survey are still
pending.

**Class scope reassessment (2026-05-20)**: Lake Massabesic surveys go
OTH routinely from a shore-based operator station — the lake is large
enough that the boat is regularly outside direct comms range. The
OTH-specific work below is therefore **class-priority**, not deferred.

**2026-05-21 update**: Attempted an OTH trackline during the 2026-05-21
deployment. Transit out worked; ended early on collision (camera mast
knocked loose against a floating platform — the trackline followed
its surveyor-defined path through it because tracklines are
by-design collision-avoidance-free, and the operator's mid-trackline
manual override was disengaged with the boat positioned *beside*, not
*past*, the obstacle, so the path follower correctly closed the
cross-track-error back into the obstacle). Operationally the partial
OTH validated: transit-out, RC-at-range, and Ruby-RHIB-plus-RC
recovery all worked. Bandwidth / saturation analysis pending in
[`#150 topic 3`](https://github.com/rolker/unh_echoboats_project11/issues/150).
[`#130`](https://github.com/rolker/unh_echoboats_project11/issues/130)
remains open — the OTH-with-completed-survey criterion isn't met yet.

**Must finish before June 4:**
- [`unh_echoboats_project11#130`](https://github.com/rolker/unh_echoboats_project11/issues/130) — field validation of OTH Starlink-only operation including a completed survey. The lake survey IS the test — but going in without a controlled validation first is the kind of risk we don't take with students aboard. Schedule a deliberate OTH validation between now and June 15.
- **Topic-budget cull** — operating OTH at lake scale is exactly the saturation scenario from 2026-05-01. Identify which topics dominate the link, cull or rate-limit accordingly. Don't wait for a future OTH attempt to re-hit the 30–60 s latency episodes.
- **Low-bandwidth status fallback** — text/heartbeat/minimal-telemetry path that survives when the full topic stream doesn't. May overlap with [`#145`](https://github.com/rolker/unh_echoboats_project11/issues/145)'s safety-critical-pinned-to-cell concept. 2026-05-01 worked around this with manual gabby SSH; the class scenario needs the fallback in the operator UI.
- **VPN-path indicator** (Starlink vs. cellular vs. WiFi) — operator awareness gap; on 2026-05-01 we lost significant diagnostic time guessing which path was carrying traffic. See [`#124`](https://github.com/rolker/unh_echoboats_project11/issues/124).
- **"OTH mode" — annunciator with range awareness** — operator-toggled (or auto-by-path-detection) mode that quiets the WiFi WARN cascade when the boat is intentionally past WiFi range. Implementation of the existing `feedback_wifi_disconnect_not_an_error` principle ("drops are data, not ERROR; let downstream consumers apply context-aware logic"). Surfaced during 2026-05-21 OTH run where WiFi WARN noise crowded out useful annunciator visibility. Not yet promoted to a focused issue — wants a brief design conversation: where does the mode-state live (CAMP toggle vs. auto-detect from Starlink-active vs. RC-out-of-range), and which diagnostics participate in the quiet-list. Small implementation once scoped.

**Defer past June 4:**
- **Bench stress-test rig** — synth topics + mininet + CAMP-stub harness so the next saturation question can be answered at the desk. The lake survey itself will produce real-water OTH data; pre-survey budget is better spent on the topic cull and the fallback channel. Revisit post-survey. See [`#124`](https://github.com/rolker/unh_echoboats_project11/issues/124).
- **RC mode-switch fringe-range hardening** — RC handheld stays at the operator station; controller doesn't follow the boat to OTH range. Captured in memory `project_bizzyboat_rc_mode_switch_at_fringe_range.md` for future relevance.

### Autonomy robustness *(new theme — 2026-05-01)*

The 2026-05-01 deployment surfaced a real BT design issue (now filed)
and validated the GUIDED stale-setpoint failsafe.

**Must finish before June 4:**
- [`unh_marine_navigation#25`](https://github.com/rolker/unh_marine_navigation/issues/25) — `SkipUnknownTaskType` catchall in `run_tasks.xml` silently marks tracklines done when a matching subtree's execution fails (e.g. `FollowPath` ABORT). Forensic match for the 2026-05-01 15:09 HOLD episode. Class-significant: a silently-marked-done line at OTH range means the operator sees a "complete" trackline and the boat parked in `done_hover` with no alert — coverage holes show up only post-mission.

**Track during class prep:**
- **Broader BT review of `marine_nav_bt_task_navigator/behavior_trees/run_tasks.xml`** — the catchall issue (`#25`) is one concrete failure mode; the tree has other shape choices a non-BT-native author may have made differently (e.g. nested `RetryUntilSuccessful num_attempts=3` around `Sequence`, `ReactiveFallback` semantics with stateful subtrees, multiple `_autoremap="true"` blackboard scopes, `KeepRunningUntilFailure`+`Inverter` patterns). Worth a Nav2-BT-experienced second pass before June 4. *(No issue yet — promote to one if the review surfaces concrete findings.)*

**Done:**
- **GUIDED stale-setpoint HOLD verified working** — when `cmd_vel` publication stops, FCU correctly enters HOLD. Confirmed Nav2-crash failsafe behaves as intended on 2026-05-01.

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
- **IzzyBoat WireGuard return path fix** — IzzyBoat is parked; tracked
  under [`unh_echoboats_project11#120`](https://github.com/rolker/unh_echoboats_project11/issues/120) (IzzyBoat parity tracker) for batched
  migration before the next IzzyBoat deployment.

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

## Appendix A: June 4 punch list — effort, boat-dependency, parallelism *(snapshot 2026-05-20)*

This appendix tags every "Must finish before June 4" item from the
Active-threads sections above with effort, where it can be worked, and
critical-path notes — and uses that to size the agent count needed to
clear the list. Refresh or remove this appendix as items land; it's a
working sizing document, not durable direction.

**Where coding**: `BF` = boat-free (implement + test off-boat) · `DI` =
desk-implement, validate on a deployment · `BI` = needs boat to
implement at all (e.g. apply FCU params, on-water test required to
exercise the change).

**Effort**: `XS` <2h · `S` 2–8h · `M` 1–3 days · `L` 3–7 days · `XL`
>7 days or unknown.

### Item-by-item

| # | Item | Effort | Where | Critical-path notes |
|---|---|---|---|---|
| **Sensor payload** | | | | |
| 1 | AML SVS bridge data capture verify | S | BF | Bag analysis; cross-confirm in next deployment |
| 2 | Mercat NTP verify (`ntpq.exe -pn`) | XS | BF | SSH to mercat |
| 3 | Sidescan decision (M3 imagery vs Garmin) | S | BF | Decision only |
| 3b | Sidescan install (if Garmin chosen) | M–L | BI | Physical install + protocol integration |
| **Surface-obstacle** | | | | |
| 4 | [`unh_marine_perception#6`](https://github.com/rolker/unh_marine_perception/issues/6) segfault | L | BF | **UNOWNED.** Blocks #5 → #6 → display path |
| 5 | [`unh_marine_perception#7`](https://github.com/rolker/unh_marine_perception/issues/7) OAK→costmap validation | M | DI | Blocked on #6; replay bags for impl, validate live |
| 6 | [`unh_marine_autonomy#127`](https://github.com/rolker/unh_marine_autonomy/issues/127) op-side costmap display | L | DI | 78% loss measured — bandwidth budget tight; replay-driven impl, validate live |
| **Navigation reliability** | | | | |
| 7 | [`unh_marine_navigation#24`](https://github.com/rolker/unh_marine_navigation/issues/24) BT `target_speed` → `/speed_limit` | M | DI | Sim/bag wire-up, verify in deployment |
| 8 | [`unh_marine_navigation#23`](https://github.com/rolker/unh_marine_navigation/issues/23) TF extrapolation fix | M | DI | Bag-debug, verify in deployment |
| 9 | [`unh_marine_navigation#19`](https://github.com/rolker/unh_marine_navigation/issues/19) costmap timeout investigate | S | BF | Bag analysis; decide fix-or-defer |
| 10 | Boat-side bathy costmap | L–XL | BF | **Triage first** — Roland's "other computer" branch may exist |
| **Both nav at base_link** | | | | |
| 11 | [`#138`](https://github.com/rolker/unh_echoboats_project11/issues/138) FCU reconfig + validation | S prep + **boat day** | BI | Bench param-write OK; sea_surface chain validation needs water |
| **Class-ready UI** | | | | |
| 12 | [`#18`](https://github.com/rolker/unh_echoboats_project11/issues/18) student deployment guide | M | BF | Writing-heavy; draft from logs |
| **Observability — small wins** | | | | |
| 13 | [`#141`](https://github.com/rolker/unh_echoboats_project11/issues/141) remove `diagnostic_aggregator` | XS | BF | Node delete + YAML cleanup |
| 14 | [`#139`](https://github.com/rolker/unh_echoboats_project11/issues/139) `output='both'` in launches | XS | BF | One-line |
| 15 | [`#140`](https://github.com/rolker/unh_echoboats_project11/issues/140) remove `bencloud` ping target | XS | BF | Trivial |
| 16 | [`ros2_network_monitor#23`](https://github.com/rolker/ros2_network_monitor/issues/23) try/except + backoff | S | BF | Defensive code |
| 17 | [`#97`](https://github.com/rolker/unh_echoboats_project11/issues/97) salmon `/diagnostics` recording wiring | XS | BF | Verify |
| **OTH** | | | | |
| 18 | [`#130`](https://github.com/rolker/unh_echoboats_project11/issues/130) OTH field validation | **boat day** | BI | Combinable with #11 |
| 19 | Topic-budget cull (measure + cull + verify) | M + **boat verify** | DI | Bag-driven measurement BF; verify under load DI |
| 20 | Low-bandwidth status fallback | L | DI | New node + UI plugin; unit-test BF, real-link DI |
| 21 | VPN-path indicator | M | DI | Cheaper than #20; UI surface for [`#124`](https://github.com/rolker/unh_echoboats_project11/issues/124) |
| **Autonomy robustness** | | | | |
| 22 | [`unh_marine_navigation#25`](https://github.com/rolker/unh_marine_navigation/issues/25) BT catchall fix | M | BF | Sim/bag testable; review-first recommended |
| 23 | Broader BT review of `run_tasks.xml` | M | BF | Should precede #22 to scope it |

### Totals

- **Boat-free implementable**: 14 items, ~25–35 agent-days
- **Desk-implement, boat-validate**: 6 items, ~10–15 agent-days impl + 1–2 boat days for validation
- **Boat-required to do at all**: 2–3 items (#11, #18 OTH val., optional #3b), need 1–2 boat days
- **Grand total**: ~40–50 agent-days + 1–2 boat days

### Parallelism — how many agents

Window: 15 calendar days to June 4, ~10 working days × N agents.

| Agents | Capacity | Coverage |
|---|---|---|
| 1 | 10 agent-days | ~25% — small wins only; everything else slips |
| 2 | 20 agent-days | ~45% — small wins + 2–3 mediums; large items mostly slip |
| 3 | 30 agent-days | ~70% — most Must-finish; 1 large item slips |
| **4** | **40 agent-days** | **~90% — full Must-finish list with thin margin** |
| 5 | 50 agent-days | 100% with comfortable margin |

**Recommendation: 4 parallel agents** to clear Must-finish with thin
margin; **5** if you want room for the broader BT review surfacing
rework or `#6` debugging exploding.

Hard caps on parallelism that more agents wouldn't relax:

1. **Reviewer bandwidth.** Each agent needs a human reviewer at PR
   time. You cannot review N PRs per day every day. This is the real
   ceiling.
2. **The #4 → #5 → #6 chain.** `unh_marine_perception#6` blocks #5
   blocks #6. Throwing agents at the chain doesn't speed it up; only
   at the segfault can things start. One focused agent on #6 + one on
   #127's bandwidth design (proceeding in parallel against stub
   costmap data) is the right shape.
3. **Boat days are serial.** One boat day = one slot for #11 + #18 +
   #19-verify + #20/#21-verify + #5-validate + #6-validate. Not
   parallel.
4. **#11 FCU reconfig blocks tide-chain validation.** Apply FCU params
   first, then everything that depends on a correct chart-datum chain
   (#19, OTH validation, costmap reliability) validates on the SAME
   boat day.

### Suggested agent allocation

| Agent | Focus | Items |
|---|---|---|
| **A — Perception** | Display path | #4 segfault → #5 OAK→costmap validation → support #6 design |
| **B — Comms / OTH** | New operator UI | #21 VPN-path indicator + #19 topic-budget cull measure phase + #20 fallback impl (stretch) |
| **C — Autonomy / BT** | Safety-critical | #23 broader BT review → #22 catchall fix → #7 BT `target_speed` wire-up → #8 TF fix |
| **D — Operability / docs / sweeps** | Class readiness | #13–17 small wins (1 day) → #12 student deployment guide → #10 bathy-costmap triage → #1/2 verifies → #3 sidescan decision |
| **You** | Boat-implement + review + decisions | #11 FCU reconfig prep, #18 OTH validation boat day, sidescan install if chosen, all PR reviews, scope decisions |

### Critical-path sequencing

1. **This week** (day 1–3): Agent D ships all small wins + sets up
   #12; Agent A starts #6 debug; Agent C does BT review; Agent B
   starts VPN-path indicator. You triage #10 bathy-costmap
   immediately and decide #3 sidescan.
2. **Mid window** (day 4–8): A finishes #6 → starts #5; B finishes
   #21 → starts topic-budget cull; C finishes review → fixes #22 →
   wires #24; D drafts #18.
3. **Boat day** (day 9–10): Apply #11 FCU reconfig, run #18 OTH
   validation, validate #20/#21/#7/#8/#19 + check #127 bandwidth fit
   if it's ready. One combined deployment validates everything
   DI-tagged.
4. **Buffer** (day 11–15): Address findings from boat day, finish
   #12 student guide, decide whether #6 planning-path or #20
   low-bandwidth fallback or the broader BT review needs to absorb
   the slip.

### Risk callout

Plan assumes:
- `#6` segfault is debuggable in ~3–5 days. If it's actually XL, the
  display path slips → Agent A pivots to support #127 bandwidth work
  and the fallback (vigilant watching + exclusion zones) becomes the
  class plan.
- `#10` bathy costmap triage finds existing work. If it's net-new XL
  effort, drop it from Must-finish and accept "no depth-derived
  costmap data at the lake."
- Boat days can be scheduled — weather + access. Need 1, ideally 2 in
  the window.

---

This document was seeded from the milestone content of
[`unh_echoboats_project11#57`](https://github.com/rolker/unh_echoboats_project11/issues/57)
(BizzyBoat field ops umbrella) when that issue was closed in favor of
the per-deployment convention. See
[`unh_echoboats_project11#92`](https://github.com/rolker/unh_echoboats_project11/issues/92)
for the close-out rationale.
