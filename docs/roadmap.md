# BizzyBoat / hydrography roadmap

What we're aiming for, and what's deferred. Scope is BizzyBoat plus the
sensor payload (M3 sonar, SBG, SVS) supporting the **2026 survey
campaigns** — the June Lake Massabesic survey and a potential August OTH
survey. The June Summer Hydro class is the training / sonar-setup /
shakedown week that feeds the June survey, not the end in itself.

This document is the **carry-over mechanism between deployments**, and — as of
2026-06-07 — the **bridge from development into production** (see *Mode* below).
Items here are durable direction; specific bounded work belongs in GitHub task
issues (referenced from here when relevant).

## End goal

**Fully autonomous survey round-trips.** Plan a survey from the
operator station; boat transits to the area, runs survey lines, returns
to the pier — all without user intervention.

## Forcing function

**2026 survey campaigns.** The roadmap is driven by real surveys, not the class
per se. Two campaigns are on the horizon:
- **June survey — Lake Massabesic, NH (~June 15 → ~June 29).** A two-week real
  survey for a real customer — the immediate driver. 10 students rotate in 3
  daily groups (3–4/day) plus engineer / intern helpers.
- **Potential OTH survey — August (tentative).** A second campaign, expected to
  be **OTH-scale** (boat operating outside direct comms range; longer-range
  autonomy / link demands). *Named as a horizon goal only — it does **not**
  re-prioritize the June must-finish work yet; revisit after the June survey.*

**Survey-prep week — June 8 → 15 (the Summer Hydro class).** One week of
**operator training + sonar setup + shakedown** ahead of the June survey: Roland
teaches boat operation while students learn survey-component integration in
parallel, and the boat + sonar payload get set up and shaken down. Heavy
development should be **done by June 8 (Monday)** — switch to maintenance mode
thereafter.

> **Schedule update (2026-06-03):** the survey-prep week (and the dev freeze)
> moved to start **June 8 (Monday)** from June 4. This buys **two more pier/dev
> days (June 4–5)** before the freeze — but it **compresses the June 8 → June 15
> prep week** (operator training + sonar setup + shakedown) into just **4–5
> days**. That compression is now the binding schedule constraint: the extra
> pier days go to finishing the must-finish list, not to slack. The survey
> date (June 15) is unchanged. Throughout this document, "before June 4" /
> "June 4" freeze references should now be read as **June 8** unless they are
> explicitly dated historical snapshots (the 2026-06-02 reality check below
> and Appendix A).

This is a real survey for a real customer, not a class exercise — the
system must work, not just demonstrate. Hydrographic-quality output is
the goal even though the operational bar is lower. The system must
support multi-operator handoff across daily cohorts.

## Mode: production / survey-prep (2026-06-07)

**The boat is going into production.** With the dev freeze landing **June 8**,
BizzyBoat shifts from a development / experiment platform to a **production survey
tool** — first the Summer Hydro class (operator training + sonar setup + shakedown,
June 8 → 15), then the Lake Massabesic survey (~June 15 → 29). Heavy development
stops; the system runs surveys, driven by student pilots and hydrographers.

**Consequence for engineering: no more controlled boat-experiment time.** Through
the spring, open questions were answered by scheduling a deployment and running the
test we needed. That option is gone — the boat is committed to surveys and teaching
and is not free for us to instrument. So the method flips: **we answer our remaining
open questions by harvesting the bags that real survey and teaching runs generate**,
not by running experiments (see *Harvesting production data* below). This raises the
stakes on **recording** — if a production run doesn't capture the topics we need,
there is no do-over, so the recording config is now a first-class concern.

Two reading rules for the rest of this document:
- The pre-freeze **"must finish before June 8"** framing (and Appendix A's sprint
  sizing) is now **historical**. Items that didn't land are not getting a dev push;
  they are accepted-as-is, harvested from production, or maintenance-mode.
- Anything still open that needs on-water evidence is tagged **"harvest from
  production"** — make sure it's recorded, then mine the operational bags.

## Survey readiness — what works, what blocks (2026-06-07)

