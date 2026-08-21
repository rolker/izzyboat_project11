# BizzyBoat Reference Geometry

Reference document for the BizzyBoat (Seafloor Systems EchoBoat 240) URDF.
All positions are relative to `base_link` using ROS conventions (REP-103):
**x = forward, y = port (left), z = up**.

## Hull Specifications (EchoBoat 240 Manual)

| Parameter | Value | Source |
|-----------|-------|--------|
| Length overall | 2.40 m (7.87 ft) | Manual sec. 1.3 |
| Beam (width) | 0.90 m (2.95 ft) | Manual sec. 1.3 |
| Draft | 0.30 m (1.0 ft) | Manual sec. 1.3 |
| Air draft | 1.32 m (4.3 ft) | Manual sec. 1.3 |
| Hull material | HDPE | Manual sec. 1.3 |
| Weight (base) | 158.75 kg (350 lbs) | Manual sec. 1.3 |
| Payload capacity | 90.7 kg (200 lbs) | Manual sec. 1.3 |

## base_link Reference Point

The `base_link` origin is the **center screw hole in the hull floor**, located
approximately amidships. This point was chosen because it is close to the
center of gravity.

- **Location**: Center screw hole in hull interior floor, roughly amidships.
  Marked with an L-shaped sticker showing X and Y axes.
- **Orientation**: x-axis points forward (bow), y-axis points port, z-axis points up
- **z = 0**: At the hull floor (deck surface level)
- **Source**: Physical observation — screw hole with axis sticker on hull floor

## Estimated Sensor Positions

All values in meters, relative to `base_link`. Positions marked **[EST]** are
estimated from photos and the manual; positions marked **[MEAS]** have been
physically measured. Update this document as measurements are taken.

### Mast Structure

The mast is a **rectangular cage frame** with four uprights (two per side),
lateral crossbars, fore-aft side rails, and a fore-aft center rail on top.

| Component | x | y | z | Size (x,y,z) | Status |
|-----------|---|---|---|--------------|--------|
| Fwd-port upright | 0.30 | 0.38→0.18 | 0.30→0.77 | 0.04 x 0.04 x 0.51 | [EST] |
| Fwd-stbd upright | 0.30 | -0.38→-0.18 | 0.30→0.77 | 0.04 x 0.04 x 0.51 | [EST] |
| Aft-port upright | -0.40 | 0.38→0.18 | 0.30→0.77 | 0.04 x 0.04 x 0.51 | [EST] |
| Aft-stbd upright | -0.40 | -0.38→-0.18 | 0.30→0.77 | 0.04 x 0.04 x 0.51 | [EST] |
| Fwd lateral crossbar | 0.30 | 0 | 0.77 | 0.04 x 0.36 x 0.04 | [EST] |
| Aft lateral crossbar | -0.40 | 0 | 0.77 | 0.04 x 0.36 x 0.04 | [EST] |
| Port side rail | -0.05 | 0.18 | 0.77 | 0.70 x 0.04 x 0.04 | [EST] |
| Stbd side rail | -0.05 | -0.18 | 0.77 | 0.70 x 0.04 x 0.04 | [EST] |
| Center rail | 0 | 0 | 0.89 | 2.10 x 0.04 x 0.04 | [EST] |
| Camera tower | 0.31 | 0.0 | 0.89→1.41 | 0.04 x 0.04 x 0.52 | [EST] |

Uprights are **slanted inward** (~23°, roll=±0.40 rad): bottom at hull sides
(y≈±0.38), top at y≈±0.18. The z=0.77 crossbar height is from the measurement
sketch. Short risers at x=0.30 and x=-0.40 connect the crossbars to the center
rail at z=0.89. The center rail runs nearly the full length of the boat (~2.1m,
x=-1.05 to x=+1.05), extending well past the GNSS antennas (x=±0.835) on both
ends — visible in the top view diagram (Fig 139). The camera tower is the factory
WiFi mast on the centerline (y=0), extended upward for the OAK camera bracket
at z=1.41.

Visible in: Manual Figures 1 (System Overview, p9), 3 (Front View, p11),
4 (Side View, p12), 139 (Top View Diagram, p115).
Photos: BizzyBoat3.jpg, BizzyBoat6.jpg.

### 4x OAK-1 PoE Cameras

Mounted at the top of the factory WiFi tower (extended) on a 3D-printed bracket.
The four cameras are oriented at 90-degree intervals (forward, port,
starboard, aft). All cameras are tilted ~5 degrees downward from horizontal.

