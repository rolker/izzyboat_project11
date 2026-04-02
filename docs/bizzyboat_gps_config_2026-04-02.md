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

## Planned FCU Parameter Changes

Assumption: GPS1 = aft antenna, GPS2 = forward antenna (same as IzzyBoat).
To be verified during testing — if heading is 180 degrees off, swap the assignment.

| Parameter | Current | New | Notes |
|-----------|---------|-----|-------|
| `GPS_POS1_X` | 0.0 | -0.835 | Aft antenna, behind CG |
| `GPS_POS1_Y` | 0.0 | 0.0 | Centerline |
| `GPS_POS1_Z` | 0.0 | -0.89 | Above CG (negative = up) |
| `GPS_POS2_X` | 0.0 | 0.835 | Forward antenna, ahead of CG |
| `GPS_POS2_Y` | 0.0 | 0.0 | Centerline |
| `GPS_POS2_Z` | 0.0 | -0.89 | Same height as GPS1 |
| `GPS_MB1_TYPE` | 0 | 1 | Enable moving baseline |
| `GPS_MB1_OFS_X` | 0.0 | -1.67 | Rover-to-base vector (aft) |
| `GPS_MB1_OFS_Y` | 0.0 | 0.0 | No lateral offset |
| `GPS_MB1_OFS_Z` | 0.0 | 0.0 | Same height |

### Sanity check against IzzyBoat

IzzyBoat's working values for comparison:

| Parameter | IzzyBoat | BizzyBoat | Ratio | Makes sense? |
|-----------|----------|-----------|-------|-------------|
| `GPS_POS1_X` | -0.341 | -0.835 | 2.4x | Yes — BizzyBoat (EchoBoat 240) is bigger than IzzyBoat (EchoBoat 160) |
| `GPS_POS1_Z` | -0.616 | -0.89 | 1.4x | Yes — BizzyBoat has taller mast/mounting |
| `GPS_MB1_OFS_X` | -0.794 | -1.67 | 2.1x | Yes — wider antenna separation on larger boat |

IzzyBoat MB offset math: -(0.341 + 0.360) = -0.701 ≈ -0.794 (close, measured values)
BizzyBoat MB offset math: -(0.835 + 0.835) = -1.67 (symmetric, from rough geometry)

## Parameters Already Correct

These are already set correctly in the baseline dump:

| Parameter | Value | Notes |
|-----------|-------|-------|
| `GPS_TYPE` | 9 | DroneCAN |
| `GPS_CAN_NODEID1` | 124 | CAN node ID |
| `GPS_AUTO_CONFIG` | 2 | AutoConfig DroneCAN |
| `EK3_SRC1_YAW` | 2 | GPS heading |
| `COMPASS_ENABLE` | 0 | Compass disabled |

## Testing Plan

1. SSH to gabby, connect to FCU via MAVProxy or QGroundControl
2. Set parameters listed above
3. Power cycle FCU
4. Check `mavros/global_position/raw/fix` for GPS fix
5. Verify heading is correct (not 180 degrees off)
6. If heading is reversed, swap GPS1/GPS2 assignments or negate MB_OFS_X

## NTRIP (deferred)

NTRIP RTK corrections are commented out in `bizzyboat_project11/launch/core_launch.py`.
Assess after basic GPS fix is confirmed. IzzyBoat uses MassDOT CORS
(`macorsrtk.massdot.state.ma.us:31000`, mountpoint `RTCM3_MASA`).
