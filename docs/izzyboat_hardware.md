# IzzyBoat Hardware Setup

Reference documentation for IzzyBoat (EchoBoat 160) hardware configuration.
Companion to [izzyboat_network.md](izzyboat_network.md).

## Flight Controller

### Hardware

- **Model**: Cube Orange (Hex/ProfiCNC)
  - Vendor ID: `0x2DAE`, Product ID: `0x1016`
  - Board revision: 9175040
- **Connection to robot computer**: USB via FTDI bridge → `/dev/ttyUSB0` at 57600 baud
- **GCS forwarding**: `udp://@192.168.12.8` (blaze — onboard Windows PC for optional monitoring)
- **Protocol**: MAVLink v2.0 (target system 1, component 1)

### Firmware

- **Autopilot**: ArduPilot
- **Vehicle type**: ArduRover (MAV_TYPE_SURFACE_BOAT)
- **Version**: 4.5.7 (git `5d8deb25`)
- **Source tree**: `/home/field/src/ardupilot` on mystique (has `ardurover` built)

_TODO: check for available ArduRover firmware updates_

### ArduPilot Parameter Configuration

Non-default FCU parameters observed 2026-03-17. Full parameter dump:
[`izzyboat_fcu_params_live.txt`](izzyboat_fcu_params_live.txt) (reference defaults:
[`ardurover_4.5_defaults.param`](ardurover_4.5_defaults.param)).

#### Board & Hardware

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `BRD_TYPE` | 3 | 0 | Cube Orange board type |
| `BRD_SAFETY_DEFLT` | 0 | 1 | Safety switch disabled by default |
| `BRD_SAFETYOPTION` | 7 | 3 | Safety options bitmask |
| `BRD_OPTIONS` | 1 | 0 | Board options bitmask |
| `BRD_VBUS_MIN` | 4.3 V | 4.5 V | Minimum FMU bus voltage |
| `BRD_HEAT_TARG` | 30 °C | -1 | IMU heater target temperature |
| `BRD_HEAT_P` | 50 | 1 | IMU heater PID P gain |
| `BRD_HEAT_I` | 0.07 | 0.1 | IMU heater PID I gain |

#### GPS

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `GPS_TYPE` | 9 | 1 | UAVCAN/DroneCAN GPS |
| `GPS_CAN_NODEID1` | 125 | 0 | CAN node ID for GPS |
| `GPS_POS1_X` | -0.341 m | 0 | GPS antenna offset X (forward) |
| `GPS_POS1_Y` | -0.024 m | 0 | GPS antenna offset Y (right) |
| `GPS_POS1_Z` | -0.616 m | 0 | GPS antenna offset Z (down) |
| `GPS_POS2_X` | 0.360 m | 0 | Moving baseline rover offset X |
| `GPS_MB1_TYPE` | 1 | 0 | Moving baseline type (enabled) |
| `GPS_MB1_OFS_X` | -0.794 m | 0 | Moving baseline antenna offset X |
| `GPS_MB1_OFS_Z` | 0.012 m | 0 | Moving baseline antenna offset Z |
| `GPS_SAVE_CFG` | 0 | 2 | Do not save GPS config on boot |

#### CAN Bus

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `CAN_P1_DRIVER` | 1 | 0 | CAN port 1 driver enabled |
| `CAN_D1_PROTOCOL` | 1 | 0 | DroneCAN protocol on CAN bus 1 |
| `CAN_D2_PROTOCOL` | 1 | 0 | DroneCAN protocol on CAN bus 2 |
| `CAN_LOGLEVEL` | 0 | 1 | CAN logging disabled |

#### Serial Ports

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `SERIAL3_BAUD` | 57 (57600) | 230 | GPS1 serial baud (`SERIAL3_PROTOCOL=5`, GPS) |
| `SERIAL4_BAUD` | 57 (57600) | 230 | Serial4 baud (MAVLink1) |
| `SERIAL4_PROTOCOL` | 1 (MAVLink1) | 5 | Serial4 protocol (MAVLink1, not GPS) |
| `SERIAL5_PROTOCOL` | 1 (MAVLink1) | 0 | Serial5 protocol enabled |
| `SERIAL6_PROTOCOL` | -1 (disabled) | 0 | Serial6 disabled |
| `SERIAL_PASS1` | 0 | -1 | Serial passthrough disabled |

