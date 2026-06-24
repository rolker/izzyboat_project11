# 2026-06-23 BizzyBoat — full-discharge power analysis

Companion to the deployment record [`docs/logs/2026/2026-06-23_dev_logs.md`](../../logs/2026/2026-06-23_dev_logs.md)
(deployment [#313](https://github.com/rolker/unh_echoboats_project11/issues/313))
and RCA [#315](https://github.com/rolker/unh_echoboats_project11/issues/315).

First real **full-charge → BMS-cutoff** on the water (the 2026-05-22 drain-to-LVD
test #160 stopped at 21.2 V; this one went all the way and the boat was towed in).

## Headline numbers

- **Distance on the charge:** 35.59 km = **19.22 nm** over **6.16 h** (09:39:20 → 15:48:52); mean SOG 3.1 kt. Died **1.29 nm from the dock**.
- **Range-optimal speed** ~3–3.5 kt (today was already there); 2 kt buys loiter time, not miles.
- **Point of no return** 15:07:45 (~22.9 V) — only ~2 min after the 23 V annunciator warning.

## Plots (committed)

- `2026-06-23_charge_distance_speed.png` — track (colour = time) + modeled range-vs-speed.
- `2026-06-23_turnback.png` — tank-left vs distance-home; point of no return.
- (charger/departure plot lives at `docs/logs/2026/2026-06-23_dock_departure_voltage.png`.)

## Provenance (uncommitted — `~/data/logs/analysis/2026-06-23/`)

`bag_arrays.npz` (cached bag extract) and the analysis scripts
`stage_a_read.py` / `stage_b_analyze.py` / `stage_c_turnback.py` /
`dock_departure_voltage.py`. Source bag:
`~/data/logs/gabby/logs/bizzyboat/2026-06-23T13-03-52+00-00` (file `_81` is
truncated — the boat lost power mid-write; readers skip it).

> Power/current figures are V-drop estimates (±~30 %, no current sensor,
> `BATT_MONITOR 3`). Distance and positions are real GPS. Coulomb-count via the
> `bag_analysis` pipeline + cross-deployment comparison (#167) is a pending follow-up.
