# BizzyBoat performance characterization — analysis tooling

Reproducible analysis behind [`docs/bizzyboat_performance.md`](../../bizzyboat_performance.md)
and [#124](https://github.com/rolker/unh_echoboats_project11/issues/124) §2
(Performance characterization). Pools 7 in-water deployments
(2026-04-24 → 2026-05-22) to extract steady-state speed, current, and
acceleration/deceleration dynamics.

## Contents

| File | Purpose |
|---|---|
| [`dynamics.py`](dynamics.py) | Max/cruise speed (circle-fit current removal) + acceleration (first-order surge fit) per deployment. |
| [`dynamics_extra.py`](dynamics_extra.py) | Battery↔STW correlation, coast-down deceleration, reverse bound. |
| [`turning.py`](turning.py) | Turn rate by flight mode, steering-PWM→yaw effectiveness, turn radius (yaw-rate-cap analysis). |
| [`xte.py`](xte.py) | Course-keeping on straight legs: track-holding precision (line-fit residual) + XTE vs the planned path. |
| [`queries.sql`](queries.sql) | Reference SQL: PWM-channel identification, in-water window, and the heading-contamination demonstration. |

## Method in one paragraph

All speed signals (`mavros/global_position/raw/gps_vel`,
`mavros/local_position/velocity_body`) are **speed-over-ground**, so they
contain tidal current. At a fixed throttle the boat's ground-velocity
vector is `v_ground = STW·(heading unit) + current`; over many headings
the `(east, north)` samples trace a **circle of radius STW centred on the
current vector**. An algebraic (Kåsa) circle fit to the steady, straight,
fixed-throttle cloud recovers speed-through-water *and* the current vector
together — no per-pair heading matching. Acceleration uses a first-order
surge model `v(t) = v∞·(1 − e^(−t/τ))` fitted to clean throttle steps;
deceleration uses the mirror decay on throttle-to-idle chops.

Throttle PWM is `mavros/rc/out.ch_0` (ESC; `ch_1` mirrors it; `ch_2`/`ch_3`
are the vectored-thrust steering servos). The EKF `velocity_body` is used
where present (2026-05-01 onward) and `gps_vel` elsewhere — both are the
universal signals recorded in every deployment.

## Reproducing — local-only artifacts

The scripts read prebuilt per-deployment SQLite extracts from
`~/data/logs/analysis/` on the dev workstation. They are **not** committed
(0.5–3 GB each) but are regeneratable from the bags:

```bash
# Deployments with a full DB already (camera + everything): 05-01, 05-21, 05-22
#   <date>_deployment.db

# Deployments needing a focused nav extract (04-24/27/29, 05-19):
#   <date>_nav.db  — small, nav/actuator topics only
source .agent/scripts/setup.bash
source layers/main/sensors_ws/install/setup.bash
ros2 run bag_analysis bag_to_sqlite \
  --bag ~/data/logs/bizzyboat/<date>T<first-session> \
  --output ~/data/logs/analysis/<date>_nav.db \
  --topics /bizzy/mavros/rc/out \
           /bizzy/mavros/global_position/raw/gps_vel \
           /bizzy/mavros/global_position/raw/fix \
           /bizzy/mavros/local_position/velocity_body \
           /bizzy/mavros/imu/data \
           /bizzy/mavros/setpoint_velocity/cmd_vel \
           /bizzy/piloting_mode/autonomous/cmd_vel
# append each subsequent session of the same day with --append.

# Run the analysis (uses the workspace venv: numpy/pandas/scipy)
.venv/bin/python3 docs/analysis/dynamics/dynamics.py        # all deployments
.venv/bin/python3 docs/analysis/dynamics/dynamics_extra.py  # battery/decel/reverse
# turning.py + xte.py need the FULL <date>_deployment.db (turning.py uses
# mavros/state; xte.py needs the plan + odom tables) — NOT the focused
# *_nav.db topic list above. Run them against 05-01/21/22 deployment DBs:
.venv/bin/python3 docs/analysis/dynamics/turning.py         # turn rate / steering / radius
.venv/bin/python3 docs/analysis/dynamics/xte.py             # course-keeping (XTE)
```

**Topic availability**: PWM (`rc/out`) and `gps_vel` are in every
deployment. The EKF `velocity_body` and SBG topics start at 2026-05-01;
`global_position/global` (used for crane-edge window detection) is absent
in April, so April nav DBs fall back to the full bag time-range.

## NOAA current cross-check

The fitted current vector is validated against NOAA CO-OPS predicted
tidal current at station **ACT0731 (Clark Island)** — the main-channel
station, not the side-pocket ACT0726. Station axis: flood→270° / ebb→85°.
The two deployments whose windows straddled NOAA slack (05-22, 04-27) fit
only ~0.1 m/s current (within those fits' rms); magnitudes are
order-consistent on the others. Direction is
approximate — the pier work area deviates from the main-channel axis, and
direction is the circle fit's least-constrained parameter on partial arcs.

## Follow-up

The circle-fit / surge-fit logic should graduate into
[`rolker/marine_tools`](https://github.com/rolker/marine_tools)'s
`bag_analysis` package as a reusable `dynamics` extractor (same path the
§1 `network_perlink.py` walker is slated to take). Controlled
steady-hold / step / reverse / crash-stop runs to fill the high-throttle
and reverse gaps are tracked in
[#88](https://github.com/rolker/unh_echoboats_project11/issues/88).
