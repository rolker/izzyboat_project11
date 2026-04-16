# BizzyBoat Deployment Guide

Deploying [project11](https://github.com/rolker/ros2_agent_workspace) on an
EchoBoat 240 (BizzyBoat). This guide covers the hardware configuration and
software setup for autonomous surface vehicle operations using ROS 2.

The EchoBoat 240 is a small, portable ASV manufactured by Seafloor Systems.
Project11 adds a robot computer, sensors, and a ROS 2 software stack for
autonomous navigation, perception, and remote operation.

## Part 1: System Reference

### Factory Hardware

The EchoBoat 240 ships with:

- **Hull and thrusters** — 2.40 m HDPE hull, 0.90 m beam, ~159 kg dry weight,
  ~91 kg payload capacity, differential thrust via two electric motors
- **Cube Orange autopilot** — runs ArduRover firmware, handles low-level motor
  control, RC failsafe, and waypoint navigation
- **RC controller** — manual control and emergency stop
- **Windows PC** — runs vendor sonar software (we renamed ours to "mercat" for
  fleet uniqueness)
- **USB camera** — factory-installed forward-facing camera
- **WiFi bridge** — MikroTik OmniTIK 5 ac (boat side) and SXTsq Lite5 (shore
  side), provides the primary data link between boat and operator station

### Added Hardware

These components were added for project11 integration. Not all are required —
the setup is modular. Alternatives are noted where applicable.

#### Robot Computer (required)

Any Ubuntu-capable PC with ethernet. We use a Neousys Nuvo 9160GC (Core
i7-14700, 32 GB RAM) running Ubuntu 24.04 Server. It connects to the onboard
LAN via ethernet and to the Cube Orange FCU via USB.

#### GNSS (recommended)

The EchoBoat does not ship with a GNSS receiver. We added a CUAV C-RTK 2HP
with dual antennas for centimeter-level RTK positioning and GPS-based heading.
The C-RTK 2HP connects to the Cube Orange via DroneCAN.

A single-antenna GPS would also work but would not provide heading. Without any
GNSS, the boat can still be driven manually via RC or joystick, but autonomous
navigation is not possible.

#### Obstacle Detection (optional)

Four Luxonis OAK-1 PoE cameras mounted on a camera tower, facing forward,
starboard, aft, and port. Each runs a `sea_surface_segmentation` node that
detects obstacles at the sea surface.

This is one approach — a lidar could replace the cameras, different camera
models could be substituted, or obstacle detection can be omitted entirely if
not needed for the mission.

#### Sonar (optional, mission-specific)

An Imagenex DeltaT multibeam sonar, controlled from the Windows PC (mercat).
Data is forwarded to the robot computer for ROS integration via the
`imagenex_deltat` driver.

#### Networking

- **Teltonika RUTX11 router** — onboard router with cellular modem, manages
  the boat's LAN, WAN failover (Starlink, cellular), and VPN
- **PoE switch** (Trendnet TI-PG80B) — powers the OAK cameras and connects
  all onboard ethernet devices
- **Starlink Mini** (optional) — offshore internet connectivity

The factory MikroTik WiFi bridge provides the primary low-latency link to the
operator station. The Teltonika router adds WAN connectivity for VPN, cellular
failover, and internet access.

### Network Architecture

```
Operator Station (192.168.13.0/24)
  ├── salmon (operator computer, .142)
  └── Operator router (.1)
        ├── WiFi bridge (172.16.20.0/24) ──── MikroTik link ──── Boat router
        └── VPN (WireGuard via BenCloud) ──── internet ──────── Boat router

Boat Onboard LAN (192.168.20.0/24)
  ├── Boat router / Teltonika RUTX11 (.1)
  │     ├── WAN: Starlink / cellular failover
  │     ├── LAN1: PoE switch (onboard LAN)
  │     └── LAN2: MikroTik OmniTIK (WiFi bridge, 172.16.20.0/24)
  ├── gabby / robot computer (.5)
  ├── mercat / Windows PC (.8)
  ├── OAK cameras (.9–.12)
  └── KVM (.50)
```

**Dual-path connectivity**: The operator station reaches the boat via two
independent paths — the WiFi bridge (~1 ms latency) and a WireGuard VPN
through a cloud relay (~37 ms). UDP bridge topics are sent over both paths
for redundancy.

**NETMAP**: Since multiple boats share the same operator LAN, each boat's
onboard subnet is NATed to a unique "virtual" subnet for VPN routing:

| Boat | Onboard | NETMAP (via VPN) |
|------|---------|------------------|
| BizzyBoat | 192.168.20.0/24 | 192.168.21.0/24 |
| IzzyBoat | 192.168.12.0/24 | 192.168.14.0/24 |

### Software Stack

**Operating system**: Ubuntu 24.04 Server (no GUI on the robot computer).

**ROS 2 Jazzy** with the following key packages:

| Package | Purpose |
|---------|---------|
| `mavros` | Communication with Cube Orange FCU (ArduRover) |
| `ntrip_client` | NTRIP corrections for RTK GPS |
| `mru_transform` | Motion reference unit transforms |
| `echo_helm` | Translates helm commands to MAVRos velocity setpoints |
| `helm_manager` | Arbitrates between autonomous and manual helm inputs |
| `udp_bridge` | Bridges ROS topics between boat and operator over UDP |
| `sea_surface_segmentation` | Obstacle detection from camera images |
| `imagenex_deltat` | DeltaT sonar driver |
| `cube_bathymetry` | Bathymetric data processing |
| `marine_autonomy` | Autonomous navigation behaviors |
| `s57_grids` | ENC chart data for navigation |
| `camp` | Operator map display |

**Workspace organization**: The project11 workspace uses a layered colcon
architecture. Layers are sourced in order — each overlays the previous:

1. **underlay** — third-party dependencies (geographic_info, nmea_navsat_driver, etc.)
2. **core** — autonomy stack (marine_autonomy, udp_bridge, helm_manager, etc.)
3. **platforms** — boat-specific packages (bizzyboat_project11, izzyboat_project11, etc.)
4. **site** — site-specific configuration (private, credentials, fleet config)
5. **sensors** — sensor drivers (OAK cameras, sonar, radar)
6. **simulation** — Gazebo worlds and sim configs
7. **ui** — operator tools (CAMP, rqt plugins)

### Launch Structure

The boat's ROS nodes are organized into three launch groups, each run in a
separate tmux pane via `start_tmux_project11.bash`:

**Core** (`core_launch.py`):
- MAVRos (FCU communication)
- MRU transform
- Echo helm + helm manager (joystick/autonomous control)
- UDP bridge (boat ↔ operator communication)
- NTRIP client (RTK corrections)
- Robot state publisher (URDF → TF)

**Perception** (`perception_launch.py`):
- 4x OAK camera nodes (sea_surface_segmentation)
- DeltaT sonar + cube_bathymetry
- USB camera
- Rosbag loggers

**Navigation** (`nav_launch.py`):
- Marine autonomy (mission execution)
- S57 chart grids
- Nav2 stack

Each group can be launched independently. For basic manual control via
joystick, only the core launch is needed.

### Coordinate Frames

The URDF defines sensor positions relative to `base_link`, located at the
hull's center of gravity. ArduPilot uses a different convention (X forward,
Y right, Z down) — the URDF uses the ROS standard (X forward, Y left, Z up).