| Camera | x | y | z | yaw (rad) | pitch (rad) | Status |
|--------|---|---|---|-----------|-------------|--------|
| Forward | 0.31 | 0.0 | 1.41 | 0 | +0.09 | [MEAS] rough |
| Port | 0.31 | 0.0 | 1.41 | 1.571 | +0.09 | [MEAS] rough |
| Starboard | 0.31 | 0.0 | 1.41 | -1.571 | +0.09 | [MEAS] rough |
| Aft | 0.31 | 0.0 | 1.41 | 3.142 | +0.09 | [MEAS] rough |

**Notes**:
- All four cameras share the same origin (center of the 3D-printed bracket)
  with different yaw orientations.
- Down-tilt is ~5 degrees (+0.09 rad in URDF convention where positive
  pitch = downward). Exact angle TBD.
- The bracket is at the top of the WiFi tower on the centerline.

### 2x CUAV C-RTK 2HP GNSS Antennas

Black **cylindrical** antennas (helical form factor, roughly 1.5x taller than
wide, unmarked — no visible part number) seated in white cylindrical risers on
white base plates, fore and aft. See `2026-04-22_GPS_antennas_aft.jpg`. They
were previously described here as "puck" antennas, which is wrong and led to a
bad phase-centre derivation — see the note below.

| Antenna | x | y | z | Status |
|---------|---|---|---|--------|
| Forward | 0.835 | 0.0 | 0.89 | [MEAS] rough |
| Aft | -0.835 | 0.0 | 0.89 | [MEAS] rough |

**Notes**:
- Baseline ~1.67m (fore-aft separation).
- **The antenna phase centre is NOT known.** This entry previously asserted
  "phase center is at the top surface of the puck". That claim is **unsourced**,
  describes the wrong form factor, and on 2026-08-21 was traced as the origin of
  a +12 cm correction in `hydro_payload_install_log.md` that live measurement
  refutes. Do not use it.
  - CUAV publishes no phase-centre, ARP or dimensional data for this antenna
    (product page and C-RTK 2HP manual give frequency bands only).
  - CUAV does not appear in the NGS antenna calibration database (ANTCAL), which
    covers 150+ manufacturers.
  - The antenna model is unrecorded (`bizzyboat_hardware.md` lists it as
    "model TBD") and the unit carries no visible marking.
  - The practical substitute is a **field calibration against the SBG**, whose
    Trimble antenna offsets were surveyed with the documented phase centre: the
    FCU-minus-SBG difference at `base_link` absorbs the CUAV phase centre and
    mounting reference together. Measured 2026-08-21: **FCU reads ~38 mm low**
    (n=450 over 90 s). Average over hours of bag to beat down the few-centimetre
    inter-receiver wander before adopting a value.
- Positions are rough measurements from base_link (center screw hole).

### Imagenex DeltaT Sonar

Mounted below the hull. Position estimated from the IzzyBoat URDF and EchoBoat
240 manual bottom-view diagram (Figure 2), which shows the sonar projector and
receiver near amidships.

| Sensor | x | y | z | roll (rad) | yaw (rad) | Status |
|--------|---|---|---|------------|-----------|--------|
| DeltaT | -0.23 | 0.0 | -0.18 | 3.142 | 3.142 | [MEAS] rough |

**Notes**:
- Orientation is flipped (roll=pi, yaw=pi) matching the IzzyBoat convention
  for a downward-facing sonar.
- Exact position and depth below hull TBD.

### Factory USB Camera

Mounted at the forward end of the center rail, ahead of the bow GNSS antenna.

| Sensor | x | y | z | Status |
|--------|---|---|---|--------|
| USB camera | 1.05 | 0.0 | 0.89 | [EST] |

**Notes**:
- At the forward end of the center rail, pointing forward.
- Height matches the rail (~0.89m above hull floor).

### AutoNav Box (Cube Orange FCU + IMU)

The AutoNav box is behind a panel at the stern of the boat. It contains the
Cube Orange flight controller with the onboard IMU. Visible in Manual Figures
4 (Side View, p12), 6 (Internal View With Equipment, p14), and 137 (Side
View Diagram, p113). The box sits inside the stern compartment, aft of the
main hatch area.

| Component | x | y | z | Status |
|-----------|---|---|---|--------|
| Box front-bottom | -0.875 | 0.0 | -0.01 | [MEAS] rough |
| Box dimensions (x × y × z) | 0.23 × 0.28 × 0.14 | | | [MEAS] from IzzyBoat photos |
| IMU (Cube Orange center) | -0.99 | 0.0 | 0.05 | [MEAS] from IzzyBoat photos |

