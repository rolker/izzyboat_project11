# BizzyBoat Hardware Setup

Reference documentation for BizzyBoat (Seafloor Systems EchoBoat 240)
hardware configuration. Hull/geometry details are covered in the
companion doc [bizzyboat_reference_geometry.md](bizzyboat_reference_geometry.md).

Seed reference: the manufacturer manual lives outside this repo at
`~/bizzyboat/EchoBoat_240_Manual_V.pdf` on the development station.
Page numbers below refer to that PDF.

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
| Thrusters | 2× electric outdrives, directed-thrust (vectored) steering | 2× skid-steer |
| Batteries | 2× Torqeedo Power 24-3500 in parallel | 4× smaller packs (model not yet characterized) |
| Current sensor | None wired | None wired |

## Propulsion

- **Top speed**: 4 kn (2 m/s)
- **Survey speed**: 2 kn (1 m/s)
- **Steering**: directed thrust (vectored), not differential. The hover
  behavior must maintain non-zero forward speed during heading
  corrections to retain turning authority — see `hover.cpp` v3/v4
  patches (`unh_marine_navigation#14`, commits `ca0dc6f`, `cfd8560`).

## Batteries

**Pack**: 2× Torqeedo Power 24-3500 in parallel.

### Torqeedo Power 24-3500 spec (Manual §3.6.1, Table 6, p. 25)

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
| Storage range | 22.6 – 24.2 V (Manual §7.4.3, p. 81) |
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
  this boat those values are wrong because no sensor is connected.
  The ADC drifts around zero under all load conditions.
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
| `BATT_LOW_VOLT` | 0 | **22.5** | Above manufacturer storage floor 22.6 V |
| `BATT_CRT_VOLT` | 0 | **21.5** | Just above manufacturer minimum 21.0 V |

`BATT_FS_LOW_ACT` and `BATT_FS_CRT_ACT` remain `0` — autonomy decisions
are owned by the ROS stack, not the FCU. The low/critical thresholds
drive the `mavros: Battery` diagnostic and annunciator indicators
only.

### Voltage reference card

| State | Voltage |
|---|---:|
| Fully charged (rest) | 29.05 V |
| Nominal / rated | 25.64 V |
| Storage upper bound | 24.2 V |
| Storage lower bound | 22.6 V |
| **Low-battery warning (WARN)** | **22.5 V** |
| **Critical (ERROR)** | **21.5 V** |
| Manufacturer minimum (damage below) | 21.0 V |
| Hard protection shutoff | 12 V |

## Power Electronics

From the manual (§1.3 p. 3, §5 block diagram p. 107+):

- System bus: 24 VDC
- Shore power charge: 100–240 VAC / 50–60 Hz
- AC inverter on board (24 VDC → 120 VAC) for sonar PC and payload
- Main Power Button with LED ring indicator (flashing = battery error)
- Fuses: servo fuse panel (5 A starboard, 5 A port)

## Autonomy Interface

- FCU speaks MAVLink 2 via USB to the onboard PC (gabby).
- ROS 2 stack uses MAVROS and drives the FCU via **`cmd_vel`**
  (`/bizzy/mavros/setpoint_velocity/cmd_vel`). The ArduPilot mission
  system, global origin, and mission-mode features are **unused** —
  all planning, BT execution, and hover logic live in the ROS stack.
- Consequence: MAVROS warnings about missing global origin, mission,
  or mode failures are expected noise and should not be treated as
  issues.

## History

- 2026-03-27 — hardware inventory, side/internal photos captured
  (`~/bizzyboat/2026-03-27_BizzyBoat*.jpg`).
- 2026-03-30 — hull measurements (`~/bizzyboat/2026-03-30_measurements.jpg`).
- 2026-04-02 — GPS antenna offsets applied (see
  `bizzyboat_fcu_custom.param`).
- 2026-04-07 — IMU position offsets applied.
- 2026-04-16 — battery param divergence from actual hardware
  identified; Torqeedo Power 24-3500 values applied (this doc,
  issue #55).

## References

- Manufacturer manual: `~/bizzyboat/EchoBoat_240_Manual_V.pdf` (local)
- Hull geometry: [bizzyboat_reference_geometry.md](bizzyboat_reference_geometry.md)
- Network setup: [../../docs/bizzyboat_network.md](../../docs/bizzyboat_network.md)
- Deployment log: [../../docs/bizzyboat_deployment_log.md](../../docs/bizzyboat_deployment_log.md)
- IzzyBoat reference (do not assume parity): [../../docs/izzyboat_hardware.md](../../docs/izzyboat_hardware.md)
