# BizzyBoat Hydro Payload Install Log

Detailed running log for M3 / SBG / SVS install and bring-up on mercat.
Summaries land in [`bizzyboat_deployment_log.md`](../../docs/bizzyboat_deployment_log.md)
(issue [#57](https://github.com/rolker/unh_echoboats_project11/issues/57)).

Tracking:
- [#76](https://github.com/rolker/unh_echoboats_project11/issues/76) — mercat bring-up and data flow
- [#77](https://github.com/rolker/unh_echoboats_project11/issues/77) — physical install, offsets, URDF, SVG diagram
- [rolker/marine_tools#1](https://github.com/rolker/marine_tools/issues/1) — QINSy → ROS bridge (peer/downstream)

Photos are kept locally on the operator workstation (not committed).
Measurements and observations extracted from them are recorded here.

## Hardware inventory

| Device | Model | Serial | Link | mercat port | Status |
|---|---|---|---|---|---|
| Kongsberg M3 sonar head | M3 | TBD | Ethernet (direct to mercat, isolated) | n/a | Installed |
| Kongsberg M3 topside unit | TBD | TBD | Ethernet | n/a | Installed |
| SBG GPS/IMU | Ellipse-D (suspected — dual-antenna INS) | TBD (read via SBG software) | Serial | TBD | Installed |
| SBG GNSS antenna (fwd) | Trimble GNSS/MSK (exact variant TBD) | TBD | SMA coax to SBG | n/a | Installed |
| SBG GNSS antenna (aft) | Trimble GNSS/MSK (exact variant TBD) | TBD | SMA coax to SBG | n/a | Installed |
| Sound speed sensor | TBD (brand), 6000 m depth rating | SN 11357 | Serial | TBD | Installed, factory mount location |

**Related existing hardware (for reference, not part of this work):**
- Cube FCU dual-antenna system: **CUAV C-RTK 2HP**, antennas at x = ±0.835 m (baseline 1.67 m). Already in `bizzyboat_reference_geometry.md`. Confirmed 2026-04-22 that these are separate from the SBG's Trimble pucks, though all four antennas share the same center rail.

## Install photo index (local-only)

All paths relative to `~/bizzyboat/` on this workstation.

| Date | File | Subject | Tape visible | Notes |
|---|---|---|---|---|
| 2026-04-22 | `2026-04-22_SBG_in_BizzyBoat.jpg` | SBG install wide, top-down | yes | Tape confirms 60 cm aft reference |
| 2026-04-22 | `2026-04-22_SBG_in_BizzyBoat_2.jpg` | SBG close-up, top face | no | Axis triad visible but small |
| 2026-04-22 | `2026-04-22_SBG_in_BizzyBoat_2_cropped.jpg` | SBG top face, cropped | no | Axis triad clearly readable: X-arrow → fwd, Y-arrow → stbd, Z marked ⊗ (into case) |
| 2026-04-22 | `2026-04-22_GPS_antennas_aft.jpg` | SBG survey antennas aft view | yes | Baseline measurement |
| 2026-04-22 | `2026-04-22_GPS_antennas_forward.jpg` | SBG survey antennas forward view | yes | Baseline measurement |
| 2026-04-22 | `2026-04-22_M3_under_BizzyBoat_1.jpg` | M3 install under hull | TBD | Not yet analyzed |
| 2026-04-22 | `2026-04-22_M3_under_BizzyBoat_2.jpg` | M3 install under hull | TBD | Not yet analyzed |
| 2026-04-22 | `2026-04-22_M3_to_BizzyBoat_fin_measurement.jpg` | M3 offset from hull fin | yes | Not yet analyzed |
| 2026-04-22 | `2026-04-22_BizzyBoat_sound_speed_probe.jpg` | SVS install, side view | no | Side-clamp mount, blue protective cap |
| 2026-04-22 | `2026-04-22_sound_speed_sensor.jpg` | SVS under-hull view | no | Reveals "6000m" + "SN 11357" markings; factory sonar transducer faces visible alongside |
| 2026-04-22 | `2026-04-22_GPS_antennas_forward_2.jpg` | Forward center-rail close-up | no | Shows Trimble antenna, disused white mount, bullet camera, Seafloor Systems enclosure |

Earlier (pre-payload) hull/mast references — see `~/bizzyboat/2026-03-27_*.jpg`, `2026-03-30_measurements.jpg`, `pages/doc-page-0{09-14,113-15}.png`, and `EchoBoat_240_Manual_V.pdf`.

## Measurement log

### 2026-04-22

- **SBG survey GPS antenna baseline**: 2.05 m (tape measure, with measuring
  tape visible in photos). Wider than Cube GPS baseline of 1.67 m (y=±0.835).
  SBG antennas mounted at the existing EchoBoat survey antenna positions —
  separate from the antennas feeding the Cube autopilot. The Trimble and
  CUAV pairs share the center rail.

#### SBG GNSS antennas — position derivation

The SBG dual antennas are **Trimble GNSS/MSK** pucks (yellow), mounted on
the center rail, one near each end. Anchored to the existing CUAV C-RTK
2HP antenna positions (x = ±0.835) by tape-measured offsets:

- Forward Trimble center is **15.5 cm forward of** the forward CUAV
- Aft Trimble center is **23 cm aft of** the aft CUAV

Derivation:

| Antenna | x | y | z | Status |
|---|---|---|---|---|
| Forward Trimble | +0.835 + 0.155 = **+0.990 m** | 0.00 | ~0.89 + phase-center Δ | [MEAS] rough |
| Aft Trimble | -0.835 - 0.230 = **-1.065 m** | 0.00 | ~0.89 + phase-center Δ | [MEAS] rough |

- Baseline: 0.990 - (-1.065) = **2.055 m** (matches tape-measured 2.05 m) ✓
- Midpoint: **-0.0375 m** — the Trimble pair is ~3.75 cm **aft** of
  base_link; **not** symmetric about the reference point.
- Forward Trimble at +0.990 is inboard of the rail end (+1.05); aft
  Trimble at -1.065 is slightly outside the current [EST] rail end
  (-1.05) — within tape tolerance, but the rail-end estimate may need
  revisiting.
- All four antennas (2 Trimble + 2 CUAV) are on the centerline (y = 0).

**z (height above hull)** — assumed rail-top at z ≈ 0.89 m from the
existing reference geometry; each Trimble puck adds a mount-stud +
phase-center offset that we'll resolve once the exact Trimble model is
identified (see unknowns below).

**Remaining GPS-antenna unknowns**:
- Exact Trimble model (only "GNSS/MSK" visible on case; need full part
  number for phase-center datasheet)
- Which Trimble feeds SBG's primary (ANT1) vs. secondary (ANT2) input
- Phase-center height above mount base for each antenna
- Independent tape verification that y = 0 for both Trimbles (currently
  relying on shared-rail geometry and user statement)

#### SBG Ellipse INS — mounting geometry and orientation

Mounted on a black plate (carbon-fiber or 3D-printed) spanning the hull
interior under a horizontal upper rail. Plate sits against the upper
surface; SBG sits on the plate with its top face (labels, axis triad,
connectors) facing up toward the viewer in the install photos.

| Quantity | Value | Method | Status |
|---|---|---|---|
| Case back face (connector side) | x = -0.60 m | Tape measure from base_link | [MEAS] |
| Case bottom | z = +0.005 m | Plate thickness (user-provided) | [MEAS] |
| Case y-position | y = 0.00 m (intended centerline) | Intent; not independently measured | [EST] |
| Body-frame rotation (vessel → SBG) | rpy = (π, 0, 0) — 180° roll about X | Axis triad on case top face | [MEAS] |

**Axis triad on SBG top face** (confirmed from cropped photo):
- SBG **X** arrow → vessel forward (+X_vessel)
- SBG **Y** arrow → vessel starboard (-Y_vessel)
- SBG **Z** marked ⊗ (into page) → vessel down (-Z_vessel)

SBG reports data in its own body frame (FRD: Forward-Right-Down),
per standard INS convention. Vessel uses REP-103 (FLU:
Forward-Left-Up). The 180° roll reconciles the two.

**Mounting orientation decisions to make**:
- Handle the FRD↔FLU rotation in the URDF tf (joint rpy),
  **or** configure it in SBG firmware "install orientation"
  settings. URDF tf is the ROS-idiomatic choice.

**Remaining SBG unknowns** (see "To refine from vendor manuals" below):
- Exact model — confirm via SBG software (probably Ellipse-D)
- IMU sensing-element offset from case exterior reference
- Case physical dimensions (length × width × height) — needed to
  place the IMU body frame origin relative to the measured case back face
- y-position independent verification (centerline assumption)

#### M3 sonar — install geometry

The M3 is a through-hull mount. The user confirmed 2026-04-22 that the
M3 occupies the **same through-hull cavity previously used by the
Imagenex DeltaT sonar**, so its fore-aft position is inherited from the
existing DeltaT reference entry.

| Quantity | Value | Method | Status |
|---|---|---|---|
| M3 x (fore-aft) | -0.23 m | Inherited from DeltaT cavity | [MEAS] rough |
| M3 y | 0.00 m | Appears centerline in under-hull photos | [EST] — confirm by tape |
| M3 z (depth below hull) | TBD | Need tape from hull floor to transducer face | [EST] |
| M3 orientation | Transducer face pointing straight down | Inspection of under-hull photos | [EST] |
| M3 yaw / roll alignment | TBD — inspect unit for vendor axis triad | Needs on-boat verification | [EST] |

Under-hull photos show the M3 head hanging below the hull with:
- Circular bolt-secured mount plate at the hull level (M3 cylindrical
  body below)
- Two green-jacketed cables exiting upward (ethernet + power)
- Hydrodynamic fairing integrated into the lower M3 housing
- Tape measurement in `2026-04-22_M3_under_BizzyBoat_2.jpg` is laid
  along the M3 body (needs interpretation once endpoints are confirmed
  — captures M3 vertical extent, not base_link offset)

**Remaining M3 unknowns**:
- z (depth) — measure from hull floor (z=0 per base_link convention) to
  M3 transducer face; nominal DeltaT was at z = -0.18, M3 may differ
- y verification (centerline assumption)
- Orientation: check M3 for a vendor axis triad similar to the SBG's;
  record any yaw/roll alignment
- Mounting angle — confirm strictly downward (no forward tilt); if
  tilted the URDF joint needs the corresponding pitch

#### Fairing Fin — position from M3 offset

The **Fairing Fin** is a factory EchoBoat 240 hull feature labeled in
the manual's bottom view (Figure 2, page 10). It sits ahead of the
sonar cavity as a hydrodynamic fairing.

Tape-measured 2026-04-22: Fairing Fin center is **0.28 m forward of the
M3 mount** (same tape, hook anchored at the fin, reading 28 cm at M3).

Derivation:
- Fin x = M3 x + 0.28 = -0.23 + 0.28 = **+0.05 m**

| Quantity | Value | Method | Status |
|---|---|---|---|
| Fairing Fin x | +0.05 m | Derived from M3@DeltaT (-0.23) + 28 cm tape | [MEAS] derived |
| Fairing Fin y | 0.00 m | Centerline per manual Fig 2 | [EST] |
| Fairing Fin z | TBD | Protrudes below hull; depth TBD | [EST] |

**Cross-check opportunity** (deferred): pixel analysis of Fig 137 side
view, using the aft GPS antenna (x = -0.835) and the WiFi mast / camera
tower (x = +0.31) as scale references, to independently recover the
Fairing Fin x. Will produce an annotated crop for visual verification
before running the calculation.

**Note on the manual vs. the current forward antenna**: the forward
GPS antenna shown in Fig 137 is at the factory position (x ≈ +0.835),
which differs from our current install. The aft antenna and the WiFi
mast remain in their factory positions and are valid references.

#### Cart-based height survey — pitch estimate + M3 z

Boat is resting on its cart. User measured (2026-04-22) these heights
above the floor with a tape:

| Point | Height above ground | Boat-frame x (m) |
|---|---|---|
| M3 transducer face | 0.405 m | -0.23 |
| Center-rail top at aft Trimble | 1.46 m | -1.065 |
| Center-rail top at fwd Trimble | 1.41 m | +0.990 |

**Pitch on the cart**: the aft rail is 5 cm higher than the fwd rail,
separated along x by 2.055 m →
**θ_pitch = atan(0.05 / 2.055) ≈ 1.39° nose-down**

This is a *cart-induced* attitude; it does not persist on the water.
Relevant only for interpreting today's ground-referenced measurements.

**Rail height at x = 0** (over base_link), by linear interpolation of
the two rail readings:

- h_rail(x=0) = 1.434 m above ground

**Base_link height above ground** (assuming existing reference geometry
z_rail = 0.89 m): h_baselink = 1.434 - 0.89 = 0.544 m above ground.

**M3 transducer face z in boat frame**:
- Rail height at x = -0.23, correcting for pitch: 1.440 m
- Rail ↔ M3 face vertical separation: 1.440 - 0.405 = **1.035 m** [MEAS]
- With z_rail = 0.89: **z_M3_face = 0.89 - 1.035 = -0.145 m** [MEAS-derived]

Compared to the DeltaT's existing z = -0.18 m entry, the M3 face sits
~3.5 cm higher. Consistent with different housing geometry in the same
through-hull cavity.

**Caveat**: the rail-to-M3-face separation (1.035 m) is a direct
measurement and will not change. The absolute boat-frame z value for
M3 inherits the uncertainty of the existing `[EST]` rail-top anchor
(z = 0.89 m). When rail-top z is refined, M3 z should update in step.

Updated measurement table:

| Quantity | Value | Status |
|---|---|---|
| Boat pitch on cart (transient) | 1.39° nose-down | [MEAS] cart |
| Rail height above ground at x=0 | 1.434 m | [MEAS] cart |
| Rail ↔ M3 face vertical separation | 1.035 m | [MEAS] |
| M3 transducer face z (boat frame) | -0.145 m | [MEAS-derived via z_rail=0.89 EST] |

#### Sound speed sensor — identification and install

From under-hull photo (`2026-04-22_sound_speed_sensor.jpg`):

- **Serial number**: SN 11357 (engraved on probe body)
- **Depth rating**: 6000 m (engraved on probe body)
- Stainless-steel cylindrical body, blue protective cap (shipped/stowed
  position — actual sensing element visible past the cap as a small
  forked transducer)
- Mounted via a side-clamp bracket bolted to the hull, passing through
  (or alongside) the factory SVS cavity
- Orientation: probe axis vertical, sensing element pointing down
- Factory mount location — same spot shown in Fig 2 (page 10, manual
  bottom view), immediately alongside the factory SONAR Projector /
  Receiver elements (both also visible in the same photo, dark circular
  transducer faces in the recessed plate)

| Quantity | Value | Status |
|---|---|---|
| Serial number | 11357 | [MEAS] |
| Depth rating | 6000 m | [MEAS] |
| Position (x, y, z) | TBD — factory mount in Fig 2, not yet tape-referenced to base_link | [EST] |
| Orientation | Vertical, sensing element down | [MEAS] photo |

**Remaining SVS unknowns**:
- Brand / model (6000 m + SN 11357 is strong, but no vendor label
  visible in photo) — resolve via serial stream when mercat is powered,
  or via a sticker we haven't photographed yet
- x, y, z coordinates relative to base_link — either tape-measure
  directly (forward of M3? beside M3?), or infer from Fig 2 with
  pixel-anchored references

## To refine from vendor manuals

- [ ] SBG case physical dimensions (length × width × height) — needed to
  compute IMU body frame origin relative to the measured back-face at x=-0.60
- [ ] SBG IMU sensing-element offset from case exterior reference (per
  model datasheet; confirm model first)
- [ ] Trimble GNSS/MSK antenna — identify exact model (part number) to
  look up phase-center offset vs. mount-base reference
- [ ] Confirm SBG ANT1 / ANT2 assignment (which Trimble is primary)
- [ ] M3 transducer acoustic center vs. housing reference
- [ ] M3 mounting angle convention per vendor
- [ ] SVS sampling point vs. housing reference
- [ ] SVS brand / model — confirm from vendor software or physical
  label (already have SN 11357, 6000 m depth rating)
- [ ] Factory SVS position from manual Fig 2 (bottom view, p10) — use
  pixel analysis with known landmarks if direct tape measurement is
  impractical
- [ ] Refine rail-top z (currently [EST] 0.89 m) — would tighten M3
  and any antenna z derivations that depend on it

## Open questions / investigations

- SVS model — pending verification from serial stream (suspected AML)
- NTRIP path for SBG — independent MACORS client, shared corrections from
  Cube chain, or routed via mercat? Tracked in
  [#76](https://github.com/rolker/unh_echoboats_project11/issues/76)
- mercat NTP — still not configured; blocking accurate timestamps for
  QINSy logging and sensor fusion
