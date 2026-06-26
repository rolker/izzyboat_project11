# 2026-06-25 BizzyBoat — power analysis + speed → throttle characterization

Companion to [`bizzyboat_project11/docs/bizzyboat_power.md`](../../../bizzyboat_project11/docs/bizzyboat_power.md)
and the cross-deployment power thread. Follows deployment
[#331](https://github.com/rolker/unh_echoboats_project11/issues/331); filed as
[#333](https://github.com/rolker/unh_echoboats_project11/issues/333).

Two parts: (1) the per-deployment power summary for 2026-06-25, in the same form as
[`docs/analysis/2026-06-23`](../2026-06-23/) / [`2026-06-24`](../2026-06-24/), and (2) a new
**speed → throttle (PWM)** characterization mined from this week's four lake surveys.

## Part 1 — 2026-06-25 deployment power summary

Coulomb count (validated quadratic PWM model `I = 8 A idle + 59 A·r²`, integrated over the GPS
dock-departure window; ±~30 %, no current sensor):

- **In-water window:** 09:55:56 → 16:24:41 = **6.48 h** (charger off 09:47:16, departed 09:55:56).
- **Distance:** 33.14 km = **17.89 nm**, mean SOG **2.76 kt**; max 0.98 nm from dock (short-radius survey).
- **Energy:** **226 Ah quad = ~83 % of the 273 Ah pack**, avg draw **35 A** (hotel/idle 23 %).
- **Voltage:** dock 28.92 V → depart 28.74 V → **return 24.10 V** → rest-end 24.79 V; min loaded 23.32 V.
- **End SOC:** ~17 % by coulomb vs ~40 % by resting voltage — returned with real margin (unlike the
  06-23 tow-in).

Efficient day: lower total draw and avg current than the two full-discharge days (06-22/06-23);
Ah/nm (12.7) matches the most-efficient prior day (06-24, 12.3), consistent with the ~2.8 kt cruise.

| Deploy | underway h | Ah (quad) | avg A | dist nm | Ah/nm | Vstart | Vend |
|---|---|---|---|---|---|---|---|
| **2026-06-25** | 6.48 | 226.4 | 35 | 17.89 | 12.7 | 28.92 | 24.79 |
| 2026-06-24 | 6.58 | 215.8 | 33 | 17.52 | 12.3 | 28.95 | 25.09 |
| 2026-06-23 | 6.22 | 273.9 | 44 | 19.33 | 14.2 | 28.68 | 20.76 |
| 2026-06-22 | 6.52 | 268.4 | 41 | 20.31 | 13.2 | 28.98 | 23.84 |

Plots: [`2026-06-25_dock_departure_voltage.png`](2026-06-25_dock_departure_voltage.png) (charger-off
step + GPS departure), [`2026-06-25_speed_vs_curve.png`](2026-06-25_speed_vs_curve.png) (today's
speed bins on the pooled endurance/range curve — the dominant 3.17 kt mode sits just past the knee).

## Part 2 — Speed → throttle (PWM), pooled 06-22/23/24/25

Throttle channel = `rc/out.ch_0` (1500 neutral, 2000 full forward, both thrusters slaved).
**throttle % = (PWM − 1500) / 5.** Two views:

**(a) Steady straight-line** — achieved odom speed, |yaw| < 0.05 rad/s (~3°/s), forward only
(18.8 h pooled). The clean hydrodynamic relationship:

| Speed | mean PWM | throttle % | ~draw |
|---|---|---|---|
| 2.0 kt | 1718 | ~44 % | 21 A |
| 2.75 kt | 1784 | ~57 % | 26 A |
| 3.0 kt | 1821 | ~64 % | 31 A |
| 3.2 kt | 1851 | ~70 % | 35 A |
| 3.3 kt | 1860 | ~72 % | 38 A |
| 3.5 kt | 1905 | ~81 % | 48 A |

**(b) Ramp-inclusive** — actual `rc/out.ch_0` binned by **commanded**
`setpoint_velocity/cmd_vel.vel_x`, no steady filter (27.8 h pooled — the steady filter discards
~32 % of survey time). Approximates typical survey-ops duty:

| commanded kt | % time | throttle % | actual kt achieved | ~draw |
|---|---|---|---|---|
| 1.36 (turns) | 10.8 % | 33 | 1.34 | 15 A |
| 3.11 | 24.9 % | 65 | 3.02 | 34 A |
| 3.32 | 9.5 % | 78 | 3.23 | 44 A |
| 3.51 | 36.4 % | 80 | 3.44 | 47 A |
| 3.88 (recovery) | 6.7 % | 94 | **3.08** | 61 A |

Plot: [`2026-06-25_cmd_throttle_current.png`](2026-06-25_cmd_throttle_current.png) — commanded speed
(x) vs throttle % and current draw (dual y), p10–p90 bands.

### Reading it

- **The PWM→speed map is strongly super-linear** (≈cubic drag). 2.75 → 3.0 kt costs +7 pts throttle;
  3.0 → 3.5 kt costs +17 pts (64 → 81 %) for the same 0.5 kt. The top of the band is expensive.
- **Cost knee ~3.0–3.1 kt:** current rises gently below it, then steeply (~34 → ~47 A, 3.1 → 3.5 kt).
  **~3.0 kt (a touch over) is the practical cruise sweet spot** — just past the ~2.9 kt range-optimal,
  before the steep cost ramp. 3.2–3.3 kt is already in the same penalty zone as the historical 3.5 kt.
- **Ramp overhead at a given commanded speed is small (+0–4 pts)** — the controller tracks well;
  re-acceleration episodes are brief relative to time-on-line, so the steady table is representative
  for "throttle to hold speed X."
- **The genuinely new finding from the commanded-speed view:** a current-heavy **post-turn recovery
  regime** — ~7 % of survey time at commanded ~3.9 kt / ~94 % throttle / ~61 A, but the hull only
  reaches ~3.1 kt. It's the controller pushing near-full throttle to re-acquire the line after turns.
  Disproportionately costly current for the speed delivered; a tuning lever (a gentler post-turn speed
  ramp trades a little line-acquisition time for materially lower peak current).

## Method

- **Stage 1 — extract:** `ros2 run bag_analysis bag_to_sqlite` (from `marine_tools`) reads each bag
  once into a focused SQLite extract (`<date>_deployment.db`; power/nav topics + the three cmd_vel
  stages). Lake current ~0 so odom SOG ≈ speed-through-water.
- **Stage 2 — coulomb / binning:** quadratic PWM-coulomb model over the GPS dock-departure window
  (dock ref = median of first 90 s of fixes; departure = first fix sustained > 10 m for 30 s; return =
  last fix > 10 m). Speed/throttle binned in 0.25 kt bins.

## Caveats

> No current sensor (`BATT_MONITOR 3`, `BATT_CURR_PIN -1`) — current/power are **modeled** (quadratic
> PWM, ±~30 %). **Relative** trade-offs and current/Ah metrics are robust; absolute amps/watts carry
> the band. Throttle % and PWM are **measured** (`rc/out.ch_0`). This pooled field data partially fills
> the throttle dimension of [#88](https://github.com/rolker/unh_echoboats_project11/issues/88) — it is
> opportunistic, not the controlled bench PWM×current sweep #88 still calls for.

## Provenance (uncommitted — `~/data/logs/analysis/2026-06-25/`)

`<date>_deployment.db` (focused extracts, 06-22/23/24/25, each re-extracted with the cmd_vel topics)
and the scripts `coulomb.py`, `dock_departure_voltage.py`, `speed_compare.py`, `speed_throttle.py`
(steady), `speed_throttle_cmdvel.py` (ramp-inclusive), `cmd_throttle_plot.py`. Source bag:
`~/data/logs/gabby/logs/bizzyboat/2026-06-25T13-05-43+00-00`.