#### EKF3 (State Estimation)

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `AHRS_EKF_TYPE` | 3 | 3 | EKF3 active (default for Rover) |
| `EK3_PRIMARY` | 1 | 0 | EKF3 primary lane index |
| `EK3_MAG_CAL` | 5 | 2 | Magnetometer calibration mode (never) |
| `EK3_ABIAS_P_NSE` | 0.003 | 0.02 | Accel bias process noise |
| `EK3_VELNE_M_NSE` | 0.5 | 0.3 | Horizontal velocity measurement noise |
| `EK3_WIND_PSCALE` | 0.5 | 1.0 | Wind speed process noise scaling |
| `EK3_SRC1_POSXY` | 3 (GPS) | 3 | Primary XY position source |
| `EK3_SRC1_VELXY` | 3 (GPS) | 3 | Primary XY velocity source |
| `EK3_SRC1_YAW` | 2 (GPS) | 2 | Primary yaw source (GPS moving baseline) |
| `EK3_SRC_OPTIONS` | 1 | 0 | Source options (fuse all velocities) |
| `AHRS_COMP_BETA` | 0.001 | 0.1 | AHRS complementary filter beta |
| `AHRS_GPS_MINSATS` | 2 | 6 | Minimum sats for GPS use |
| `AHRS_TRIM_X` | 0.02959 rad | 0 | Accelerometer trim (calibrated) |
| `AHRS_TRIM_Y` | -0.00477 rad | 0 | Accelerometer trim (calibrated) |
| `AHRS_YAW_P` | 0.4 | 0.2 | AHRS yaw P gain |

#### Compass

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `COMPASS_ENABLE` | 0 | 1 | **Compass disabled** (GPS yaw used instead) |
| `COMPASS_USE` | 0 | 1 | Compass 1 not used |
| `COMPASS_USE2` | 0 | 1 | Compass 2 not used |
| `COMPASS_USE3` | 0 | 1 | Compass 3 not used |
| `COMPASS_AUTODEC` | 0 | 1 | Auto declination disabled |
| `COMPASS_DEC` | -0.1041 rad | 0 | Manual declination (~−6°, NH area) |
| `COMPASS_OFS_X` | 10 | 0 | Calibrated offset X |
| `COMPASS_OFS_Y` | 39 | 0 | Calibrated offset Y |
| `COMPASS_OFS_Z` | -79 | 0 | Calibrated offset Z |
| `COMPASS_DIA_X/Y/Z` | 1.09/0.86/1.12 | 1.0 | Calibrated diagonal matrix |

#### INS / IMU

Calibration values set automatically by ArduPilot during accelerometer and gyro
calibration. Not intended for manual editing.

| Parameter | Notes |
|-----------|-------|
| `INS_ACC_ID`, `INS_ACC2_ID`, `INS_ACC3_ID` | Hardware sensor IDs (auto-set) |
| `INS_GYR_ID`, `INS_GYR2_ID`, `INS_GYR3_ID` | Hardware sensor IDs (auto-set) |
| `INS_ACCOFFS_*`, `INS_ACC2OFFS_*`, `INS_ACC3OFFS_*` | Accelerometer offsets (calibrated) |
| `INS_ACCSCAL_*`, `INS_ACC2SCAL_*`, `INS_ACC3SCAL_*` | Accelerometer scale factors (calibrated) |
| `INS_GYROFFS_*`, `INS_GYR2OFFS_*`, `INS_GYR3OFFS_*` | Gyro offsets (calibrated) |
| `INS_POS1_*` | IMU position offsets: X=0.667m, Y=0.044m, Z=−0.052m |
| `INS_ACCEL_FILTER` | 10 Hz (default: 20 Hz) — low vibration environment |
| `INS_GYRO_FILTER` | 4 Hz (default: 20 Hz) — low vibration environment |
| `INS_FAST_SAMPLE` | 5 (default: 1) |
| `INS_GYRO_RATE` | 1 (default: 0) |

#### Battery Monitor

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `BATT_MONITOR` | 4 | 0 | Analog voltage+current monitor enabled |
| `BATT_CAPACITY` | 16000 mAh | 3300 | Battery capacity |
| `BATT_VOLT_PIN` | 14 | — | Voltage sense pin |
| `BATT_CURR_PIN` | 15 | — | Current sense pin |
| `BATT_VOLT_MULT` | 12.02 | — | Voltage multiplier (calibrated) |
| `BATT_AMP_PERVLT` | 39.88 A/V | — | Amps-per-volt (calibrated) |

