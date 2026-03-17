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

**Plugin configs** (from `mavros/launch/apm_pluginlists.yaml` and `apm_config.yaml`):
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

From `echoboat_project11/config/echo.yaml`:

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
