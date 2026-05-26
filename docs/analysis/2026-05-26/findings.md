# 2026-05-26 deployment — post-mission analysis findings

Deployment [#173](https://github.com/rolker/unh_echoboats_project11/issues/173). Focus of the day was **reflex collision avoidance** (Phase A feed + Phase B Collision Monitor, both merged 2026-05-26).

Analysis artifacts (on dev, `~/data/logs/analysis/2026-05-26/`): `launch_recovery.db`, `collision.db` (+ `cloud_range` table), and the reusable scripts `enumerate_collision_events.py`, `extract_cloud_range.py`, `margin_vs_speed.py`. Source bags: `~/data/logs/bizzyboat/2026-05-26T{15-50-33,16-36-35,17-48-49}+00-00`.

This is a **first pass** — the headline collision-avoidance result is settled; the stopping-distance-vs-speed curve is flagged as incomplete (see §5).

## 1. In-water window

Detected from the altitude profile (SBG-EKF + mavros, longest contiguous run within 2 m of the minimum smoothed altitude, spanning the two in-water bags):

| | Time (EDT) |
|---|---|
| Launch (settled in water) | **12:48:54** |
| Recovery (lifted out) | **14:08:40** |
| In-water duration | **1 h 19 m 46 s** |

The wider 12:43 → 14:17 wall-clock span (real-time log) brackets the crane operations on each end; the above is the actual on-water window.

## 2. Collision avoidance — gating correctness

The Collision Monitor publishes `/bizzy/collision_monitor_state` only on action and flickers as the ~1 Hz reflex cloud updates, so raw transition counts (802 NONE→SLOWDOWN, 180 into STOP) over-represent discrete attempts. Clustering engaged samples by time gap:

| Clustering gap | In-water engagement episodes |
|---|---|
| 15 s | 61 |
| 30 s | 29 |
| 60 s | 6 |

The 6-at-60 s figure is closest to "distinct approach campaigns" (buoy set + the breakwater runs at increasing speed); finer counts are individual engagements within those.

**Gating behaves as configured:**
- **Slowdown** → gated `/bizzy/piloting_mode/autonomous/cmd_vel` reduced to **≈0.22–0.30×** the commanded `/bizzy/cmd_vel_nav` (matches the configured `slowdown_ratio: 0.3`).
- **Stop** → gated output driven to **0.00**.

**Approach speed range:** STOP-reaching approaches spanned commanded speeds **0 → 2.57 m/s** (median 0.88; ~5 kt at the top — well above survey speed). Speed bands of STOP events: `<0.5`: 12, `0.5–1.0`: 10, `1.0–1.5`: 13, `1.5–2.0`: 2, `≥2.0`: 4.

## 3. Stopping margin & the near-blind zone (key finding)

Obstacle range was taken from the reflex cloud itself — published in `bizzy/base_link_level` (body frame, z=0), so the nearest forward point's planar range is the obstacle distance.

- Across 26 clean approach-and-stop events, the nearest *detected* obstacle range never fell below **2.0 m** (median min-range **2.2 m**) — **no contact**, consistent with the operator's observation.
- That ~2 m is also a **detection floor**: the forward camera's projection geometry cannot place an obstacle closer than ~2 m to the waterline. Obstacles that get inside ~2 m **disappear from the cloud**, so the monitor cannot sustain a stop on them.

**Operator-observed consequence (the important part):**
- A **buoy** (small): as it slipped into the ~2 m near-zone it vanished from the cloud → the monitor cleared → **the boat resumed the track**.
- The **floating breakwater** (large/extended; this is what was loosely called a "seawall"): big enough that points stayed visible beyond 2 m even as the boat closed in → the **stop sustained**.

**Conclusion:** the reflex CA reliably stops for **large/extended** obstacles (breakwater, shoreline, docks, large vessels) but **does not reliably stop for small obstacles** (buoys, mooring balls). The small-obstacle case is exactly the recurring-collision hazard (2026-05-01 mooring-ball near-miss, 2026-05-21 floating platform, 2026-05-22 mooring). The deployment validated CA for the big-structure case; the motivating mooring-ball problem is **not fully solved**.

**Mitigation directions (to scope as follow-up, not decided):**
- **Stop-latch / obstacle-memory** — hold the stop for a few seconds after an obstacle vanishes in the near zone instead of resuming instantly (likely cheapest, highest leverage).
- **Near-field coverage** — a forward-down camera or other sensor for the <2 m blind zone.
- **Speed cap** so coast-down cannot carry a small obstacle into the blind zone before the boat halts (depends on the §5 stopping-distance curve).

## 4. `pid_state` recording — confirmed

`/bizzy/FollowPath/pid/pid_state` (`control_msgs/PidState`) recorded **10,310 + 3,234** messages across the two in-water bags. The objective-3 "did it land in the bag" check is closed; the #164 cross-track-error analysis is unblocked. The topic is namespaced under `/bizzy/` (verified live by the gabby agent), not the global `/FollowPath/...` the issue's source-note predicted.

## 5. Sound speed (#163) — resolved

`/bizzy/sensors/sound_speed/sound_speed` (`marine_interfaces/SoundSpeed`) during the in-water window:

- **98.8% valid readings** (117,961 of 119,346); only **1.2% zero-dropouts**.
- Real values **1481.9–1491.0 m/s, median 1489.9** — a tight, plausible saltwater sound speed for ~10–12 °C coastal water.
- First valid reading **19 s after launch** (12:49:13) — the probe settling on water entry; that 19 s is the single longest zero-gap. The remaining dropouts are 70 brief scattered spans.
- Pre-launch (on the cart) reads 0.0 — dry, expected.

This is a complete turnaround from the 2026-05-22 all-NUL failure ([#163](https://github.com/rolker/unh_echoboats_project11/issues/163)): the AML SVS probe produced good, stable data in the water. **#163 can move toward closed.** Minor follow-up: watch the ~1.2% intermittent zero-dropouts if M3 sound-speed accuracy proves sensitive (M3 presumably holds last value). See `sound_speed.png` in the analysis artifacts.

## 6. Coast distance vs. approach speed — inconclusive (next pass)

Intended to answer: does the ~10–15 m coast-down (no reverse action; [#88](https://github.com/rolker/unh_echoboats_project11/issues/88)) eat the stopping margin as approach speed climbs, and what is the safe survey speed?

The first-pass metric (path length from first gated≈0 to first halt, per STOP episode) came out **contaminated** — several events show implausible 40–106 m "coast," which reflects loiter / repositioning / possible manual control within an engagement episode, not a single physical deceleration. `corr(speed, coast) = +0.46` is weak and not trustworthy.

A clean stopping-distance-vs-speed curve needs: isolation of the **single monotonic deceleration** from peak approach to halt, **autonomous-only** filtering (drop manual segments), and cross-check of the high-speed runs against the camera video. Deferred to the next analysis pass.

## 7. Pending (next analysis pass)

- Coast / stopping-distance vs. approach speed (§6) → safe survey speed.
- Transit-path turning behavior: yaw cap 1.0 + planner min radius 1.5 m, from `/bizzy/plan` curves + execution (the limits were exercised only in transit-to-line-start planning this run — individual tracklines, no survey-pattern apron turns).
- `pid_state` cross-track-error dig (#164).
- Mission re-send replay — `mission_manager` `Current Nav Task` + `behavior_tree_log` around the reproductions (git-bug `7709673`). Note: `follow_path`/`run_tasks` action-status goal UUIDs were not recorded (transient_local rosbag2 gap), limiting offline goal-id correlation.