#### Vehicle & Navigation

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `FRAME_CLASS` | 2 (boat) | 1 (rover) | Surface boat frame |
| `CRUISE_SPEED` | 1.0 m/s | 2.0 m/s | Target cruise speed |
| `CRUISE_THROTTLE` | 35% | 50% | Throttle at cruise speed |
| `TURN_RADIUS` | 0.0 m | 0.9 m | Min turn radius (skid-steer, set to 0) |
| `WP_RADIUS` | 1.5 m | 2.0 m | Waypoint acceptance radius |
| `WP_PIVOT_ANGLE` | 120° | 60° | Pivot turn entry angle |
| `WP_PIVOT_RATE` | 90°/s | 60°/s | Pivot turn rate |
| `LOIT_RADIUS` | 3.0 m | 2.0 m | Loiter radius |
| `MIS_DONE_BEHAVE` | 1 (loiter) | 0 (hold) | Behavior after mission completes |
| `RALLY_INCL_HOME` | 1 | 0 | Include home in rally points |
| `RALLY_LIMIT_KM` | 0.5 km | 1.0 km | Rally point search radius |
| `SRTL_POINTS` | 150 | 500 | Smart RTL path points |

#### Attitude & Steering Control

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `ATC_STR_RAT_P` | 1.0 | 0.2 | Steering rate PID P |
| `ATC_STR_RAT_I` | 0.5 | 0.2 | Steering rate PID I |
| `ATC_STR_RAT_FF` | 0.5 | 0.2 | Steering rate feed-forward |
| `ATC_STR_RAT_MAX` | 360°/s | 120°/s | Max steering rate |
| `ATC_STR_ACC_MAX` | 180°/s² | 120°/s² | Max steering acceleration |
| `ATC_ACCEL_MAX` | 5.0 m/s² | 1.0 m/s² | Max longitudinal acceleration |
| `ATC_BRAKE` | 0 | 1 | Auto-braking disabled |
| `ATC_TURN_MAX_G` | 0.4 g | 0.6 g | Max lateral g in turns |
| `PSC_VEL_P` | 0.3 | 1.0 | Velocity control P gain |
| `PSC_VEL_D` | 0.015 | 0.0 | Velocity control D gain |
| `PILOT_STEER_TYPE` | 3 | 0 | Steering type (two paddles) |

#### Flight Modes

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `MODE_CH` | 5 | 8 | RC channel for mode selection |
| `MODE3` | 5 (Steering) | 0 (Manual) | Switch position 3 |
| `MODE4` | 5 (Steering) | 0 (Manual) | Switch position 4 |
| `MODE5` | 10 (Auto) | 0 (Manual) | Switch position 5 |
| `MODE6` | 10 (Auto) | 0 (Manual) | Switch position 6 |

#### RC Channels

RC inputs calibrated for the operator controller. Key non-default values:

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `RCMAP_PITCH` | 3 | 2 | Pitch mapped to CH3 |
| `RCMAP_THROTTLE` | 2 | 3 | Throttle mapped to CH2 |
| `RC1_MIN/MAX/TRIM` | 982/2006/1494 | 1100/1900/1500 | CH1 (steering) calibrated |
| `RC2_MIN/MAX/TRIM` | 1340/2006/1496 | 1100/1900/1500 | CH2 (throttle) calibrated |
| `RC5_TRIM` | 1161 | 1500 | CH5 (mode switch) calibrated |
| `RC7_OPTION` | 153 | 0 | CH7 option set |
| `RC9_OPTION` | 153 | 0 | CH9 option set |
| `RC1_DZ`, `RC2_DZ` | 30 | 0 | Deadzone set |

#### Servos (Motor Outputs)

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `SERVO1_FUNCTION` | 73 (throttle left) | 0 | Left thruster |
| `SERVO2_FUNCTION` | 74 (throttle right) | 0 | Right thruster |
| `SERVO1_MIN/MAX` | 1350/2000 | 1100/1900 | Left thruster range |
| `SERVO2_MIN/MAX` | 1350/2000 | 1100/1900 | Right thruster range |
| `SERVO6_FUNCTION` | 1 (RCPassThru) | 0 | Servo 6 RC passthrough |