Key sensor positions (approximate, from `base_link`):

| Sensor | X (m) | Y (m) | Z (m) | Notes |
|--------|-------|-------|-------|-------|
| GNSS forward | 0.835 | 0.0 | 0.89 | On center rail |
| GNSS aft | -0.835 | 0.0 | 0.89 | On center rail |
| Cameras (all 4) | 0.31 | 0.0 | 1.41 | Tower top, 90 deg apart |
| DeltaT sonar | -0.23 | 0.0 | -0.18 | Below hull, downward |
| Factory USB cam | 1.05 | 0.0 | 0.89 | Forward end of rail |
| FCU / IMU | -0.975 | 0.0 | 0.065 | Aft, inside electronics bay |

GNSS baseline (antenna-to-antenna): ~1.67 m.

---

## Part 2: Setup Guide

### Prerequisites

- EchoBoat 240 with Cube Orange FCU running ArduRover 4.5+
- Robot computer with Ubuntu 24.04 installed, connected to onboard LAN
- Ethernet connectivity between all onboard devices
- SSH access to the robot computer
- An NTRIP account for RTK corrections (e.g., MassDOT MACORS for New England,
  or your regional CORS network)

### 1. ROS 2 Installation

Install ROS 2 Jazzy (base, no desktop) on the robot computer following the
[official instructions](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html):

