# BizzyBoat Power & Battery

Consolidated reference for BizzyBoat's electrical/energy behaviour: the battery system,
measured current anchors, discharge characterization, the (sensor-free) power model, and
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

## Measured current anchors (2026-04-27 external clamp meter)
Two operating points, from a Bluetooth DC clamp on the combined post-parallel output, in-water
(`docs/logs/2026/2026-04-27_dev_logs.md`):
- **Idle ≈ 8 A** (PWM 1500 both, all systems on). Composition: gabby + USB + sensors 2–4 A,
  Cube + servos + ESCs 1–2 A, comms 1–2 A, cooling/lights 1–2 A.
- **Full throttle = 67 A** (PWM 2000 both, under load) → ~1715 W at 25.6 V.
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
- **Real survey endurance ≈ 6 h / one full pack** at ~42 A average draw (06-23: 19.2 nm in 6.16 h;
  06-22: 6.5 h). The "8–12 h" cruise extrapolation below was optimistic.
- **Usable capacity to the BMS cutoff ≈ the full ~273 Ah nameplate** (cutoff ~20.6 V loaded).

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
- **Recharge time between cohorts is not yet characterized** (only the charge-curve start was
  captured) — **measure full charge time** at the next opportunity. BizzyBoat charges **in place**
  (batteries are not field-swappable), so recharge-to-full time bounds the day/cohort cadence.

### Drive efficiently (extends every mission)
- **Plan for ~6 h of survey per full charge** (measured 2026-06-23 + 06-22, ~42 A average). Full
  throttle ≈ 4 h; a real survey is **~6 h to empty** — *not* the older 8–12 h cruise extrapolation.
- **Survey speed is already near range-optimal (~3–3.5 kt)** — 2026-06-23 modeling shows slowing to
  2 kt buys loiter *time*, not *miles* (fixed ~8 A hotel load); >4 kt range falls off fast.
- **Steady straight legs are cheapest**; accel-/turn-heavy patterns cost more (bollard load).
- **Minimize crabbing & oscillation:** align survey lines with the set/drift; address the
  SE-line undulation (#164 — over-steer wastes energy *and* coverage); use gentle/wide turns.

## Known gaps / follow-ups
- **#88** — PWM × current sweep (+ multiple speeds/steering angles) + dockside idle clamp +
  optional measured full-discharge capacity. The unlock for real (not ±30 %) numbers.
- **#171 / #162** — annunciator never warns at LVD → manual voltage watch required (class-blocking).
- **Recharge curve** — uncharacterized; measure a full charge for cohort-cadence planning (charge-in-place; no battery swap).
- Cross-deployment power analysis detail: see #167.
