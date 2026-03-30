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

The mast consists of two vertical stainless steel uprights bolted to the hull
sides, connected at the top by a **single fore-aft center rail** running down the
centerline (y=0). This is NOT a port-to-starboard crossbar — the rail runs
bow-to-stern along the center of the boat. The GNSS antennas mount at the
forward and aft ends of this center rail; the USB camera and other equipment
also mount on it.

Estimated mast height is ~1.1m above the hull floor (based on air draft of
1.32m minus hull height above waterline).

Visible in: Manual Figures 1 (System Overview, p9), 3 (Front View, p11),
4 (Side View, p12), 139 (Top View Diagram, p115).

The URDF models this as a fore-aft box along y=0, spanning ~1.67m from the
forward GNSS antenna to the aft GNSS antenna.

### 4x OAK-1 PoE Cameras

Mounted at the top of the port-side mast upright on a 3D-printed bracket.
The four cameras are oriented at 90-degree intervals (forward, port,
starboard, aft). All cameras are tilted ~10 degrees downward from horizontal.

| Camera | x | y | z | yaw (rad) | pitch (rad) | Status |
|--------|---|---|---|-----------|-------------|--------|
| Forward | 0.31 | 0.0 | 1.41 | 0 | -0.17 | [MEAS] rough |
| Port | 0.31 | 0.0 | 1.41 | 1.571 | -0.17 | [MEAS] rough |
| Starboard | 0.31 | 0.0 | 1.41 | -1.571 | -0.17 | [MEAS] rough |
| Aft | 0.31 | 0.0 | 1.41 | 3.142 | -0.17 | [MEAS] rough |

**Notes**:
- All four cameras share the same origin (center of the 3D-printed bracket)
  with different yaw orientations.
- Down-tilt is ~10 degrees (0.17 rad) — exact angle TBD.
- The bracket is at the top of the mast, slightly forward of amidships.

### 2x CUAV C-RTK 2HP GNSS Antennas

Black puck antennas in white mounting brackets, fore and aft.

| Antenna | x | y | z | Status |
|---------|---|---|---|--------|
| Forward | 0.835 | 0.0 | 0.89 | [MEAS] rough |
| Aft | -0.835 | 0.0 | 0.89 | [MEAS] rough |

**Notes**:
- Baseline ~1.67m (fore-aft separation).
- GNSS antenna phase center is at the top surface of the puck.
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

Mounted on the horizontal crossbar (the same rail the GNSS antennas are on),
toward the forward end. Positioned at roughly the same height as the GNSS
pucks.

| Sensor | x | y | z | Status |
|--------|---|---|---|--------|
| USB camera | 0.55 | 0.0 | 0.89 | [EST] |

**Notes**:
- On the center fore-aft rail, forward of the GNSS antennas, pointing forward.
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
| IMU (est. center of box) | -0.975 | 0.0 | 0.065 | [EST] |

**Notes**:
- Front-bottom of the box is the measured reference point.
- Box dimensions ~0.20 x 0.15 x 0.15m estimated from photos. The mechanical
  diagrams (Fig 137) may provide better dimensions — needs closer inspection.
- The Cube Orange IMU position within the box needs refinement.
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

1. ~~**Mast crossbar orientation**~~: Fixed — URDF now has a fore-aft center rail
   along y=0, spanning ~1.67m between the GNSS antennas.

2. ~~**Center rail length**~~: Fixed — rail modeled as 1.67m box along x-axis.

3. **Sonar placement**: Bottom view (Fig 2) confirms sonar projector and receiver
   are near amidships on the hull bottom, consistent with current DeltaT position.

4. **AutoNav box**: Confirmed at stern inside hull (Figs 4, 6). Mechanical diagram
   (Fig 137) may have exact dimensions — needs closer reading of dimension callouts.

## What Needs Measurement

| Item | Current value | How to measure |
|------|---------------|----------------|
| Camera bracket height (z) | 1.41m [MEAS] rough | Refine with tape measure from hull floor to bracket center |
| Camera bracket fore-aft (x) | 0.31m [MEAS] rough | Refine from base_link screw hole to bracket |
| Camera down-tilt angle | 10 deg [EST] | Inclinometer on camera face, or CAD angle |
| GNSS baseline | 1.67m [MEAS] rough | Refine center-to-center between pucks |
| GNSS height (z) | 0.89m [MEAS] rough | Refine with tape measure from hull floor to puck top |
| GNSS fore-aft (x) | ±0.835m [MEAS] rough | Refine from base_link screw hole to each puck |
| DeltaT position (x, z) | -0.23, -0.18 [MEAS] rough | Refine from screw hole; depth below hull |
| AutoNav box dimensions | ~0.20 x 0.15 x 0.15 [EST] | Measure box length, width, height |
| IMU position within AutoNav box | center [EST] | Locate Cube Orange inside box, measure offset from front-bottom |
| IMU orientation | identity [EST] | Verify Cube Orange axes align with boat frame |
| USB camera position | 0.55, 0, 0.89 [EST] | Measure from base_link reference along center rail |
| base_link to bow distance | ~1.2m [EST] | Measure from screw hole to bow tip |
| base_link to stern distance | ~1.2m [EST] | Measure from screw hole to transom |
