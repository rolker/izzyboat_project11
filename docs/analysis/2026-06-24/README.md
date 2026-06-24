# 2026-06-24 BizzyBoat — speed → power / endurance / range characterization

Companion to [`bizzyboat_project11/docs/bizzyboat_power.md`](../../../bizzyboat_project11/docs/bizzyboat_power.md)
(§ *Speed → power, endurance, range*) and the cross-deployment power comparison that
began with the 2026-06-24 Massabesic survey
([#326](https://github.com/rolker/unh_echoboats_project11/issues/326)).

Pools **three Massabesic lake surveys** (2026-06-22, 06-23, 06-24 — ~14 h of steady
straight-line running) into an empirical speed→power curve. The lake has negligible
current, so odometry speed-over-ground ≈ speed-through-water; the curve is clean across
the operational ~2–4 kt band.

## Headline

- **Range plateau is ~2.0–2.9 kt** (~27–28 nm / ~31–33 statute mi on a full pack).
  **3.5 kt — the historical most-used cruise — is past the plateau** (~20 nm, ≈ −25 % range).
- **Endurance** ranges from ~13.5 h at 2.0 kt to ~5.9 h at 3.5 kt — more than 2× by
  slowing down, which matters when time-on-station (not distance) is the constraint.
- Sweet spot for mixed range/endurance constraints ≈ **2.9–3.0 kt**; push to 3.5+ kt only
  when the clock is the hard limit and reserve has margin.

## Plot (committed)

- `speed_endurance_range_curve.png` — 3 panels: endurance vs speed, range vs speed,
  and time-at-speed + mean current vs speed (pooled lake surveys).

## Method

- **Stage 1 — extract:** `bag_to_sqlite` (from `marine_tools` `bag_analysis`) reads each
  bag once into a focused SQLite extract (`<date>_deployment.db`, power/nav topics).
- **Stage 2 — coulomb count:** validated **quadratic** PWM model
  `I = 8 A idle + 59 A·r²`, `r = min(|pwm−1500|/500, 1)`, integrated over the in-water
  window; paired to odom speed and measured bus voltage. Endurance = 273 Ah pack ÷ draw
  (current includes the ~8 A hotel load); range = speed × endurance.
- **In-water window = GPS dock departure/return** (the boat is tied to a dock at the lake,
  so the crane-altitude launch/recovery detector does not apply): dock ref = median of the
  first 90 s of fixes; departure = first fix sustained > 10 m; return = last fix > 10 m.
- **Validation:** the 06-23 full-charge → BMS-cutoff run gives 273.9 Ah (quad) over its
  in-water window vs the 273 Ah pack nameplate (it actually emptied), and 273 Ah ÷ 44 A
  avg = 6.2 h predicted, matching its measured underway time.

## Caveats

> No current sensor (`BATT_MONITOR 3`, `BATT_CURR_PIN -1`) — current/power are **modeled**
> (quadratic PWM, ±~30 %). The **relative** speed trade-offs and the current/Ah-based
> metrics are robust; absolute amps/watts carry the band. Pier deployments are **excluded**
> — tidal current makes their speed-over-ground an unreliable stand-in for speed-through-water.

## Provenance (uncommitted — `~/data/logs/analysis/2026-06-24/`)

`2026-06-24_deployment.db` (focused bag extract) and the scripts `coulomb.py`
(cross-deployment coulomb + per-day detail), `speed_bins.py` (single-day 3.0 vs 3.25 kt),
and `speed_curve.py` (the pooled lake speed curve + this plot). Source bag:
`~/data/logs/gabby/logs/bizzyboat/2026-06-24T12-11-05+00-00`. Regenerate the DB with
`ros2 run bag_analysis bag_to_sqlite` then rerun `speed_curve.py`.
