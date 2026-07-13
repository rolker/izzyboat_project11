# BizzyBoat / hydrography roadmap

What we're aiming for, and what's deferred. Scope is BizzyBoat plus the
sensor payload (M3 multibeam, SBG, SVS, Garmin sidescan). This document is
the **carry-over mechanism between deployments**: items here are durable
direction; specific bounded work belongs in GitHub task issues (referenced
from here when relevant).

*Reframed 2026-07-13
([#368](https://github.com/rolker/unh_echoboats_project11/issues/368)) after
the 2026 Lake Massabesic campaign wrapped. The campaign-era roadmap —
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
  fast-iterate harness).
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
- **Honest gap**: the OTH/comms items are the hardest to verify in
  simulation — sim exercises autonomy, not link saturation. The deferred
  **bench stress-test rig** (synth topics + mininet + CAMP-stub) is the only
  desk-side way to answer saturation questions before the ROC goes live.
  Promote it or consciously accept boat-time for comms validation — don't
  let it stay deferred by inertia. (See
  [#124](https://github.com/rolker/unh_echoboats_project11/issues/124).)

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

## Active threads

Cross-references — the roadmap is not the source of truth for any specific
task; the linked issue is.

### OTH operations — the operating baseline *(survey-priority)*

The ROC makes every comms weakness an operations-stopper. Priority order:

- [`#365`](https://github.com/rolker/unh_echoboats_project11/issues/365) —
  Izzlink/Starlink telemetry instability RCA (buffered commands + choppy
  video at Massabesic). The headline comms item.
- **Topic-budget cull** — identify which topics dominate the link and cull /
  rate-limit. The 2026-05-01 saturation episodes (30–60 s latency) are what
  the ROC cannot afford. Related metering mechanism:
  [`udp_bridge#19`](https://github.com/rolker/udp_bridge/issues/19)
  (per-topic priority/class scheduling).
- **Low-bandwidth status fallback** — a text/heartbeat/minimal-telemetry path
  that survives when the full topic stream doesn't. At the ROC there is no
  "walk to the shore and look" fallback.
- [`#145`](https://github.com/rolker/unh_echoboats_project11/issues/145) —
  concurrent Starlink + cell with safety-critical traffic pinned to cell
  (removes the failover blind gap).
- [`udp_bridge#34`](https://github.com/rolker/udp_bridge/issues/34) —
  stale-packet gate opt-in redesign (over-broad default flagged during the
  June 29 import).
- **VPN-path indicator** + **"OTH mode" annunciator quiet-list** — operator
  awareness items carried from the campaign roadmap; the quiet-list matters
  more when *everything* is OTH (WiFi WARN noise is permanent otherwise).
- [`#130`](https://github.com/rolker/unh_echoboats_project11/issues/130) —
  the "OTH with a completed survey" validation criterion. The Shoals survey
  *is* this test — which argues for a deliberate pre-survey OTH validation
  run rather than making the customer survey the first attempt.
- Maintenance-tier bridge items:
  [`udp_bridge#20`](https://github.com/rolker/udp_bridge/issues/20)
  (stats-timer stall — observability, not data path),
  [`udp_bridge#21`](https://github.com/rolker/udp_bridge/issues/21).

### Survey execution quality

Protect what worked; fix the two guidance RCAs; make speed behavior
survey-appropriate.

- [`#363`](https://github.com/rolker/unh_echoboats_project11/issues/363) —
  trackline engagement runs full-speed off the line until a goto reseats
  guidance (slew-limiter re-seed hypothesis). Directly visible in survey
  data quality.
- [`#361`](https://github.com/rolker/unh_echoboats_project11/issues/361) —
  controller doesn't slow for turns (excess power draw; turn speed exceeded
  `default_speed` at Massabesic). Endurance is mission-shaping for the
  Shoals transits.
- [`nav#58`](https://github.com/rolker/unh_marine_navigation/issues/58) —
  mid-line resume after a goto override re-runs the line from the start.
  Operators redirect mid-line constantly during real surveys.
- [`nav#73`](https://github.com/rolker/unh_marine_navigation/issues/73) —
  CA gate chatters STOP during autonomous hover; station-keep can't settle.
- [`nav#5`](https://github.com/rolker/unh_marine_navigation/issues/5) —
  regression tests for the crabbing path follower (see *Mode* above).
- Coverage-planner operator tuning
  ([`#358`](https://github.com/rolker/unh_echoboats_project11/issues/358)) —
  line spacing / swath knobs at the operator station.

### Costmap & planning trust

Front of the line because the Shoals reverses Massabesic's simplification:
ENC coverage exists again, and the boat works close to charted hazards.

- [`#364`](https://github.com/rolker/unh_echoboats_project11/issues/364) —
  costmap paints caution areas LETHAL: bathy store `chart` layer unrecognized
  by `bathymetry_layer` + the reference-bathy pipeline needs validation.
  Must be understood before trusting any costmap at the Shoals.
- **Chart + bathy layering at a charted site** — the
  [`nav#63`](https://github.com/rolker/unh_marine_navigation/issues/63)
  class of problem (charted-feature inflation steering the boat) returns
  from "moot at the lake". The S57-split direction (chart-bathy vs
  obstacles) and the layer ordering need to be exercised against real ENC
  data *in sim* before August.
- **Cost-model rework** (midpoint depth + per-band uncertainty, worst-case
  clearance) — the designed enhancement for shore-keepoff; nearshore
  gap-fill is its motivating use case. Enhancement, not a blocker — the
  layer is usable today.
- [`nav#19`](https://github.com/rolker/unh_marine_navigation/issues/19) —
  costmap update timeout (confirmed real during the campaign; reliability
  factor for any costmap-consuming autonomy).
- **Planning in clutter** — the deferred planning-path items (costmap
  delivery, ahead-replanning). Long pole toward the end goal; not
  Shoals-gating (tracklines remain CA-free by design, obstacle avoidance
  stays the fallback posture).

### Acquisition data quality *(foundational — corrupts everything downstream)*

Swell at the Shoals amplifies attitude/timing errors that a flat lake hides
(the M3 is not roll-stabilized):

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
  decision, not an accident of the last field fix.
- **Sound-speed robustness** —
  [`marine_tools#53`](https://github.com/rolker/marine_tools/issues/53)
  temperature-derived SVS failover. Ocean stratification makes sound speed
  matter more than the lake did; an AML fault at the ROC can't be fixed by
  wading out to the boat.

### Tide / vertical-datum chain *(returns with salt water)*

Massabesic substituted a lake-datum polygon; the Shoals needs the real
thing, end-to-end:

- The `map → map_tide` chain has been validated at the pier but never
  through a full survey. It gates the costmap (tide-relative clearance) —
  exercise it in sim + at the pier before August.
- The **deliverable vertical datum**: survey data is recorded
  WGS84-ellipsoidal (corrigible downstream — the Massabesic lesson), but
  merging with the larger vessel's coverage forces an explicit datum
  agreement for the processed product.

### Data products & exploration

The other half of the end goal: data that's ready for review when the boat
returns.

- **Survey data exploration umbrella** —
  [`unh_marine_autonomy#258`](https://github.com/rolker/unh_marine_autonomy/issues/258):
  tile-indexed explorer over the stores (overview) down to raw un-averaged
  soundings and single-pass sidescan; per-tile CUBE re-runs with custom
  parameters; surface texturing / sidescan drape. Stage 1 (survey index +
  "which bags saw this spot" query CLI) is
  [`uma#259`](https://github.com/rolker/unh_marine_autonomy/issues/259) —
  the immediate unlock for Massabesic target review (re-survey / ROV-dive
  candidates).
- **Draft→processed promotion** — the workflow between "collected" and
  "deliverable" is thin; the Shoals deliverable (merge with the larger
  vessel's coverage) makes it real. Builds on the simplified store formats
  ([`uma#248`](https://github.com/rolker/unh_marine_autonomy/issues/248) +
  [`cube#96`](https://github.com/rolker/cube_bathymetry/issues/96), both
  merged — stores are regenerable caches over the bags of record).
- [`cube#98`](https://github.com/rolker/cube_bathymetry/issues/98) —
  reference blunder gate has no coverage where the prior is NoData; the
  extreme false-deep outliers survive at edges. The explorer's per-tile CUBE
  lab is the natural tuning harness for this gate.
- Sidescan track: live mosaic + offline pipeline validation
  ([`uma#171`](https://github.com/rolker/unh_marine_autonomy/issues/171) /
  [`uma#185`](https://github.com/rolker/unh_marine_autonomy/issues/185));
  the standalone sidescan store exists — wet validation and the Shoals will
  tell us what it's worth over rock.

### Autonomy robustness *(toward the end goal)*

The long-running thread; nothing here is Shoals-gating, everything here is
end-goal-gating.

- **Operator-intervention rate is the autonomy metric.** Each survey should
  need fewer takeovers per hour than the last; count them per deployment.
- Broader BT review of `run_tasks.xml` (carried; promote to an issue if a
  Nav2-BT-experienced pass surfaces concrete findings).
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
