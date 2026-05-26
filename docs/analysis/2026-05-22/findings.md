# 2026-05-22 BizzyBoat deployment — analysis findings

Companion to [`rolker/unh_echoboats_project11#169`](https://github.com/rolker/unh_echoboats_project11/issues/169)
(umbrella) and the deployment issue
[`#160`](https://github.com/rolker/unh_echoboats_project11/issues/160).

Living document — sections map to the standard per-deployment checklist in #169.
Status keys: ✅ done · 🟡 partial · ⬜ not started.

## Setup

- **DB**: `~/data/logs/analysis/2026-05-22_deployment.db` (1.8 GB, 4,184,152 messages, 46 topics).
- **Source bag**: `~/data/logs/bizzyboat/2026-05-22T21-05-06+00-00` (209.3 min recorded: pre-launch dockside → ~22 min post-recovery charging).
- **Detected in-water window** (`bag_analysis` altitude detector):
  - Launch: **2026-05-22T21:28:52Z = 17:28:52 EDT**
  - Recovery: **2026-05-23T00:12:18Z = 20:12:18 EDT**
  - Duration: **2h 43m 26s (163.4 min)**
- Robot namespace: `bizzy`.

---

## §1 Tier-1 `bag_analysis` report ✅

Rendered with `ros2 run bag_analysis sqlite_to_report`. Output (`summary.md` + 7 PNG plots:
altitude_heave, comms, mode_timeline, power, sensor_health, speed_heading, track) kept with the
analysis artifacts at `~/data/logs/analysis/2026-05-22/report/` (provenance — not committed; see
[`README.md`](README.md)).

Headline numbers:

| Area | Value |
|---|---|
| GNSS | 125,558 fixes, all status `fix` |
| Speed | odom max \|v\| 2.02 m/s (mean 0.73); GPS SOG max 2.43 m/s |
| Comms | wire-out peak 17.33 Mbps, mean 8.70; rate-limit drop peak 0.747 Mbps; **send-failed 0** |
| Diagnostics | 163,166 msgs; peak ERROR 2, peak WARN 5 |
| Altitude/heave | smoothed −25.27 to −23.51 m; std 0.385 m (heave proxy) |
| Battery (voltage — real) | resting 24.94 V → 22.19 V; in-water 21.18–24.95 V, mean 23.59 V |

> **Power caveat.** BizzyBoat has **no current meter** — voltage is the only real
> electrical measurement. The tier-1 report's current/energy/power figures
> (peak ~152.9 A / 3471 W; ~1047 Wh ≈ 15% of 7000 Wh nominal) are a **modeled
> V-drop estimate (±~30%)**, not measurements. The actual power-usage analysis
> is tracked in [`#167`](https://github.com/rolker/unh_echoboats_project11/issues/167);
> trends are usable, absolutes are not.

---

## §8 Diagnostics summary ✅

ERROR drill-down complete; annunciator correlation (§8.D) and milestone health snapshots (§8.F) also complete.

**18,637 of 163,166 diagnostic messages carried an ERROR**, from 5 sources:

| Source | ERROR msgs | Pattern | Verdict |
|---|---:|---|---|
| `sound_speed_bridge` | 12,556 | 1 Hz continuous, entire bag (dockside→recovery) | **Standing fault** |
| `mavros: System` | 4,597 | sporadic until 19:15, then pegged 1 Hz to recovery | **Low-battery failsafe** |
| udp_bridge `operator: vpn`+`wifi` | 910 | nil until 19:35 blip, big spike 20:25 | Benign (link loss, mostly post-recovery) |
| udp_bridge `resend give-ups` | 534 | steady 7–46/10-min throughout | Benign (structural ~30% resend) |
| `starlink: link` | 40 | scattered blips | Benign |

### §8.A `mavros: System` = low-battery, as designed
Steps into continuous ERROR at **19:15 EDT**, exactly as voltage crosses into the
low-22 V band. rosout at **19:18:07**: `bizzy.mavros.sys: "FCU: Battery 1 is low
22.88V used 0 mAh"`. Voltage continued to a 21.18 V min by 20:05. This is the
deliberate **drain-to-LVD** objective of #160; the `SYS_STATUS` health bit stays
asserted (continuous diagnostic ERROR) while the statustext fires once.

**No auto-failsafe mode change fired.** The boat ran **GUIDED continuously from
18:18:46 until 20:10:05** (→ MANUAL for recovery; recovery 20:12:18). Despite the
low-battery warning and the slide to 21.2 V, ArduPilot did not auto-RTL/HOLD —
the battery-failsafe action is **intentionally disabled** for the controlled drain
(confirmed). Accepted trade-off: no autopilot-side auto-protection if a drain test
overruns.

*(Power-field placeholders confirm the no-current-meter reality: `percentage` =
−0.01, `power_supply_health` = 0/UNKNOWN, "used 0 mAh". Only voltage is real; the
failsafe surfaces via statustext, not the BatteryState fields.)*

### §8.B `sound_speed_bridge` ERROR the entire deployment
Exactly 600/10-min = 1 Hz from first to last message, including dockside
pre-launch. The sound-velocity bridge never produced valid data this deployment.
→ ties to AML probe [`#163`](https://github.com/rolker/unh_echoboats_project11/issues/163) (class-blocking).

### §8.C Benign link errors
udp_bridge vpn+wifi ERRORs cluster at the 20:25 spike (post-recovery, boat being
pulled / powered down) with a brief 19:35 blip — over-horizon/range behavior, not
faults. Resend give-ups are steady background (structural ~30% resend overhead,
per the 2026-05-18 link calibration). Starlink blips are minor path flaps.

### §8.D Operator-annunciator cross-check ✅ → gaps filed
The conditions above largely **did not surface to the operator annunciator**.
`bizzyboat_operator_annunciator.yaml` carries only network/link indicators — no
battery, sound-speed, or FCU-system indicator — so during the drain-to-LVD the
operator got no battery warning, no SV-failure indication, and no FCU-error
indication. The boat annunciator's `Battery` indicator keys on `mavros: Battery`
(level), which stayed OK; low voltage surfaced on `mavros: System` instead. Filed
[`#171`](https://github.com/rolker/unh_echoboats_project11/issues/171) (battery
voltage-threshold + SV + `mavros: System` indicators; config-only).

### §8.E Time-in-ERROR per source (in-water, ~1 Hz samples)
| Source | Time in ERROR | % in-water |
|---|---|---|
| `sound_speed_bridge` | 163.4 min | **100%** (standing — SV pipeline dead) |
| `mavros: System` (low-batt) | 54.5 min | 33% (final third, from ~19:15) |
| udp_bridge resend give-ups | 7.4 min | 4.5% (intermittent background) |
| udp_bridge link (wifi/vpn) | 2.3 min | 1.4% (mostly near recovery) |
| starlink link | 0.2 min | 0.1% |

### §8.F Milestone health snapshots
| Milestone | ERROR | Notable WARN |
|---|---|---|
| Pre-launch (17:10) | sound_speed (+resend give-ups) | mavros:Mount, starlink alerts, mikrotik ether2–5 |
| Launch+settled (17:30) | sound_speed (+resend give-ups) | + ping salmon_vpn |
| Mid-mission (18:50) | sound_speed (+resend give-ups) | (baseline) |
| Recovery (20:11) | sound_speed, **mavros:System (low-batt)**, resend | + wifi link, ping router_op_vpn/salmon_direct |

- The only ERROR through most of the mission is **sound_speed** (standing) plus occasional
  resend give-ups; **mavros:System (low-batt) joins only in the final third** — which is
  why the ceiling was "peak ERROR 2."
- Persistent **benign** WARNs: `mavros: Mount` (mount/gimbal, unconfigured), `starlink
  alerts`, `mikrotik ether2–5` (unused wired ports down), and intermittent `ping` failures
  (OTH/range — a mode of operation, not faults).

---

## §6 Survey-pattern execution ✅ — root cause + execution metrics (XTE → #164)

Triggered by an FCU `"target not received last 3secs, stopping"` event. **Not a
stack restart** (all topics kept flowing); it's a survey **line-transition gap**.

**Root cause (navigator BT, `unh_marine_navigation`).** At each survey line→line
handoff, `TransitAndSurveyLine` → `NavigateThroughWaypoints` runs
`CancelAllNavigation` + `ClearPath` + a transit re-plan (`ComputePathThroughPoses`
gated by `RateController hz=0.5`) + `FollowPath`. During that window the controller
is uncommanded and `CrabbingPathFollower` returns a zero `Twist`. A zero command is
emitted at **every** line boundary; the gap is variable.

**Worst case — line2→line3 (18:32:03–18:32:07):** ~4 s gap in both
`autonomous_cmd_vel` and forwarded `setpoint_velocity/cmd_vel` → exceeded
ArduPilot's 3 s GUIDED watchdog → "stopping". Boat speed fell **1.5 → 0.66 m/s**,
~16 s to recover. Even clean transitions dip to ~0.9 m/s.

**Bonus — yaw-rate cap = 0.5 rad/s (= `max_yaw_speed`).** Through the turn,
`autonomous_cmd_vel` requested `omega_z` to −2.4 rad/s but the forwarded setpoint was
pinned at −0.5; `vel_x` passed through unchanged. This is the **`max_yaw_speed`
capability backstop**, which [`#172`](https://github.com/rolker/unh_echoboats_project11/pull/172)
raises 0.5→1.0. **Correction (per #124 §2 / PR #172):** yaw on this hull is **vectored
thrust — ω ∝ thrust×steering, *not* speed** — so rudder intuition doesn't apply, and my
earlier "turn radius = v/ω ≈ 3 m" was geometric coincidence, not a fixed turn constraint.
The *survey* turn-rate limit belongs in the **Nav2 smoother**, not the backstop. →
[`#164`](https://github.com/rolker/unh_echoboats_project11/issues/164) /
[`#168`](https://github.com/rolker/unh_echoboats_project11/issues/168).

### §6.1 Execution metrics
- **23 passes** of `pattern0000` (a short lawnmower set), run back-to-back over the
  mission — the same box re-surveyed repeatedly.
- **112 line executions**, mean dwell **55.3 s/line** (min 0.5 s = churn/aborted
  re-engagements; max 303 s = one long-running line).
- **Surveyed box ≈ 121 m × 138 m** (odom x/y span, in-water).
- **Mean speed 0.93 m/s** while autonomous (max 2.02) — the turn-slowdowns (root cause
  above) pull the mean well below the ~1.5 m/s line cruise.

### §6.2 XTE / undulation → analyzed in §12 (#164)
Planned geometry is in `/bizzy/plan` (poses in `bizzy/map_tide`, whose x,y equal odom
x,y since `map_tide` is a pure z-offset of `odom`); the per-line track is in `odom`. So
per-line XTE and the **SE-vs-NW undulation asymmetry** are computable — the quantitative
analysis was performed in **§12** ([`#164`](https://github.com/rolker/unh_echoboats_project11/issues/164),
now **closed**): undulation is real (~1.6 m median RMS), but the SE-only asymmetry could
not be confirmed from this mission's single travel heading.

---

## §2 Mission timeline reconstruction ✅

**Mode split (in-water, `piloting_mode`):** autonomous **132.5 min (81%)**, standby 23.1
min (14%), manual 8.0 min (5%) — predominantly autonomous.

| Phase | Window (EDT) | Mode | Activity |
|---|---|---|---|
| Dockside / pre-launch | 17:05 – 17:28:52 | standby/manual | arming tests, mode toggling |
| **Launch** | 17:28:52 | — | in-water |
| Survey pass 1 | 17:35 – 17:42:51 | autonomous | pattern0000 line0–5 |
| End-of-pattern hover | 17:42:51 – 17:53:50 | auton/standby | ~11 min station hold (longest) |
| Survey pass 2 | 17:53:50 – 18:02:41 | autonomous | pattern0000 line0–3 |
| Manual/standby interlude | 18:02:41 – 18:18:46 | standby/manual | ~16 min operator-held |
| Main autonomous survey | 18:18:46 – 20:10:05 | autonomous* | repeated pattern0000 passes (line0–7), hovers between |
| **Recovery** | 20:10:05 – 20:12:18 | manual | MANUAL handoff for recovery |

\* brief manual breaks at 18:20, 19:30–19:35, 19:44.

- **Repeated-pattern structure:** `pattern0000` (a short lawnmower set) was run **many
  times** back-to-back — each pass ~5–8 lines (~45–60 s/line), separated by end-of-pattern
  hovers. The same small box was surveyed repeatedly, not one large area.
- **~10+ hover engagements** (17:42, 17:53, 18:03, 18:28, 18:36, 18:42, 18:49, 19:05,
  19:21, …) — a good population for the **#165** hover-drift cross-event analysis.
- Apply the §5 settling caveat to any position-derived phase boundary.

---

## §3 Topic completeness check ✅

Source of truth = `ros2 bag info` on the recording bags (the extracted DB omits
image/sonar payloads by design).

**Telemetry bag** (`bizzyboat/2026-05-22T21-05-06+00-00`, 49 topics): all structured
topics present at expected rates (mavros 10 Hz, SBG 25/5/1 Hz, tf ~31 Hz,
diagnostics 13 Hz; cmd_vel/plan/response are expected-intermittent). **Three
zero-count topics:**
- `/bizzy/sensors/sound_speed/sound_speed` — **0 msgs**. Confirms the SV pipeline
  produced *nothing* (not merely ERROR — see §8.B). → #163 / #171.
- `/bizzy/collision_monitor_state` — **0 msgs**. No collision monitor running. → #170.
- `/bizzy/mavros/local_position/accel` — 0 msgs. Minor (mavros not publishing accel).

**Sonar bag** (`bizzyboat_sonar/2026-05-22…`, 1.31 M msgs): duplicates nav/SBG/tf/
diagnostics. `/bizzy/sensors/deltat/soundings` = **0 msgs** — **expected: the Imagenex
DeltaT multibeam is not currently installed on the boat** (config still lists it for
when it returns). `sound_speed` = **0** again (the genuine gap — see below).

**Image bag**: no `2026-05-22` bag under `~/data/logs/bizzy_images` — **by design:
camera/segmentation image bags are recorded selectively at operator discretion due to
size.** Not a recording fault. (Caveat: there is therefore no post-hoc segmentation
data for runs where images weren't captured, including this one.)

> **Resolved (Roland, 2026-05-25):** of the empty/absent streams, only **SV is a genuine
> fault** (tracked #163 / #171). DeltaT-0 = sensor not installed; image bag absent =
> selective recording by design.

## §4 Bag integrity ✅ — clean

| Topic | Max inter-msg gap | gaps > 1 s |
|---|---|---|
| mavros/imu/data (10 Hz) | 0.84 s | 0 |
| sbg/imu_data (25 Hz) | 1.22 s | 1 |
| /tf (~31 Hz) | 1.27 s | 3 |
| /diagnostics | 0.85 s | 0 |

- No significant data gaps in steady-state topics — a few ~1.2 s blips on SBG/tf,
  nothing structural.
- **Recv-vs-header skew** (mavros/imu): avg **0.2 ms**, max 813 ms (one outlier) —
  recording latency negligible.
- **No missing/zero header stamps** on mavros topics (0/125,558).
- **Timestamps sane from the first message** — recv span 17:05:07–20:34:23 EDT,
  monotonic, no pre-epoch/garbage. The TM2000B/sysfixtime cold-boot clock issue is
  **not present** this run (bag starts after the clock was synced).

## §5 Tide / chart-datum chain plausibility ✅ — healthy after excluding launch settling

| Topic | n (in-water) | NaN/inf | Notes |
|---|---|---|---|
| `/bizzy/tide_estimate` (10 Hz) | 97,994 | 0 | live; see settling caveat |
| `/bizzy/mllw_offset` (1 Hz) | 9,806 | 0 | constant −28.013 m |
| `/bizzy/mhhw_offset` (1 Hz) | 9,806 | 0 | constant −25.149 m |

- **⚠ Post-launch settling transient (first ~30 s).** `tide_estimate` spikes to
  **−22.95 m** in the first 30 s after the altitude-detected launch (17:28:52) — 2.2 m
  *above* MHHW (−25.15), i.e. not a real water level — then settles to **−24.88 m by
  17:29:22**. The raw in-water min/max (−26.15 … −22.95) is therefore misleading: the
  high end is an artifact. A similar transient appears in the last bin approaching
  recovery. **Value analysis of tide/nav-derived topics must drop the first ~30 s after
  launch** (and a buffer before recovery).
- **Settled tide is a clean ebb** — smooth, monotonic fall from **−24.88 m (17:33)** to
  **−26.1 m (20:03)**, ~1.2 m over ~2.5 h. It sits ~0.3 m above MHHW early (plausible for
  a spring high) and ebbs toward ~1.9 m above MLLW — a sensible falling tide near high
  water. It never genuinely exceeds MHHW once settled.
- **`map_tide` TF healthy** — `bizzy/odom → bizzy/map_tide` at **9.99 Hz** (97,995
  transforms), z tracks `tide_estimate` (including the same launch transient). Two brief
  gaps (max 3.82 s).
- MLLW/MHHW datum offsets are stable constants, no NaN.

Chain validates (PR #153) **once the launch settling window is excluded** — which is
itself a finding. The related activation-time race is
[#157](https://github.com/rolker/unh_echoboats_project11/issues/157) (local_costmap
waiting on the first `map_tide` TF).

## §7 Link statistics summary ✅

Aggregate boat-side udp_bridge stats, in-water, bytes→Mbps (×8). The DB extraction
flattened BridgeInfo to aggregates, so per-link (wifi/vpn/starlink) and per-topic
attribution are **not** available here — they need the 2026-05-01-style perlink script
re-run against the raw bag. (The per-remote `remotes/operator` tables in this
extraction are internally inconsistent — resend > wire, sent > offered — and were not
used; the `name=bizzy` aggregate tables are coherent and match the tier-1 report.)

| Metric (in-water) | Mean | Peak |
|---|---|---|
| Wire-out (boat→all) | 8.67 Mbps | 17.33 Mbps |
| Resend (duplicate) | 0.06 Mbps | 1.13 Mbps |
| Offered to bridge | 50.05 Mbps | 73.85 Mbps |
| Sent (success) | 8.36 Mbps | 19.6 Mbps |
| Send-failed | 0 | 0 |
| Send-dropped (rate-limiter) | ~0 | 0.75 Mbps |
| Received (operator→boat) | 0.17 Mbps | — |

**Headline — the link was clean and stable this deployment, in sharp contrast to
2026-05-01:**
- **Resend overhead 0.7% of wire** (vs ~30% structural on 2026-05-01 and the
  2026-05-18 calibration). Either the link was low-loss this run or the udp_bridge
  resend rework is helping — can't attribute from the aggregate alone.
- **No send failures; negligible rate-limiter drops** (peak 0.75 Mbps, mean ~0). The
  ~42 Mbps gap between offered (50) and sent (8.4) is **topic selection** (costmap/
  camera not forwarded to operator), not loss — contrast 2026-05-01, where the limiter
  shed >1 MB/s of camera ffmpeg.
- **Wire steady ~8.6–9.1 Mbps throughout, no late-mission degradation** (2026-05-01 had
  aggressive late drops + a resend storm near recovery).

### §7.1 Per-link / per-topic (perlink script)
Re-parsed the raw bag with `2026-05-22_network_perlink.py` → `per_link_stats`
(33,080 rows) + `per_topic_stats` (1,290,256 rows). Two links: **wifi (cap 12 Mbps)**
and **vpn/Starlink (cap 8 Mbps)** — no cellular this run (matches 2026-05-18 calibration).

**Per-link, boat→operator, in-water:**

| Link | Sent mean | Sent peak | Cap | % cap | Resend % | Drop peak |
|---|---|---|---|---|---|---|
| wifi | 4.75 Mbps | 13.32 | 12 | 40% | 3.6% | 5.87 (one blip) |
| vpn (Starlink) | 3.92 Mbps | 6.68 | 8 | 49% | 0.2% | 0.44 |

- Load split fairly evenly (sum 8.67 = aggregate ✓); each link ~40–49% of cap on
  average — comfortable headroom, neither saturated.
- **WiFi took the congestion** (peaked over its 12 Mbps cap, 3.6% resend, one brief
  dropped burst); **VPN/Starlink was very clean** (steady 49% cap, 0.2% resend).

**Per-topic (offered, in-water):** `/bizzy/local_costmap/costmap` dominates at
**25.0 Mbps mean / 52.2 peak** — half the ~50 Mbps offered — then 4× OAK segmentation
(~1.5 each) and 4× OAK ffmpeg (~0.8 each). Costmap is throttled/selected down before
the wire (its drops are negligible), not rate-limiter-killed.

**Per-topic drops negligible:** largest per-(topic,link) drop peak was **0.16 Mbps**
(an OAK ffmpeg stream on VPN); means ~0. **Sharp contrast with 2026-05-01**, where the
limiter shed >1 MB/s of camera ffmpeg. The link comfortably carried the forwarded set.

Artifacts: `2026-05-22_network_perlink.py`; tables `per_link_stats` / `per_topic_stats`.

## §9 Notable-events extraction ✅

Cross-referencing `2026-05-22_dev_logs.md` (which integrates gabby §§1–8 + salmon §§2–12)
against the bag-precise findings. Many dev-log entries carry only `~HH:??` field times; the
bag pins them.

| Field observation (dev log) | Bag-precise time / data | Cross-check |
|---|---|---|
| Pre-launch CAMP freeze + annunciator all-red; root cause boat WiFi router dead | dockside, before launch | link WARNs pre-launch → **#166** |
| 🚤 Launch | **17:28:52** | matches dev log |
| M3 not getting sound speed (AML emitting NULs) | `sound_speed` topic **0 msgs all mission** | confirms §3/§8 → **#163** |
| Mooring-stuck incident → RHIB → freed → loiter | aligns with the **18:02:41–18:18:46 standby/manual interlude** (§2) | the obstacle-avoidance gap motivating **#17/#28/#29** |
| Battery 23 V WARN crossing | `mavros:System` ERROR onset **19:15–19:18** ("FCU: Battery 1 is low 22.88V") | confirms §8 |
| **Annunciator never went yellow/red** at 22–23 V (DEFINITIVE bug) | low-batt surfaced on `mavros:System`; Battery annunciator keys on `mavros:Battery` (stayed OK) | confirms **#171** diagnosis |
| SE-only undulation ("straighter NW than SE") | §6 yaw-clamp + undulation | → **#164** |
| Drift test (manual, no thrust): 22.8→23.0 V, sag ~0.2 V | a manual interlude ~19:30–19:44 (§2) | low-SOC sag → **#167** |
| End-of-survey hover drift | one of the ~10+ hover engagements (§2) | → **#165** |
| Speed series 1/2/**4 kt** | **4 kt ≈ 2.06 m/s = odom max 2.02 m/s** | confirms → **#167/#168** |
| 🛟 Recovery | **20:12:18** | matches dev log |
| Charging started, 22.43 V | ~20:34 (bag runs to 20:34:23) | bonus charge-curve data |

**Most useful cross-confirmation:** the field-observed "annunciator silent at low battery"
(#162/#171) is fully explained by the bag — the low-battery condition surfaced on
`mavros: System` (ERROR from 19:15), **not** on `mavros: Battery` (which the annunciator
watches, and which stayed OK). This confirms #171's threshold/source framing and corrects the
salmon-log "missing from `/diagnostics`" hypothesis (the data path was fine; the bug is the
threshold/source mapping). Full per-host technical detail lives in gabby §§1–8 / salmon
§§2–12.

## §10 Findings register ✅ (roadmap feed = draft for curation)

### Validated / healthy (positive)
- **Multi-instance `sea_surface_layer` (#14 fix)** held the full 2h43m — no segfault under
  in-water + thrust + low-battery + sunset. Durably validated.
- **Drain-to-LVD succeeded** — voltage to 21.2 V loaded, no auto-failsafe interrupted (by
  design); 3-sample cross-deployment discharge data captured (→ #167).
- **Comms link clean & stable** — 0.7% resend (vs ~30% prior), negligible drops, both links
  ~40–49% of cap, no late-mission degradation (§7).
- **Tide/chart-datum chain healthy** (PR #153) once launch settling excluded (§5).
- **Bag integrity clean** — no structural gaps, sub-ms skew, sane timestamps; the TM2000B
  cold-boot clock issue is absent this run (§4).
- **#157 activation race did not bite** (single-attempt, 6.16 s).
- **Segmentation robust to sunset / low light.**

### Gaps / defects (negative) — all tracked
- Survey lines **open-loop w.r.t. obstacles** → mooring-stuck incident (3rd of this class).
  → #17 / #170 / #28 / #29 / #31.
- **Line-transition stall** trips FCU 3 s watchdog → #28.
- **Yaw clamp ≈0.5 rad/s** shapes turns → #164 / #168.
- **SV pipeline dead** all mission (AML NULs) → #163.
- **Annunciator misses battery-LVD / SV / FCU-errors** (operator safety) → #171 / #162.
- **SE-only undulation** → #164. **Hover convergence drift** → #165.
- **4:3 OAK video stall** → unh_marine_perception#10. **CAMP froze twice** → #166.

### Roadmap candidates (class-prep, June 4) — for curation into `docs/roadmap.md`
1. **Obstacle avoidance = next core priority** — reflex layer (#17/#170) near-term; coverage
   planner (#29) long-term. (Matches the dev-log "Lessons Learned.")
2. **Annunciator coverage** (#171/#162) — class-blocking operator safety.
3. **AML SV probe config** (#163) — verify before class.

The above is the feed for the next-deployment scope. The `docs/roadmap.md` update derived
from this analysis **is included in this PR** — a Power/endurance section plus placements for
#33 (hover), #164, #171 (annunciator), #173 (next deployment), and camp#52.

---

## Cross-cutting findings

1. **The drain-to-LVD test worked as intended** — voltage fell to 21.2 V, FCU
   raised low-battery, no auto-failsafe interrupted the controlled drain. The
   failsafe action is intentionally disabled for the drain test (confirmed).
2. **Sound-velocity was never online this deployment** (standing ERROR dockside→
   recovery) — a real gap for the survey mission, tracked in #163.
3. **Survey line transitions are open-loop and brittle.** The per-line
   cancel/clear/replan model emits a stop at every boundary and occasionally
   stalls past the FCU watchdog. This is the deepest finding and spawned a scoped
   roadmap (below).
4. **Link errors are over-horizon/recovery artifacts**, not faults — consistent
   with the "wireless drop is a mode of operation, not an ERROR" principle.

## Follow-up issues filed

From the survey-line / obstacle-avoidance thread (see #169 comment for grouping):

- [`unh_marine_perception#17`](https://github.com/rolker/unh_marine_perception/issues/17)
  — segmentation→sensor adapter for nav2 Collision Monitor (near-term reflex layer)
- [`unh_echoboats_project11#170`](https://github.com/rolker/unh_echoboats_project11/issues/170)
  — configure nav2 Collision Monitor for BizzyBoat (near-term)
- [`unh_marine_navigation#28`](https://github.com/rolker/unh_marine_navigation/issues/28)
  — line-transition stall trips FCU 3 s GUIDED watchdog (narrow bug)
- [`unh_marine_navigation#30`](https://github.com/rolker/unh_marine_navigation/issues/30)
  — decompose tracklines into skippable segments (near–mid term)
- [`unh_marine_navigation#29`](https://github.com/rolker/unh_marine_navigation/issues/29)
  — port Alex's coverage planner + MPC (long-term)
- [`unh_marine_navigation#31`](https://github.com/rolker/unh_marine_navigation/issues/31)
  — COLREGS dynamic-vessel avoidance (stretch)

Pre-existing, reinforced here: #163 (AML/SV), #164 (SE undulation), #168 (survey
efficiency), #157 (nav activation race).

## Open questions

- **Battery failsafe action** (§8.A) — *resolved 2026-05-26*: intentionally disabled
  for the controlled drain test (confirmed); the slide to 21.2 V ran with no
  autopilot auto-protection by design (accepted trade-off for drain tests).
- **Yaw-rate clamp** — confirm the ≈0.5 rad/s cap on forwarded `omega_z` holds
  across the whole mission (only one turn inspected) and locate where it's set in
  the mux/mavros bridge. (§6)
- **76 unpopulated `current task` msgs** — benign skew, or a real gap? (§3)
- **Empty/absent sensor recordings** (§3) — *resolved 2026-05-25*: SV (0) is the only
  genuine gap (#163 / #171); DeltaT-0 is sensor-not-installed; the image bag is absent
  by design (selective recording due to size).

---

## §11 Survey efficiency (#168) — coverage = track-per-charge × sonar swath

> **Correction (operator, 2026-05-25):** the 2026-05-22 line geometry (tight ~1–6 m spacing,
> short 58 m lines, same box re-run 23×) was a **battery-drain-while-staying-near-the-pier**
> artifact — *not* representative survey spacing. Coverage-per-energy must **not** be read off this
> mission's geometry (an earlier per-pass-spacing version of this section did that and under-stated
> real coverage ~10–20×).

**Real survey coverage is governed by the sonar swath, not the line spacing flown.** The boat's
transferable contribution is **track-distance per charge** (= #167 range): ~40 km @ 1.5 m/s
(ideal) / **~32 km de-rated**. Then **coverage = track × swath**, where swath is the M3 multibeam's
across-track coverage (∝ water depth × beam angle) — a sonar/depth parameter, not a power one, and
**not determined by this mission**. (A real survey's line spacing ≈ swath × (1−overlap).)

Coverage per charge (de-rated ~32 km track @ 1.5 m/s), by swath:

| Sonar swath | Coverage rate @1.5 m/s | Area / charge |
|---|---|---|
| 5 m | ~2.7 ha/hr | ~16 ha |
| 10 m | ~5.4 ha/hr | ~32 ha |
| 20 m | ~11 ha/hr | ~64 ha |
| 40 m | ~22 ha/hr | ~128 ha |

**Levers (in order):**
1. **Sonar swath** — the dominant coverage driver (∝ depth); use the widest the depth/sonar gives.
2. **Track-distance per charge** — speed/efficiency (#167); ~32 km de-rated @ 1.5 m/s.
3. **Turn overhead** — longer survey lines amortize turns (the 58 m test lines were short).

Caveats: track/charge is ±30 % (no current sensor, #167); the swath is a separate sonar+depth
question (not in this mission); STW.

---

## §12 SE-undulation (#164) — undulation confirmed; directional asymmetry inconclusive

**Undulation is real, pervasive, significant.** Per-line cross-track wobble (PCA fit to each
`pattern0000/lineN` track segment; 101 lines): **median 1.57 m RMS, p75 2.32 m, max 15.9 m** on
~59 m lines. >90 % of lines wobble >1 m; ~37 % >2 m; 8 "severe" (>4 m). Quantitatively confirms the
dev-log "very undulating" — and ±2 m (up to ±16 m) wobble on a survey line leaves coverage
gaps/overlaps (degrades #168).

**It's a tracking issue, not speed/thrust.** Wobble is ~independent of speed (1.27–1.41 m/s across
all wobble bins); longer lines accumulate more (severe avg 72 m). So it's the path-follower weaving
(cross-track PID limit-cycling), not low thrust authority.

**The SE-only directional asymmetry (the issue's central claim) could NOT be cleanly confirmed.**
The captured line-following was predominantly **one travel heading** (~N in odom — the survey ran
~unidirectional with transits between lines, and weaving scatters course), so there's no clean
SE/NW pair to compare within this mission. The operator's "straighter NW than SE" is plausible but
needs a **dedicated reciprocal-line test** (clean N–S–N–S, constant speed, same conditions).

**Candidates (consistent with evidence):** CrabbingPathFollower cross-track PID over-gain →
limit-cycling; interaction with the 0.5 rad/s yaw cap (follower commands corrections the clamped
yaw can't execute — §6, #172/#124); steering bias (ch_2 mean ~1429, below 1500 neutral). Fix =
follower tuning / re-enable the velocity smoother. Caveats: PCA wobble includes the transit-into-
line portion (inflates the severe tail); STW.

**Decision (2026-05-25): #164 closed — "characterized, awaiting recurrence-with-data."** The
discriminating signal (`control_msgs/PidState`: XTE + p/i/d terms + crab output) was published but
not recorded, so limit-cycling-of-validated-gains vs. disturbance-the-gains-can't-reject is
unresolvable from this instance. The gains (kp ≈ −20) are IzzyBoat-validated → frame as *what was
different*, not retune. Two things change for the next run (both in #173): `pid_state` recording is
now queued, and the yaw cap was raised 0.5→1.0 (a candidate mechanism — clamp couldn't execute the
follower's corrections). Reopen / re-file on recurrence, ideally via a dedicated reciprocal-line
test (N–S–N–S, constant speed).

---

## §13 Hover pre-convergence drift (#165) — root cause: momentum overshoot at the survey→hover transition

**Resolved.** Root cause characterized; fix design + recovered legacy reference tracked in `rolker/unh_marine_navigation#33`. #165 closed.

**Finding.** Across **12/12 genuine hover engagements** (gated on `mission_manager.current_nav_task ∈ {done_hover, hover_override}`, ≥15 s, next-line-departure filtered), the boat starts *on* the hold point (`d0≈0`) and drifts **off** it — median **9.2 m** (4.2–13.5 m), still moving outward at 15 s, settling ~20–40 s. The hover holds the **position at engagement**, so the symptom is post-engagement *overshoot*, not "pre-convergence" approach (issue framing inverted).

**Ruled out.** *Battery* (issue candidate #1, an agent guess): no SOC correlation (drifty spans uniform 22.2–24.7 V); station-keeping uses a small fraction of thrust. *Environmental set*: velocity-at-engagement = **12/12 coast** (speed decays from ~1.5 m/s; drift aligned ≤7° with pre-hover velocity); drift bearing ≈ survey-leg heading (SE), not the logged forcing (Clark Island current westward→slack; wind light south). → **carried momentum**.

**Mechanism.** `marine_nav_behaviors::Hover` is a position-only P controller (speed on `current_range` only; no velocity/decel term). `deceleration_` declared-unused — fossil of the pre-nav2 stop-point projection deferred in the nav2 port (also vestigial as the dead `PredictStoppingPose` + `SetPoseFromTask` stubs in `nav2.btproj`).

**Fix (→ `rolker/unh_marine_navigation#33`).** Restore the stop-point projection (the legacy `predict_stopping_pose.cpp` + `HoverTask` wiring are intact at git `1c5db5a^` — port, don't re-derive: re-add the `goal_pose` port to `Hover.action`, implement `PredictStoppingPose`/`SetPoseFromTask`, reactive `Hover`/`TransitTo` fallback, capability-derived params). Plus a live `point_at_target` param (ArduPilot `LOIT_TYPE` analog). Matches ArduPilot Rover Loiter, the earlier "more efficient than hover" observation. Shared/cross-platform → on-water re-validation.

**Scripts:** `~/data/logs/analysis/2026-05-22_hover_drift{,_v2,_v3,_v4}.py`.

---

## §14 CAMP froze twice (#166) — root cause UNCONFIRMED; capture plan filed

**Status: NOT root-caused.** What we have is a hypothesis consistent with the evidence; the hard logs are largely explained by mundane causes. Forward work (capture next occurrence) tracked in `rolker/camp#52`. #166 left open.

**Hard facts (logs/data):**
- E1 (16:30): camp+rqt died exit -9. But this is the **launch's SIGINT→SIGTERM→SIGKILL shutdown escalation** after the operator restarted the stack (camp `signal_handler` fired 16:29:52; SIGKILL 16:30:02). **~6 other nodes also needed SIGKILL** in that shutdown due to **rmw_zenoh "close operation timed out"** — so camp's -9 is *not* evidence of a freeze.
- E2 (19:37): boat-side both udp_bridge legs ERROR 19:35–36 + survey-resume `path_follower_visualization` 0→253/min + new `/plan` at 19:37:06.
- No OOM (operator confirmed `sudo journalctl -k` clean).
- CAMP architecture: `MultiThreadedExecutor` (ROS) + Qt thread, `shared_ptr` marker-snapshot handoff (`node_thread.cpp`, `markers.h`).

**Soft / unconfirmed:**
- That CAMP actually "froze" rests on real-time operator/agent perception (operator does not clearly recall; field logs are agent-written). E1's "coupled CAMP+udp_bridge death" = the operator restarting the stack because CAMP *seemed* unresponsive (per operator). E2 is the better-attested hang (alive + solo-kill while stack survived) but still agent-narrated.
- Trigger (link-stress burst) = temporal correlation only. Mechanism (executor↔Qt handoff) = architectural suspect, unproven.

**Why we can't be sure:** a GUI hang leaves no log trace; the only definitive evidence is a **thread backtrace of the hung process**, never captured. The deeper the dig, the more E1's signature dissolved into restart + the zenoh shutdown hang.

**Plan (`rolker/camp#52`):** Qt-timer GUI heartbeat → if it stalls while the ROS executor thread is alive = definitive GUI-hang signature → auto-dump backtraces; + operator one-liner; + optional bench repro (bag replay + `tc netem`); + code audit of the handoff.

**Shutdown-anomaly footnote (corrected after verification):** the degraded 16:30 restart hit rmw_zenoh "close operation timed out" → SIGKILL of many nodes; the **healthy 20:27 shutdown was clean** (no close-timeouts). **zenoh is loopback-only** (stock config: sessions connect `tcp/localhost:7447`, listen `tcp/localhost:0`; router `connect` empty; multicast off; no `ZENOH_*_CONFIG_URI`) → **NOT network-caused** — the dead WiFi can't touch loopback zenoh. Cause **unverified** (candidate: local `zenohd` unresponsive under the 16:30 churn). One-off; **not a tracked issue.** (An earlier draft wrongly called this general + network-linked — retracted.)

**`-11` SIGSEGV identified:** the segfault in the 16:31 session was **CAMP crashing on shutdown at 20:27** (mission end) — *not* a mid-mission crash, *not* the 19:37 hang (`starlink_diagnostics` also exited 1 then). So the 20:27 shutdown was clean of the zenoh-hang/mass-SIGKILL pattern but CAMP segfaulted on exit. Minor CAMP **teardown** bug; noted on `rolker/camp#52` as teardown-fragility context (same Qt/executor area as the hang).