```bash
# Add ROS 2 apt repository (see official docs for current key/source setup)
sudo apt install ros-jazzy-ros-base
```

Verify the installation:

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic list
```

### 2. Workspace Bootstrap

Clone and build the workspace. If using a local git server (like gitcloud for
field deployments), substitute the appropriate URLs:

```bash
git clone https://github.com/rolker/ros2_agent_workspace.git project11
cd project11
NONINTERACTIVE=1 make build
```

The first `make build` automatically runs bootstrap, imports the manifest
repositories, and builds all layers. This pulls in ~400 packages and may take
30+ minutes on first build.

Install ROS dependencies:

```bash
cd layers/main
rosdep install -i --from-paths underlay_ws/src/ core_ws/src/ platforms_ws/src/ site_ws/src/ sensors_ws/src/ -y
```

Note: `rosdep` may pull in simulation dependencies (e.g., Gazebo) that are not
needed on a field robot. This is a known issue.

### 3. Network Configuration

#### Onboard Router

Configure the Teltonika RUTX11 (or equivalent):

- **LAN**: 192.168.20.0/24, gateway 192.168.20.1
- **DHCP**: Pool 192.168.20.200–249 for transient devices; static leases for
  the robot computer, Windows PC, cameras, and any other permanent devices
- **WAN**: Connect to your internet source (Starlink, cellular, marina WiFi)
- **VPN**: WireGuard to your relay server for remote access

#### WiFi Bridge

The factory MikroTik radios provide the primary boat-to-shore link. Configure
them on a dedicated bridge subnet (e.g., 172.16.20.0/24) separate from the
onboard LAN. The boat router and operator router each get an interface on this
bridge subnet with static routes to reach each other's LANs.

#### Operator Router

The operator station needs routes to the boat's onboard LAN, either through
the WiFi bridge subnet or through the VPN. If operating multiple boats, use
NETMAP to give each boat a unique virtual subnet on the VPN.

### 4. Device Setup

#### USB Device Symlinks (udev)

Create udev rules for stable device names. USB device enumeration order is not
guaranteed, so `/dev/ttyACM0` may change between boots. Udev rules create
persistent symlinks based on vendor ID and serial number:

```
# /etc/udev/rules.d/99-echoboat.rules

# Cube Orange FCU (MAVLink interface)
SUBSYSTEM=="tty", ENV{ID_USB_VENDOR_ID}=="2dae", ENV{ID_USB_MODEL_ID}=="1016", \
  ENV{ID_USB_INTERFACE_NUM}=="00", SYMLINK+="fcu", MODE="0666"

# Add similar rules for other USB devices (winch, sensors, etc.)
# Use udevadm to discover vendor IDs and serial numbers:
#   udevadm info -a -n /dev/ttyACM0
#   udevadm info -q property -n /dev/ttyACM0
```

Reload and test:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
ls -la /dev/fcu
```

Add the robot user to the `dialout` group for serial access:

```bash
sudo usermod -aG dialout $USER
```

#### OAK Camera IP Assignment

OAK-1 PoE cameras get their IPs from DHCP. Assign static leases in the router
based on MAC address, then update the per-camera YAML config files
(`config/oak_forward.yaml`, etc.) with the correct IPs.

### 5. FCU Configuration

#### GPS Antenna Offsets

If using dual-antenna GPS for heading (e.g., CUAV C-RTK 2HP), configure the
antenna position offsets in ArduPilot. Connect to the FCU via MAVProxy:

```bash
# Install MAVProxy in a virtualenv
python3 -m venv .venv
.venv/bin/pip install MAVProxy 'setuptools<81'
.venv/bin/mavproxy.py --master=/dev/fcu,57600
```

Set the GPS parameters (adjust positions for your antenna mounting):

```
# In MAVProxy:
param set GPS_MB1_TYPE 1          # Enable moving baseline
param set GPS_POS1_X <forward_offset>    # GPS1 position from CG (meters)
param set GPS_POS1_Z <height_offset>     # Negative = above CG in ArduPilot
param set GPS_POS2_X <aft_offset>
param set GPS_POS2_Z <height_offset>
param set GPS_MB1_OFS_X <baseline>       # Antenna-to-antenna distance
```

