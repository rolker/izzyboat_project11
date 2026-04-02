# BizzyBoat vs IzzyBoat FCU Parameter Comparison

**Date**: 2026-03-31
**BizzyBoat source**: `bizzyboat_project11/config/fcu/bizzyboat_fcu_baseline.param` (935 params)
**IzzyBoat source**: `docs/izzyboat_fcu_params_live.txt` (934 params)
**Total differences**: 172 (including calibration/stats)
**Meaningful differences**: ~90 (excluding per-unit calibration, IMU offsets, baro, RC trim, statistics)

## Steering & Tuning

BizzyBoat is more conservative — lower rates, lower G limits.

| Parameter | IzzyBoat | BizzyBoat | Notes |
|-----------|----------|-----------|-------|
| `ATC_STR_ACC_MAX` | 180 | 120 | Steering acceleration limit |
| `ATC_STR_RAT_FF` | 0.5 | 1.0 | Steering rate feedforward |
| `ATC_STR_RAT_MAX` | 360 | 120 | Max steering rate |
| `ATC_TURN_MAX_G` | 0.4 | 0.2 | Max lateral G in turns |
| `CRUISE_SPEED` | 1.0 | 3.0 | Default cruise speed (m/s) |
| `PILOT_STEER_TYPE` | 3 (two-paddle) | 0 (default) | RC steering mode |
| `TURN_RADIUS` | 0.0 | 0.5 | Min turn radius (m) |
| `WP_PIVOT_ANGLE` | 120 | 45 | Angle to trigger pivot turn |
| `WP_PIVOT_RATE` | 90 | 30 | Pivot turn rate (deg/s) |
| `WP_RADIUS` | 1.5 | 5.0 | Waypoint acceptance radius (m) |
| `LOIT_RADIUS` | 3.0 | 1.0 | Loiter radius (m) |
| `LOIT_SPEED_GAIN` | 0.5 | 0.3 | Loiter speed gain |

## Servo / Drivetrain

Different physical configurations — IzzyBoat is skid-steer, BizzyBoat has throttle + steering.

| Parameter | IzzyBoat | BizzyBoat | Notes |
|-----------|----------|-----------|-------|
| `SERVO1_FUNCTION` | 73 (throttle left) | 70 (throttle) | |
| `SERVO2_FUNCTION` | 74 (throttle right) | 70 (throttle) | |
| `SERVO1_MIN` / `SERVO2_MIN` | 1350 | 1000 | |
| `SERVO3_FUNCTION` | 0 (disabled) | 26 (ground steering) | |
| `SERVO3_REVERSED` | 0 | 1 | |
| `SERVO4_FUNCTION` | 0 (disabled) | 26 (ground steering) | |
| `SERVO4_REVERSED` | 0 | 1 | |
| `SERVO8-16_FUNCTION` | 0 (disabled) | 1 (passthrough) | BizzyBoat enables passthrough on 8-16 |

## RC Mapping

| Parameter | IzzyBoat | BizzyBoat | Notes |
|-----------|----------|-----------|-------|
| `RCMAP_THROTTLE` | 2 | 1 | |
| `RCMAP_ROLL` | 1 | 4 | |
| `RCMAP_PITCH` | 3 | 4 | |
| `RCMAP_YAW` | 4 | 1 | |
| `RC_OPTIONS` | 4 | 32 | |
| `RC9_OPTION` | 153 | 0 | IzzyBoat uses CH9 for a function |

## Compass

BizzyBoat uses compass; IzzyBoat has it disabled.

| Parameter | IzzyBoat | BizzyBoat | Notes |
|-----------|----------|-----------|-------|
| `COMPASS_USE` | 0 | 1 | |
| `COMPASS_USE2` | 0 | 1 | |
| `COMPASS_LEARN` | 0 | 1 | |
| `COMPASS_ORIENT` | 0 | 8 | Rotation_180 |

## GPS

IzzyBoat has moving baseline RTK with position offsets; BizzyBoat does not.

| Parameter | IzzyBoat | BizzyBoat | Notes |
|-----------|----------|-----------|-------|
| `GPS_MB1_TYPE` | 1 (enabled) | 0 (disabled) | Moving baseline RTK |
| `GPS_MB1_OFS_X` | -0.794 | (absent) | Antenna offset |
| `GPS_POS1_X` | -0.341 | 0.0 | GPS position offset |
| `GPS_POS1_Y` | -0.024 | 0.0 | |
| `GPS_POS1_Z` | -0.616 | 0.0 | |
| `GPS_POS2_X` | 0.360 | 0.0 | |
| `GPS_AUTO_CONFIG` | 1 | 2 | |
| `GPS_CAN_NODEID1` | 125 | 124 | Different CAN node ID |

## Obstacle Avoidance

Different OA systems — IzzyBoat uses AVOID_*, BizzyBoat uses OA_* (BendyRuler).

| Parameter | IzzyBoat | BizzyBoat | Notes |
|-----------|----------|-----------|-------|
| `AVOID_ENABLE` | 3 | 0 | IzzyBoat uses simple avoidance |
| `OA_TYPE` | 0 (disabled) | 1 (BendyRuler) | BizzyBoat uses BendyRuler |
| `OA_BR_LOOKAHEAD` | (absent) | 15 | |
| `OA_DB_*` | (absent) | (configured) | Object database params |

## CAN Bus

| Parameter | IzzyBoat | BizzyBoat | Notes |
|-----------|----------|-----------|-------|
| `CAN_P2_DRIVER` | 0 (disabled) | 1 (enabled) | Second CAN driver |
| `CAN_D2_PROTOCOL2` | 0 | 1 | |

## EKF

| Parameter | IzzyBoat | BizzyBoat | Notes |
|-----------|----------|-----------|-------|
| `EK3_IMU_MASK` | 3 (2 IMUs) | 7 (3 IMUs) | |
| `EK3_ABIAS_P_NSE` | 0.003 | 0.020 | |
| `EK3_SRC1_VELZ` | 0 (none) | 3 (GPS) | |
| `EK3_WIND_PSCALE` | 0.5 | 1.0 | |

## Telemetry Stream Rates

IzzyBoat runs all streams at 10Hz; BizzyBoat is lower bandwidth.

| Parameter | IzzyBoat | BizzyBoat |
|-----------|----------|-----------|
| `SR1_EXTRA1` | 10 | 4 |
| `SR1_EXTRA2` | 10 | 4 |
| `SR1_EXTRA3` | 10 | 2 |
| `SR1_EXT_STAT` | 10 | 2 |
| `SR1_POSITION` | 10 | 2 |
| `SR1_RAW_CTRL` | 10 | 1 |
| `SR1_RAW_SENS` | 10 | 2 |
| `SR1_RC_CHAN` | 10 | 2 |
| `SR1_ADSB` | 10 | 0 |

## Failsafe & Misc

| Parameter | IzzyBoat | BizzyBoat | Notes |
|-----------|----------|-----------|-------|
| `FS_THR_ENABLE` | 0 (disabled) | 2 (continue in auto) | |
| `FENCE_MARGIN` | 2.0 | 3.0 | |
| `SERIAL2_BAUD` | 57 (57600) | 115 (115200) | |
| `INS_FAST_SAMPLE` | 5 | 7 | |
| `NTF_BUZZ_PIN` | 0 | -1 (disabled) | |
| `RELAY1/2` | configured (pins 54/55) | disabled | IzzyBoat has relays for ??? |
| `PSC_VEL_P` | 0.3 | 1.0 | |
| `PSC_VEL_D` | 0.015 | 0.0 | |
