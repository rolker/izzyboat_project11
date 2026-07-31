# 2026-07-31 BizzyBoat — recharge characterization (dockside voltage log)

Companion to [`bizzyboat_project11/docs/bizzyboat_power.md`](../../../bizzyboat_project11/docs/bizzyboat_power.md)
(§ *Recharge characterization*) and issue
[#196](https://github.com/rolker/unh_echoboats_project11/issues/196)
(charger idle-current capture + power-model review). Closes the long-standing
"recharge time is not yet characterized" gap using data already on hand: gabby's
dockside battery logger (1-minute FCU voltage samples), 2026-06-09 → 07-30,
covering **15 charge events** including three near-empty starts.

## Headline

- **Full recharge from empty takes ~14–16 h on 120 VAC** (boat systems on during
  charge, as is standard practice — the logger itself needs gabby up). Deepest
  event: 06-23, the BMS-cutoff day — the last telemetry row before the cutoff
  outage reads 20.94 V (a `source=mavros` row; the `fcu` log gaps 85 min and
  resumes at 22.24 V rested) — ramp 22.5 → 28.95 V in **14.2 h**. 07-20: 15.5 h.
  One 21.1 h outlier (06-27): an initial dip/pause accounts for ~1.5 h of the
  excess, the rest was a genuinely slower ramp (presumably heavier hotel load) —
  don't skip the pre-launch resting-voltage check after an overnight charge.
- **Same-day turnaround from empty is not possible on 120 VAC** — a ~6 h
  run-to-empty survey needs ~15 h of charge. Overnight works: plug in by ~17:00,
  full by ~08:00. This is the binding cohort-cadence number the power doc
  previously flagged as unmeasured.
- **AC draw at 120 VAC ≈ 7–8 A peak (bulk), ~2 A at float** — inferred, see method.
  A standard 15 A outlet has ample margin.
- Charge terminates at a **29.0 V plateau** (max observed 29.06 V; matches the
  29.05 V final-charge spec). The main ramp ends at ~28.8 V; the last 0.15 V is
  a ~1 h taper.

## Plot (committed)

- `charge_ramps.png` — left: all 15 charge ramps aligned at charge start
  (near-empty starts colored, partial recharges gray); right: recharge duration
  vs starting voltage.

## Event table (from the script)

| Charge start | V at start | h → 28.8 V | h → 28.95 V |
|---|---|---|---|
| 06-09 16:30 | 27.28 | 4.0 | 5.0 |
| 06-11 16:12 | 27.56 | 3.6 | 4.5 |
| 06-12 19:41 | 26.77 | 8.6 | 9.9 |
| 06-15 17:01 | 26.41 | 7.7 | 8.9 |
| 06-16 17:06 | 25.09 | 12.0 | 13.3 |
| 06-17 17:37 | 24.05 | 15.6 | (unplugged at 28.8) |
| **06-23 17:17** | **22.46** | **13.1** | **14.2** |
| 06-24 16:56 | 25.13 | 12.6 | 13.9 |
| 06-25 16:44 | 24.85 | 9.8 | 10.8 |
| **06-27 12:06** | **21.77** | 19.7 | 21.1 |
| 06-29 17:16 | 24.80 | 13.3 | 14.8 |
| **07-20 14:08** | **23.28** | **14.4** | **15.5** |
| 07-21 14:10 | 27.14 | 10.3 | 11.4 |
| 07-23 19:42 | 24.54 | 10.7 | (unplugged at 28.94) |
| 07-29 14:50 | 27.10 | 4.8 | 5.8 |

Spread at similar starting voltage (e.g. 06-25 vs 06-29, both ~24.8 V: 10.8 vs
14.8 h) is expected — the hotel load during the charge varies with what was left
running, and the detector's charge-start point is ±the 1-minute sample cadence
plus post-run voltage recovery.

## Method

- **Input:** gabby's `bizzy_battery` cron logger — 1-minute `timestamp,voltage_v`
  samples from the FCU (`source=fcu` rows), synced to the dev machine at
  `~/data/logs/gabby/logs/bizzy_battery/battery_YYYY-MM-DD.csv`. ~29 k samples
  over 52 days.
- **Detection:** 5-sample median smoothing; a charge ramp starts when voltage is
  below 28.3 V and rises at > 0.10 V/h sustained over 30 min; it ends at 28.95 V,
  at a > 3 h data gap, or when a > 0.6 V drop shows discharge resumed. Events
  reaching at least 28.8 V are kept.
- **AC-side inference (no measurement on this hull):** the Torqeedo fast charger
  is rated 750 W **out** @ 100 VAC / 1700 W **out** @ 240 VAC (EchoBoat 240 manual
  §3.6.1) — output scales linearly with input voltage, i.e. the charger is
  input-current-limited at ~8 A from the wall (7.1–7.5 A output-equivalent,
  ~7.9–8.3 A actual at ~90 % conversion efficiency), giving ~850 W out (~950 W in)
  at 120 VAC. Cross-check from the data: replacing ~7000 Wh in ~14.2 h *plus* the
  ~180 W hotel load (6.2 A × ~29 V, the measured charger idle/maintenance reading)
  ≈ 670 W DC ≈ 730 W from the wall at 90 % ≈ **6 A average at 120 V** — consistent
  with a ~8 A bulk-phase draw and taper.

## Caveats

> No current sensor and no charger-side logging — every charge event includes
> whatever hotel load was left on (gabby at minimum), so these are **operational**
> recharge times, not bare-battery times; they are the right numbers for cadence
> planning but will shorten if the boat is powered down while charging. The
> manual's "~5 h at 240 VAC" is unverified on this hull (US 120 VAC shore power).
> AC amps are inferred from charger ratings + energy balance, not measured.

## Provenance (uncommitted — `~/data/logs/analysis/2026-07-31/`)

`charge_ramps.py` — loads the CSVs, prints the event table, writes
`charge_ramps.png`. Rerun with
`python3 charge_ramps.py <this directory>` as more charge cycles accrue.