#### Arming & Failsafe

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `ARMING_CHECK` | 0 | 1 | **All pre-arm checks disabled** |
| `ARMING_RUDDER` | 0 | 2 | Rudder arming disabled |
| `FS_ACTION` | 0 | 1 | **Failsafe action disabled** (no RTL/Hold) |
| `FS_EKF_ACTION` | 0 | 1 | **EKF failsafe disabled** |
| `FS_THR_ENABLE` | 0 | 1 | **Throttle failsafe disabled** |
| `FS_TIMEOUT` | 1.0 s | 1.5 s | Failsafe timeout |

#### Obstacle Avoidance

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `AVOID_ENABLE` | 3 | 0 | Fence + proximity avoidance enabled |

#### Logging

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `LOG_BACKEND_TYPE` | 0 (none) | 1 (file) | No onboard dataflash logging |
| `LOG_DISARMED` | 1 | 0 | Log while disarmed |
| `GCS_PID_MASK` | 1 | 0 | PID tuning data streamed to GCS |

#### MAVLink Stream Rates

SR0 (USB/serial0), SR1–SR2 (telemetry), SR3 (serial3), SR4 (serial4).
All non-zero where default is 0.

| Streams | SR0 | SR1 | SR2 | SR3 | SR4 |
|---------|-----|-----|-----|-----|-----|
| EXTRA1/2/3 | 4 | 10 | 10 | 1 | 1 |
| EXT_STAT | 4 | 10 | 10 | 1 | 1 |
| POSITION | 4 | 10 | 10 | 1 | 1 |
| RAW_CTRL/SENS | 4 | 10 | 10 | 1 | 1 |
| RC_CHAN | 4 | 10 | 10 | 1 | 1 |
| ADSB | 4 | 10 | 10 | 0 | 0 |
| PARAMS | 10 | 10 | 10 | 10 | 10 |

#### Miscellaneous

| Parameter | Value | Default | Notes |
|-----------|-------|---------|-------|
| `FORMAT_VERSION` | 16 | 1 | EEPROM format version (auto-set) |
| `STAT_BOOTCNT` | 356 | — | Boot count |
| `STAT_FLTTIME` | 912262 s (~253 h) | — | Total flight/run time |
| `NTF_LED_BRIGHT` | 3 | 1 | LED brightness max |
| `NTF_LED_TYPES` | 199 | 0 | LED type bitmask |
| `NTF_BUZZ_TYPES` | 5 | 1 | Buzzer type bitmask |
| `RC_OPTIONS` | 4 | 0 | RC options bitmask |
| `RC_PROTOCOLS` | 1 | 0 | RC protocol (PWM) |
| `RELAY1_FUNCTION` | 1 | — | Relay 1 function |
| `RELAY1_PIN` | 54 | — | Relay 1 GPIO pin |
| `RELAY2_FUNCTION` | 1 | — | Relay 2 function |
| `RELAY2_PIN` | 55 | — | Relay 2 GPIO pin |

### MAVROS Configuration

MAVROS runs as a ROS 2 node under the `/izzy/mavros/` namespace. It is configured
to respawn on failure (5-second delay).

**Parameters** (from `echoboat_project11/config/echo.yaml` and `mavros.yaml`):
- `system_id`: 255 (GCS ID)
- `component_id`: 240
- `tgt_system`: 1
- `tgt_component`: 1
- `conn.timesync_rate`: 0.0 (disabled)
- `global_position.tf.send`: false
- `local_position.tf.send`: false
- `setpoint_velocity.mav_frame`: BODY_NED

**Plugin configs** (from `mavros/launch/apm_pluginlists.yaml` and `apm_config.yaml` in the `mavros` ROS package — external, not in this repo):
standard ArduPilot plugin set.

### Navigation Sources

The `platform_sender` node (from `izzyboat.yaml`) accepts two navigation sources:

| Source | Orientation | Position | Velocity | Status |
|--------|-------------|----------|----------|--------|
| `mru` (MAVROS/FCU) | `mavros/imu/data` | `mavros/global_position/raw/fix` | `mavros/global_position/raw/gps_vel` | Active (primary) |
| `posmv` (Applanix POS MV) | `sensors/posmv/orientation` | `sensors/posmv/position` | `sensors/posmv/velocity` | Inactive (POS MV removed) |

