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
- Graduate the circle-fit / surge-fit tooling into `marine_tools`
  `bag_analysis` as a reusable `dynamics` extractor.
