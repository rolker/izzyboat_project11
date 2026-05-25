# BizzyBoat performance characterization

Current-corrected speed and acceleration/deceleration dynamics, pooled
across 7 in-water deployments (2026-04-24 → 2026-05-22). This is a living
document; numbers are derived from logged-bag analysis and are refined as
deployments accumulate.

- **Issue**: [#124](https://github.com/rolker/unh_echoboats_project11/issues/124) §2 (Performance characterization)
- **Reproducible analysis**: [`docs/analysis/dynamics/`](analysis/dynamics/) (method, scripts, regen recipe)
- **Supersedes for speed**: [`docs/bizzyboat_dynamics_2026-04-24.md`](bizzyboat_dynamics_2026-04-24.md) (single-deployment, *not* current-corrected)
- **Controlled-experiment follow-up**: [#88](https://github.com/rolker/unh_echoboats_project11/issues/88)

## TL;DR specifications

| Metric | Value | Confidence |
|---|---|---|
| **Max forward speed** | **~1.9 m/s (3.7 kt)** STW, full throttle | Good — two clean independent fits agree |
| **Cruise speed** | **~1.52 m/s (3.0 kt)** STW @ PWM 1750–1850 | High — three clean fits agree exactly |
| **Hard-launch acceleration** | **~0.6 m/s² peak**, τ ≈ 2.5 s (reaches ~1.6 m/s) | Moderate — few clean step events |
| **Survey throttle ramp** | ~0.1 m/s², τ ≈ 8 s | Good |
| **Coast-down deceleration** | ~0.15 m/s² (up to ~0.25), τ ≈ 9–10 s (~10–15 m to stop from cruise) | Moderate |
| **Max reverse speed** | ~1.4 m/s (2.7 kt) peak, briefly | Low — sustained reverse under-sampled |
| **Yaw-rate cap (autonomy)** | **1.0 rad/s** (raised from 0.5; = helm default) | vehicle-capability backstop; ~0.9 rad/s pivot at full throttle (vectored thrust) |
| **Min turn radius @ cruise** | ~1.5 m (was ~3 m) | governed by planner `minimum_turning_radius` 3.0→1.5 m; helm 1.0 cap now aligns |
| **Course-keeping (track-holding)** | **~0.13 m RMS** on straight legs | decimeter-scale; not a survey-limiting factor (XTE vs commanded line ~0.5 m) |

All speeds are **speed-through-water (STW)**, current-removed. Throttle is
expressed as ESC PWM (`mavros/rc/out.ch_0`): 1500 = neutral, 2000 = full
ahead, 1000 = full astern.

## Why current removal matters

Every speed signal on the boat (`gps_vel`, EKF `velocity_body`) is
**speed-over-ground** and therefore contains tidal current. The effect is
first-order, not a nuisance: at a *fixed* full throttle the raw
speed-over-ground varies up to **3×** with heading (≈0.8 m/s upstream vs
≈2.3 m/s downstream on 2026-05-01). Binning speed against PWM alone — the
preliminary 2026-04-24 method — therefore measures whatever heading/current
mix the mission happened to run, not the boat.

The fix (see [`analysis/dynamics/`](analysis/dynamics/)): at a fixed throttle
the ground-velocity vectors over varied headings trace a circle of radius =
STW centred on the current vector. A circle fit recovers both. Fit quality
tracks **heading-arc coverage and speed steadiness**, not current magnitude:
the cleanest circles (rms ≤ 0.06 m/s) are the cruise fits, which pair a wide
heading spread with stable speed. A weak-current full-throttle fit can still
be noisy if its heading arc is partial.

## Forward speed

Circle-fit STW at full throttle (PWM 1950–2000) across deployments:

| Deployment | STW | fit rms | fitted current | note |
|---|---|---|---|---|
| 2026-04-27 | **1.94 m/s (3.78 kt)** | 0.21 | 0.10 | |
| 2026-05-21 | **1.91 m/s (3.71 kt)** | 0.14 | 0.47 | cleanest high-n fit |
| 2026-05-22 | 1.55 m/s (3.01 kt) | 0.20 | 0.10 | noisier fit |
| 2026-05-01 | 1.33 m/s (2.58 kt) | 0.20 | 0.61 | noisier, high current |

(2026-04-24/29 and 05-19 had too few sustained full-throttle samples.)

The two cleanest fits agree at **~1.9 m/s (3.7 kt)**, taken as the max
forward STW. The lower values come from noisier fits (high current, partial
heading arcs), **not** from a slower boat — see the battery note below.

**Cruise (PWM 1750–1850)** is exceptionally well-determined — three
independent *clean* fits (rms ≤ 0.06 m/s):

| Deployment | STW | fit rms |
|---|---|---|
| 2026-04-29 | 1.51 m/s | 0.050 |
| 2026-05-19 | 1.53 m/s | 0.059 |
| 2026-05-21 | 1.53 m/s | 0.058 |

→ **~1.52 m/s (3.0 kt)**. The intermediate PWM band (1550–1750) is not
cleanly resolved from opportunistic survey data (insufficient heading
diversity at fixed sub-cruise throttle); the controlled steady-hold runs in
[#88](https://github.com/rolker/unh_echoboats_project11/issues/88) are the
way to fill in the curve between idle, cruise, and full.

### Battery sag — tested, not detected

The full-throttle spread (1.33–1.94 m/s) was hypothesised to be battery
voltage sag over long missions. **It is not supported by the data**:
within-mission full-throttle STW does not track voltage, and across
deployments the gross voltage difference does not either (2026-05-22 ran at
22–23 V yet its STW sits *between* the 26–27 V days). The spread is
fit-quality-driven. BizzyBoat has no current meter, so true electrical power
is unmeasurable; only battery voltage is logged (and used here as context,
never as power).

## Acceleration

First-order surge fits `v(t) = v∞·(1 − e^(−t/τ))` on clean throttle steps
(EKF `velocity_body`, 2026-05-01+):

- **Hard launch (idle → full throttle)**: peak surge **≈0.6 m/s²**,
  τ ≈ 2.5 s, settling near ~1.6 m/s. Consistent across the (few) clean
  launch events.
- **Gentle survey throttle ramp**: peak surge ≈0.1 m/s², τ ≈ 8 s.

## Deceleration

Coast-down (throttle chopped to neutral, passive drag only), first-order
decay fit:

- Peak deceleration **~0.15 m/s²** (median; up to ~0.25), τ ≈ 9–10 s,
  from a cruise of ~1.5 m/s.
- Implication: passive stopping distance is **~10–15 m** from cruise. **The
  boat does not stop quickly on throttle-off** — fast stops require active
  reverse thrust, which is the braking authority and is under-characterised
  (see Reverse).

## Reverse

Reverse is under-determined. The boat rarely holds a straight reverse
heading, so the circle fit starves (no heading diversity). What the data
bounds:

- **Peak reverse**: body-frame ~1.4 m/s (2.7 kt) reached *briefly*
  (−1.37 m/s on 05-01, −1.42 on 05-21).
- Sustained straight-reverse STW is not reliably measurable from
  opportunistic data.

A dedicated straight-reverse + crash-stop run is needed for a firm reverse
spec and braking distance — folded into
[#88](https://github.com/rolker/unh_echoboats_project11/issues/88).

## Turning

Analysis in [`analysis/dynamics/turning.py`](analysis/dynamics/turning.py),
using the EKF yaw rate (`velocity_body.omega_z`), steering servo PWM
(`rc/out.ch_2`; `ch_3` is bit-identical — a single slaved steering DOF),
and flight mode (`mavros/state`).

Steering is **vectored thrust** — the thrusters themselves rotate (servos
`ch_2`/`ch_3`, bit-identical = one slaved steering DOF), there is no rudder.
So yaw authority comes from **thrust × steering angle**, not from water flow
over a control surface, and works at any boat speed.

### The yaw-rate cap and how binding it is

During the analyzed deployments the helm clamped `cmd_vel.angular.z` to
`max_yaw_speed` = **0.5 rad/s** (`bizzyboat.yaml`; the helm's own default is
1.0, sim nodes hardcode 0.5) — **since raised to 1.0** (see *Change applied*
below).
0.5 was not a tuned-to-capability value: per the deployment log it was
reduced 1.5 → 0.5 during an April steering-direction-reversal investigation
(for steering "range/resolution"). That reversal is a **stationary
controls-check artifact** — it still occurs with the boat on the trailer
(no yaw feedback, suspected `PILOT_STEER_TYPE=0` PID windup) and is
**orthogonal to this parameter**; on-water steering has been sound across
clean autonomous missions.

The cap is **binding**: the crabbing path-follower emits raw heading error
as `angular.z` (range ±π, no proportional shaping), and the fraction of
nonzero yaw commands pinned at the 0.5 ceiling ranges **8% (05-01) to 39%
(05-22)** across deployments (~21% pooled) — so the clamp directly sets
line-transition sharpness ("turn at max until aligned").

### Yaw authority is thrust-driven (PWM as steering-angle proxy)

Median yaw rate (rad/s) by throttle × steering deflection (`ch_2 − ~1435`
centre; full deflection ±~500):

| throttle | full-left (−450) | centre | full-right (+450) |
|---|---|---|---|
| idle (1500–1650) | ≈ 0 | 0 | ≈ 0 |
| mid (1650–1800) | −0.15 | 0 | +0.18 |
| full (1800–2000) | −0.32 to −0.43 | 0 | +0.35 to +0.44 |

At **idle, full steering yields ~zero yaw** (no thrust to vector); at **full
throttle, steering yields strong yaw even at zero speed** — the peak sample
is **0.91 rad/s at full throttle + near-full steering + 0.08 m/s** (pivoting
in place). This is the vectored-thrust signature: turning authority scales
with thrust, not speed.

### What that means at cruise

In GUIDED the achieved yaw is gated at the clamp (cruise p99 0.39–0.45);
**unclamped MANUAL turns reached 0.74 rad/s at cruise** (speeds to ~1.8 m/s),
so the boat *does* exceed 0.5 at speed — what's missing is a *sustained
commanded* turn at the higher rate. Because vectoring thrust to turn diverts
it from forward, the boat **slows into a hard turn** (and lower speed means
*more* yaw authority, not less — no rudder-style stall).

For **Nav2-planned** motion the binding constraint is not the helm clamp but
the planner's `minimum_turning_radius` (`SmacPlannerHybrid`): a planned arc
that radius wide never demands more yaw than `v / R`. It was **3.0 m**
(≈ 0.5 rad/s at cruise — which exactly matched the *old* helm clamp) and has
been **reduced to 1.5 m** ([seafloor_echoboat_project11#24](https://github.com/rolker/seafloor_echoboat_project11/pull/24),
shared config) ≈ 1.0 rad/s at cruise — now aligned with the raised helm cap.
So planned line-transitions tighten from ~3 m to ~1.5 m; the helm cap only
bites on heading-error transients, hover, and manual. (Whether the Smac
planner is actually in the loop for survey line-transitions vs. the trackline
being fed straight to the follower is unconfirmed from logs — the filter
chain was disconnected during troubleshooting — so verify on the next
deployment.)

### Change applied + caveat

`max_yaw_speed` raised **0.5 → 1.0 rad/s** — i.e. set to the helm's own
default, treating this clamp as the **vehicle-capability backstop** rather
than an operational limit. 1.0 sits just above the demonstrated peak (~0.9
pivot, 0.97 raw), so the helm now rarely clamps — the boat turns as hard as
it can, with no speed-dependent stall (vectored thrust). **Validate on the
next deployment**: confirm GUIDED cruise turns track the command without
oscillation, and watch steering-direction consistency at the higher rate
(given the stationary reversal history). A controlled yaw-vs-throttle sweep
is folded into [#88](https://github.com/rolker/unh_echoboats_project11/issues/88).

**Survey-turn gentleness is currently unenforced — by design, for now.** A
"turn gently for survey lines" limit belongs at the Nav2 layer, not the helm.
The cmd_vel filter chain that would host it — the **velocity_smoother and
other cmd_vel filters were deliberately disconnected during an earlier
boat-troubleshooting pass** — so the helm clamp is presently the *sole*
cmd_vel governor. (Consistent with the logs: the FCU clamped at exactly the
helm value, never the smoother's configured 0.45, and the crabbing follower
emits raw ±π with no shaping.) So with the helm opened to 1.0, nothing bounds
line-transition sharpness right now. Re-enabling the filter chain and siting
the survey yaw limit in the smoother — ideally with a Bizzy-specific Nav2
config rather than the inherited EchoBoat one — is deferred until there's a
real need (see Open gaps).

## Course-keeping (XTE on straight legs)

Analysis in [`analysis/dynamics/xte.py`](analysis/dynamics/xte.py), over
straight, moving, GUIDED-mode legs (≥8 s) across 05-01 / 05-21 / 05-22. Two
measures per leg:

- **Track-holding precision** — RMS perpendicular scatter about the leg's own
  best-fit line (plan-independent; how *steadily* it holds a straight line):
  **~0.13 m RMS median** (best legs ~0.02 m, worst ~1.4 m), and remarkably
  **consistent across all three deployments**. The boat holds a line to ~0.1 m
  — course-keeping is *not* a survey-limiting factor.
- **XTE vs the commanded line** — RMS distance to the active `/bizzy/plan`
  (the plan's `map_tide` frame and odom are horizontally coincident per the
  logged TF — `odom→map_tide` translation is `(0, 0, −23.5)`, vertical datum
  only — so no transform needed): **median-leg-RMS ~0.4–0.8 m**, broadly
  sub-meter and consistent with the preliminary 04-24 observation
  ("sub-meter, max 0.61 m"). This adds the constant cross-track *bias* the
  track-holding metric fits out, but is noisier — its high tail (worst ~10 m)
  is plan-matching artifact (stale / adjacent-line), not real wander.

Net: tight track-holding (~0.13 m precision), sub-meter absolute accuracy to
the commanded line. Comfortably within survey line-spacing tolerances.

## Tidal current — magnitudes, NOAA-validated

The fitted current vectors (0 – 0.6 m/s across deployments) are validated
against NOAA CO-OPS predictions at station ACT0731 (Clark Island):

- The two deployments whose windows straddled NOAA **slack water**
  (2026-05-22, 2026-04-27) fit only **~0.1 m/s** current (within these
  fits' ~0.2 m/s rms) — consistent with the method tracking genuine tide
  rather than imposing a spurious offset.
- Magnitudes are order-consistent on the flooding/ebbing days.
- Direction is approximate (fitted vectors rotate off the 270°/85° channel
  axis): the pier work area deviates from the main-channel station, and
  direction is the circle fit's least-constrained parameter on partial arcs.

## Resolved: "1.5 m/s commanded, ~1.0 m/s tracked"

The standing observation from the 2026-05-01 mission (#124) — autonomy
commanding 1.5 m/s while the boat tracked ~1.0 m/s — is explained: on
upstream survey legs a ~0.5–0.6 m/s current subtracts directly from
speed-over-ground, and at full throttle the boat's STW ceiling left no
headroom to compensate. It is **current plus throttle ceiling, not an
autonomy/controller cap**.

## Open gaps (→ #88)

- Intermediate PWM→speed points (1550–1750) via steady-hold runs.
- High-throttle tail with deliberate reciprocal legs (cleaner max STW).
- Straight-reverse speed and active crash-stop braking distance.
- **Yaw-rate vs throttle sweep** — validate the raised 1.0 rad/s cap at
  cruise (commanded step-turns in a safe area); the clamp gated this in all
  logged data.
- **If/when a real need arises** (survey-turn gentleness or cmd_vel
  smoothing): re-enable the cmd_vel filter chain (velocity_smoother et al.,
  deliberately disconnected during earlier troubleshooting) and site the
  survey yaw limit in the smoother, with a Bizzy-specific Nav2 config rather
  than the inherited EchoBoat one. No action unless needed.
- Graduate the circle-fit / surge-fit tooling into `marine_tools`
  `bag_analysis` as a reusable `dynamics` extractor.