Where the system actually stands going into the survey, synthesized across the spring
deployments and the 2026-06-05 runs ([`#228`](https://github.com/rolker/unh_echoboats_project11/issues/228) bag analysis).

**Line-following loops — SOLVED ([`nav#66`](https://github.com/rolker/unh_marine_navigation/issues/66)).**
This *was* the #1 survey blocker (the boat over-corrected into full 360° loops on planner
paths). Fixed by [`PR #72`](https://github.com/rolker/unh_marine_navigation/pull/72)
(CrabbingPathFollower: progress-preserving localization + pure-pursuit look-ahead +
tunable/clamped yaw) + [`PR #70`](https://github.com/rolker/unh_marine_navigation/pull/70)
(viz recolor), both merged 2026-06-05. **On the 2026-06-05 deployment (run with these fixes)
the boat ran the survey line cleanly** — on the genuine survey line (`pattern0001/line0`)
cross-track error held median **0.19 m, 89 % within 1 m, no loops** (analysis:
`~/data/logs/analysis/2026-06-07_issue228/`). The pure-pursuit look-ahead + clamped yaw absorb
the jumpy planner output downstream — `cmd_vel_nav` yaw still spikes to ±3 rad/s but
`cmd_vel_smoothed` clamps it to ±1.0. (An earlier read of large XTE on "trackline0002" turned
out to be a **~280 m transit *to* the line**, not line-following — the global planner routing
to the goal through the pier's chart-inflation costmap, i.e. nav#63, which is **moot at the
lake** with no S57; not a survey-line churn.) nav#66 stays OPEN only for the **nav#5 regression
test**. **Regression watch:** confirm clean tracking holds across full survey patterns
(harvest `pid_state`).

**Safety floor — CA helm gate validated on water ([`nav#64`](https://github.com/rolker/unh_marine_navigation/issues/64)).**
The marine CA safety node replaced the nav2 Collision Monitor as the **default helm gate**;
its mechanism was confirmed on the 2026-06-05 run: idle passthrough is exact, slowdown
throttles speed while **preserving yaw** (anti-deadlock), the stop box drives a
**reverse-assisted brake** (clamped −0.5 m/s), and **yaw is cancelled during reverse**
(`cancel_yaw_during_reverse=true`, 350/350 samples). **Gaps:** no clean *high-speed
autonomous* obstacle pass yet (interventions were ≤~1.5 m/s); and a hover interaction —
[`nav#73`](https://github.com/rolker/unh_marine_navigation/issues/73) (gate chatters STOP
during an autonomous hover, so station-keep can't settle).

**Yaw governor — resolved, with a watch.** The velocity_smoother yaw-accel cap was
field-tuned ±0.5 → **±3.0 rad/s²** (deliberate — ±0.5 lagged the path-follower PID → line
hunting), and the value is locked by `test_param_compose` ([`seafloor#45`](https://github.com/rolker/seafloor_echoboat_project11/issues/45)); the 2026-06-05 bag confirms 3.0 is
enforced. **Watch:** ±3.0 re-opens the deployment-197 snap-roll — sharp autonomous yaw
reversals rolled the hull up to **~22°** (sub-197 ~30°, but real). If a reversal rolls the
hull on a survey, back off toward ±1.5. Harvest SBG roll vs yaw-rate.

**Autonomy posture — fallback, not relied on.** Turning a camera image into a *reliable*
costmap is hard (#201 mooring-field regression); autonomous obstacle avoidance stays the
**fallback** with students aboard: vigilant camera-watching + pre-planned exclusion zones +
drilled manual / RC takeover. The CA reflex + helm gate are the safety floor under that,
not a substitute for it.

**Sensors / hydro data — student-led this week.** M3 + SBG + SVS pipeline is live (SBG nav
and AML SVS `sound_speed` healthy in the ROS bags). The hydrographic data-quality side —
sonar / QINSy / offsets / datum — is the **students' focus during class week and lives
outside GitHub**, so it is not tracked as dev work in this roadmap; QINSy verifies
survey-data quality, not the ROS bags. (Dev's parallel sonar work is the *display* side —
see *Sonar coverage surfaces in CAMP* under Active threads.)

## Harvesting production data — regression shake-out (the method)

The boat is controllable; the real near-term risk is **what regressions are hiding in a
stack that changed a lot in the last two weeks** and has only had the 2026-06-05 shakedown:
the CA helm gate (nav#64), the nav#66 line-following fixes, the velocity_smoother re-enable
+ ±3.0 yaw-accel, and the hover / station-keep changes. With no dedicated experiment time
(production), we shake these out by **harvesting the bags that real survey / teaching runs
generate** — make sure the topics are recorded, then mine them for anomalies. The job shifts
from "schedule a test" to "make sure it's recorded, then mine the bag."

| Recently changed — watch for regressions | Generated by | Harvest from |
|---|---|---|
| Line-following holds across full patterns (nav#66 fresh fix) | survey lines + apron turns | `FollowPath/pid/pid_state`, `cmd_vel_nav`, `cmd_vel_smoothed`, `plan` |
| CA gate at survey speed (Goal-1 gap) / hover-stop ([`nav#73`](https://github.com/rolker/unh_marine_navigation/issues/73)) | normal autonomy + station-keep | `collision_monitor_state`, `cmd_vel_smoothed`, `piloting_mode/autonomous/cmd_vel` |
| Snap-roll on sharp reversals (yaw ±3.0) | any sharp autonomous yaw reversal | SBG `ekf_quat` (roll) + `imu_data` (gyro) vs `cmd_vel_smoothed` |
| Mid-line resume / redirect ([`nav#58`](https://github.com/rolker/unh_marine_navigation/issues/58) open; nav#35 fresh fix) | operators overriding mid-line | `behavior_tree_log`, `plan`, heartbeat |
| Turning-limit / undulation ([`#164`](https://github.com/rolker/unh_echoboats_project11/issues/164)) | sustained clean survey lines | `pid_state` (XTE), odom |
| OTH link at lake scale ([`#130`](https://github.com/rolker/unh_echoboats_project11/issues/130)) | surveys run OTH from shore by default | `udp_bridge` stats, operator bag size |

**Recording is now load-bearing.** A production run that doesn't record these topics can't
answer the question it would otherwise have answered, and there's no re-run. Confirm the
bag-recording config captures the controller-internal topics (the sim-recorder gap behind
[`marine_simulation#62`](https://github.com/rolker/unh_marine_simulation/issues/62) is the
same class of risk on the boat). Reference harvest: `~/data/logs/analysis/2026-06-07_issue228/`
(the #228 June-5 analysis). *(Hydrographic data quality — sonar / QINSy / offsets / datum —
is student-led during class week and lives outside GitHub; it is not tracked as dev work here.)*

## Line-following loops — diagnosis (historical — 2026-06-04; SOLVED 2026-06-05)

> **Resolved.** This was the #1 survey blocker; the fixes landed
> ([`PR #72`](https://github.com/rolker/unh_marine_navigation/pull/72) / [`#70`](https://github.com/rolker/unh_marine_navigation/pull/70),
> merged 2026-06-05) and the boat ran lines cleanly on the 2026-06-05 deployment (see
> *Survey readiness* above). Kept for the diagnosis record; nav#66 stays open only for the
> regression test (nav#5).

**The #1 problem to solve: the boat over-corrects into full 360° loops while
line-tracking, especially on planner-generated paths —
[`nav#66`](https://github.com/rolker/unh_marine_navigation/issues/66).** This is a
**survey blocker**: a boat that loops cannot run survey lines, transit, or return.

Unlike [`nav#63`](https://github.com/rolker/unh_marine_navigation/issues/63) (the
pier-inflation weave, which is **location-specific and likely moot at the lake** — no
S57 coverage), nav#66 is a **cross-track control instability that travels with the
boat**. It will show up on Lake Massabesic's planner transit/survey paths too, so it
cannot be sidestepped the way nav#63 can.

Mechanism (2026-06-04 bag analysis, `~/data/logs/bizzyboat/2026-06-04T13-43-04+00-00`):
the cross-track PID commands yaw **3–4× beyond the hull's turn capability** → undamped
overshoot / limit cycle that closes into full 360s at speed. It's a **synergy** of two
operating-point changes — (a) the yaw-rate ceiling raised **0.5 → 1.0 rad/s** (set from
the hull's real capability), which removed the amplitude cap that kept the latent
overshoot to a weave; and (b) **jumpy planner reference paths** (short, curved, replanned
every ~15 s — a new path every second at one point — with ~5 m discontinuous cross-track
steps on segment re-index) that drive the PID to saturation. The gains are tuned for the
**old** operating point (low ceiling + smooth fixed survey lines).

Fix directions (see nav#66): retune / add damping + anti-windup to the cross-track PID;
cap survey yaw-rate separately from the capability backstop; reduce planner reference
churn (replan hysteresis / path continuity). Add a regression test (nav#5).

> This **supersedes the earlier "line-following held sub-metre" optimism** for
> *planner-path* following — clean sub-metre tracking held only on **straight, fixed
> survey lines at the old 0.5 ceiling**. On planner paths at the 1.0 ceiling it can go
> fully unstable.

## Pre-freeze reality check (historical — 2026-06-02, post-#201)

> **Superseded by *Mode* / *Survey readiness* above (2026-06-07).** Kept for the
> record of how the must-finish list stood entering the freeze. The data-quality
> #138 note, the #205 outcome, and the nav#63-is-moot-at-the-lake reasoning remain
> accurate; the "must finish before the freeze" framing does not — we are now in
> production and harvesting, not finishing a sprint.

With ~2 boat-days left before the freeze, #201 (2026-06-01) reset the
must-finish list. This section supersedes the now-stale per-theme "Must finish
before June 4" optimism below and the Appendix A sizing snapshot.

> **Schedule update (2026-06-03):** the freeze moved June 4 → **June 8** (see
> Forcing function). The "~2 boat-days left" above was the 2026-06-02 count;
> there are now **two more pier days (June 4–5)** on top of the June 3 day, so
> the must-finish list below gets more on-water time — but the June 8 → 15
> student-training / survey-setup window is correspondingly tighter (4–5 days).

**Accepted as fallback — NOT must-finish:** autonomous obstacle avoidance.
*Turning a camera image into a reliable costmap is hard* — costmap delivery
([`nav#56`](https://github.com/rolker/unh_marine_navigation/issues/56)) and the
avoider ahead-replan ([`nav#57`](https://github.com/rolker/unh_marine_navigation/issues/57))
are unsolved offline-tuning problems, not 2-day fixes. Students operate with the
**fallback**: vigilant camera-watching + exclusion zones + manual override
(drilled). See *Surface-obstacle awareness → Planning path regression*.

**Real must-finish (priority order):**
1. ~~**#138 FCU reconfig + tide/chart-datum validation** (boat day) — data quality~~ — **largely delivered, demoted.** FCU `EK3_SRC1_POSZ=3` + the chain fix are in (see [`#138`](https://github.com/rolker/unh_echoboats_project11/issues/138) detail below). The ROS `tide_estimate`/datum chain is **costmap-only** (Nav2 `map_tide`), **NOT** hydrographic data — survey data is collected via QINSy outside ROS, with students verifying lever arms/offsets. The residual ≤~0.5 m datum-reference offset is a **costmap-only, low-priority** follow-up, not a data-quality must-finish.
2. **One clean survey run** — validate what works (line-following held sub-metre on #201) and characterize mid-line resume ([`nav#58`](https://github.com/rolker/unh_marine_navigation/issues/58)) / mission re-send ([`nav#35`](https://github.com/rolker/unh_marine_navigation/issues/35)).
3. **Operator perception display ([`unh_marine_autonomy#127`](https://github.com/rolker/unh_marine_autonomy/issues/127)) + document the costmap-delivery hack ([`nav#56`](https://github.com/rolker/unh_marine_navigation/issues/56))** — the fallback depends on operators *seeing* clearly.
4. **[`#18`](https://github.com/rolker/unh_echoboats_project11/issues/18) student deployment guide** (boat-free) — class-blocking.
5. **Fallback SOP** — manual-override / RC drill + exclusion zones, practised with students.

Binding constraint = boat days (serial, weather-dependent). With #1 largely
delivered, the final pre-class boat day centers on **#2 (clean survey validation)
+ OTH** ([`#130`](https://github.com/rolker/unh_echoboats_project11/issues/130));
#3–5 proceed off-water in parallel. Boat-day checklist pre-staged at
[`#211`](https://github.com/rolker/unh_echoboats_project11/issues/211).

**#205 update (2026-06-02 — UNH-pier shakedown).** Must-finish #2 (clean survey
run) **attempted, not met.** Line-following hunting was fixed on the water
(velocity_smoother yaw-accel ±0.5→±3.0, [`seafloor#38`](https://github.com/rolker/seafloor_echoboat_project11/issues/38)),
but a **persistent swerving blocks "clean"** — root-caused to the avoider-in-loop
(#206) weaving the line along the charted pier's 150 m inflation gradient
([`nav#63`](https://github.com/rolker/unh_marine_navigation/issues/63), fix open).
**This is the new blocker for #2.** On the plus side, the **first on-water
autonomous avoidance** worked (routed around a moored sailboat), and
costmap-over-bridge to CAMP ([`nav#56`](https://github.com/rolker/unh_marine_navigation/issues/56)/PR #61)
validated — but a survey-speed near-miss
([`nav#64`](https://github.com/rolker/unh_marine_navigation/issues/64)) reinforces
**avoidance stays the fallback (low-speed-only + manual override)**, not a
must-finish. OTH ([`#130`](https://github.com/rolker/unh_echoboats_project11/issues/130))
still untested. Sensor/sonar readiness met for the teaching goal.

**nav#63 is location-specific — likely moot at the lake.** The swerving is driven by
the charted pier's S57 inflation gradient; Lake Massabesic has **no S57 coverage**, so
the `chart_layer` is empty there and the avoider returns zero deviation (straight lines).
So nav#63 is **not a fix-before-freeze blocker**. For clean-survey validation *at the
pier* (final prep day, [`#211`](https://github.com/rolker/unh_echoboats_project11/issues/211)),
set `FollowPath.obstacle_avoidance_weight=0` live on `controller_server` to sidestep it.

## Active threads (have task issues)

Cross-references — the roadmap is not the source of truth for any
specific task; the linked issue is. Listed here so the threads are
visible from one place.

### Sensor payload integration (M3 + SBG + SVS on mercat)

**Verify (production readiness):**
- AML SVS bridge — **RESOLVED on #173 (2026-05-26)**: after the #160 all-NUL regression, the probe produced valid in-water sound speed (~1490 m/s, 98.8% valid, median 1489.9); the all-NUL behavior did not reproduce (`minicom` confirmed flow pre-deploy). [`#163`](https://github.com/rolker/unh_echoboats_project11/issues/163) **kept open as a watch item** for a few more deployments (minor ~1.2% intermittent zero-dropouts, mostly early-run settling).

**Resolved since 2026-05-22:**
- [`unh_echoboats_project11#163`](https://github.com/rolker/unh_echoboats_project11/issues/163) — AML SVS all-NUL. **No longer blocking — resolved on #173 (2026-05-26)** (see Verify-before-June-8 above): the probe now delivers valid in-water SV, which M3 needs for correct depth.

**Open decision (decide before June 8):**
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
- Mercat NTP — **verified textbook-healthy 2026-05-22** (#160 dev log). `ntpq.exe -pn` is now in-class teaching content for students.

### Sonar coverage surfaces in CAMP (camp2-enabled) *(new — 2026-06-07)*

Pointer-thread (detail lives in the linked repos). **Goal:** display **MBES and sidescan
coverage surfaces** in CAMP for the operator, leveraging camp2's better grid views +
colormap support. This is dev's active parallel work during class week (while students run
the boat); it is the *display* counterpart to the student-led hydro-data work above.

- **MBES → CUBE surface — working in rviz.** M3 bridge + cube bathymetry is wired into the
  BizzyBoat perception launch ([`#225`](https://github.com/rolker/unh_echoboats_project11/issues/225), **closed**) and produces a clean gridded surface in rviz. **Next:** get it into CAMP
  and make it robust.
- **On-disk persistent grid store** — [`unh_marine_autonomy#86`](https://github.com/rolker/unh_marine_autonomy/issues/86) (persistent multi-source bathymetric data store using GGGS,
  **OPEN**). The durable "save the survey grid to disk" mechanism the CUBE surface feeds;
  GGGS grid-index bugs already fixed ([`#77`](https://github.com/rolker/unh_marine_autonomy/issues/77), closed).
- **Sidescan feed** — Garmin GCV-10 driver ([`garmin_sidescan#15`](https://github.com/rolker/garmin_sidescan/issues/15) / [`#20`](https://github.com/rolker/garmin_sidescan/issues/20)). 2026-06-05
  test (`~/data/logs/bizzy_sidescan/bag_2026-06-05T14.07.32_sidescan_raw`): data flows but
  **decodes incorrectly**, and the **rqt waterfall viewer has performance issues** — two
  separate efforts (protocol decode in `garmin_sidescan`; perf in the rqt waterfall /
  `marine_colormap` GPU path). May be solid by the next water day, or at least better
  instrumented to troubleshoot.
- **Sidescan persisted coverage grid** — wanted, **not yet filed** (a sidescan analogue of
  #86's on-disk grid).
- **Display foundation** — camp2 ([`camp#59`](https://github.com/rolker/camp/issues/59) / [`PR #60`](https://github.com/rolker/camp/pull/60)) grid views + shared
  [`marine_colormap`](https://github.com/rolker/marine_colormap) colormap support.

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

**Reflex collision avoidance — validated on-water 2026-05-26 ([#173](https://github.com/rolker/unh_echoboats_project11/issues/173)).** Independent of the costmap path: the segmentation → `collision_monitor/pointcloud` → Nav2 Collision Monitor reflex (`perception#17` + [`#170`](https://github.com/rolker/unh_echoboats_project11/issues/170) Phase A/B) was exercised on the water and **reliably slows + stops for large/extended obstacles** (a floating breakwater; slowdown ≈0.3×/stop gating correct up to ~5 kt approach, no contact). **Known gap — ~2 m forward near-blind zone**: small obstacles (a buoy) vanish from the cloud inside ~2 m and the boat resumes; large/extended obstacles sustain the stop. Since small obstacles (mooring balls) are the recurring-collision hazard, the motivating problem isn't fully solved — **handle the small-obstacle case as part of the segmentation→costmap evolution** (spatial obstacle memory + planner route-around), not an urgent reflex patch. Operator awareness of CA state → [`#183`](https://github.com/rolker/unh_echoboats_project11/issues/183) (CAMP map overlay of reflex obstacles + slowdown/stop polygons + gating state, plus an annunciator row). (#186 added concrete motivation — the dense-buoy CA-churn where the operator couldn't see what CA was reacting to.)

**Planning path — first on-water close (2026-05-28, [#186](https://github.com/rolker/unh_echoboats_project11/issues/186)).** The autonomy planner **did route around camera-detected obstacles** for the first time — it threaded a path between a sailboat and a buoy seen only by the OAK cameras (segmentation → costmap → planner). The section's premise above ("the planner has no awareness") is now refuted for **large / solidly-marked** obstacles: the loop closes, and on-water acceptance evidence for the #7 end-state is posted on [`unh_marine_perception#7`](https://github.com/rolker/unh_marine_perception/issues/7). **Two gaps remain** — (a) *marking robustness*: small/dim targets under dark skies mark poorly (the strict argmax gate scores marginal-red as a *miss*, plus segmentation false-negatives in low contrast) → [`unh_marine_perception#22`](https://github.com/rolker/unh_marine_perception/issues/22) (gate + graded vote), [`unh_marine_perception#23`](https://github.com/rolker/unh_marine_perception/issues/23) (core export), offline **tuning tool** [`marine_perception_tools#1`](https://github.com/rolker/marine_perception_tools/issues/1); (b) *planning in clutter*: the boat got stuck / orbited in dense-buoy geometries (CA behaved correctly — the planner drove into spots it couldn't gracefully escape). **Planning quality in clutter — not CA tuning — is the next priority.**

**Planning path — major regression on a mooring field (2026-06-01, [#201](https://github.com/rolker/unh_echoboats_project11/issues/201)).** #186's "loop closes" optimism does **not** generalize. Against a 3-buoy mooring field the planner **never autonomously avoided** the buoys, via two distinct mechanisms now filed: (a) the costmap was **never reliably delivered/maintained** — operator-side delivery is subscriber-gated lazy publish ([`unh_marine_navigation#56`](https://github.com/rolker/unh_marine_navigation/issues/56)) and the controller logged `Costmap timed out waiting for update` ×14; and (b) the corridor avoider **only re-plans behind the boat, never ahead** ([`unh_marine_navigation#57`](https://github.com/rolker/unh_marine_navigation/issues/57)). **Net takeaway: turning a camera image into a reliable costmap is hard — the planning path is NOT class-ready.** For June 8 the **fallback (vigilant camera-watching + exclusion zones + manual takeover — ~20 USB-controller takeovers were needed on #201)** is the operating plan; autonomous obstacle avoidance is **not** to be relied on with students. (Reflex CollisionStop did fire on buoys, but light contact still occurred.)

**Priority for June 8** (display path):
- [`rolker/unh_marine_perception#6`](https://github.com/rolker/unh_marine_perception/issues/6) — `SeaSurfaceLayer::matchSize()` segfault. **CLOSED** ([`PR #11`](https://github.com/rolker/unh_marine_perception/pull/11)). Multi-instance variant tracked separately as [`#14`](https://github.com/rolker/unh_marine_perception/issues/14) — also **CLOSED**; durably validated under in-water, low-battery, sunset/low-light conditions across the full 2h 43m mission window during #160 (2026-05-22). No segfaults observed; 4-instance `sea_surface_layer` is production-ready for the class.
- [`rolker/unh_marine_perception#7`](https://github.com/rolker/unh_marine_perception/issues/7) — end-to-end OAK → costmap validation. Blocked on #6. End state for display-first: "a costmap is being published, populated by segmentation, and the operator can see it." **On-water close on #186 (2026-05-28)** — the planner routed around camera-detected obstacles; screengrab acceptance evidence posted on the issue.
- [`rolker/unh_marine_autonomy#127`](https://github.com/rolker/unh_marine_autonomy/issues/127) — operator-side perception display over the bridge. **Broadened 2026-05-26** from costmap-only to *all relevant perception topics* (costmap, costmap_updates, reflex pointcloud, segmentation) after hit-and-miss rviz/CAMP display on #173. Leading costmap idea: **send as a compressed image** (camera streams deliver 92–99% vs raw OccupancyGrid ~1–2%, see [`#68`](https://github.com/rolker/unh_echoboats_project11/issues/68)); reflex pointcloud needs QoS-matching (best-effort); `costmap_updates` companion was missing from the bridge `topics_list`.
- Per-camera `frame_ids` + URDF-aligned `<label>_optical_frame` default via [PR #9](https://github.com/rolker/unh_marine_perception/pull/9) (2026-04-28). *(Done.)*

**Defer past June 8** (planning path):
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

**Production-critical — status + harvest:**
- [`rolker/unh_marine_navigation#35`](https://github.com/rolker/unh_marine_navigation/issues/35) — **mission re-send mid-line doesn't take effect.** Operator Executes a new trackline; the heartbeat shows it but the boat keeps following the *old* line's path (workaround: clear + resend). Root-caused on #173: the BT latches the path — `SetPathFromTask` runs once behind a memory `Sequence`, and survey-line re-entry is gated on task *type*, not *id*, so a same-type (`survey_line→survey_line`) switch never halts/recomputes `FollowPath`. **Class-significant** — students will hit this redirecting the boat mid-mission. Fix: gate re-entry on task id (or preempt-cancel the running nav). Normal sequential surveys are unaffected. Full analysis: [`docs/analysis/2026-05-26/findings.md`](analysis/2026-05-26/findings.md) §8. **CLOSED** ([`PR #36`](https://github.com/rolker/unh_marine_navigation/pull/36) merged) — id-gated re-entry landed. *(Distinct: the #186 hover re-send failure was traced to a **CAMP-side command-send gap** — the commands were never published — not this BT task-latch family.)* **Harvest from production:** confirm on a real run that an Execute of a new same-type line now redirects the boat without the clear+resend workaround (`behavior_tree_log` + `plan` + heartbeat).
- [`rolker/unh_marine_navigation#58`](https://github.com/rolker/unh_marine_navigation/issues/58) — **mid-line resume after a goto override re-runs the line from the start** instead of resuming from the boat's current position (on-water regression of the merged #52/#53, which was sim-validated). Updatable goto re-target itself worked; only the resume failed. **Class-significant** — students will override mid-line and expect resume, not a full re-run. Candidate: `RobotOnPath` 5 m tolerance missed under heavy crab. New on #201 (2026-06-01).
- [`rolker/unh_marine_navigation#73`](https://github.com/rolker/unh_marine_navigation/issues/73) — **CA helm gate chatters STOP during autonomous hover** — station-keep can't settle (the boat is near-stationary so the reflex cloud keeps clipping the stop polygon → STOP↔release ~every 0.5–1 s). Filed from the 2026-06-05 (#228) bag analysis. **Class-relevant** — students will hover/station-keep near features. Related: #67 (stalled-at-obstacle recovery), #50 (task-BT redesign). Harvest from production: `collision_monitor_state` + `piloting_mode/autonomous/cmd_vel` during GUIDED hover.
- ~~[`rolker/unh_marine_navigation#23`](https://github.com/rolker/unh_marine_navigation/issues/23) — TF extrapolation on multi-line survey goals.~~ **RESOLVED / CLOSED** — no recurrence across recent multi-line surveys (incl. #201, no TF-extrapolation errors in boat-side rosout); operator confirms many clean multi-line surveys since with no recurrence. #23 closed; not a must-finish.

**Investigate — harvest from production:**
- [`rolker/unh_marine_navigation#19`](https://github.com/rolker/unh_marine_navigation/issues/19) — costmap-update timeout too aggressive at 1.0s. **Confirmed real on #201 (2026-06-01)**: `Costmap timed out waiting for update` logged ×14 (controller_server, 14:32–16:20) while the boat was working the mooring field — promote from "investigate" to a real reliability factor in the costmap/avoidance failure. Tied to the costmap-delivery mechanism ([`unh_marine_navigation#56`](https://github.com/rolker/unh_marine_navigation/issues/56)).
- **Boat-side bathy costmap — our own bathymetry replaces the chart layer.** Lake Massabesic
  has no S57 ENC coverage, so the Nav2 `chart_layer` is empty there — no depth-derived
  "don't-go-shallow" data. **Plan:** feed *our own collected bathymetry* into the costmap as
  the chart-layer replacement, and **refine it as we survey**:
  - **Start crude** — a contour-derived bathy map (NHGranIT depth contours) gives a first
    "shallow here" layer to launch with.
  - **Refine with collected data** — the **M3 → CUBE surface** (now working in rviz,
    [`#225`](https://github.com/rolker/unh_echoboats_project11/issues/225)) persisted to the
    **GGGS on-disk grid store** ([`unh_marine_autonomy#86`](https://github.com/rolker/unh_marine_autonomy/issues/86)) becomes the depth source as coverage builds.
  - **Closes a loop:** the survey *produces* the bathymetry that improves the costmap that
    guides the next survey. Ties into the *Sonar coverage surfaces in CAMP* thread (same
    CUBE/GGGS pipeline, different consumer — costmap vs. operator display).

  Borrowable plumbing in `s57_tools` / `marine_charts` for the depth-grid → costmap layer.
  *(Flip side of nav#63: at the pier the `chart_layer` inflation **caused** the weave; at the
  lake the gap is the opposite — no layer at all — so our own bathy is the fix, not the
  problem.)* Confirm whether Roland's "other computer" contour work exists; then link or open
  an issue.
- **Turning-limit validation — STILL PENDING after #173 (2026-05-26).** The two field-untested changes (helm yaw cap 0.5→1.0 rad/s, [PR #172](https://github.com/rolker/unh_echoboats_project11/pull/172) / #124 §2; planner min turning radius 3.0→1.5 m) were **not assessed** — #173 went to collision-avoidance testing. They were exercised only incidentally in transit-to-line-start planning (individual tracklines, no survey-pattern apron turns), so the tight-apron case the 1.5 m radius most affects is still untested. `pid_state` (cross-track-error) recording **landed ✓** on #173. **Harvest from production:** the first clean student survey lines (and survey-pattern apron turns) are exactly the data this needs — capture `cmd_vel_*` + `pid_state` + odom and assess the 1.5 m radius / 1.0 ceiling on a real pattern. (Still pending through #186/#201 — both were buoy/CA/perception days with no clean survey lines; turning behaviour went unobserved.)
- **velocity_smoother re-enabled in the cmd_vel chain — [`rolker/seafloor_echoboat_project11#36`](https://github.com/rolker/seafloor_echoboat_project11/issues/36) (DONE, merged 2026-06-02).** The smoother is back in the active path and `lifecycle_nodes` (`cmd_vel_nav → velocity_smoother → cmd_vel_smoothed → [helm gate]`), so the survey **accel / yaw-rate limiting** (#124 §2) is active again. The 2026-06-05 bag confirms it enforces the yaw-accel cap. Yaw-accel was field-tuned ±0.5 → **±3.0 rad/s²** (`d35a795`; locked by `test_param_compose` in [`seafloor#45`](https://github.com/rolker/seafloor_echoboat_project11/issues/45)) — **not** a regression (closes the #228 Goal-3 question). **Watch (harvest from production):** ±3.0 re-opens the deployment-197 snap-roll — sharp autonomous yaw reversals rolled the hull up to ~22° on 2026-06-05 (sub-197, but real). Back off toward ±1.5 if a sharp reversal rolls the hull on a survey.

**Maintenance mode (deferred):**
- [`unh_echoboats_project11#96`](https://github.com/rolker/unh_echoboats_project11/issues/96) — BizzyBoat-specific nav2 params override (decouple from seafloor echoboat defaults). Not critical for single-boat ops; promote when joint Bizzy + Izzy ops come into scope.
- [`unh_echoboats_project11#164`](https://github.com/rolker/unh_echoboats_project11/issues/164) — CrabbingPathFollower SE-undulation. **Closed** — undulation real (~1.6 m median RMS) but SE-only asymmetry unconfirmed. `pid_state` recording **now landed ✓** (#173), but the #173 dig was **inconclusive**: it was a collision-test day with no sustained clean survey line — clean stretches held sub-meter XTE, the large excursions were collision-stop/re-acquisition artifacts. **Needs a clean-survey deployment** to characterize undulation. Reopen on recurrence. **#201 (2026-06-01)**: cleanest read yet — clean stretches |XTE| median **0.47 m** (71% ≤ 1 m) held under heavy crab; large excursions still avoidance/manual-takeover artifacts. Still no fully-clean sustained survey line.

**Done:**
- [`rolker/unh_marine_navigation#24`](https://github.com/rolker/unh_marine_navigation/issues/24) — wire BT `target_speed` → `/speed_limit`. Field-implemented during #160 (`task.speed=1 kt → cmd_vel.linear.x=0.515 m/s`); **CLOSED 2026-05-25**, field commits reconciled to origin via [`PR #27`](https://github.com/rolker/unh_marine_navigation/pull/27).
- [`rolker/unh_marine_navigation#33`](https://github.com/rolker/unh_marine_navigation/issues/33) — Hover overshoots station on engagement. Was opportunistic/Defer; **MERGED 2026-05-27** ([`PR #34`](https://github.com/rolker/unh_marine_navigation/pull/34)) — restored the stop-point projection (`pos + v²/2a`) + optional live `point_at_target`. Cross-platform; on-water re-validation folds into the next clean-survey deployment. (Triggered a sibling sweep retiring the now-dead `hover.deceleration` param across the nav2 config repos: [`sim #61`](https://github.com/rolker/unh_marine_simulation/pull/61), [`ben #25`](https://github.com/rolker/ben_project11/pull/25), [`seafloor #31`](https://github.com/rolker/seafloor_echoboat_project11/pull/31).)

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

**Production-critical — status + harvest:**
- [`unh_echoboats_project11#138`](https://github.com/rolker/unh_echoboats_project11/issues/138) — `mru_transform` durable nav-input choice + FCU reconfig. **Substantive FCU change is only `EK3_SRC1_POSZ = 3`** (GPS), so the FCU EKF Z stops tracking atmospheric pressure. (Earlier brief drafts also called for an `EK3_GPS_OFFS_*` family — those params don't exist on ArduPilot Rover; the GPS antenna lever-arm goes through `GPS_POS1_*` only, which was already at the right values from #91.) Field-side revert to `mavros/global_position/raw/fix` is a workaround; FCU reconfig is the durable answer. **Status (2026-05-21)**: bench-side validation passed — `/global` altitude back in chart-datum band, `tide_estimate` plausible, suppression warnings gone — and `mru_transform` switched back from `raw/fix` → `/global` in field commit `f348f66`. In-water trackline validation didn't run (nav stack unhealthy — see [`#150`](https://github.com/rolker/unh_echoboats_project11/issues/150) topic 6); offline bag analysis pending in [`#150 topic 1`](https://github.com/rolker/unh_echoboats_project11/issues/150). **Status update (2026-05-22 bag review)**: gabby §9's initial "lever-arm double-count" hypothesis was superseded by gabby §10. The actual mechanism was a *missing* lever-arm: `mru_transform` was still consuming `raw/fix` (a 2026-05-19 field workaround) — and mavros publishes `raw/fix` as antenna altitude labelled `base_link`. Switching back to `/global` (field commit `f348f66`, now in this PR) restores correct base_link altitude in the chain. The §10 closure claim ("+0.03 m residual ✓ after ~0.7 m freeboard") is also revised — freeboard is actually ≤ ~0.22 m (sonar face at z=-0.22 m from base_link per URDF is "definitely submerged" per operator), so the residual against NOAA forecast is ~+0.5 m, not near zero. Candidate causes for the remaining ~0.5 m: geoid/datum reference mismatch (VDatum-at-pier vs NOAA-Fort-Point-station — both within mm at the pier, but NOAA forecast is referenced to the gauge's local zero), or unmodeled small offsets. **MLLW value from the bag is sound** (`chart_datum` node banner: −28.012 m at the pier on 2026-05-21, matching 2026-05-19 §13 to mm). #138's FCU-side change is delivered; chain-side fix is delivered; residual ≤ 0.5 m is a smaller follow-up (likely fits in [`#110`](https://github.com/rolker/unh_echoboats_project11/issues/110) scope or a new dedicated issue).

**Wrap-up / housekeeping:**
- [`unh_echoboats_project11#111`](https://github.com/rolker/unh_echoboats_project11/issues/111) — lever-arm / base_link contract. SBG half resolved live 2026-05-01; FCU half folds into #138's reconfig. Plan: fold the remaining FCU-side scope into #138's body, then close #111 with a pointer.

**Maintenance mode (deferred):**
- [`unh_echoboats_project11#110`](https://github.com/rolker/unh_echoboats_project11/issues/110) — URDF gap (SBG INS + GNSS antennas + IMU mounting). Becomes load-bearing when the camera-image → costmap pipeline ships (need accurate geometric placement for segmentation projection), but it's not on the critical path for the tide / chart-datum chain — which uses the position+altitude topics directly. Until then, documentation-correctness work that can live in maintenance mode.

**Done:**
- [`unh_echoboats_project11#112`](https://github.com/rolker/unh_echoboats_project11/issues/112) — record EKF3 streams. **CLOSED** ([PR #123](https://github.com/rolker/unh_echoboats_project11/pull/123) merged 2026-05-18).

### Power / endurance *(new — 2026-05-26, from #167)*

Battery/endurance characterized across the chained 2026-05-19 → 21 → 22 single charge cycle ([`#167`](https://github.com/rolker/unh_echoboats_project11/issues/167), **closed**). Durable reference: [`bizzyboat_power.md`](../bizzyboat_project11/docs/bizzyboat_power.md).

- **Field-ready output**: the **voltage ladder** (pre-launch resting-V go/no-go + in-mission loaded-V recovery ladder) is measured and reliable — use it for mission planning. All current / power / energy / endurance figures are **modeled (±~30 %)** — no current meter on this hull.
- **No battery swap** — BizzyBoat charges **in place**, so **recharge-to-full time between deployment days / cohorts is the binding cadence constraint** (not swap logistics). The recharge curve is still **uncharacterized** — measure a full charge at the next opportunity.
- **First measured charger-current datapoint (#186, 2026-05-28)**: ~6.2 A external-charger draw after a multi-day in-place charge (idle/maintenance load near full). No current meter on the hull, so charger-side readings are the only **measured** current we get — a real anchor for the otherwise-modeled charge side. Capture + power-model review: [`#196`](https://github.com/rolker/unh_echoboats_project11/issues/196).
- **Defer past June 8**: [`#88`](https://github.com/rolker/unh_echoboats_project11/issues/88) — PWM × current sweep, the precision unlock that removes the ±30 %. The field-ready voltage rules don't need it.

### Class-ready operator UI

The interactive surface (logbook, checklist, camera grid) is in
good-enough shape — Phase-1 plugins exist or the current config works,
and students can fall back to text editor / paper for the recording
parts. Documentation for student operators is the only must-finish.

**Production-critical — status + harvest:**
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

**Design thread — defer past June 8** *(surfaced 2026-05-21 from
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

### Documentation — keep the manuals current *(2026-06-07)*

Standing discipline, now load-bearing: the boat is in production with **students operating
from the manuals**, so the operator / student / field-season docs must track the system as it
changes. When a change lands that affects how the boat is operated — CA helm-gate behavior,
line-following, hover / station-keep, sonar displays, comms / OTH — update the relevant manual
in the same breath, not "later." A manual that lies to a student operator is worse than a
missing one.

The manual set:
- [`#18`](https://github.com/rolker/unh_echoboats_project11/issues/18) — student deployment guide.
- [`#202`](https://github.com/rolker/unh_echoboats_project11/issues/202) — BizzyBoat operator manual (student-facing).
- [`#219`](https://github.com/rolker/unh_echoboats_project11/issues/219) — 2026 BizzyBoat Field Season Guide.
- [`camp#61`](https://github.com/rolker/camp/issues/61) — CAMP user manual (operator-facing).
- [`unh_marine_autonomy#132`](https://github.com/rolker/unh_marine_autonomy/issues/132) — project11 marine-autonomy framework guide.

Changes the manuals should reflect *now*: the CA safety helm gate ([`nav#64`](https://github.com/rolker/unh_marine_navigation/issues/64)) as the default helm gate (slowdown + reverse-stop
behavior, and the hover-stop caveat [`nav#73`](https://github.com/rolker/unh_marine_navigation/issues/73)), the nav#66 line-following fix, and — as it ships — the sonar-coverage-in-CAMP work.

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

**Done — shipped before June 4** *(the class-blocking item + the whole small-wins batch landed; reconciled 2026-05-27 via #189)*:
- [`unh_echoboats_project11#162`](https://github.com/rolker/unh_echoboats_project11/issues/162) — Battery annunciator stayed green below `BATT_LOW_VOLT` (threshold→color mapping). The operator's safety contract. **CLOSED 2026-05-26** ([`PR #179`](https://github.com/rolker/unh_echoboats_project11/pull/179)).
- [`unh_echoboats_project11#171`](https://github.com/rolker/unh_echoboats_project11/issues/171) — operator annunciator **missing indicator rows**: battery-voltage-threshold, **sound-speed** (SV-failure), **FCU-system** (`mavros:System`). Field config added all three rows to `bizzyboat_operator_annunciator.yaml` (validated green on-panel); imported to `jazzy` via the 2026-05-26 wrap-up (commit `0cd42f5`, [`PR #182`](https://github.com/rolker/unh_echoboats_project11/pull/182)). Issue closed during the #189 reconciliation.
- [`unh_echoboats_project11#141`](https://github.com/rolker/unh_echoboats_project11/issues/141) — removed `diagnostic_aggregator` from operator launches (annunciator subscribes to `/diagnostics` directly). **CLOSED** ([`PR #146`](https://github.com/rolker/unh_echoboats_project11/pull/146)).
- [`unh_echoboats_project11#139`](https://github.com/rolker/unh_echoboats_project11/issues/139) — `output='screen'` → `output='both'` in BizzyBoat launches. **CLOSED**.
- [`unh_echoboats_project11#140`](https://github.com/rolker/unh_echoboats_project11/issues/140) — removed stale `bencloud` ping target. **CLOSED** ([`PR #148`](https://github.com/rolker/unh_echoboats_project11/pull/148)).
- [`rolker/ros2_network_monitor#23`](https://github.com/rolker/ros2_network_monitor/issues/23) — try/except + backoff for `mikrotik_monitor` / `teltonika_monitor` (silent-startup-crash shape). **CLOSED**.
- [`unh_echoboats_project11#97`](https://github.com/rolker/unh_echoboats_project11/issues/97) — salmon-side monitor nodes + `/diagnostics` recording. **CLOSED** ([`PR #109`](https://github.com/rolker/unh_echoboats_project11/pull/109)).

**Desirable, defer if needed:**
- [`rolker/camp#52`](https://github.com/rolker/camp/issues/52) — CAMP GUI froze twice during #160 ([`#166`](https://github.com/rolker/unh_echoboats_project11/issues/166), root cause **unconfirmed** — a GUI hang leaves no log trace). Deliverable is a *capture plan* (Qt-timer heartbeat + auto-backtrace-on-stall) so the next freeze self-documents. **Before June 8 if cycles allow, low priority**; workaround is solo `pkill camp` (rest of stack survives).
- [`rolker/ros2launch_session#5`](https://github.com/rolker/ros2launch_session/issues/5) — observability mode. Substantial implementation. Catches the lifecycle-abort + silent-process-death failure shapes as a general mechanism. Would close the biggest remaining observability hole, but the rest of the easy wins above already deliver most operator-visible value. Treat as stretch goal — if it ships before June 8 great, otherwise the workaround is documented manual checks at launch time + students drilled to recognize "I queued a goal and nothing happened" as a system problem requiring expert help.
- [`unh_echoboats_project11#142`](https://github.com/rolker/unh_echoboats_project11/issues/142) — host thermals as `DiagnosticStatus` (lm-sensors + NVMe SMART). Off-the-shelf package available; do if quick, defer if not.

**Future:**
- annunciator stale-stream indicator on `rqt_operator_tools`.
- topic-staleness layer via `topic_statistics` + aggregator analyzers (the analyzer module — doesn't require running the aggregator node).

### Network reliability under load *(new theme — 2026-04-27)*

2026-05-19 cross-deployment analysis ([`#144`](https://github.com/rolker/unh_echoboats_project11/issues/144) + [`udp_bridge#22`](https://github.com/rolker/udp_bridge/issues/22) comment thread) showed the bridge is in good operational shape: resend storms on wifi loss are by-design behavior, milder than 2026-05-01's worst, and stay within configured rate limits. The remaining items here are real but not class-critical — defer to maintenance mode unless one of them recurs during class prep.

**Track during class prep:**
- [`rolker/udp_bridge#10`](https://github.com/rolker/udp_bridge/issues/10) — bridge wedges when remote subscriber dies. Real bug; not observed during 2026-05-01 or 2026-05-19. If it surfaces during student-led ops it could be operationally bad, but track rather than promote unless it recurs.

**Maintenance mode after June 8:**
- [`rolker/udp_bridge#23`](https://github.com/rolker/udp_bridge/issues/23) — restrict resend response to requesting connection. Wire-format change (`connection_id` field). Modest impl, reduces resend amplification under loss. Filed 2026-05-20; `[PLAN]` PR [`#25`](https://github.com/rolker/udp_bridge/pull/25) merged 2026-05-21 (plan document only — implementation still pending).
- [`rolker/udp_bridge#20`](https://github.com/rolker/udp_bridge/issues/20) — stats-timer publication stalls. Made operator panels blind for 1h17m during 2026-05-19 (data plane unaffected). Stats are observability — not data path. Less urgent than the observability theme's main vehicle.
- [`rolker/udp_bridge#21`](https://github.com/rolker/udp_bridge/issues/21) — "after N attempts" value varies 5/6/1. Counter interpretation question. Investigate when convenient.

**Future (post-June-8):**
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
OTH-specific work below is therefore **survey-priority**, not deferred.

> **Survey-campaign framing (2026-06-03):** OTH capability is the through-line
> between both 2026 campaigns — the June lake survey is OTH from shore, and the
> **potential August OTH survey** would lean on it even harder (likely
> larger-scale / longer-range). The June survey still drives the near-term
> priorities below; the August campaign is a **horizon goal** that reinforces
> this theme rather than re-ordering it — revisit OTH scaling after the June survey.

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

**Production-critical — status + harvest:**
- [`unh_echoboats_project11#130`](https://github.com/rolker/unh_echoboats_project11/issues/130) — field validation of OTH Starlink-only operation including a completed survey. The lake survey IS the test — but going in without a controlled validation first is the kind of risk we don't take with students aboard. Schedule a deliberate OTH validation between now and June 15.
- **Topic-budget cull** — operating OTH at lake scale is exactly the saturation scenario from 2026-05-01. Identify which topics dominate the link, cull or rate-limit accordingly. Don't wait for a future OTH attempt to re-hit the 30–60 s latency episodes.
- **Low-bandwidth status fallback** — text/heartbeat/minimal-telemetry path that survives when the full topic stream doesn't. May overlap with [`#145`](https://github.com/rolker/unh_echoboats_project11/issues/145)'s safety-critical-pinned-to-cell concept. 2026-05-01 worked around this with manual gabby SSH; the class scenario needs the fallback in the operator UI.
- **VPN-path indicator** (Starlink vs. cellular vs. WiFi) — operator awareness gap; on 2026-05-01 we lost significant diagnostic time guessing which path was carrying traffic. See [`#124`](https://github.com/rolker/unh_echoboats_project11/issues/124).
- **"OTH mode" — annunciator with range awareness** — operator-toggled (or auto-by-path-detection) mode that quiets the WiFi WARN cascade when the boat is intentionally past WiFi range. Implementation of the existing `feedback_wifi_disconnect_not_an_error` principle ("drops are data, not ERROR; let downstream consumers apply context-aware logic"). Surfaced during 2026-05-21 OTH run where WiFi WARN noise crowded out useful annunciator visibility. Not yet promoted to a focused issue — wants a brief design conversation: where does the mode-state live (CAMP toggle vs. auto-detect from Starlink-active vs. RC-out-of-range), and which diagnostics participate in the quiet-list. Small implementation once scoped.

**Maintenance mode (deferred):**
- **Bench stress-test rig** — synth topics + mininet + CAMP-stub harness so the next saturation question can be answered at the desk. The lake survey itself will produce real-water OTH data; pre-survey budget is better spent on the topic cull and the fallback channel. Revisit post-survey. See [`#124`](https://github.com/rolker/unh_echoboats_project11/issues/124).
- **RC mode-switch fringe-range hardening** — RC handheld stays at the operator station; controller doesn't follow the boat to OTH range. Captured in memory `project_bizzyboat_rc_mode_switch_at_fringe_range.md` for future relevance.

### Autonomy robustness *(new theme — 2026-05-01)*

The 2026-05-01 deployment surfaced a real BT design issue (now filed)
and validated the GUIDED stale-setpoint failsafe.

**Production-critical — status + harvest:**
- [`unh_marine_navigation#25`](https://github.com/rolker/unh_marine_navigation/issues/25) — `SkipUnknownTaskType` catchall in `run_tasks.xml` silently marks tracklines done when a matching subtree's execution fails (e.g. `FollowPath` ABORT). Forensic match for the 2026-05-01 15:09 HOLD episode. Class-significant: a silently-marked-done line at OTH range means the operator sees a "complete" trackline and the boat parked in `done_hover` with no alert — coverage holes show up only post-mission. **In progress** — implementation code-complete (Switch dispatch + marine RecoveryNode), in review 2026-05-27 ([`PR #37`](https://github.com/rolker/unh_marine_navigation/pull/37)).

**Track during class prep:**
- **Broader BT review of `marine_nav_bt_task_navigator/behavior_trees/run_tasks.xml`** — the catchall issue (`#25`) is one concrete failure mode; the tree has other shape choices a non-BT-native author may have made differently (e.g. nested `RetryUntilSuccessful num_attempts=3` around `Sequence`, `ReactiveFallback` semantics with stateful subtrees, multiple `_autoremap="true"` blackboard scopes, `KeepRunningUntilFailure`+`Inverter` patterns). Worth a Nav2-BT-experienced second pass before June 8. *(No issue yet — promote to one if the review surfaces concrete findings.)*

**Done:**
- **GUIDED stale-setpoint HOLD verified working** — when `cmd_vel` publication stops, FCU correctly enters HOLD. Confirmed Nav2-crash failsafe behaves as intended on 2026-05-01.

## Deferred / lower priority — no current issue

These items are explicitly not on deck. Promote to a task issue when
they become relevant.

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
- **In production mode (June 2026+):** the boat isn't free for dedicated
  tests, so open questions advance by *harvesting* — confirm the needed
  topics are recorded, then mine the survey/teaching bags (see *Harvesting
  production data*). After a survey day, fold what the bags answered back
  into the relevant thread here.

## Appendix A: June 4 punch list — effort, boat-dependency, parallelism *(snapshot 2026-05-20, refreshed 2026-05-22; status reconciled 2026-05-27 via #189; refreshed 2026-05-28 post-#186)*

> **Historical snapshot — dates not updated.** This appendix is a point-in-time
> sizing made against the **original June 4** freeze (and superseded by the
> reality check near the top). The freeze later moved to **June 8** (see
> Forcing function, 2026-06-03); the "15 calendar days to June 4" framing below
> reflects the date as it stood at snapshot time and is left as-is for the record.

This appendix tags every "Must finish before June 4" item from the
Active-threads sections above with effort, where it can be worked, and
critical-path notes — and uses that to size the agent count needed to
clear the list. Refresh or remove this appendix as items land; it's a
working sizing document, not durable direction.

> **2026-05-27 status note:** the entire observability batch (#162, #141,
> #139, #140, `ros2_network_monitor#23`, #97, and #171), plus nav #24 and
> the opportunistic nav #33, have landed since this was sized — done rows
> are struck below. The **Totals / Parallelism / agent-allocation** math
> further down is now stale (it assumed the small-wins batch was open) and
> should be re-sized or dropped at the next planning pass. Remaining genuine
> gaps: #5 (perception #7), #6 (#127), #8 (nav #23), #9 (nav #19), #10
> (bathy), #11 (#138 boat day), #12 (#18 deploy guide), #18–21 (OTH),
> #22 (nav #25 — in review). #3 (sidescan decision) still open.

> **2026-05-28 status (post-#186) — how far behind:** since 05-27, two more
> landed — **nav #25** ([PR #37](https://github.com/rolker/unh_marine_navigation/pull/37) **merged**; fail-forward validated on-water at #186) and
> **nav #23** (**closed**) — and **perception #7** got **on-water acceptance
> evidence** at #186 (the planner routed around camera-detected obstacles; the
> #6-segfault risk is long moot). Marking *robustness* (small/dim targets) spun
> out as **post-June-4** work ([`unh_marine_perception#22`](https://github.com/rolker/unh_marine_perception/issues/22) / [`#23`](https://github.com/rolker/unh_marine_perception/issues/23) / [`marine_perception_tools#1`](https://github.com/rolker/marine_perception_tools/issues/1)) — not Must-finish.
>
> **Schedule gap:** the sizing below assumed *15 calendar days* to June 4; as of
> 2026-05-28 it's **~7 calendar days (~5 working)**. The small-wins batch +
> several mediums are done, and the scariest technical unknown (does
> perception→planning work?) resolved **positively**. Remaining Must-finish is
> **execution-capacity-bound, not technical-unknown-bound**:
> - **#6 [`unh_marine_autonomy#127`](https://github.com/rolker/unh_marine_autonomy/issues/127)** op-side costmap display (L, bandwidth) — the genuinely hard one, **open**.
> - **#12 [`#18`](https://github.com/rolker/unh_echoboats_project11/issues/18)** student deployment guide (M, writing) — **open**.
> - **Boat day** — #11 [`#138`](https://github.com/rolker/unh_echoboats_project11/issues/138) FCU/nav-input + on-water validation of #5/#127/#9; serial, weather-dependent, **not yet scheduled in the window**.
> - **#10** bathy (triage), **#9 [`nav#19`](https://github.com/rolker/unh_marine_navigation/issues/19)** (S), **#1 [`#163`](https://github.com/rolker/unh_echoboats_project11/issues/163)** AML SVS, **#3** sidescan decision.
> - OTH (#18–21, [`#130`](https://github.com/rolker/unh_echoboats_project11/issues/130)) — **natural drop for the lake** (not OTH-scale).
>
> **Read: behind on the L items + the boat day, but de-risked technically.** If
> #127 slips, the fallback (vigilant camera-watching + exclusion zones — and the
> #186 milestone shows the planner *can* route around solidly-marked obstacles)
> is viable. The **Totals / Parallelism / agent-allocation** math below remains
> stale (sized at 15 days with the small-wins batch open) — read it for shape,
> not current numbers.

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
| 1 | [`#163`](https://github.com/rolker/unh_echoboats_project11/issues/163) AML SVS probe outputs all-NUL bytes | S–M | BF | **NEW 2026-05-22**: probe not generating output (hardware/config, not parser). Bench test, verify config, replace if faulty |
| 2 | ~~Mercat NTP verify (`ntpq.exe -pn`)~~ | — | — | **DONE 2026-05-22** (#160 dev log: textbook-healthy) |
| 3 | Sidescan decision (M3 imagery vs Garmin) | S | BF | Decision only |
| 3b | Sidescan install (if Garmin chosen) | M–L | BI | Physical install + protocol integration |
| **Surface-obstacle** | | | | |
| 4 | ~~[`unh_marine_perception#6`](https://github.com/rolker/unh_marine_perception/issues/6) segfault~~ | — | — | **DONE** (#6 + #14 closed; durably validated in-water 2026-05-22) |
| 5 | [`unh_marine_perception#7`](https://github.com/rolker/unh_marine_perception/issues/7) OAK→costmap validation | M | DI | **On-water acceptance evidence at #186 (2026-05-28)** — planner routed around camera-detected obstacles; close-out remaining |
| 6 | [`unh_marine_autonomy#127`](https://github.com/rolker/unh_marine_autonomy/issues/127) op-side costmap display | L | DI | 78% loss measured — bandwidth budget tight; replay-driven impl, validate live |
| **Navigation reliability** | | | | |
| 7 | ~~[`unh_marine_navigation#24`](https://github.com/rolker/unh_marine_navigation/issues/24) BT `target_speed` → `/speed_limit`~~ | — | — | **DONE 2026-05-25** — field commits reconciled to origin via [PR #27](https://github.com/rolker/unh_marine_navigation/pull/27) |
| 8 | ~~[`unh_marine_navigation#23`](https://github.com/rolker/unh_marine_navigation/issues/23) TF extrapolation fix~~ | — | — | **DONE** — #23 closed |
| 9 | [`unh_marine_navigation#19`](https://github.com/rolker/unh_marine_navigation/issues/19) costmap timeout investigate | S | BF | Bag analysis; decide fix-or-defer |
| 10 | Boat-side bathy costmap | L–XL | BF | **Triage first** — Roland's "other computer" branch may exist |
| **Both nav at base_link** | | | | |
| 11 | [`#138`](https://github.com/rolker/unh_echoboats_project11/issues/138) FCU reconfig + validation | S prep + **boat day** | BI | Bench param-write OK; sea_surface chain validation needs water |
| **Class-ready UI** | | | | |
| 12 | [`#18`](https://github.com/rolker/unh_echoboats_project11/issues/18) student deployment guide | M | BF | Writing-heavy; draft from logs |
| **Observability — class-blocking** | | | | |
| 12b | ~~[`#162`](https://github.com/rolker/unh_echoboats_project11/issues/162) Battery annunciator threshold-to-color logic~~ | — | — | **DONE 2026-05-26** ([PR #179](https://github.com/rolker/unh_echoboats_project11/pull/179)) |
| **Observability — small wins** | | | | |
| 12c | ~~[`#171`](https://github.com/rolker/unh_echoboats_project11/issues/171) annunciator missing rows (battery/SV/FCU-system)~~ | — | — | **DONE** — field config imported via `0cd42f5` / [PR #182](https://github.com/rolker/unh_echoboats_project11/pull/182) |
| 13 | ~~[`#141`](https://github.com/rolker/unh_echoboats_project11/issues/141) remove `diagnostic_aggregator`~~ | — | — | **DONE** ([PR #146](https://github.com/rolker/unh_echoboats_project11/pull/146)) |
| 14 | ~~[`#139`](https://github.com/rolker/unh_echoboats_project11/issues/139) `output='both'` in launches~~ | — | — | **DONE** |
| 15 | ~~[`#140`](https://github.com/rolker/unh_echoboats_project11/issues/140) remove `bencloud` ping target~~ | — | — | **DONE** ([PR #148](https://github.com/rolker/unh_echoboats_project11/pull/148)) |
| 16 | ~~[`ros2_network_monitor#23`](https://github.com/rolker/ros2_network_monitor/issues/23) try/except + backoff~~ | — | — | **DONE** |
| 17 | ~~[`#97`](https://github.com/rolker/unh_echoboats_project11/issues/97) salmon `/diagnostics` recording wiring~~ | — | — | **DONE** ([PR #109](https://github.com/rolker/unh_echoboats_project11/pull/109)) |
| **OTH** | | | | |
| 18 | [`#130`](https://github.com/rolker/unh_echoboats_project11/issues/130) OTH field validation | **boat day** | BI | Combinable with #11 |
| 19 | Topic-budget cull (measure + cull + verify) | M + **boat verify** | DI | Bag-driven measurement BF; verify under load DI |
| 20 | Low-bandwidth status fallback | L | DI | New node + UI plugin; unit-test BF, real-link DI |
| 21 | VPN-path indicator | M | DI | Cheaper than #20; UI surface for [`#124`](https://github.com/rolker/unh_echoboats_project11/issues/124) |
| **Autonomy robustness** | | | | |
| 22 | ~~[`unh_marine_navigation#25`](https://github.com/rolker/unh_marine_navigation/issues/25) BT catchall fix~~ | — | — | **DONE** — [PR #37](https://github.com/rolker/unh_marine_navigation/pull/37) merged; fail-forward validated on-water at #186 |
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
