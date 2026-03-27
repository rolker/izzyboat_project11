# Create bizzyboat_project11 ROS 2 package

**Date**: 2026-03-27
**Issue**: rolker/unh_echoboats_project11#13
**Host**: Development on workstation, testing on gabby (BizzyBoat)
**Operator**: Roland + Claude Code Agent

## Context

Creating a new ROS 2 package for BizzyBoat (EchoBoat 240), following the
`izzyboat_project11` pattern. Sub-issues: URDF (#25), OAK camera static IPs
(CCOMJHC/ccomjhc_project11#9).

## Hardware Reference

- **Computer**: Neousys Nuvo 9160GC (gabby), Ubuntu 24.04 Server
- **GNSS**: CUAV C-RTK 2HP (MAVRos only, no PosMV)
- **Cameras**: 4× OAK-1 PoE (.217, .227, .238, .242 on 192.168.20.x) + 1× factory USB
- **Sonar**: 1× Imagenex DeltaT
- **Winch**: Arduino-controlled CTD winch (ttyACM2)
- **FCU**: CubeOrange ArduPilot (ttyACM0/ttyACM1)
- **Network**: See `docs/bizzyboat_network.md`

## Progress

### Step 1: Plan and open questions

Modeling after `izzyboat_project11`. Key differences:
- Namespace `bizzy`, frame prefix `bizzy/`
- No PosMV, no Norbit — MAVRos-only nav, DeltaT-only sonar
- 4× OAK PoE cameras instead of 1× OAK + 1× USB + JoLo
- FCU on ttyACM0 (CubeOrange) instead of ttyUSB0

**Open questions**:
1. EchoBoat 240 hull dimensions (length × width)? → deferred to URDF sub-issue #25
2. OAK camera mounting positions/names? → 90° apart on a mast: oak_forward, oak_starboard, oak_aft, oak_port
3. Startup script: source layered workspace (`site_ws/install/setup.bash`) instead of `jazzy_ws`? → yes, layered

**Issue comments (Roland, 2026-03-26)**:
- Manifest tasks (config/bootstrap.yaml, repos files) already completed in #15/#17
- Use modular launch files instead of one monolithic launch:
  **core** — FCU (mavros), URDF/TF, platform sender, UDP bridge, NTRIP
  **perception** — OAK cameras, DeltaT sonar, USB camera, rosbag loggers
  **nav** — mission manager / autonomy (from echoboat_project11:echo_launch.py)
- Rationale: restart components (e.g., nav stack) without restarting everything
- Filed [rolker/seafloor_echoboat_project11#5](https://github.com/rolker/seafloor_echoboat_project11/issues/5) to split `echo_launch.py` and update izzyboat later

### Step 2: Package created

Package builds successfully in `platforms_ws`.

**Files created**:
- `package.xml`, `CMakeLists.txt` — skeleton matching izzyboat pattern
- `config/platform.yaml` — placeholder dimensions for EchoBoat 240
- `config/bizzyboat.yaml` — UDP bridge (wifi+vpn), rosbag logging, MAVRos-only nav
- `config/oak_{forward,starboard,aft,port}.yaml` — per-camera configs with PoE IPs (placeholder assignment)
- `config/operator.yaml` — operator UDP bridge (gabby_bb/gabby_v hostnames)
- `launch/core_launch.py` — mavros, mru_transform, sea surface, UDP bridge, NTRIP, URDF
- `launch/perception_launch.py` — 4× OAK cameras, DeltaT + cube_bathymetry, USB cam, rosbag loggers
- `launch/nav_launch.py` — marine_autonomy, echo_helm, s57_grids, nav2
- `launch/oak_cameras_launch.py` — helper to launch all 4 OAK nodes
- `launch/publish_state_launch.py` — robot_state_publisher + joint_state_publisher
- `launch/ntrip_launch.py` — NTRIP client for RTK corrections
- `launch/operator_core_launch.py` — operator-side bridge + autonomy + foxglove
- `scripts/start_tmux_project11.bash` — tmux startup (3 panes: core, perception, nav)
- `urdf/bizzyboat.urdf.xacro` — modular xacro URDF with sensor frames (#25)

**Key design decisions**:
- Did not use `echo_launch.py` wholesale — pulled individual components into modular launches
- Startup script sources layered workspace (`site_ws/install/setup.bash`)
- OAK camera IPs assigned to names as placeholders — need to verify which IP is which camera on gabby

**Open**: Camera IP-to-position mapping, NTRIP credentials (reused izzyboat's for now)
