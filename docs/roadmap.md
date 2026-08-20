# BizzyBoat / hydrography roadmap

What we're aiming for, and what's deferred. Scope is BizzyBoat plus the
sensor payload (M3 multibeam, SBG, SVS, Garmin sidescan). This document is
the **carry-over mechanism between deployments**: items here are durable
direction; specific bounded work belongs in GitHub task issues (referenced
from here when relevant).

*Reframed 2026-07-13
([#368](https://github.com/rolker/unh_echoboats_project11/issues/368)) after
the 2026 Lake Massabesic campaign wrapped; updated 2026-07-23
([#390](https://github.com/rolker/unh_echoboats_project11/issues/390)) with
the findings of the 2026-07-23 shakedown deployment
([#386](https://github.com/rolker/unh_echoboats_project11/issues/386));
OTH sections reconciled against delivered work 2026-07-31
([#401](https://github.com/rolker/unh_echoboats_project11/issues/401));
reconciled 2026-08-20
([#413](https://github.com/rolker/unh_echoboats_project11/issues/413),
same-day status sweep
[#439](https://github.com/rolker/unh_echoboats_project11/issues/439))
against the chart-bathy delivery arc, the 2026-08 Lewes/Broadkill week
(deployments [#406](https://github.com/rolker/unh_echoboats_project11/issues/406)
→ [#428](https://github.com/rolker/unh_echoboats_project11/issues/428)), and
the stores→world work, with the operator's stated priorities recorded under
*Active threads*. The campaign-era roadmap —
Summer Hydro survey-prep framing, dev freeze, production mode, punch lists —
is preserved at
[`roadmap_archive_2026_massabesic.md`](roadmap_archive_2026_massabesic.md).*

## End goal

**Fully autonomous survey round-trips.** Plan a survey from the operator
station; the boat transits to the area, runs survey lines, adapts to what it
finds, and returns to the pier — all without user intervention. The operator
*supervises* rather than pilots, and the data products are ready for review
when the boat is back.

Everything on this roadmap serves that goal from one of two directions:
making the **boat** more capably autonomous, or making the **data** it
collects easier to trust, deliver, and explore.

## Forcing function: Isles of Shoals survey (late August 2026)

A real survey with a real deliverable, and a step up in operational
difficulty from Massabesic:

- **Mission**: multibeam survey filling the gap between deeper water
  (surveyed by a larger vessel) and the shore, around the Isles of Shoals.
  Nearshore gap-fill means working **shallow, near rocks, in swell** — the
  shore-side edge of the survey area is exactly where costmap trust and
  depth-derived keepoff matter most.
- **Operations**: BizzyBoat + the same payload (M3 + SBG + SVS + sidescan).
  Operators at a **Remote Operation Center (ROC) at UNH** — the entire
  operation is **over-the-horizon by design**. There is no WiFi fallback at
  any point; Starlink/cell is the *only* link. OTH stops being a resilience
  topic and becomes the operating baseline.
- **Deliverable**: our data must **merge with the larger vessel's deeper-water
  coverage** — the draft→processed promotion story and a defensible vertical
  datum stop being internal conveniences and become customer-facing.
- **Environment**: back to salt water. The real tide / chart-datum chain
  (`map → map_tide`) is load-bearing again (Massabesic ran on a lake-datum
  polygon), and **ENC coverage exists** — the chart costmap layer comes back
  to life, along with its known failure modes.

## Mode: office / simulation iteration (2026-07 → survey)

The inverse of the campaign's "no experiments, harvest from production" mode:
a few weeks in the office, boat available, no field pressure. The method:

- **Fix and improve what Massabesic surfaced** — the RCAs and data-quality
  items below — and **verify in simulation** wherever the failure reproduces
  there (the Massabesic sim assets and the m3_dryrun bag remain the
  fast-iterate harness). The 2026-07-23 shakedown deployment
  ([#386](https://github.com/rolker/unh_echoboats_project11/issues/386))
  already ran this loop once — its findings are folded into the threads
  below.
- **Don't break what worked.** The campaign proved a lot of the stack on the
  water (line-following, the CA helm gate, the live coverage pipeline, the
  operator toolset). Protecting that is a first-class thread, not hygiene:
  - Pay down the **sim-verify debts** owed from campaign-era merges: the
    live CUBE settled-state reload / eviction
    ([cube#70](https://github.com/rolker/cube_bathymetry/issues/70), merged,
    sim-verify owed), the live MapSheet→GeoMapSheet migration
    ([cube#21](https://github.com/rolker/cube_bathymetry/issues/21), same),
    and the CAMP live-cache eviction
    ([camp#160](https://github.com/rolker/camp/issues/160), same).
  - Land the line-following **regression test**
    ([nav#5](https://github.com/rolker/unh_marine_navigation/issues/5)) —
    the 0.19 m-median cross-track performance is now a survey asset worth
    fencing.
- **Honest gap, revised (2026-07-31)**: the OTH/comms items are the
  hardest to verify in simulation — sim exercises autonomy, not link
  saturation. The past month of routine OTH operation has been doing that
  validation continuously on the water, which demotes the **bench
  stress-test rig** from prerequisite to regression protection: it remains
  the only *desk-side* way to reproduce saturation/wedge failure modes
  before code changes ship, rather than the gate for going OTH at all.
  (Saturation history:
  [#124](https://github.com/rolker/unh_echoboats_project11/issues/124), a
  closed data-review issue; the rig is tracked as
  [`udp_bridge#18`](https://github.com/rolker/udp_bridge/issues/18).)

## 2026 Massabesic campaign — outcome (brief)

Surveys ran ~June 15 → July 1; final deployment
[#362](https://github.com/rolker/unh_echoboats_project11/issues/362) wrapped
2026-07-02. The submerged-object search produced **6 operator contact marks**
worth follow-up, and the canonical bathy/backscatter stores were rebuilt from
the retrofitted bags (99.49 % of 11.0 M pings). A return visit to finish
uncovered areas is a **horizon item** (below), not a driver.

What it proved on the water: clean autonomous line-following, the CA helm
gate as safety floor, the bathy costmap (usable after the tide-frame fix),
the live coverage pipeline boat→CAMP, and the three-tool operator set
(coverage display, live coverage, target marking).

What it surfaced (the open RCAs driving the threads below):
[#363](https://github.com/rolker/unh_echoboats_project11/issues/363) trackline
engagement runs full-speed off-line,
[#364](https://github.com/rolker/unh_echoboats_project11/issues/364) costmap
paints caution areas lethal,
[#365](https://github.com/rolker/unh_echoboats_project11/issues/365)
Izzlink/Starlink telemetry instability,
[#361](https://github.com/rolker/unh_echoboats_project11/issues/361)
controller doesn't slow for turns (power), plus the acquisition data-quality
pair [#337](https://github.com/rolker/unh_echoboats_project11/issues/337) /
[#338](https://github.com/rolker/unh_echoboats_project11/issues/338).

Full campaign-era detail: the
[archive](roadmap_archive_2026_massabesic.md) and the per-deployment issues.

## 2026 Lewes / Broadkill week — outcome (brief)

The 2026 Autonomous Systems Bootcamp week (UDel CEOE, Lewes DE, Aug 3–7)
became the salt-water shakedown the Shoals prep needed: four survey days on
the Broadkill River / Lewes sites, all three stores (bathy, backscatter,
sidescan) populated, deployments
[#406](https://github.com/rolker/unh_echoboats_project11/issues/406) →
[#428](https://github.com/rolker/unh_echoboats_project11/issues/428) all
wrapped.

What it proved: the **real tide/chart-datum chain and ENC costmap ran live
in salt water** (chart+bathy re-enable
[#405](https://github.com/rolker/unh_echoboats_project11/pull/405), D10
`depth_costs` flip
[#416](https://github.com/rolker/unh_echoboats_project11/pull/416)); the
2026-08-04 link-saturation RCA turned into shipped transport fixes
([`udp_bridge#44`](https://github.com/rolker/udp_bridge/issues/44) resend
budget cap + [`udp_bridge#43`](https://github.com/rolker/udp_bridge/issues/43)
AIMD admission control, both merged 08-05); and the live-coverage robustness
cluster (camp#168–170) was fixed mid-week and field-checked.

What it surfaced (now open threads below):
[#408](https://github.com/rolker/unh_echoboats_project11/issues/408) ~60 %
lethal costmap RCA,
[#422](https://github.com/rolker/unh_echoboats_project11/issues/422)
unknown-space renders FREE,
[#430](https://github.com/rolker/unh_echoboats_project11/issues/430) /
[#431](https://github.com/rolker/unh_echoboats_project11/issues/431)
buoy-strike bag analysis + entanglement/drag detection,
[#407](https://github.com/rolker/unh_echoboats_project11/issues/407) WiFi
bridge path carries no coverage tiles, and
[#432](https://github.com/rolker/unh_echoboats_project11/issues/432) the
capability-envelope re-measure (the differential-drive experiment of 08-04
was reverted to vectored thrust on 08-06, leaving the new helm capability
curve disabled with stale numbers). Field-import stopgaps: both
[`s57_tools#36`](https://github.com/rolker/s57_tools/pull/36) (D10
suppressed-mode cell claim) and
[`nav#106`](https://github.com/rolker/unh_marine_navigation/pull/106)
(RobotOnPath lead-in threshold) merged 2026-08-20 with the full
GitHub⇄gitcloud field-import reconciliation.

## Active threads

Cross-references — the roadmap is not the source of truth for any specific
task; the linked issue is.

**Operator priorities (stated 2026-08-20).** Ahead of the Shoals and as the
post-Lewes focus, the operator named four outcomes to drive toward, in
order:

1. **Complete the stores→world arc** — finish the `world/` data-home
   consolidation and the draft/processed re-split (see *Data products &
   exploration*).
2. **Live bathy coverage view working reliably** — the remaining
   eviction/reload tail of the live-coverage cluster (see *ROC operator
   awareness*).
3. **Datum-aware depth display in CAMP** — depths presented against chart
   datum, not raw ellipsoid (see *Tide / vertical-datum chain*).
4. *(stretch)* **Public web view of position + live coverage** for project
   participants off the boat's network (see *Shore & stakeholder
   visibility*).

### OTH operations — the operating baseline *(survey-priority)*

**Status change (2026-07-31 reconcile): OTH is no longer an aspiration —
it has been the routine operating mode across the past month of
deployments.** The foundations are delivered and closed:

- **Concurrent Starlink + cell**
  ([`#145`](https://github.com/rolker/unh_echoboats_project11/issues/145),
  closed as-built): dual WireGuard tunnels carried concurrently — the cell
  tunnel WAN-pinned to cellular at the boat router — with the
  safety-critical uplink (`command`, `joystick_helm`) carried redundantly
  on all three paths (wifi, vpn, cell) in `operator.yaml`; cell-path DNS via
  [CCOMJHC/ccomjhc_project11#74](https://github.com/CCOMJHC/ccomjhc_project11/pull/74).
  No failover blind gap: critical traffic rides every live link at once. This
  also substantially covers the old "low-bandwidth status fallback" idea —
  the residual there is *verifying the critical-topic set*, not building a
  mechanism.
- **Operator-side costmap display**
  ([`uma#127`](https://github.com/rolker/unh_marine_autonomy/issues/127),
  closed as-delivered): `costmap_window` → `costmap_windowed` over
  udp_bridge, in routine use.
- **OTH validation**
  ([`#130`](https://github.com/rolker/unh_echoboats_project11/issues/130),
  closed): passed by the operating record rather than a staged run. The
  Shoals will be the first *customer survey* fully OTH — that's its
  deliverable, not an open gate.

The residual list is what was actually observed **while operating OTH**:

- [`#365`](https://github.com/rolker/unh_echoboats_project11/issues/365) —
  Izzlink/Starlink telemetry instability RCA (buffered commands + choppy
  video at Massabesic). Still the headline diagnosis item; with the cell
  pinning live, assess whether a repeat is contained before ranking it.
- Coverage-tile transmission
  ([`#389`](https://github.com/rolker/unh_echoboats_project11/issues/389),
  **closed 2026-07-31**): large level-11 tiles rate-starved the link on two
  deployments (07-23 max-data raise; 07-29 return-rate override — both
  unsaved field workarounds). Resolved by persisting the field-proven VPN
  cap (1.5 MB/s) + slowing tiles to 1/s
  ([PR#403](https://github.com/rolker/unh_echoboats_project11/pull/403);
  field check rides the next deployment). The **structural residual** —
  bounding the message size itself at the publisher — is
  [`cube_bathymetry#112`](https://github.com/rolker/cube_bathymetry/issues/112).
  Related: [`udp_bridge#19`](https://github.com/rolker/udp_bridge/issues/19)
  (per-topic priority/class scheduling);
  [`udp_bridge#36`](https://github.com/rolker/udp_bridge/issues/36)
  (transport rework umbrella).
- **Topic-budget cull** — identify which topics dominate the link and cull /
  rate-limit. The 2026-05-01 saturation episodes (30–60 s latency) are what
  the ROC cannot afford. The cell path's curated topic list covers the
  critical uplink; this is about headroom on the main stream.
- **Link-saturation defenses — delivered (2026-08).** The 2026-08-04
  saturation episode at Lewes produced the shipped pair
  [`udp_bridge#44`](https://github.com/rolker/udp_bridge/issues/44)
  (per-connection resend bandwidth cap with ack-starvation backoff) +
  [`udp_bridge#43`](https://github.com/rolker/udp_bridge/issues/43)
  (adaptive AIMD admission control), and
  [`udp_bridge#35`](https://github.com/rolker/udp_bridge/issues/35)
  (reorder/jitter buffer, merged 2026-08-20; ships disabled —
  `reorder_hold_window_ms: 0`) rounds out the out-of-order handling.
  Residuals: the [`udp_bridge#45`](https://github.com/rolker/udp_bridge/issues/45)
  saturation RCA write-up is unstarted, and
  [`#427`](https://github.com/rolker/unh_echoboats_project11/issues/427)
  (bridge the boat's `bridge_info`/`topic_statistics` to the operator) is
  what would have made the congestion triage visible from salmon.
- [`udp_bridge#34`](https://github.com/rolker/udp_bridge/issues/34) —
  stale-packet gate opt-in redesign (over-broad default flagged during the
  June 29 import); also where per-topic tuning of the #35 hold window
  lands.
- **VPN-path indicator** + **"OTH mode" annunciator quiet-list** — operator
  awareness items carried from the campaign roadmap; the quiet-list matters
  more when *everything* is OTH (WiFi WARN noise is permanent otherwise).
  The operator-declared OTH mode itself is tracked as
  [`uma#128`](https://github.com/rolker/unh_marine_autonomy/issues/128).
- Maintenance-tier bridge items:
  [`udp_bridge#20`](https://github.com/rolker/udp_bridge/issues/20)
  (stats-timer stall — observability, not data path),
  [`udp_bridge#21`](https://github.com/rolker/udp_bridge/issues/21).

### ROC operator awareness & control *(promoted by the ROC)*

Everything the shore operator knows arrives over the link, and there is no
walk-to-the-boat fallback. Silent failures and invisible state are
qualitatively worse at a ROC than at a pier — this cluster of carried
campaign items graduates from "nice to have" to survey-relevant:

- ~~operator-side costmap display~~ — **delivered**
  ([`uma#127`](https://github.com/rolker/unh_marine_autonomy/issues/127)
  closed 2026-07-31): the windowed costmap (`costmap_windowed`) reaches the
  operator over the bridge and is in routine use. The link-capacity fix for
  coverage tiles landed via #389/PR#403; the structural message-size bound
  is [`cube_bathymetry#112`](https://github.com/rolker/cube_bathymetry/issues/112).
- [`#183`](https://github.com/rolker/unh_echoboats_project11/issues/183) —
  CAMP overlay of the CA reflex state (obstacles, slowdown/stop polygons,
  gating). The operator must see *what the boat is reacting to* from shore.
- [`#274`](https://github.com/rolker/unh_echoboats_project11/issues/274) /
  [`#275`](https://github.com/rolker/unh_echoboats_project11/issues/275) —
  annunciator runtime checks: RTCM/NTRIP correction flow and boat-side
  Starlink diagnostics reaching the operator panel.
- [`ros2launch_session#5`](https://github.com/rolker/ros2launch_session/issues/5)
  — observability mode: detect silent lifecycle aborts / process deaths.
  The "queued a goal and nothing happened" failure shape cost expert
  diagnosis time at the pier; at the ROC it costs the survey day.
  (Related: [`camp#52`](https://github.com/rolker/camp/issues/52) GUI-freeze
  capture plan,
  [`#142`](https://github.com/rolker/unh_echoboats_project11/issues/142)
  host thermals,
  [`uma#139`](https://github.com/rolker/unh_marine_autonomy/issues/139)
  boat-core wedge liveness/watchdog.)
- **Live-coverage display reliability** *(operator priority #2)*. The
  2026-07-23 crash/restart cluster is **fixed and field-checked at Lewes**:
  re-add after remove ([`camp#168`](https://github.com/rolker/camp/issues/168)),
  request resume on enable ([`camp#169`](https://github.com/rolker/camp/issues/169)),
  and the oversized-tile unbounded allocation
  ([`camp#170`](https://github.com/rolker/camp/issues/170)) all closed
  2026-08-05 ([camp PR#185](https://github.com/rolker/camp/pull/185)); the
  blurry-overview render
  ([`camp#103`](https://github.com/rolker/camp/issues/103)) closed via the
  GGGS LOD/overview arc
  ([camp PR#182](https://github.com/rolker/camp/pull/182) /
  [camp PR#183](https://github.com/rolker/camp/pull/183) /
  [camp PR#184](https://github.com/rolker/camp/pull/184), 2026-07-31); and the
  **eviction/reload lifecycle closed 2026-08-20**
  ([`camp#171`](https://github.com/rolker/camp/issues/171) eviction budget +
  [`camp#172`](https://github.com/rolker/camp/issues/172) in-session fine-tile
  reload, via [camp PR#190](https://github.com/rolker/camp/pull/190) — the
  world-store-LOD step-4 live cache). The remaining tail:
  [`camp#163`](https://github.com/rolker/camp/issues/163) (overview
  lifecycle on catalog retraction), plus the boat-side structural bound
  [`cube_bathymetry#112`](https://github.com/rolker/cube_bathymetry/issues/112)
  (chunk large dirty windows at the publisher) and the config gap
  [`#407`](https://github.com/rolker/unh_echoboats_project11/issues/407)
  (WiFi bridge path carries no coverage topics at all). At the ROC the
  coverage panel is the survey's progress gauge — it has to survive
  restarts, re-adds, large tiles, *and eviction*.
- **Device-control plugin reliability** — checked-but-no-tab
  ([`rqt_operator_tools#109`](https://github.com/rolker/rqt_operator_tools/issues/109))
  and device discovery that never refreshes after load
  ([`rqt_operator_tools#110`](https://github.com/rolker/rqt_operator_tools/issues/110)).
  At the ROC the marine_control panel is the only way to reach device knobs
  mid-survey.
- **Operator-side CA tuning levers** —
  [`uma#168`](https://github.com/rolker/unh_marine_autonomy/issues/168)
  (CA-pipeline tuning/disable controls umbrella) +
  [`perception#30`](https://github.com/rolker/unh_marine_perception/issues/30)
  (radar-style segmentation→costmap controls). When glint false positives
  stop the boat mid-line (see *Survey execution quality*), the ROC
  operator's only alternatives today are watching it struggle or taking the
  helm — and the takeover itself currently costs lines (nav#104).
- **Design thread (carried — not yet issues): platform-aware speed override
  + on-the-fly trackline editing.** Gentler operator interventions than a
  full manual takeover (from the 2026-05-21 collision debrief): a speed
  slider backed by platform `default_speed`/`max_speed` metadata, and
  dragging a trackline waypoint past an obstacle instead of taking the
  helm. Both want scoping conversations (message schema, CAMP UI surface)
  before promotion to issues; at ROC ranges these become the *primary*
  intervention tools.

### Survey execution quality

Protect what worked; fix the two guidance RCAs; make speed behavior
survey-appropriate.

- [`#363`](https://github.com/rolker/unh_echoboats_project11/issues/363) —
  trackline engagement runs full-speed off the line until a goto reseats
  guidance (slew-limiter re-seed hypothesis). Directly visible in survey
  data quality.
- [`#361`](https://github.com/rolker/unh_echoboats_project11/issues/361) —
  controller doesn't slow for turns. The mechanism **shipped 2026-08-05**:
  curvature-preserving speed regulation from a per-platform capability
  envelope ([`uma#292`](https://github.com/rolker/unh_marine_autonomy/issues/292),
  enabled on BizzyBoat via
  [PR#418](https://github.com/rolker/unh_echoboats_project11/pull/418)) —
  but it is currently **disabled**, because its envelope was measured on the
  short-lived differential-drive configuration and the boat reverted to
  vectored thrust on 08-06. Re-measuring the vectored envelope and
  re-enabling is
  [`#432`](https://github.com/rolker/unh_echoboats_project11/issues/432).
- [`nav#58`](https://github.com/rolker/unh_marine_navigation/issues/58) —
  mid-line resume after a goto override re-runs the line from the start.
  Operators redirect mid-line constantly during real surveys.
- [`nav#73`](https://github.com/rolker/unh_marine_navigation/issues/73) —
  CA gate chatters STOP during autonomous hover; station-keep can't settle.
- [`nav#104`](https://github.com/rolker/unh_marine_navigation/issues/104) —
  mission consumes survey-line tasks during manual override: on 2026-07-23,
  two lines were silently marked failed-done while the operator drove
  through CA false positives, and the boat resumed two lines over. At the
  ROC a manual takeover is the *primary* intervention — the mission must
  survive one without eating lines. Sits with the
  [`nav#43`](https://github.com/rolker/unh_marine_navigation/issues/43) /
  [`nav#77`](https://github.com/rolker/unh_marine_navigation/issues/77) /
  [`nav#79`](https://github.com/rolker/unh_marine_navigation/issues/79)
  transition family under the
  [`nav#50`](https://github.com/rolker/unh_marine_navigation/issues/50)
  BT-redesign umbrella.
- **Segmentation glint/reflection false positives** —
  [`perception#34`](https://github.com/rolker/unh_marine_perception/issues/34)
  (in-domain fine-tune, the durable fix) /
  [`perception#42`](https://github.com/rolker/unh_marine_perception/issues/42)
  (WaSR-T temporal-segmentation evaluation). Escalated 2026-07-23: no longer
  just hover drift — repeated CA stops at a line end triggered the nav#104
  two-line skip, so the false-positive cluster now costs survey coverage
  directly. Sun and swell at the Shoals will not be gentler than a lake.
- [`#388`](https://github.com/rolker/unh_echoboats_project11/issues/388) —
  commanded velocity jumping in an rqt panel (unresolved 2026-07-23 thread;
  gabby bag analysis pending, which also carries the nav#104 mechanism
  check).
- [`nav#5`](https://github.com/rolker/unh_marine_navigation/issues/5) —
  regression tests for the crabbing path follower (see *Mode* above).
- Coverage-planner operator tuning
  ([`#358`](https://github.com/rolker/unh_echoboats_project11/issues/358)) —
  line spacing / swath knobs at the operator station.

### Costmap & planning trust

*(Reconciled 2026-08-20 per
[#413](https://github.com/rolker/unh_echoboats_project11/issues/413) — the
chart-bathy arc of 2026-07-24 → 08-03 delivered most of what this section
used to ask for, and Lewes ran it in salt water.)*

**Delivered (the ENC→store→costmap chain, ADR-0010)**: vdatum library
([`uma#274`](https://github.com/rolker/unh_marine_autonomy/issues/274)),
store chart layer + atomic regeneration
([`uma#275`](https://github.com/rolker/unh_marine_autonomy/issues/275)),
`s57_to_geotiff` exporter with CATZOC→σ
([`s57_tools#27`](https://github.com/rolker/s57_tools/issues/27)),
chart-layer stage/commit CLI
([`uma#289`](https://github.com/rolker/unh_marine_autonomy/issues/289)),
worst-case-clearance cost model + confidence gate
([`uma#276`](https://github.com/rolker/unh_marine_autonomy/issues/276) —
the old "cost-model rework" line, now real), the D10 chart-vs-bathy split
([`s57_tools#30`](https://github.com/rolker/s57_tools/issues/30) +
the `depth_costs: false` config flip
[PR#416](https://github.com/rolker/unh_echoboats_project11/pull/416)),
the s57+bathy-override re-enable (#276 closed via
[PR#405](https://github.com/rolker/unh_echoboats_project11/pull/405)), and
the cron-friendly ENC updater
([`s57_tools#28`](https://github.com/rolker/s57_tools/issues/28)).

**Remaining — validation, not construction**:

- [`#408`](https://github.com/rolker/unh_echoboats_project11/issues/408) —
  the Lewes observation: ~60 % of the local area painted lethal. Isolate
  which layer; review ENC cell selection + costmap resolution vs chart
  scale. This is the concrete successor to the old
  [`#364`](https://github.com/rolker/unh_echoboats_project11/issues/364)
  framing — the new chain exists; what remains is validating it on real
  data.
- [`#422`](https://github.com/rolker/unh_echoboats_project11/issues/422) —
  `track_unknown_space` unset: uncharted water renders FREE, so unknown
  looks navigable (paired with the near-dock takeover analysis
  [`#423`](https://github.com/rolker/unh_echoboats_project11/issues/423)).
- **Dockside trial** *(operator decision 2026-08-05, replacing the
  sim-first wording)*: boat at the dock, costmap look-see, then a live
  on-water check — the acceptance path for the chain at a charted site.
- Chart-content tail: Lewes ENC import acceptance into the store `chart/`
  layer + migrating the 16 interim tiles out of `reference/` (owed from
  [`uma#289`](https://github.com/rolker/unh_marine_autonomy/issues/289));
  [`s57_tools#32`](https://github.com/rolker/s57_tools/issues/32);
  [`s57_tools#26`](https://github.com/rolker/s57_tools/issues/26)
  (stale cached tide_offset when chart_datum disappears).
- [`nav#19`](https://github.com/rolker/unh_marine_navigation/issues/19) —
  costmap update timeout (reliability factor for any costmap-consuming
  autonomy).
- **Planning in clutter** — the deferred planning-path items (costmap
  delivery, ahead-replanning). Long pole toward the end goal; not
  Shoals-gating (tracklines remain CA-free by design, obstacle avoidance
  stays the fallback posture).

### Acquisition data quality *(foundational — corrupts everything downstream)*

Swell at the Shoals amplifies attitude/timing errors that a flat lake hides
(the M3 is not roll-stabilized):

- [`cube#110`](https://github.com/rolker/cube_bathymetry/issues/110) —
  validity-gate M3 no-bottom returns before they grid into draft tiles.
  2026-07-23: shallow-water bottom-detection dropouts put deep-negative
  flyers into several draft tiles (some unsalvageable). Nearshore gap-fill
  at the Shoals is *exactly* the shallow regime that produced them — without
  the gate, the deliverable inherits the contamination. Complements the
  prior-based gates
  ([`cube#98`](https://github.com/rolker/cube_bathymetry/issues/98) /
  [`cube#91`](https://github.com/rolker/cube_bathymetry/issues/91)).
- [`#337`](https://github.com/rolker/unh_echoboats_project11/issues/337) —
  FCU 3D-gyro health fault (phantom roll → bathy artifacts via
  `mru_transform`).
- [`#338`](https://github.com/rolker/unh_echoboats_project11/issues/338) —
  time-sync diagnostics gabby ↔ mercat ↔ M3 (the +6.03 s stamp regression
  class — detect clock skew live instead of discovering it in the data).
- **Durable MRU source policy** —
  [`#339`](https://github.com/rolker/unh_echoboats_project11/issues/339)
  (SBG-primary) merged, but the field deployments **reverted to FCU-primary**
  (June 29/30). The configuration that surveys the Shoals needs to be a
  decision, not an accident of the last field fix. Open tracker for the
  durable-source decision:
  [`#138`](https://github.com/rolker/unh_echoboats_project11/issues/138).
- **Sound-speed robustness** —
  [`marine_tools#53`](https://github.com/rolker/marine_tools/issues/53)
  temperature-derived SVS failover. Ocean stratification makes sound speed
  matter more than the lake did; an AML fault at the ROC can't be fixed by
  wading out to the boat.
- [`#137`](https://github.com/rolker/unh_echoboats_project11/issues/137) —
  M3 intermittent missing pings (suspected ping-rate × depth correlation).
  Carried from the campaign era; the Shoals' depth range makes the
  suspected correlation directly testable.

### Tide / vertical-datum chain *(live in salt water since Lewes)*

Lewes ran the real `map → map_tide` chain through four survey days — the
"never through a full survey" caveat is retired. The datum *infrastructure*
also firmed up: the `world/datum/` support-data home is delivered
([`uma#288`](https://github.com/rolker/unh_marine_autonomy/issues/288)
items 1–3 + the
[`s57_tools#37`](https://github.com/rolker/s57_tools/issues/37) provisioner —
geoid grid with SHA-256 pin + VDatum bundles, updater-managed) — and as of
2026-08-20 the importer consumes those grids too:
[`uma#315`](https://github.com/rolker/unh_marine_autonomy/issues/315)
(merged) gives `import_geotiff` per-cell MLLW→ellipsoid conversion
(`--source-datum mllw`), so a tidal-datum-referenced reference grid — the
pending 1 m Appledore grid,
[`uma#314`](https://github.com/rolker/unh_marine_autonomy/issues/314)
step 2 — imports without hand-computed offsets. What remains:

- **Datum-aware depth display in CAMP** *(operator priority #3)*: depths
  shown to the operator should be referenced to chart datum, not raw
  ellipsoid. The cursor depth readout exists
  ([`camp#180`](https://github.com/rolker/camp/issues/180), closed
  2026-07-31 via the depth-provider walk); the open piece is the
  datum-referenced presentation —
  [`camp#181`](https://github.com/rolker/camp/issues/181) (topo-bathy
  colormap pivoted at chart datum) is the concrete ticket, and the readout
  itself needs the same datum treatment (scoping to confirm whether that is
  in #181 or its own issue).
- Sim-side datum wiring
  ([`#288`](https://github.com/rolker/unh_echoboats_project11/issues/288))
  so the sim exercises the same chain the boat runs.
- The **deliverable vertical datum**: survey data is recorded
  WGS84-ellipsoidal (corrigible downstream — the Massabesic lesson), but
  merging with the larger vessel's coverage forces an explicit datum
  agreement for the processed product.

### Data products & exploration

The other half of the end goal: data that's ready for review when the boat
returns.

- **Stores→world arc completion** *(operator priority #1)*. The `world/`
  consolidation ([`uma#288`](https://github.com/rolker/unh_marine_autonomy/issues/288)
  umbrella, ADR-0010 D3 amendment) is well underway — delivered: datum
  grids + user polygons + ENC/S-102 product homes (items 1–3), the
  [`s57_tools#37`](https://github.com/rolker/s57_tools/issues/37) datum
  provisioner, and the S-102 area importer
  ([`uma#278`](https://github.com/rolker/unh_marine_autonomy/issues/278)).
  The **closeout set (filed 2026-08-20)** is the named finish line, and
  most of it landed the same day:
  [`uma#308`](https://github.com/rolker/unh_marine_autonomy/issues/308)
  D8 re-split restoring the quality axis (survey/ → draft/ live +
  processed/ offline re-run; store-writer co-land
  [`cube#133`](https://github.com/rolker/cube_bathymetry/issues/133)) —
  **both merged 2026-08-20**, as did
  [`uma#309`](https://github.com/rolker/unh_marine_autonomy/issues/309)
  (shallowest-preserving depths pyramid). Remaining:
  [`uma#310`](https://github.com/rolker/unh_marine_autonomy/issues/310)
  `~/data/stores` → `~/data/world` root migration,
  [`uma#311`](https://github.com/rolker/unh_marine_autonomy/issues/311)
  housekeeping, and the
  [`uma#288`](https://github.com/rolker/unh_marine_autonomy/issues/288)
  umbrella items 4–6 (including the
  updater-run acceptance gate on the operator/boat hosts). The D8
  re-split *completes* the old "draft→processed promotion is thin"
  line — promotion is now the offline re-run into `processed/`. The
  ENC side got rescheme-proofed the same day:
  [`s57_tools#40`](https://github.com/rolker/s57_tools/issues/40)
  region-driven cell selection derives the updater's cell set from the
  live catalog's coverage polygons (the Shoals bbox selects 13 cells
  where a hand-pinned list had 3), and the first world-root store at
  `~/data/world/store` carries that chart layer
  ([`uma#314`](https://github.com/rolker/unh_marine_autonomy/issues/314)
  step 1).
- **CUBE quality chain — delivered, activation owed.** The slope+gate
  chain completed 2026-08-18:
  [`cube#59`](https://github.com/rolker/cube_bathymetry/issues/59)
  touchdown interpolation activates slope correction,
  [`cube#91`](https://github.com/rolker/cube_bathymetry/issues/91) /
  [`cube#119`](https://github.com/rolker/cube_bathymetry/issues/119)
  live prior-layer seeding + Chart-layer import gate,
  [`cube#118`](https://github.com/rolker/cube_bathymetry/issues/118)
  gate re-prime on evict/revisit, and
  [`cube#115`](https://github.com/rolker/cube_bathymetry/issues/115)
  level-walk fallback. Activation on the boat is
  [`#434`](https://github.com/rolker/unh_echoboats_project11/issues/434)
  (`prior_store_dir` in the bizzyboat config). Still open in this family:
  [`cube#110`](https://github.com/rolker/cube_bathymetry/issues/110)
  (M3 no-bottom validity gate — see *Acquisition data quality*) and
  [`cube#98`](https://github.com/rolker/cube_bathymetry/issues/98)
  (no gate coverage where the prior is NoData).
- **Survey data exploration umbrella** —
  [`unh_marine_autonomy#258`](https://github.com/rolker/unh_marine_autonomy/issues/258):
  stages 1–3 (survey index, integrated explorer shell, time bar) merged;
  stages 4–5 (box CUBE lab + sidescan drape) built and in PR
  ([`mpt#31`](https://github.com/rolker/marine_perception_tools/pull/31));
  the sidescan DEM-drape orthorectification
  ([`uma#297`](https://github.com/rolker/unh_marine_autonomy/issues/297))
  merged 2026-08-18 (perf follow-up
  [`uma#306`](https://github.com/rolker/unh_marine_autonomy/issues/306)).
  The per-tile CUBE lab is the natural tuning harness for the cube#98
  gate.
- Sidescan track: live mosaic + offline pipeline validation
  ([`uma#171`](https://github.com/rolker/unh_marine_autonomy/issues/171) /
  [`uma#185`](https://github.com/rolker/unh_marine_autonomy/issues/185));
  the standalone sidescan store exists and Lewes populated it — wet
  validation over rock is still the open question for the Shoals.
- **Contact curation & distribution** —
  [`uma#157`](https://github.com/rolker/unh_marine_autonomy/issues/157)
  (contact manager: CRUD store, curate/confirm, map distribution). The
  explorer covers *reviewing* the 6 Massabesic marks; #157 is where a
  reviewed mark becomes a curated, distributable contact (re-survey / ROV
  target list).

### Shore & stakeholder visibility *(new thread; stretch — operator priority #4)*

Project participants who are **not** on the boat's network (bootcamp
partners, the larger survey vessel, PIs following along) currently have no
view of the operation at all — everything lives behind the operator VPN.
The stated want: a **publicly reachable web view showing boat position and
live survey coverage**, read-only and low-bandwidth.

- Existing design seed:
  [`uma#166`](https://github.com/rolker/unh_marine_autonomy/issues/166)
  (web situational-awareness viewer: contacts + bathy on a browser map) —
  re-scope it around this audience: position + live coverage first,
  contacts/sidescan later.
- Constraints to respect from day one: the boat link is the scarce
  resource, so the web view must be fed from the **shore side** (salmon /
  a cloud relay) off data already crossing the bridge — never a second
  stream from the boat; and public exposure needs an explicit
  auth/anonymization decision (position of an active survey asset).
- Scoping conversation needed before issues: serving surface (static tiles
  + GeoJSON position vs. a live map service), hosting (UNH vs. cloud), and
  what "live" means (tens of seconds is fine for this audience).

### Autonomy robustness *(toward the end goal)*

The long-running thread; nothing here is Shoals-gating, everything here is
end-goal-gating.

- **Operator-intervention rate is the autonomy metric.** Each survey should
  need fewer takeovers per hour than the last; count them per deployment.
- Broader BT review of `run_tasks.xml` — now tracked as
  [`nav#50`](https://github.com/rolker/unh_marine_navigation/issues/50)
  (task-switching latch family), with the 2026-07-23 nav#104 finding as
  fresh input.
- **Lifecycle nodes vs. respawn** *(carried from 2026-07-23; no tracker
  yet)*: `respawn=True` restarts a process but does not re-drive lifecycle
  transitions — a respawned cube_bathymetry sat unconfigured until manually
  advanced (known behavior, caught the field agent by surprise). The
  boat-resilience question is a lifecycle-manager / activation-on-respawn
  policy for every lifecycle node in the launch tree, not a per-node fix.
- Recovery behaviors: stalled-at-obstacle, station-keep interactions
  (nav#73 above), mission resume semantics (nav#58 above).
- Planning-path costmap trust (see *Costmap & planning trust*) — the
  prerequisite for autonomy planning around obstacles rather than through
  the fallback posture.

## Horizon items *(not drivers)*

- **Massabesic return** — finish uncovered areas; re-survey and/or ROV-dive
  the target candidates the explorer surfaces from the June data. Scope
  follows from the uma#258 stage-1 review, not before.
- **Student-facing deployment guide**
  ([`#18`](https://github.com/rolker/unh_echoboats_project11/issues/18)) —
  still open; matters again whenever students next operate.
- **Power precision** —
  [`#88`](https://github.com/rolker/unh_echoboats_project11/issues/88)
  PWM×current sweep /
  [`#196`](https://github.com/rolker/unh_echoboats_project11/issues/196)
  charger-current capture — the ±30 % model held for Massabesic; longer OTH
  transits will eventually want better.
- **IzzyBoat parity**
  ([`#120`](https://github.com/rolker/unh_echoboats_project11/issues/120)) —
  promote when multi-boat ops come back into scope.

## What's not on this roadmap

- Specific bug fixes — those are task issues
- Specific deployments — those get their own deployment issues
- Anything on deck for the **next** deployment — that goes in the next
  deployment issue's body, not here

## How this roadmap stays useful

- At deployment start: planner reads this + open task issues → picks the
  next deployment's scope.
- At deployment wrap-up: items that came up but aren't bounded enough for a
  task issue and aren't going to be done next time → land here.
- In office/sim mode: prefer changes that can be **verified in simulation**;
  anything that needs on-water evidence gets queued for a deliberate
  validation day, not discovered at the survey.
- Periodically: if "deferred" items have been sitting more than a couple of
  months without any pull toward them, they're probably dropped, not
  deferred. Edit them out.

---

This document was reframed 2026-07-13
([#368](https://github.com/rolker/unh_echoboats_project11/issues/368));
the campaign-era version (originally seeded from
[#57](https://github.com/rolker/unh_echoboats_project11/issues/57)) is
preserved at
[`roadmap_archive_2026_massabesic.md`](roadmap_archive_2026_massabesic.md).
