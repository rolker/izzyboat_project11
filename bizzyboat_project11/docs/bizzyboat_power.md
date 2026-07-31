# BizzyBoat Power & Battery

Consolidated reference for BizzyBoat's electrical/energy behaviour: the battery system,
measured current anchors, discharge and recharge characterization, the (sensor-free) power model, and
**operational deployment-planning rules**. Companion to
[`bizzyboat_hardware.md`](bizzyboat_hardware.md) (electrical hardware) and
`bizzyboat_performance.md` (speed/dynamics; added in [PR #172](https://github.com/rolker/unh_echoboats_project11/pull/172)).

> **Key constraint — no current sensor.** `BATT_MONITOR 3` (voltage-only; `4` was the inherited
> IzzyBoat baseline) with `BATT_CURR_PIN -1` — no shunt is wired between the Torqeedo packs and
> the Cube, so current reads ~0 A. **Voltage is the only
> real electrical measurement.** All current / power / energy figures here are **modeled** from
> PWM plus two clamp-meter anchors and are **±~30 %**. The **voltage-based field rules
> ([Operational](#operational--deployment-planning)) are measured and reliable** — use those.

## Battery system
- **2× Torqeedo Power 24-3500 LiFePO4 in parallel** — 7000 Wh nominal ≈ **273 Ah** (7000 Wh ÷
  25.6 V nominal; *derived*, not measured on this hull).
- 8S LiFePO4: ~29.2 V full · 25.6 V nominal · ~21 V floor (manufacturer min); storage range
  22.6–24.2 V.
- **FCU thresholds:** `BATT_LOW_VOLT` (WARN) **23.0 V**, `BATT_CRT_VOLT` **21.5 V**, each with a
  10 s sustain (`BATT_LOW_TIMER`). `BATT_FS_LOW_ACT=0` / `BATT_FS_CRT_ACT=0` → **annunciator-only,
  no autopilot action** at either threshold.
- `BatteryState.current` (~0.01 A) and `.percentage` (−0.01) are **placeholders** — do not use.

## Measured current anchors
Two operating points from a Bluetooth DC clamp on the combined post-parallel output, in-water
(2026-04-27, `docs/logs/2026/2026-04-27_dev_logs.md`), plus one charger-side reading:
- **Idle ≈ 8 A** (PWM 1500 both, all systems on). Composition: gabby + USB + sensors 2–4 A,
  Cube + servos + ESCs 1–2 A, comms 1–2 A, cooling/lights 1–2 A.
- **Full throttle = 67 A** (PWM 2000 both, under load) → ~1715 W at 25.6 V.
- **Charger idle/maintenance ≈ 6.2 A** — external fast-charger display at/near full charge,
  all systems on; taken as the charger-reported **DC output current** (the display units
  are assumed — not 120 VAC input current, which would be ~740 W, far above any idle load)
  (operator-read 2026-05-28 after a multi-day in-place charge,
  [#186](https://github.com/rolker/unh_echoboats_project11/issues/186) →
  [#196](https://github.com/rolker/unh_echoboats_project11/issues/196); re-read 2026-06-04). ≈ 180 W at the ~29 V plateau — consistent with the ~8 A × ~25.6 V
  clamp idle within the measurement band. With no shunt on the hull, charger-side readings
  are the only measured current available dockside.
- These anchor the V-drop model (`R_int ≈ 12.9 mΩ` from the 0.864 V **steady-state** drop at
  67 A; note the 2026-04-27 log's ~25 mΩ is from the 1.7 V **peak transient** sag — a different
  measure, not a conflict).
- **Steering servos are 5 A-fused** (vectored thrust) — small, partly inside the idle figure.
- A full **PWM × current sweep** (idle → full, reverse, at multiple boat speeds and steering
  angles) is the gating measurement → **#88**.

## RC channel map (relevant to power)
- `rc/out.ch_0` ≡ `ch_1` = **throttle** (both thruster units, slaved — *not* differential).
- `rc/out.ch_2` ≡ `ch_3` = **steering** (vectored-thrust servos).
- **Propulsion current is driven by the throttle channel only**; steering is a servo (minor).

## Discharge characterization (single charge cycle 2026-05-19 → 21 → 22)
A full charge cycle with no recharge between deployments (opening resting voltage stepped
28.6 → 27.0 → 25.0 V; 05-19 = first since a fresh charge):
- **LiFePO4 curve:** flat **plateau** high up (lots of charge moves little voltage — 05-19 dropped
  ~0.4 V across a whole session) → steep **knee** near empty (05-22: 25 → 21 V fast). **Voltage-
  based SoC is unreliable mid-range**, usable only near full and near empty.
- **Sag vs SOC (SOC-matched, validated across 7 deployments / ~3 months):** the mid-throttle
  **load sag is small (~0.05–0.12 V) and only mildly SOC-dependent** (~0.07 V high-SOC → ~0.10 V
  near-empty). All 7 deployments (2026-04-24 → 05-22) cluster within measurement noise at matched
  SOC, so the behaviour is **reproducible**. R_int is roughly stable → the constant 12.9 mΩ is a
  fair approximation; the strong dependence is on **PWM**, not SOC. (Measured by pairing each
  throttle sample to a nearby idle sample to remove within-deployment SOC drift.)
- **Speed-dependent prop load:** at fixed full throttle the drop is largest near static
  (bollard) and shrinks ~0.3–0.4 V as the boat speeds up (prop unloads). The 67 A anchor is the
  *running* load; bollard/acceleration current is **higher**.
- **Discharge rate accelerates toward empty:** ~0.5 V/hr on the plateau-edge → **~1.5 V/hr in the
  knee** (the last volt goes ~3× faster). **2026-06-23 update (first full-discharge):** the final
  knee was steeper still — ~23.0 V (15:00) → 20.6 V (15:52) loaded ≈ **~2.8 V/hr** in the last hour.

### Validated full-discharge — 2026-06-23 (first run to BMS cutoff)
The 2026-06-23 Massabesic survey ([#313](https://github.com/rolker/unh_echoboats_project11/issues/313))
is the **first real full-charge → BMS hard-cutoff on the water** (the 2026-05-22 drain-to-LVD
stopped at 21.2 V). It validates the **quadratic** PWM-coulomb model and corrects two figures:
- **Quadratic coulomb = 272.6 Ah consumed in-water; the pack (273 Ah nameplate) actually emptied.**
  A near-exact hit → **use the quadratic model.** The *linear* model over-predicts (~323 Ah, +19 %).
- **The V-drop energy model under-counts badly — do not trust it for absolute energy.** On 06-22 it
  read "~4154 Wh ≈ 59 % used"; the validated coulomb-quad says **~98 %**. (06-22 and 06-23 both ran
  the pack ~dry — two consecutive days at the edge.)
- **Real survey endurance ≈ 6 h / one full pack** at ~44 A average draw (06-23: 19.2 nm in 6.16 h;
  06-22: 6.5 h). The "8–12 h" cruise extrapolation below was optimistic.
- **Usable capacity to the BMS cutoff ≈ the full ~273 Ah nameplate** (cutoff ~20.6 V loaded).

#### SOC ↔ voltage reference (from the 2026-06-23 full discharge)
SOC from the validated quadratic coulomb count; voltage measured at each SOC. **Approximate
(single discharge, ±).** Resting (OCV) and loaded-at-survey-throttle are within ~0.1–0.2 V on the
plateau — load sag is small until near empty. This is the OCV lookup the live SOC estimator
([#318](https://github.com/rolker/unh_echoboats_project11/issues/318)) uses for voltage re-anchoring.

| SOC | Resting (OCV) | Loaded @ survey |
|---|---|---|
| **100 %** | ~28.7 V (full) | ~28.5 V |
| 90 % | 27.9 V | 27.8 V |
| 80 % | 27.0 V | 27.0 V |
| 70 % | 26.4 V | 26.5 V |
| 60 % | 25.9 V | 25.8 V |
| 50 % | 25.3 V | 25.1 V |
| 40 % | 24.8 V | 24.7 V |
| **30 %** | 24.3 V | 24.4 V ← knee begins |
| 20 % | 23.8 V | 23.7 V |
| 10 % | 22.9 V | 22.9 V |
| **0 %** | ~21.5 V (floor) | ~20.6 V (BMS cutoff) |

- Voltage declines ~0.5–0.9 V per 10 % — a *coarse* gauge, steepening below ~30 %; a ~0.3 V
  sag/measurement error ≈ 5–10 % SOC, so it cannot replace coulomb counting mid-range.
- **The 23.0 V FCU WARN sits at only ~15 % SOC** — by the time it fires you are near the bottom of
  the tank (see the turn-back-reserve finding, [#315](https://github.com/rolker/unh_echoboats_project11/issues/315)).
- Endpoints (100 % / 0 %) are the measured full-charge plateau and BMS cutoff, not interpolated.

## Recharge characterization (dockside voltage log, 2026-06-09 → 07-30)
Measured from gabby's dockside battery logger (1-minute voltage samples, `source=fcu` rows;
**15 charge events** including three near-empty starts). Full analysis, event table, and plot:
[`docs/analysis/2026-07-31/`](../../docs/analysis/2026-07-31/)
([`charge_ramps.png`](../../docs/analysis/2026-07-31/charge_ramps.png)). Fills the
recharge-time gap tracked in [#196](https://github.com/rolker/unh_echoboats_project11/issues/196).
- **Full recharge from empty ≈ 14–16 h on 120 VAC** with boat systems on (deepest event
  06-23 — the BMS-cutoff day — took 14.2 h; 07-20 took 15.5 h; one ~21 h outlier on 06-27,
  mostly a genuinely slower ramp, not just its initial dip/pause). **Plan ~15 h: plug in by
  ~17:00 and it's full by ~08:00** — 2 of the 3 near-empty events made that window; the
  outlier shows an overnight charge can run past sunrise, so power down non-essential
  loads while charging and don't skip the pre-launch resting-voltage go/no-go (≥ 27 V,
  § *Pre-launch go/no-go*) after an overnight charge.
- **Same-day turnaround from empty is not possible on 120 VAC** — a ~6 h run-to-empty
  survey costs ~15 h of charge. Recharge-to-full, not range, binds back-to-back cadence
  (now measured, previously a modeled expectation).
- Mid-pack starts (~24–25 V): ~11–15 h among completed events; the interrupted 06-17
  event (24.05 V start, unplugged at 28.8 V after 15.6 h) was on pace for ~17 h.
  Near-full starts (~27 V): ~4.5–6 h (one 11.4 h outlier). Spread at equal starting
  voltage is real — it tracks the hotel load left running during the charge.
- **Charge profile:** a continuous voltage ramp (no flat LiFePO4 mid-plateau at this low
  ~0.1 C charge rate); the main ramp ends at ~28.8 V, then a ~1 h taper to the 29.0 V
  standby plateau (max observed 29.06 V ≈ the 29.05 V final-charge spec).
- **AC draw at 120 VAC ≈ 7–8 A during bulk, ~2 A at float (inferred, not measured):** the
  fast charger's two rated points (750 W **out** @ 100 VAC, 1700 W **out** @ 240 VAC —
  EchoBoat 240 manual §3.6.1) scale linearly with input voltage: an input-current-limited
  design drawing ~8 A from the wall (rated output ÷ input voltage implies 7.1–7.5 A at a
  hypothetical 100 % efficiency; ~7.9–8.3 A at the realistic ~90 %). At 120 VAC that
  means a **~850 W output ceiling (~950 W from the wall)** — ~29 A gross DC at the ~29 V plateau, ~23 A net into the 273 Ah bank
  after the ~6 A hotel load ≈ 0.08 C. Energy-balance cross-check from the data: ~7000 Wh ÷
  14.2 h + ~180 W hotel ≈ 670 W DC ≈ 730 W from the wall at 90 % ≈ 6 A average at 120 V —
  consistent with ~8 A bulk plus taper. A standard 15 A outlet has ample margin. The
  manual's "~5 h @ 240 VAC" charge time is unverified on this hull.

## Speed → power, endurance, range (empirical)
Pooled from **four Massabesic lake surveys** (2026-06-22 / 06-23 / 06-24 / 06-25, ~19 h of steady
straight-line running). The lake has negligible current, so odometry speed-over-ground ≈
speed-through-water and the curve is clean across the operational 2–4 kt band. Current/power are
the **quadratic** PWM-coulomb model; endurance = 273 Ah pack ÷ draw (current **includes** the
~8 A hotel load); range = speed × endurance. The **Throttle** column is **measured**
(`rc/out.ch_0`, throttle % = (PWM − 1500) / 5). **The table is for steady straight-line legs** —
real lawn-mower surveys draw more (see the derate note below). Full reproduction notes + plots:
[`docs/analysis/2026-06-24/`](../../docs/analysis/2026-06-24/)
([`speed_endurance_range_curve.png`](../../docs/analysis/2026-06-24/speed_endurance_range_curve.png)),
[`docs/analysis/2026-06-25/`](../../docs/analysis/2026-06-25/) (throttle characterization).

| Speed (steady leg) | Throttle | Draw | Endurance | Range (nm) | Range (mi) | Efficiency |
|---|---|---|---|---|---|---|
| 2.0 kt | ~44 % | ~20 A | ~13.5 h | ~27 | ~31 | 4.6 mi/kWh |
| 2.5 kt | ~50 % | ~24 A | ~11.5 h | ~28 | ~32 | 4.5 mi/kWh |
| **2.9 kt** | ~62 % | ~29 A | ~9.3 h | ~27 | ~31 | **4.2 mi/kWh** |
| 3.1 kt | ~66 % | ~35 A | ~7.8 h | ~24 | ~28 | 3.8 mi/kWh |
| 3.5 kt *(historical cruise)* | ~81 % | ~46 A | ~5.9 h | ~20 | ~23 | 3.35 mi/kWh |
| 3.9 kt | ~91 % | ~57 A | ~4.8 h | ~18 | ~21 | 2.9 mi/kWh |

**Range plateaus at ~2.0–2.9 kt** (~27–28 nm of *steady-leg* distance on a full pack); the
historical ~3.5 kt cruise is already past it, costing ~25 % range. Draw and throttle **climb
steeply through ~3.2 kt** (~35 → ~46 A and ~66 → ~81 % throttle from 3.1 to 3.5 kt — the quadratic
prop law, smooth, not a true step). The **current/throttle cost knee is ~3.0–3.1 kt**: below it the
draw curve is gentle, above it it ramps hard. Below ~2.9 kt the range curve flattens — slower buys
*time*, not *miles* (the fixed ~8 A hotel load dominates).

> ⚠ **Derate for real surveys (turns cost energy).** The table is steady-leg; a lawn-mower
> pattern's turns and accel/decel raise the **average** draw by roughly one speed bin. The only
> full-discharge survey (06-23) ran a **3.1 kt mean SOG yet averaged ~44 A** — the 3.5 kt steady
> bin, not the 35 A the 3.1 kt row implies — and made **19.2 nm**, ~20 % below the ~24 nm the
> steady 3.1 kt row predicts. **Plan whole-survey range/endurance off the *next-higher* draw bin
> (~−20 %); use the steady-leg row only for individual transit legs.** (Preliminary — the derate
> rests on one full-discharge survey; it is mission-profile-dependent and will firm up as more
> turn-heavy runs accrue.)

**Pick the operating point by the binding constraint:**

| Constraint | Best speed | Why |
|---|---|---|
| **Range** (cover the most distance) | **~2.9 kt** | top of the range plateau; faster loses miles quickly |
| **Endurance / loiter** (stay out longest) | **~2.0 kt** | ~13.5 h vs ~5.9 h at 3.5 kt — more than double the time on station |
| **Time** (finish a fixed job fastest) | 3.5 kt | finishes a fixed job ~14 % faster than 3.0 kt but ~20 % less range — only with reserve to spare |

For mixed range+endurance missions, **~2.9 kt (top of the ~2.0–2.9 kt plateau) is the all-around
point** — 3.0 kt sits between the 2.9 and 3.1 kt rows. Versus the usual 3.5 kt it's ~17 % slower
but, from the table, **+3.4 h endurance (9.3 vs 5.9 h) and +8 mi range (31 vs 23 mi)**.

> **Caveat (same as the model below):** no current sensor — current/power are modeled (quadratic
> PWM, ±~30 %). The *relative* trade-offs and the current/Ah-based columns are robust; absolute
> amps/watts carry the band. The **endurance hours are anchored** by the 06-23 run-to-empty
> (273 Ah ÷ 44 A avg = 6.2 h, matching its measured underway time). Pier deployments are excluded
> (tidal current corrupts speed-over-ground). This pooled curve **partially fills #88** for the
> operational 2–4 kt band — it is opportunistic field data, not the controlled bench PWM×current
> sweep #88 still calls for. Related: [#315](https://github.com/rolker/unh_echoboats_project11/issues/315)
> (distance-aware reserve), [#318](https://github.com/rolker/unh_echoboats_project11/issues/318)
> (live SOC estimator), [#196](https://github.com/rolker/unh_echoboats_project11/issues/196)
> (idle/charger current).

### Speed → throttle (PWM): steady vs survey duty
Two complementary views of the throttle channel (`rc/out.ch_0`; 1500 neutral, 2000 full forward,
both thrusters slaved), pooled across the four lake surveys. Full detail + plot:
[`docs/analysis/2026-06-25/`](../../docs/analysis/2026-06-25/)
([`2026-06-25_cmd_throttle_current.png`](../../docs/analysis/2026-06-25/2026-06-25_cmd_throttle_current.png) —
commanded speed vs throttle % and current draw).

- **Steady straight-line** (achieved speed, transients removed) → the throttle column in the table
  above. The clean hydrodynamic map: ~57 % at 2.75 kt, ~64 % at 3.0 kt, ~70 % at 3.2 kt, ~81 % at 3.5 kt.
- **Ramp-inclusive** (actual throttle binned by **commanded** `setpoint_velocity/cmd_vel.vel_x`, no
  steady filter — captures accel-onto-line and post-turn recovery). At a given commanded speed the
  **ramp overhead is small (+0–4 pts)** — the controller tracks well and re-acceleration is brief
  relative to time-on-line, so the steady throttle is representative for "throttle to hold speed X."

> **Watch the post-turn recovery burst.** The commanded-speed view surfaces a current-heavy regime
> the steady table hides: ~7 % of survey time at **commanded ~3.9 kt / ~94 % throttle / ~61 A, but
> the hull only reaches ~3.1 kt** — the controller pushing near-full throttle to re-acquire the line
> after a turn. Disproportionately costly current for the speed delivered (~28 min/day near full
> throttle). A gentler post-turn speed ramp would trade a little line-acquisition time for materially
> lower peak current — a tuning lever, not a hull limit.

## Power model (sensor-free) and its limits
Current ≈ **f(PWM, SOC, boat speed, steering)**. Estimated via the V-drop model
(`marine_tools` `bag_analysis/plots/power.py`: `I = (V_oc − V_load)/R_int`) and/or PWM-coulomb
counting (idle 8 A / full 67 A anchors; quadratic per the propeller power law).
- **Anchored at only two points** → mid-throttle (where surveys live) is interpolated.
- **Constant R_int** — a fair approximation (§B: load sag is only mildly SOC-dependent,
  validated across 7 deployments), so a minor limitation; the strong dependence is on **PWM**.
- **Speed / steering axes uncalibrated** — and not separable from opportunistic field bags.
- **Coulomb model — now anchored by the 2026-06-23 full discharge:** the **quadratic** PWM-coulomb
  is validated (272.6 Ah predicted, pack emptied at 273 Ah nameplate); the **linear** variant
  over-predicts ~19 %. Use quadratic. The **V-drop** energy model under-counts substantially (06-22:
  V-drop "59 %" vs coulomb-quad ~98 %) — trust it for *trends*, not absolute Wh/Ah. The #88 PWM×current
  sweep is still the unlock for mid-throttle current; until then treat *modeled current* as ±30 %, but
  **energy/endurance hours are now anchored by a real run-to-empty** (≈ one pack per ~6 h survey).

## Operational — deployment planning
*Voltage rules are the reliable output (measured, not modeled) and are **load-conservative**
(derived from a turn-heavy survey + speed runs; a gentler load buys more time).*

### Pre-launch go/no-go — **resting** voltage
| Resting V (pre-launch) | Read | Plan |
|---|---|---|
| ≥ 27 V | full / near-full | full mission OK |
| 25–26 V | mid-pack | ~2–2.5 h mission, but you'll reach the knee — stay closer to pier, plan recovery |
| < 25 V | already low | **top up before launching** — the knee comes fast |

Read resting V at a thrust pause; loaded V sags below it (~0.1 V idle, ~0.9 V at survey throttle
when low-SOC).

### In-mission recovery ladder — **loaded** survey voltage (60 s mean)
| Loaded mean V | Survey time left | Action |
|---|---|---|
| 24 V | ~2 h | nominal |
| **23 V (FCU WARN)** | **~1 h** | plan the return leg |
| 22.5 V | ~30 min | head back now |
| **22 V** | **~15 min** | **recover immediately** |
| 21.5 V (FCU CRT) | floor | (transient mins already below) |

**Validated 2026-06-23 (full discharge):** the *time-left* column held up — 23 V at 15:05 → dark
at 15:52 ≈ 47 min (~1 h ✓); 22 V at ~15:38 → dark 15:52 ≈ 14 min (~15 min ✓).

> ✅ **The annunciator now fires** (yellow at the 23.0 V `BATT_LOW_VOLT` threshold) — #171/#162
> are fixed and **confirmed working on 2026-06-23**. The operator no longer has to watch raw voltage.
>
> ⚠ **But the ladder is *time-left*, not *homeward reach*.** On 2026-06-23 the boat ran a box
> ~1.5–2 nm out; when the annunciator fired at 23 V it had only ~10 % return margin, and the
> **point of no return was ~2 min later (~22.9 V)** — it died 1.29 nm short of the dock. **For ops
> >~1.5 nm out, turn back *before* 23 V** (interim: ~23.5–24 V loaded), and on the warning go
> *straight* home — don't finish the line. A distance-aware reserve rule is
> [#315](https://github.com/rolker/unh_echoboats_project11/issues/315).

### Battery management across a day / between cohorts
- Idle/hotel load (~5–8 A) drains the pack **even dockside**. **Charge to full before each
  deployment day** and **power gabby down between groups** when not surveying.
- Don't rely on "yesterday's charge" — one full charge ≈ a handful of in-water hours, but idle
  dominates the budget.
- **Recharge time is now measured** (§ *Recharge characterization*): **~15 h from empty on
  120 VAC** (14–16 h band) — overnight covers it; a same-day full turnaround does not.
  BizzyBoat charges **in place** (batteries are not field-swappable), so recharge-to-full
  time bounds the day/cohort cadence.

### Drive efficiently (extends every mission)
- **Plan for ~6 h of survey per full charge** (measured 2026-06-23 + 06-22, ~44 A average). Full
  throttle ≈ 4 h; a real survey is **~6 h to empty** — *not* the older 8–12 h cruise extrapolation.
- **Survey speed: ~3.0 kt (a touch over) is the all-around cruise sweet spot** — it sits right at the
  **current/throttle cost knee** (~64 % throttle, ~31–35 A), just past the ~2.9 kt range-optimum and
  before the steep cost ramp above ~3.2 kt. The pooled four-survey curve (§ *Speed → power, endurance,
  range*) shows range plateaus at ~2.0–2.9 kt; the historical ~3.5 kt cruise (~81 % throttle, ~46 A) is
  already well past the knee (~25 % less range). 3.2–3.3 kt is already in the same penalty zone as 3.5 kt.
  Slowing below ~2.9 kt buys loiter *time*, not *miles* (fixed ~8 A hotel load); >3.5 kt range falls off
  fast. Drop toward ~2 kt only when time-on-station (not distance) is the goal; push to 3.5+ kt only when
  the clock is the hard limit and reserve has margin.
- **Steady straight legs are cheapest**; accel-/turn-heavy patterns cost more (bollard load).
- **Minimize crabbing & oscillation:** align survey lines with the set/drift; address the
  SE-line undulation (#164 — over-steer wastes energy *and* coverage); use gentle/wide turns.

## Known gaps / follow-ups
- **#88** — PWM × current sweep (+ multiple speeds/steering angles) + dockside idle clamp +
  optional measured full-discharge capacity. The unlock for real (not ±30 %) numbers. The
  **measured speed↔throttle map** is now characterized from field data (§ *Speed → throttle (PWM)*,
  [`docs/analysis/2026-06-25/`](../../docs/analysis/2026-06-25/)); what #88 still owes is the
  current side (clamp-meter anchors across the PWM range) to retire the ±30 % band.
- **#171 / #162** — annunciator never warns at LVD → manual voltage watch required (class-blocking).
- **Recharge curve — characterized 2026-07-31** from the dockside voltage log
  (§ *Recharge characterization*, [`docs/analysis/2026-07-31/`](../../docs/analysis/2026-07-31/)).
  Still open on [#196](https://github.com/rolker/unh_echoboats_project11/issues/196):
  log charger current (today's readings are operator-eyeball only), bare-battery
  (systems-off) charge time, and verifying the manual's ~5 h @ 240 VAC claim.
- Cross-deployment power analysis detail: see #167.
