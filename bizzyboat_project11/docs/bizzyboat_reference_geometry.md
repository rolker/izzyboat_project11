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

- **Location**: Center of hull interior floor, roughly amidships
- **Orientation**: x-axis points forward (bow), y-axis points port, z-axis points up
- **z = 0**: At the hull floor (deck surface level)
- **Source**: Physical observation (screw hole in hull floor)

## Estimated Sensor Positions

All values in meters, relative to `base_link`. Positions marked **[EST]** are
estimated from photos and the manual; positions marked **[MEAS]** have been
physically measured. Update this document as measurements are taken.

### Mast Structure

The mast consists of two vertical stainless steel uprights bolted to the hull
sides, connected by a horizontal aluminum crossbar. Estimated mast height is
~1.1m above the hull floor (based on air draft of 1.32m minus hull height
above waterline).

### 4x OAK-1 PoE Cameras

Mounted at the top of the port-side mast upright on a 3D-printed bracket.
The four cameras are oriented at 90-degree intervals (forward, port,
starboard, aft). All cameras are tilted ~10 degrees downward from horizontal.

| Camera | x | y | z | yaw (rad) | pitch (rad) | Status |
|--------|---|---|---|-----------|-------------|--------|
| Forward | 0.15 | 0.0 | 1.25 | 0 | -0.17 | [EST] |
| Port | 0.15 | 0.0 | 1.25 | 1.571 | -0.17 | [EST] |
| Starboard | 0.15 | 0.0 | 1.25 | -1.571 | -0.17 | [EST] |
| Aft | 0.15 | 0.0 | 1.25 | 3.142 | -0.17 | [EST] |

**Notes**:
- All four cameras share the same origin (center of the 3D-printed bracket)
  with different yaw orientations.
- Down-tilt is ~10 degrees (0.17 rad) — exact angle TBD.
- The bracket is at the top of the mast, slightly forward of amidships.

### 2x CUAV C-RTK 2HP GNSS Antennas

Black puck antennas in white mounting brackets, one at each end of the
horizontal crossbar. The baseline (distance between antennas) spans nearly
the full crossbar width.

| Antenna | x | y | z | Status |
|---------|---|---|---|--------|
| Port | 0.15 | 0.40 | 1.15 | [EST] |
| Starboard | 0.15 | -0.40 | 1.15 | [EST] |

**Notes**:
- Baseline ~0.80m (crossbar width).
- The crossbar is slightly below the camera bracket height.
- GNSS antenna phase center is at the top surface of the puck.

### Imagenex DeltaT Sonar

Mounted below the hull. Position estimated from the IzzyBoat URDF and EchoBoat
240 manual bottom-view diagram (Figure 2), which shows the sonar projector and
receiver near amidships.

| Sensor | x | y | z | roll (rad) | yaw (rad) | Status |
|--------|---|---|---|------------|-----------|--------|
| DeltaT | -0.15 | 0.0 | -0.15 | 3.142 | 3.142 | [EST] |

**Notes**:
- Orientation is flipped (roll=pi, yaw=pi) matching the IzzyBoat convention
  for a downward-facing sonar.
- Exact position and depth below hull TBD.

### Factory USB Camera

Mounted on the mast structure. Position estimated from the manual overview
diagram (Figure 1) which shows the USB camera on the bow mast arm.

| Sensor | x | y | z | Status |
|--------|---|---|---|--------|
| USB camera | 0.50 | 0.0 | 0.80 | [EST] |

**Notes**:
- Position is rough — needs confirmation on BizzyBoat's specific mounting.

## Coordinate Frame Conventions

Each camera has two TF frames:
- `bizzy/<name>` — standard ROS frame (x-forward, y-left, z-up)
- `bizzy/<name>_optical` — optical frame (x-right, y-down, z-forward),
  rotated -90deg around x then -90deg around z from the standard frame.
  Required by ROS image processing pipeline.

GNSS antennas publish to their respective frames; the dual-antenna heading
is computed from the baseline vector between `bizzy/gnss_port` and
`bizzy/gnss_starboard`.

## What Needs Measurement

| Item | Current value | How to measure |
|------|---------------|----------------|
| Camera bracket height (z) | 1.25m [EST] | Tape measure from hull floor to bracket center |
| Camera bracket fore-aft (x) | 0.15m [EST] | Measure from base_link screw hole to bracket |
| Camera down-tilt angle | 10 deg [EST] | Inclinometer on camera face, or CAD angle |
| GNSS baseline | 0.80m [EST] | Measure center-to-center between pucks |
| GNSS height (z) | 1.15m [EST] | Tape measure from hull floor to puck top |
| DeltaT position (x, z) | -0.15, -0.15 [EST] | Measure from screw hole; depth below hull |
| USB camera position | 0.50, 0, 0.80 [EST] | Measure from base_link reference |
| base_link to bow distance | ~1.2m [EST] | Measure from screw hole to bow tip |
| base_link to stern distance | ~1.2m [EST] | Measure from screw hole to transom |
