# BizzyBoat Hardware Setup

Reference documentation for BizzyBoat (Seafloor Systems EchoBoat 240).

This doc catalogs **both** the factory kit and the project11 add-on
hardware. It replaces the hardware list in
[unh_echoboats_project11#8](https://github.com/rolker/unh_echoboats_project11/issues/8),
which asked for this information to be moved into a document.

Seed reference: the manufacturer manual lives outside this repo at
`~/bizzyboat/EchoBoat_240_Manual_V.pdf` on the development station.
Page numbers below refer to that PDF. The manual shows **all possible**
equipment for the EchoBoat 240 platform; not everything shown is
installed on BizzyBoat. Items not present on our boat are noted
explicitly.

Companion docs:
- [bizzyboat_reference_geometry.md](bizzyboat_reference_geometry.md) — URDF / hull geometry
- [../../docs/bizzyboat_network.md](../../docs/bizzyboat_network.md) — network architecture
- [../../docs/bizzyboat_deployment_log.md](../../docs/bizzyboat_deployment_log.md) — session-by-session log
- [../../docs/izzyboat_hardware.md](../../docs/izzyboat_hardware.md) — IzzyBoat reference (do not assume parity)

## Differences from IzzyBoat

BizzyBoat is **not** a mechanical clone of IzzyBoat. The two boats
are similar enough to invite copying config between them, but their
hulls, thrusters, and batteries differ. Verify against this doc
before assuming shared parameter values are correct.

| | BizzyBoat | IzzyBoat |
|---|---|---|
| Model | EchoBoat **240** | EchoBoat **160** |
| Length × width × draft | 2.4 m × 0.9 m × 0.3 m | smaller |
| Weight (base) | 158.75 kg (350 lb) | lighter |
| Payload | 90.7 kg (200 lb) | |
| Thrusters | 2× electric outdrives — directed-thrust (vectored) steering | 2× skid-steer |
| Batteries | 2× Torqeedo Power 24-3500 in parallel | 4× smaller packs (model not yet characterized) |
| Current sensor | None wired | None wired |

---

## Factory Hardware

All items in this section are as-delivered from Seafloor Systems.
Hull-overview figures (Figs 1–7, pp. 9–15) give at-a-glance layouts;
individual items below may also cite detail figures elsewhere in the
manual.

### Hull & Structure

- HDPE hull, 7.87 ft × 2.95 ft, 1 ft draft, 1.32 m air draft
- 316 stainless hardware
- Lifting point, drain plug, carry handles, bumper
- Main hatch, bow hatch, main switch panel
- Tower (mast)
- Tracking fins (bottom), fairing fin (stern)
- Custom trailer

### Propulsion

- 2× electric outdrive thrusters (Fig 1, 2)
- Directed-thrust (vectored) steering via 2× servos (5 A fused, Fig 54)
  — servos **replaced 2026-08-06** after both failed during the
  2026-08-03 Broadkill River deployment (operator reported difficulty
  steering plus a strange noise on the return leg). Between 2026-08-04
  and 2026-08-06 the servos were removed, both outdrives were fixed
  pointing aft and the boat ran **differentially (skid-steer)** on a
  temporary FCU/Nav2/helm envelope. That interval is closed: the FCU and
  all config are back to vectored thrust. Turning figures measured on the
  differential drivetrain do not describe the current vehicle — see
  `docs/bizzyboat_performance.md` §Turning.
- 2× ESCs (Electronic Speed Controllers, Fig 7)
- Capacitor Box, Fuse Box (Fig 7)

### Power

- **Batteries**: 2× **Torqeedo Power 24-3500** in parallel — full spec in the [Batteries](#batteries-detail) section below
- 24 VDC main bus
- AC Inverter (24 VDC → 120 VAC) for sonar PC and payload
- Main Power Button with LED ring indicator (flashing = battery error)
- Power 24-3500 Fast Charger (topside, 100–240 VAC)

### Navigation & Sensing (factory)

- **Primary / Secondary GPS Antenna mounting positions** (bow / stern) — factory mounting spots exist but **no factory antennas were provided**. Added GPS antennas are installed at these positions for a future sonar system (see [Added Hardware](#positioning)).
- **SmartCast** + **Winch** — lowerable sensor system for profiling
- **Arduino CTD winch controller** — part of the factory SmartCast system (VID:PID `2341:0043`, serial `342343139313512040B1`, USB `ttyACM2`)
- **USB Camera** (tower-mount, HD, VID:PID `32e4:9230`) — factory UVC camera; used as backup situational-awareness camera (intentionally uncalibrated, not logged to rosbag)

**Not installed on BizzyBoat** (shown in manual but absent from this hull):
- SVP (Sound Velocity Profiler — Fig 2; not provided)
- SVS (Sound Velocity Sensor — Fig 2; not provided)
- IMU (Fig 2 — optional add-on slot; not present)
- T50 SONAR (Receiver, Projector, Topside — Fig 2, 6; not present)
- LiDAR (tower-mount — Fig 1, 3; not present)
- Stereo Camera (tower-mount — Fig 1, 3; not present)
- CAA Topside (Collision Avoidance Assist — Fig 4, 6; optional add-on, not present)

### Factory Comms

- **MikroTik OmniTIK 5 ac** (`RBOmniTikG-5HacD`) — boat-side WiFi bridge radio. Factory-provided; reconfigured for project11 network (see [bizzyboat_network.md](../../docs/bizzyboat_network.md)). RouterOS 7.22, AP bridge mode, 5 GHz a/n/ac.
- Onboard Antenna (hull-top, for shoreside RC link)
- Receiver Box (houses RF link components)
- Shoreside Antenna + Shoreside PoE (topside kit)

### Factory Compute

- **AutoNav** box (Fig 4, 6) — Seafloor Systems' autopilot enclosure containing the **Cube Orange** FCU:
  - **Hex/ProfiCNC Cube Orange** running ArduPilot ArduRover
  - Serial number: `43001E000A51323237373236` (observed 2026-03-27)
  - VID:PID `2dae:1016`, USB `ttyACM0` / `ttyACM1`
  - Connection to gabby: USB, MAVLink 2, target system 1, component 1
  - Firmware updated to support the CUAV C-RTK 2HP GPS; existing factory params kept, selectively overridden as needed
  - Param baseline: `bizzyboat_project11/config/fcu/bizzyboat_fcu_baseline.param`
  - Overrides: `bizzyboat_project11/config/fcu/bizzyboat_fcu_custom.param`
- **PC** — Windows sonar PC (Fig 4, 6). Used for the factory hydrographic
  software. Separate from the project11 compute stack (gabby).

### RCU / Topside Kit

- Remote Control Unit (RCU): Taranis Q-X7 Access Transmitter — USB mini charging
- Long Range Module (for RCU)
- 2S LiPo battery + Cube Balance Charger
- Voltage Tester (LiPo cell check)
- AML3 Adapter (for connecting the AML probe to SmartCast)
- USB drive (Seafloor software/drivers/manual)
- Programming cables: ESC programming cable, DB9 null modem, DB9 gender changer, USB-to-serial adapter

---

## Added Hardware (project11 retrofit)

These items are not part of the stock EchoBoat 240 kit — they were
installed to integrate the boat with the project11 autonomy framework.
Seed list from
[unh_echoboats_project11#8](https://github.com/rolker/unh_echoboats_project11/issues/8),
expanded with items discovered during deployment (see
[bizzyboat_deployment_log.md](../../docs/bizzyboat_deployment_log.md)
entries from 2026-03-26 onward).

### Compute

| Item | Model | Role | Host name |
|---|---|---|---|
| Onboard Linux PC | **Neousys Nuvo-9160GC** (Intel Core i7-14700, 32 GB RAM) | ROS 2 autonomy compute | `gabby` |

Mounted in one of the two finned enclosures in the electronics bay
(right-hand side; left-hand finned enclosure is the factory Windows
sonar PC).

### Positioning

| Item | Model | Role |
|---|---|---|
| Dual-antenna GNSS / heading module | **CUAV C-RTK 2HP** | Centimeter-level RTK position + moving-baseline heading |
| GPS antennas (for C-RTK 2HP) | *(model TBD)* × 2 | Mounted at non-factory positions (not the bow/stern factory antenna spots) |
| GPS antennas (for future sonar) | *(model TBD)* × 2 | Mounted at the factory Primary/Secondary antenna positions (bow/stern); not yet connected to any active system |

- C-RTK 2HP connected to the FCU via CAN (GPS node ID 124)
- Antenna offsets set in `bizzyboat_fcu_custom.param` (2026-04-02):
  forward antenna `GPS_POS1 = (+0.835, 0, -0.890)`, aft antenna
  `GPS_POS2 = (-0.835, 0, -0.890)`
- Moving-baseline: `GPS_MB1_TYPE=1`, `GPS_MB1_OFS = (+1.670, 0, 0)`

### Perception

| Item | Model | Count | Network location |
|---|---|---|---|
| Depth / RGB cameras | Luxonis **OAK-D** (PoE) | 4 | `192.168.20.9` – `192.168.20.12` |

DHCP reservations tracked in
[CCOMJHC/ccomjhc_project11#9](https://github.com/CCOMJHC/ccomjhc_project11/issues/9).
Driver: `depthai_marine` from the sensors layer
([unh_echoboats_project11#23](https://github.com/rolker/unh_echoboats_project11/issues/23)).

### Sonar & Sound Velocity

| Item | Model | Status |
|---|---|---|
| Multibeam sonar | Imagenex **DeltaT** | Physically installed on hull; ROS driver **not yet integrated**. Topic `/bizzy/sensors/deltat/soundings` is advertised but publishes zero messages as of 2026-04-16. Driver tracked in [unh_marine_autonomy#111](https://github.com/rolker/unh_marine_autonomy/issues/111). |
| Sidescan sonar | Garmin **GCV-20** sonar module + **GT34UHD-TM** transducer | 16-bit. SideVü ~1120 kHz (0.44° × 55°); ClearVü ~820 kHz (0.74° × 46°) — full −3 dB beamwidths. Lives on the Garmin Marine Network (reachable from mercat only); imagery reaches gabby via the mercat proxy (see [bizzyboat_network.md](../../docs/bizzyboat_network.md)). ROS driver: `garmin_sidescan` in `marine_tools`. |
| Sound velocity probe | **AML** (model *TODO: confirm*) | Attached to the factory SmartCast winch |

### Time Synchronization

| Item | Model | Role | Network location |
|---|---|---|---|
| GPS NTP appliance | **Time Machines TM2000B** | Stratum-1 time source for all boat and operator compute | `time.bizzy.p11.lan` (192.168.20.123) |

- MAC: `d4:e9:5e:06:15:63`
- Requires 3D GPS fix before serving NTP
- Feeds NTP hierarchy: TM2000B (s1) → boat router (s2) → LAN clients / operator router
- Full NTP architecture documented in `docs/bizzyboat_ntp_investigation_2026-04-09.md`

### Network

Portable rack (black frame, see `~/bizzyboat/2026-03-27_BizzyBoat*.jpg`):

| Item | Model | Role |
|---|---|---|
| Cellular / WiFi router | **Teltonika RUTX11** (RUTX11100400) | Boat-side router: LTE backhaul, Starlink WAN aggregation, LAN |
| PoE switches | **Trendnet TI-PG80B** × 2 | PoE power/data for OAK cameras + MikroTik |
| Satellite uplink | **Starlink Mini** | WAN failover via Teltonika WAN1 |

Note: the **MikroTik OmniTIK 5 ac** WiFi bridge radio is factory-provided
(see [Factory Comms](#factory-comms) above), though it was reconfigured for
the project11 network.

Diagnostics monitors for these publish under
`Teltonika: router.bizzy:*`, `MikroTik: wifi.bizzy:*`, and
`Starlink: starlink.bizzy:*` on `/diagnostics`.

### Udev / Device Rules

Rules for USB devices (Cube Orange, Arduino, USB camera) live in
`bizzyboat_project11/config/udev/`
([unh_echoboats_project11#26](https://github.com/rolker/unh_echoboats_project11/issues/26)).

---

## Batteries (detail)

Pack: 2× **Torqeedo Power 24-3500** in parallel (factory).

### Spec (Manual §3.6.1, Table 6, p. 25)

| Property | Value |
|---|---|
| Rated voltage | 25.64 V |
| Final charging voltage (full) | 29.05 V |
| Final discharging voltage (mfr minimum) | 21.00 V |
| Max voltage at terminals | 29.05 V |
| Max discharge current | 180 A per pack (360 A combined) |
| Usable energy | 3500 Wh per pack (7000 Wh combined) |
| Shutdown (hard protection) | 12 V |
| IP rating | IP67 |
| Storage range | 22.6 – 24.2 V (Manual §7.2, p. 76) |
| Operating ambient | -22 °F to +131 °F (-30 °C to +55 °C) |
| Charging ambient | 32 °F to +113 °F (0 °C to +45 °C) |
| Declared endurance | 9 h at survey speed, 1 m/s (Manual §1.3, p. 3) |

Combined nominal capacity:

    7000 Wh / 25.64 V ≈ 273 Ah ≈ 273 000 mAh

### Telemetry

- **Voltage** is wired to the Cube analog input (pin 14,
  `BATT_VOLT_PIN=14`) via a divider with `BATT_VOLT_MULT=12.02`.
  Voltage reads correctly per 2026-04-16 field-test data.
- **Current sensor**: **none wired.** The Torqeedo packs include an
  internal BMS but it uses a proprietary bus with no accessible
  CAN/J1939 output. The factory baseline
  (`bizzyboat_fcu_baseline.param`) ships with `BATT_MONITOR=4` and
  `BATT_CURR_PIN=15` set as if an analog current sensor existed; on
  this boat no sensor is connected and the ADC drifts around zero
  under all load conditions.
- Consequence: `sensor_msgs/BatteryState.percentage` cannot be
  integrated from consumed mAh and was observed frozen at 0.99 across
  4.5 h of thruster activity on 2026-04-16.

### FCU parameter overrides

Applied via `bizzyboat_project11/config/fcu/bizzyboat_fcu_custom.param`
(issue #55):

| Param | Baseline | Custom | Reason |
|---|---:|---:|---|
| `BATT_MONITOR` | 4 | **3** | Voltage only — no current sensor |
| `BATT_CAPACITY` | 16000 | **273000** | Document true pack capacity |
| `BATT_CURR_PIN` | 15 | **-1** | Disable unconnected ADC |
| `BATT_LOW_VOLT` | 0 | **23.0** | Head-home buffer above storage floor 22.6 V |
| `BATT_CRT_VOLT` | 0 | **21.5** | Just above manufacturer minimum 21.0 V |

`BATT_FS_LOW_ACT` and `BATT_FS_CRT_ACT` remain `0` — autonomy decisions
are owned by the ROS stack, not the FCU. The low/critical thresholds
drive the `mavros: Battery` diagnostic and annunciator indicators only.

### Voltage reference card

| State | Voltage |
|---|---:|
| Fully charged (rest) | 29.05 V |
| Nominal / rated | 25.64 V |
| Storage upper bound | 24.2 V |
| Storage lower bound | 22.6 V |
| **Low-battery warning (WARN)** | **23.0 V** |
| **Critical (ERROR)** | **21.5 V** |
| Manufacturer minimum (damage below) | 21.0 V |
| Hard protection shutoff | 12 V |

---

## Measured Performance

Speed and acceleration measured from logged-bag analysis across 7 in-water
deployments (2026-04-24 → 2026-05-22), current-corrected to
speed-through-water (STW). Full method, per-deployment data, and
reproducible scripts:
[`../../docs/bizzyboat_performance.md`](../../docs/bizzyboat_performance.md)
and [`../../docs/analysis/dynamics/`](../../docs/analysis/dynamics/)
([#124](https://github.com/rolker/unh_echoboats_project11/issues/124) §2).

| Metric | Value | Notes |
|---|---|---|
| Max forward speed | ~1.9 m/s (3.7 kt) STW | full throttle (ESC PWM 2000) |
| Cruise speed | ~1.52 m/s (3.0 kt) STW | PWM 1750–1850; well-determined |
| Hard-launch acceleration | ~0.6 m/s² peak, τ ≈ 2.5 s | idle → full |
| Coast-down deceleration | ~0.15 m/s² (up to ~0.25), τ ≈ 9–10 s | passive; ~10–15 m to stop from cruise |
| Max reverse speed | ~1.4 m/s (2.7 kt) peak, provisional | sustained reverse under-sampled — see [#88](https://github.com/rolker/unh_echoboats_project11/issues/88) |
| Yaw-rate cap (autonomy) | 1.0 rad/s (`helm_manager.max_yaw_speed`) | raised from 0.5 to the helm default = vehicle-capability backstop; ~0.9 rad/s pivot at full throttle; sustained cruise turn unvalidated |
| Min turn radius @ cruise | ~1.5 m at the 1.0 cap | set by the yaw clamp; <1 m pivot at low speed |
| Course-keeping (track-holding) | ~0.13 m RMS on straight legs | decimeter-scale; XTE vs commanded line ~0.5 m. Not survey-limiting |

- All speeds are **speed-through-water** (tidal current removed); observed
  speed-over-ground varies with current and heading.
- Cruise (~1.5 m/s) sits comfortably above the manufacturer's declared
  survey speed of 1 m/s (Batteries §, *Declared endurance*).
- Reverse speed and deceleration / crash-stop braking distance are
  provisional pending the controlled field experiment in
  [#88](https://github.com/rolker/unh_echoboats_project11/issues/88).

---

## Autonomy Interface

- FCU speaks MAVLink 2 via USB to the onboard PC (gabby).
- ROS 2 stack uses MAVROS and drives the FCU via **`cmd_vel`**
  (`/bizzy/mavros/setpoint_velocity/cmd_vel`). The ArduPilot mission
  system, global origin, and mission-mode features are **unused** —
  all planning, BT execution, and hover logic live in the ROS stack.
- Consequence: MAVROS warnings about missing global origin, mission,
  or mode failures are expected noise and should not be treated as
  issues.

---

## History

- 2026-03-18 — Hardware seed list opened as [issue #8](https://github.com/rolker/unh_echoboats_project11/issues/8)
- 2026-03-27 — USB hardware enumeration on gabby (Cube, Arduino, USB camera); portable rack + finned enclosures photographed (`~/bizzyboat/2026-03-27_BizzyBoat*.jpg`)
- 2026-03-30 — hull measurements (`~/bizzyboat/2026-03-30_measurements.jpg`); DHCP reservations for 4× OAK cameras verified
- 2026-04-02 — GPS antenna offsets applied (`bizzyboat_fcu_custom.param`)
- 2026-04-07 — IMU position offsets applied
- 2026-04-16 — battery param divergence from actual hardware identified; Torqeedo Power 24-3500 values applied (this doc, [issue #55](https://github.com/rolker/unh_echoboats_project11/issues/55))

## References

- Manufacturer manual: `~/bizzyboat/EchoBoat_240_Manual_V.pdf` (local)
- Deployment log: [../../docs/bizzyboat_deployment_log.md](../../docs/bizzyboat_deployment_log.md)
- Network setup: [../../docs/bizzyboat_network.md](../../docs/bizzyboat_network.md)
- Hull geometry: [bizzyboat_reference_geometry.md](bizzyboat_reference_geometry.md)
- IzzyBoat reference (do not assume parity): [../../docs/izzyboat_hardware.md](../../docs/izzyboat_hardware.md)
- Parent setup issue: [rolker/unh_echoboats_project11#5](https://github.com/rolker/unh_echoboats_project11/issues/5)
- Hardware seed list: [rolker/unh_echoboats_project11#8](https://github.com/rolker/unh_echoboats_project11/issues/8)
