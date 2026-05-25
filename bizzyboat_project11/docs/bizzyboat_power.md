# BizzyBoat Power & Battery

Consolidated reference for BizzyBoat's electrical/energy behaviour: the battery system,
measured current anchors, discharge characterization, the (sensor-free) power model, and
**operational deployment-planning rules**. Companion to
[`bizzyboat_hardware.md`](bizzyboat_hardware.md) (electrical hardware) and
`bizzyboat_performance.md` (speed/dynamics; added in PR #172).

> **Key constraint — no current sensor.** `BATT_MONITOR=4` (inherited from IzzyBoat) reports
> ~0 A because no shunt is wired between the Torqeedo packs and the Cube. **Voltage is the only
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
- These anchor the V-drop model (`R_int ≈ 12.9 mΩ` from a 0.864 V drop at 67 A).
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
- **Sag vs SOC:** voltage drop at a *fixed* throttle grows **~10×** from full (~0.06 V) to
  near-empty (~0.9 V) — R_int rises in the knee *and* lower pack voltage draws more current for
  the same power. (So the constant 12.9 mΩ R_int is a simplification.)
- **Speed-dependent prop load:** at fixed full throttle the drop is largest near static
  (bollard) and shrinks ~0.3–0.4 V as the boat speeds up (prop unloads). The 67 A anchor is the
  *running* load; bollard/acceleration current is **higher**.
- **Discharge rate accelerates toward empty:** ~0.5 V/hr on the plateau-edge → **~1.5 V/hr in the
  knee** (the last volt goes ~3× faster).

## Power model (sensor-free) and its limits
Current ≈ **f(PWM, SOC, boat speed, steering)**. Estimated via the V-drop model
(`marine_tools` `bag_analysis/plots/power.py`: `I = (V_oc − V_load)/R_int`) and/or PWM-coulomb
counting (idle 8 A / full 67 A anchors; quadratic per the propeller power law).
- **Anchored at only two points** → mid-throttle (where surveys live) is interpolated.
- **Constant R_int** ignores the ~10× SOC dependence above (should be SOC-dependent).
- **Speed / steering axes uncalibrated** — and not separable from opportunistic field bags.
- Cross-deployment coulomb estimate **over-predicts ~20–30 %** vs the 273 Ah pack — a built-in
  self-consistency check (a single cycle cannot exceed the pack). **Treat all energy / endurance
  hours as ±30 % heuristics** until #88.

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

> ⚠ **No automatic warning today.** The annunciator does not fire at low battery
> (**#171 / #162**). Until fixed, the operator must watch voltage against this ladder
> **manually** — students cannot be expected to monitor raw voltage. Class-blocking.

### Battery management across a day / between cohorts
- Idle/hotel load (~5–8 A) drains the pack **even dockside**. **Charge to full before each
  deployment day** and **power gabby down between groups** when not surveying.
- Don't rely on "yesterday's charge" — one full charge ≈ a handful of in-water hours, but idle
  dominates the budget.
- **Recharge time between cohorts is not yet characterized** (only the charge-curve start was
  captured) — **measure full charge time** at the next opportunity for swap planning.

### Drive efficiently (extends every mission)
- **Survey throttle, not full** — full throttle ≈ 4 h to empty; cruise/survey stretches that ~2–3×.
- **Steady straight legs are cheapest**; accel-/turn-heavy patterns cost more (bollard load).
- **Minimize crabbing & oscillation:** align survey lines with the set/drift; address the
  SE-line undulation (#164 — over-steer wastes energy *and* coverage); use gentle/wide turns.

## Known gaps / follow-ups
- **#88** — PWM × current sweep (+ multiple speeds/steering angles) + dockside idle clamp +
  optional measured full-discharge capacity. The unlock for real (not ±30 %) numbers.
- **#171 / #162** — annunciator never warns at LVD → manual voltage watch required (class-blocking).
- **Recharge curve** — uncharacterized; measure a full charge for cohort-swap planning.
- Cross-deployment power analysis detail: see #167.