### GPS Status (observed 2026-03-17, lab/indoor)

- **Fix type**: 3D
- **Satellites visible**: 14
- **Position**: ~43.136°N, 70.939°W (Durham, NH — UNH campus area)
- **Horizontal accuracy**: ~6.9m (indoor, no RTK)

### Battery (observed 2026-03-17)

- **Voltage**: 23.4V (single cell reported)
- **Percentage**: 100%
- **Current**: 0.0A (idle)

## Vehicle Parameters

Physical dimensions from `izzyboat_project11/config/platform.yaml`; navigation speed/tuning parameters from an earlier project11 configuration layout (no longer present as a single file in this repo):

| Parameter | Value | Notes |
|-----------|-------|-------|
| Width | 0.8 m | |
| Length | 1.75 m | |
| Reference X | -0.225 m | Offset from center |
| Reference Y | 0.05 m | Offset from center |
| Max speed | 2.0 m/s | |
| Max yaw rate | 1.5 rad/s | |
| Turn radius | 4.0 m | |
| Default speed | 1.5 m/s | |
| Helm output type | twist | |

### PID Tuning (path follower)

- Kp: 20.0
- Ki: 0.5
- Kd: 0.6

## Sensors

### Imagenex DeltaT Multibeam Sonar

- **Address**: `192.168.0.2` (hardcoded)
- **ROS namespace**: `/izzy/sensors/deltat/`
- **Frame ID**: `izzy/deltat`
- **Topics**: `soundings`, `grid`
- **Processing**: `cube_bathymetry` node (cell size 0.5m, map frame `izzy/map`)

### Norbit Winghead Multibeam Sonar (temporary, loaner/eval)

- **Address**: `192.168.53.34`
- **ROS namespace**: `/izzy/sensors/norbit/`
- **Frame ID**: `izzy/norbit`
- **Topics**: `soundings`, `detections`
- **Config**: range 1–100m, trigger mode 6, power on
- **Note**: Currently commented out in launch file; was active during Summer Hydro
  and evaluation period

### Applanix POS MV (currently removed)

- **Address**: `192.168.12.4` (`posmv_izzyboat`)
- **ROS namespace**: `/izzy/sensors/posmv/`
- **Topics**: `position`, `orientation`, `velocity`
- **Note**: Launch section commented out; referenced as secondary nav source in
  `platform_sender` config

### OAK-D Camera (front)

- **ROS namespace**: `/izzy/sensors/cameras/front/oak/`
- **Features**: segmentation, detection (JOLO), pointcloud generation
- **Processing pipeline**: segmentation → segments_to_pointcloud

### USB Camera (top)

- **ROS namespace**: `/izzy/sensors/cameras/top/`
- **Node**: `usb_cam` (`top_camera`)
- **Resolution**: 640x360, 5 fps, MJPEG
- **Frame ID**: `izzy/top_camera_optical`

### AML Sound Speed Sensor

- **Type**: Winch-deployed sound speed profiler
- **Connection**: WiFi AP (SSID `AML_A30894`), boat router connects as client
- **Router interface**: `ifWan3` (2.4 GHz radio, `relayd` zone)
- **Status**: disabled when not in use
- **Note**: Experimental automation; important for multibeam sonar data quality

## Data Logging

Two rosbag recorders run simultaneously:

### Main Logger

Records general topics (navigation, autonomy, camera, diagnostics) to
`/home/field/project11/logs/izzyboat/`. Split every 5 minutes, zstd compression.

### Sonar Logger

Records sonar-specific topics (DeltaT/Norbit soundings, navigation for
georeferencing) to `/home/field/project11/logs/izzyboat_sonar/`. Split every
5 minutes, zstd compression.

## URDF

Robot model defined in `izzyboat_project11/urdf/izzyboat.urdf`.

_TODO: document sensor frame transforms from URDF_

## Considerations for BizzyBoat

- **Flight controller**: likely same model (Cube Orange) with ArduRover;
  needs separate parameter tuning for larger 240 hull
- **Vehicle parameters**: width, length, turn radius, max speed, PID all need
  adjustment for EchoBoat 240
- **Sensors**: DeltaT may be shared or a second unit purchased; BizzyBoat may
  get the Norbit Winghead if purchased
- **Frame IDs**: need unique prefix (e.g., `bizzy/`) to avoid TF conflicts