**Notes**:
- Front-bottom of the box is the measured reference point on BizzyBoat.
- Box dimensions measured from IzzyBoat AutoNav photos (2024-06-14) with tape
  measure — same model (Seafloor Systems AutoNav) used on both boats.
  X=0.23m depth (fore-aft, ~9"), Y=0.28m width (~11"), Z=0.14m height (~5.5").
- Cube Orange is in the lower compartment, roughly centered fore-aft and laterally,
  ~0.06m above box bottom. IMU is at center of Cube Orange (~65mm cube).
- IMU position in base_link frame: (-0.875 - 0.115, 0.0, -0.01 + 0.06) = (-0.99, 0.0, 0.05).
- The IMU orientation relative to base_link needs verification.

## Coordinate Frame Conventions

Each camera has two TF frames:
- `bizzy/<name>` — standard ROS frame (x-forward, y-left, z-up)
- `bizzy/<name>_optical` — optical frame (x-right, y-down, z-forward),
  rotated -90deg around x then -90deg around z from the standard frame.
  Required by ROS image processing pipeline.

GNSS antennas publish to their respective frames; the dual-antenna heading
is computed from the baseline vector between `bizzy/gnss_forward` and
`bizzy/gnss_aft`.

## Manual Diagram Analysis

Extracted pages from the EchoBoat 240 Manual V (PDF offset = 5; document page
N is at PDF page N+5). Key diagrams stored in `~/bizzyboat/pages/doc-page-NNN.png`.

### Key Figures Referenced

| Figure | Doc Page | Description |
|--------|----------|-------------|
| 1  | 9   | System Overview — 3/4 perspective showing single center rail, GNSS antennas, cameras |
| 2  | 10  | Bottom View — sonar projector/receiver placement, tracking fins, SVP tube |
| 3  | 11  | Front View — mast uprights with center rail, antenna, equipment |
| 4  | 12  | Side View — both sides; shows AutoNav box, receiver box, sonar topside |
| 5  | 13  | Internal View — top-down and side cross-sections with dimensions |
| 6  | 14  | Internal View With Equipment — AutoNav, PC, CAA module, T50 sonar, batteries |
| 137 | 113 | Side View Diagram — mechanical drawing with dimension callouts |
| 138 | 114 | Front View Diagram — width/height dimensions |
| 139 | 115 | Top View Diagram — plan view showing overall layout |

### URDF Corrections Identified from Diagrams

1. ~~**Mast crossbar orientation**~~: Fixed — URDF now models full rectangular
   cage frame with four uprights, lateral crossbars, side rails, and center rail.

2. ~~**Center rail length**~~: Fixed — rail modeled as 2.10m box along x-axis,
   extending well past GNSS antennas per top view diagram (Fig 139).

3. **Sonar placement**: Bottom view (Fig 2) confirms sonar projector and receiver
   are near amidships on the hull bottom, consistent with current DeltaT position.

4. **AutoNav box**: Confirmed at stern inside hull (Figs 4, 6). Mechanical diagram
   (Fig 137) may have exact dimensions — needs closer reading of dimension callouts.

5. **Frame upright positions**: The four upright x-positions (0.30 and -0.40)
   are estimated from photos. Refine with measurements from base_link.

## What Needs Measurement

| Item | Current value | How to measure |
|------|---------------|----------------|
| Camera bracket height (z) | 1.41m [MEAS] rough | Refine with tape measure from hull floor to bracket center |
| Camera bracket fore-aft (x) | 0.31m [MEAS] rough | Refine from base_link screw hole to bracket |
| Camera down-tilt angle | 5 deg [EST] | Inclinometer on camera face, or CAD angle |
| GNSS baseline | 1.67m [MEAS] rough | Refine center-to-center between pucks |
| GNSS height (z) | 0.89m [MEAS] rough | Refine with tape measure from hull floor to puck top |
| GNSS fore-aft (x) | ±0.835m [MEAS] rough | Refine from base_link screw hole to each puck |
| DeltaT position (x, z) | -0.23, -0.18 [MEAS] rough | Refine from screw hole; depth below hull |
| AutoNav box dimensions | 0.23 x 0.28 x 0.14 [MEAS] from IzzyBoat photos | Confirm on BizzyBoat |
| IMU position within AutoNav box | -0.115, 0.0, 0.06 from box front-bottom [MEAS] from IzzyBoat photos | Confirm on BizzyBoat |
| IMU orientation | identity [EST] | Verify Cube Orange axes align with boat frame |
| USB camera position | 1.05, 0, 0.89 [EST] | At forward end of center rail — refine with measurement |
| Frame upright fwd x | 0.30 [EST] | Measure from base_link to forward upright pair |
| Frame upright aft x | -0.40 [EST] | Measure from base_link to aft upright pair |
| Frame crossbar height (z) | 0.77 [EST] | Measure from hull floor to top of lateral crossbars |
| Hull gunwale height (z) | 0.30 [EST] | Measure from hull floor to top of hull side |
| base_link to bow distance | ~1.2m [EST] | Measure from screw hole to bow tip |
| base_link to stern distance | ~1.2m [EST] | Measure from screw hole to transom |
