# BizzyBoat GPS Antenna Offset Configuration

**Date**: 2026-04-02
**Issue**: #37
**Hardware**: 2x CUAV C-RTK 2HP (DroneCAN, dual-antenna moving baseline RTK)

## Reference

- ArduPilot GPS-for-Yaw: https://ardupilot.org/rover/docs/common-gps-for-yaw.html
- CUAV C-RTK 2HP: https://ardupilot.org/rover/docs/common-cuav-c-rtk2-hp.html
- BizzyBoat reference geometry: `bizzyboat_project11/docs/bizzyboat_reference_geometry.md`
- IzzyBoat live params (working reference): `docs/izzyboat_fcu_params_live.txt`

## ArduPilot Body Frame Convention

- X = forward, Y = right, Z = down
- `GPS_POS1_X/Y/Z` — GPS1 antenna offset from vehicle CG
- `GPS_POS2_X/Y/Z` — GPS2 antenna offset from vehicle CG
- `GPS_MB1_OFS_X/Y/Z` — vector from rover antenna to base antenna
  (equals the sum of the two POS offsets along each axis, negated)

## Antenna Positions (from reference geometry, rough measurements)

BizzyBoat origin is at the CG. Antennas are fore and aft on the centerline.

| Antenna | URDF (x, y, z-up) | ArduPilot (X fwd, Y right, Z down) |
|---------|-------------------|-------------------------------------|
| Forward | 0.835, 0.0, 0.89 | 0.835, 0.0, -0.89 |
| Aft     | -0.835, 0.0, 0.89 | -0.835, 0.0, -0.89 |

Baseline (antenna-to-antenna): ~1.67 m

## FCU Parameter Changes (applied 2026-04-02)

**Key finding**: GPS1 (CAN node 124) is the **forward** antenna on BizzyBoat.
This differs from IzzyBoat where GPS1 (CAN node 125) is the aft antenna.
Discovered during testing — initial assumption of GPS1=aft gave heading 180° off.

| Parameter | Before | After | Notes |
|-----------|--------|-------|-------|
| `GPS_POS1_X` | 0.0 | 0.835 | Forward antenna, ahead of CG |
| `GPS_POS1_Y` | 0.0 | 0.0 | Centerline |
| `GPS_POS1_Z` | 0.0 | -0.89 | Above CG (negative = up) |
| `GPS_POS2_X` | 0.0 | -0.835 | Aft antenna, behind CG |
| `GPS_POS2_Y` | 0.0 | 0.0 | Centerline |
| `GPS_POS2_Z` | 0.0 | -0.89 | Same height as GPS1 |
| `GPS_MB1_TYPE` | 0 | 1 | Enable moving baseline |
| `GPS_MB1_OFS_X` | 0.0 | 1.67 | Base-to-rover vector (positive = forward) |
| `GPS_MB1_OFS_Y` | 0.0 | 0.0 | No lateral offset |
| `GPS_MB1_OFS_Z` | 0.0 | 0.0 | Same height |

### Comparison with IzzyBoat

| Parameter | IzzyBoat | BizzyBoat | Notes |
|-----------|----------|-----------|-------|
| `GPS_POS1_X` | -0.341 (aft) | 0.835 (fwd) | GPS1 is opposite end on each boat |
| `GPS_POS1_Z` | -0.616 | -0.89 | BizzyBoat has taller mounting |
| `GPS_MB1_OFS_X` | -0.794 | 1.67 | Sign differs (GPS1 assignment differs) |
| `GPS_CAN_NODEID1` | 125 | 124 | Different CAN node IDs |

IzzyBoat MB offset math: -(0.341 + 0.360) = -0.701 ≈ -0.794 (close, measured values)
BizzyBoat MB offset math: (0.835 + 0.835) = 1.67 (symmetric, from rough geometry)

### Test results

- **GPS fix type**: 3 (3D fix)
- **Satellites**: 28
- **Heading**: ~74° (ENE) — confirmed correct for boat orientation at pier
- **Position**: 43.072°N, 70.712°W (UNH pier area)

## Parameters Already Correct

These are already set correctly in the baseline dump:

| Parameter | Value | Notes |
|-----------|-------|-------|
| `GPS_TYPE` | 9 | DroneCAN |
| `GPS_CAN_NODEID1` | 124 | CAN node ID |
| `GPS_AUTO_CONFIG` | 2 | AutoConfig DroneCAN |
| `EK3_SRC1_YAW` | 2 | GPS heading |
| `COMPASS_ENABLE` | 0 | Compass disabled |

## Testing Log

1. Connected to FCU via MAVProxy on gabby (`~/project11/.venv/bin/mavproxy.py --master=/dev/fcu,57600`)
2. Set GPS position offsets and enabled moving baseline
3. Rebooted FCU — `GPS_MB1_OFS` params only appear after reboot with `GPS_MB1_TYPE=1`
4. Initial heading was ~254° (WSW) — 180° off from actual ENE orientation
5. Negated `GPS_MB1_OFS_X` (-1.67 → +1.67) and swapped POS1/POS2 X values
6. Heading corrected to ~74° (ENE) — matches boat orientation at pier

## NTRIP / RTK (verified 2026-04-06)

NTRIP RTK corrections verified working on BizzyBoat.

### MACORS Setup

1. Registered at https://macors.massdot.state.ma.us/
2. Created device account (convention: one account per device)
3. Subscribed to real-time GPS corrections service (free, activated same day)
4. Credentials stored in `ccomjhc_project11/configuration/bizzyboat_ntrip.yaml`
   (private repo, loaded at launch via `FindPackageShare`)

### Connection Details

- Host: `macorsrtk.massdot.state.ma.us`
- Port: `31000`
- Mountpoint: `RTCM3_MASA`
- Same CORS network as IzzyBoat (MassDOT MACORS)

### Activation

- Uncommented NTRIP in `core_launch.py`, relaunched on gabby
- RTK fix confirmed — position visibly tighter and more stable in CAMP