Reboot the FCU after setting `GPS_MB1_TYPE` — the `GPS_MB1_OFS` parameters
only appear after a reboot with moving baseline enabled.

Verify heading is correct by comparing the reported heading with the boat's
known orientation. If heading is 180 degrees off, swap the POS1/POS2 values
and negate the MB1_OFS vector — your GPS1 and GPS2 assignment may differ from
what you expect.

#### ArduRover Parameters

Save a baseline parameter dump before making changes:

```
# In MAVProxy:
param save /path/to/baseline.param
```

Key parameters to review:

| Parameter | Purpose | Notes |
|-----------|---------|-------|
| `SERVO1_FUNCTION` | Throttle (70) or left motor (73) | Depends on drivetrain |
| `SERVO3_FUNCTION` | Steering (26) if applicable | |
| `ARMING_CHECK` | Pre-arm checks | Set to 0 only for bench testing |
| `FS_THR_ENABLE` | Throttle failsafe | RC signal loss behavior |
| `EK3_SRC1_YAW` | Yaw source | 2 = GPS heading (for dual antenna) |
| `COMPASS_ENABLE` | Compass | 0 if using GPS heading instead |

#### Safety Notes

- **Always test with the boat secured** (on a cart or in the water with a
  tether) when first configuring the FCU
- **Clear any stale missions** before entering GUIDED mode — ArduRover will
  attempt to navigate to the first waypoint if a mission exists
- **Keep the RC controller powered on** — flicking to MANUAL mode is the
  emergency stop
- **Set ARMING_CHECK back to default** after bench testing is complete

### 6. NTRIP / RTK Setup

Register with your regional CORS network for NTRIP corrections. For New
England, MassDOT MACORS provides free real-time corrections:

1. Register at your CORS provider's website
2. Create a device account (convention: one per boat)
3. Subscribe to the real-time corrections service

Configure the NTRIP client parameters:

- Host, port, mountpoint (from your CORS provider)
- Username and password
- `authenticate: true` (the ntrip_client node defaults to unauthenticated)

The `ntrip_launch.py` file loads these from a YAML config file. Store
credentials outside of public repositories.

### 7. Launch Verification

#### Core Launch

Start with just the core launch to verify FCU communication and basic control:

```bash
ros2 launch bizzyboat_project11 core_launch.py
```

Verify:
- MAVRos connects to the FCU (check for "Connected!" in mavros logs)
- GPS fix (check `/bizzy/mavros/global_position/global`)
- Joystick control works from the operator station (requires UDP bridge and
  helm nodes)

#### Sensors

```bash
ros2 launch bizzyboat_project11 perception_launch.py
```

Verify camera images are published and visible on the operator station via
UDP bridge.

#### Navigation

```bash
ros2 launch bizzyboat_project11 nav_launch.py
```

Requires ENC chart data installed on the robot computer for S57 grids.

#### Operator Station

On the operator computer, launch the operator UI:

```bash
ros2 launch bizzyboat_project11 operator_ui_launch.py
```

This starts CAMP (map display) and rqt. The boat's position should appear on
the chart. Camera feeds and other telemetry are received via UDP bridge.

### 8. Field Deployment

#### Startup

The `start_tmux_project11.bash` script creates a tmux session with three panes
(core, perception, navigation). For convenience, add it to the robot user's
`.bashrc` or create a symlink:

```bash
ln -s ~/project11/layers/main/platforms_ws/install/bizzyboat_project11/share/bizzyboat_project11/scripts/start_tmux_project11.bash ~/start_tmux_project11.bash
```

#### Git-based Deployment Workflow

For iterating on configuration changes in the field:

1. Make changes on a development machine
2. Commit and push to a git server accessible from the boat (we use a local
   Forgejo instance called "gitcloud")
3. Pull and rebuild on the robot computer
4. Relaunch the affected nodes

This avoids editing files directly on the robot computer and keeps all changes
tracked in version control.

#### Pre-launch Checklist

- [ ] RC controller powered on and bound
- [ ] GPS has fix (check satellite count and fix type)
- [ ] RTK corrections flowing (check NTRIP connection status)
- [ ] WiFi bridge link established (ping operator station)
- [ ] Clear any stale missions from FCU
- [ ] Verify boat position on operator map (CAMP)
- [ ] Test joystick control before leaving the dock
