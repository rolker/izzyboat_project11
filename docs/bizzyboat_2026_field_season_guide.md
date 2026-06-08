# 2026 BizzyBoat Field Season Guide — Borrowed Hydro Payload *(draft)*

> ⚠️ **Draft — corrections welcome.** This is a first draft from the 2026 field
> setup; some details (offsets, wiring specifics, commands) may be approximate,
> incomplete, or out of date. If you hit something incorrect, unclear, or missing,
> **open an issue** in `unh_echoboats_project11` (label `documentation`) describing
> what you saw. Field corrections are how this becomes trustworthy.

This guide documents the **borrowed hydrographic payload** carried on BizzyBoat
for the Summer Hydro 2026 class — the **M3 multibeam sonar** and the **SBG
Ellipse-D INS** — and, most importantly, **how they are wired into the boat**.

It is the companion to the [BizzyBoat Operator Manual](bizzyboat_operator_manual.md):
the operator manual covers how to *run the boat*; this guide covers the
*temporary survey kit bolted on for this season*.

> **Why a separate, season-scoped guide?** The M3 and SBG are **class-loaner
> hardware** — they go back at the end of the season, and the boat reverts to
> its base configuration (nav from the FCU + dual GNSS antennas via mavros).
> Their topics (`/bizzy/sensors/sbg/...`, the sound-speed feed) will not be in
> the bag afterward. Keeping them in a dated field-season guide — instead of the
> permanent operator manual or framework guide — means nothing in the durable
> docs goes stale the day the loaners leave.

Everything below is grounded in the boat's launch files and config
(`bizzyboat_project11/launch/*.py`, `config/sbg_ellipse_d*.yaml`) and the
[hydro payload install log](../bizzyboat_project11/docs/hydro_payload_install_log.md).
**All mounting offsets are approximate** — derived from tape measurements and
photos during install — and are flagged as such throughout. **Refining them is
a Summer Hydro class task** (see [Offsets](#6-offsets--approximate-refine-this-season)).

---

## 1. The payload at a glance

| Sensor | Model | What it does | Lives on | Host link |
|--------|-------|--------------|----------|-----------|
| **SBG Ellipse-D** | Ellipse-D-G4A2-B1 (SN 000034256) | Dual-antenna INS — position, attitude, heading, heave | Inside hull, on a plate | gabby serial (ROS) + mercat (QINSy) |
| **M3 multibeam** | Kongsberg M3 | Survey multibeam sonar | Through-hull, under the boat | mercat (QINSy / acquisition) |
| **AML SVS** | AML (SN 11357) | Sound-velocity probe (feeds the M3) | Through-hull, alongside the M3 | gabby serial (ROS bridge) |

The **SBG** and **M3** are the borrowed instruments. The **AML sound-velocity
sensor** is part of the same hydro install; its *device* details live in the
operator manual, but the **path by which its data reaches the M3** is documented
here because it's part of how the payload is integrated.

Two computers are involved (see the operator manual for the full host map):

- **gabby** — the boat's Linux/ROS computer. Hosts the serial bridges that wire
  the payload into the autonomy stack and forward data to mercat.
- **mercat** — the boat's Windows computer running **QINSy** for survey
  acquisition. Receives nav from the SBG and drives the M3.

---

## 2. Serial / port allocation on gabby

The payload uses gabby's four native MezIO rear-panel RS-232 ports. Current
allocation (from the launch files):

| Port | Device | Direction | Used by |
|------|--------|-----------|---------|
| `/dev/ttyS0` | **AML SVS** | RX-only | `sound_speed_launch.py` |
| `/dev/ttyS1` | **SBG Ellipse-D** (PORT_E) | bidirectional | `sbg_launch.py` |
| `/dev/ttyS2` | **ZDA out → M3** | TX-only | `zda_launch.py` |

> **Why these assignments?** The AML probe is RX-only (it just emits
> sound-velocity sentences), so it tolerates `ttyS0` even though that path has a
> known **TX-side fault** (not fully isolated — gabby's line driver vs. the old
> SBG cable). The SBG needs bidirectional comms (it both emits data and accepts
> RTCM corrections on the same line), so it owns the healthy `ttyS1`. See the
> [install log](../bizzyboat_project11/docs/hydro_payload_install_log.md) for the
> diagnosis. (`ttyS0` also has an open data-integrity issue — see
> [Known issues](#7-known-issues--open-tickets).)

All three bridges are brought up automatically by `core_launch.py` on gabby; you
do not start them by hand during normal operation.

---

## 3. SBG Ellipse-D integration

### 3.1 Role

The Ellipse-D is a **dual-antenna inertial navigation system**. On BizzyBoat
this season it provides:

- A high-rate attitude + heave solution to **QINSy** on mercat (the survey
  side), and
- A parallel nav stream into ROS (`/bizzy/sensors/sbg/...`) used for
  cross-checking against the FCU's own GNSS/INS solution.

It is **supplementary**, not the boat's primary nav source — autonomy still runs
off the FCU via mavros. Treat SBG topics as available *only this season*.

### 3.2 ROS launch and topics

`sbg_launch.py` runs the stock `sbg_driver` under the `bizzy/sensors` namespace,
so its outputs land at `/bizzy/sensors/sbg/<name>` (e.g. `.../imu_data`,
`.../ekf_nav`, `.../ekf_quat`, `.../utc_time`, `.../gps1_hdt`).

Key config (`config/sbg_ellipse_d.yaml`):

- **`confWithRos: false`** — the driver runs **read-only**. It does **not** push
  settings to the device. **sbgCenter (on mercat) is the configuration
  authority.** Output messages on PORT_E must be enabled in sbgCenter before the
  ROS driver will see anything.
- Serial: `portName: /dev/ttyS1`, `portID: 4` (PORT_E), `115200` baud.
- `use_enu: false` — output is **NED** (matches QINSy and the FCU).

> A checked-in *configuration push* template exists at
> `config/sbg_ellipse_d_configure.yaml` (`confWithRos: true`) for the case where
> you want to write the device flash from version control instead of sbgCenter.
> It **writes to device flash** and requires a temporary rewire to PORT_A — read
> its header before running. Not loaded by the production launch.

### 3.3 RTK aiding — how NTRIP reaches the SBG

The boat makes **one** NTRIP caster connection and uses it to correct **both**
the FCU and the SBG. There is no second NTRIP client for the SBG.

```
                          ccomjhc_project11/configuration/bizzyboat_ntrip.yaml
                                          │ (caster credentials + mountpoint)
                                          ▼
   GGA (1 Hz, throttled) ───►  ntrip_client  (ntrip_launch.py, /bizzy/sensors/ntrip)
                                          │ mavros_msgs/RTCM
                                          ▼
                          /bizzy/mavros/gps_rtk/send_rtcm  ──►  FCU (Cube Orange, mavros gps_rtk)
                                          │
                                          │  rtcm_relay_node.py  (copies + retypes:
                                          │  mavros_msgs/RTCM → rtcm_msgs/Message)
                                          ▼
                              /bizzy/sensors/rtcm  ──►  SBG driver (remap ntrip_client/rtcm → rtcm)
                                                              │ over ttyS1 / PORT_E
                                                              ▼
                                                        SBG accepts RTCM ("Forward
                                                        Corrections" on PORT_E)
```

Details, grounded in the launch files:

- **`ntrip_launch.py`** starts `ntrip_client`, which publishes
  `mavros_msgs/RTCM`; a `SetRemap` sends it to
  `/bizzy/mavros/gps_rtk/send_rtcm`, feeding the FCU directly. The same launch
  throttles mavros' `~10 Hz` fix down to **1 Hz** on `.../sensors/ntrip/fix` for
  the GGA echoback that network/VRS mountpoints require.
- **`rtcm_relay_node.py`** subscribes to that same FCU RTCM stream and
  re-publishes each message as `rtcm_msgs/Message` on `/bizzy/sensors/rtcm` —
  same RTCM3 payload, the package/field name the SBG driver expects.
- **`sbg_launch.py`** remaps the driver's `ntrip_client/rtcm` subscription to
  `rtcm`, so the relay and the driver meet at `/bizzy/sensors/rtcm`. On the
  device side, PORT_E is configured (in sbgCenter) to accept RTCM in on the same
  RS-232 line it emits data on.

The net effect: plug in NTRIP once and both receivers go RTK-corrected.

### 3.4 Mounting geometry and lever arms — *approximate*

Measured/derived during the 2026-04-22 install. **All values approximate; refine
this season.** Vessel frame is REP-103 (x-forward, y-port, z-up); SBG body frame
is FRD (x-forward, y-right, z-down), reconciled by a 180° roll.

| Quantity | Approx. value | Status |
|----------|--------------|--------|
| SBG case back face (connector side) | x ≈ -0.60 m | tape [MEAS] |
| SBG case bottom | z ≈ +0.005 m | [MEAS] |
| SBG y | 0.00 m (centerline, assumed) | [EST] |
| Body rotation (vessel → SBG) | rpy = (π, 0, 0) | [MEAS] from axis triad |
| IMU lever arm from vehicle origin (FRD) | (−0.577, 0.000, −0.029) m | applied in sbgCenter |
| ANT1 (primary, **aft**) lever from IMU | (−0.488, 0.000, −0.881) m | applied |
| ANT2 (secondary, **fwd**) lever from IMU | (+1.567, 0.000, −0.881) m | applied |
| Dual-antenna baseline | ≈ 2.055 m (tape ≈ 2.05 m) | [MEAS] derived |
| Motion profile | Marine | configured |

The dual GNSS antennas are **Trimble GNSS/MSK** pucks on the center rail:
forward ≈ x +0.990 m, aft ≈ x −1.065 m (both y = 0). `ANT1 = aft`, `ANT2 = fwd`
was confirmed by the heading matching the FCU solution. Antenna **z** values
still inherit the rail-top z ≈ 0.89 m `[EST]` anchor and a puck phase-center
offset — a prime refinement target.

> The IMU lever arm and antenna lever arms above are the values applied in
> sbgCenter. They can be refined without redoing the whole config — the
> dominant errors shift the IMU origin by a few mm and the antenna z by 5–10 cm.

---

## 4. M3 multibeam integration

### 4.1 Role

The M3 is the survey multibeam, acquired through **QINSy on mercat**. The boat
side (gabby/ROS) does not process M3 pings; its job is to **feed the M3 two
things it needs** — sound velocity and time — and to deliver SBG nav to QINSy.

### 4.2 What the M3 needs, and how the boat provides it

```
   AML SVS (gabby ttyS0, RX) ─► sound_speed_bridge ─┬─► /bizzy/sensors/sound_speed/*  (ROS)
                                                     └─► Valeport-format UDP ─► mercat:20003  (M3)

   SBG SbgUtcTime ─► zda_serial_bridge ─► $GPZDA on gabby ttyS2 ─► M3 serial input  (time)

   SBG nav/attitude ─► QINSy (mercat) ─► drives + georeferences the M3
```

**Sound velocity → M3** (`sound_speed_launch.py`):

- The AML probe on gabby `ttyS0` is read by `sound_speed_bridge` (from
  `rolker/marine_tools`). It parses the AML `$AML,SVM,<value>` sentence and
  publishes ROS topics under `/bizzy/sensors/sound_speed/` (`sound_speed`,
  `temperature`, `fluid_pressure`).
- The same node fans out a **Valeport-format UDP** copy to **`mercat:20003`**,
  where the M3's built-in Valeport listener consumes it. This replaced an
  interim PowerShell stand-in (`aml_bridge.ps1`).

**Time → M3** (`zda_launch.py`):

- `zda_serial_bridge` (also from `rolker/marine_tools`) subscribes to the SBG's
  `/bizzy/sensors/sbg/utc_time` and emits NMEA **`$GPZDA`** on gabby `ttyS2` into
  the M3's serial input.
- Output is **gated on the SBG's UTC status** (`min_utc_status: 2` = UTC valid +
  leap-second almanac downloaded) so the M3 never receives a wrong wall-clock
  during cold start.

**Nav → QINSy**: the SBG feeds QINSy its position/attitude/heave on mercat
(configured in sbgCenter / QINSy, not in ROS). M3 pings are georeferenced there.
See the install log for the QINSy-side I/O setup.

### 4.3 Mounting geometry — *approximate*

The M3 is a **through-hull mount occupying the same cavity** the Imagenex DeltaT
sonar previously used, so its fore-aft position is inherited from that entry.
**Approximate; refine this season.**

| Quantity | Approx. value | Status |
|----------|--------------|--------|
| M3 x (fore-aft) | -0.23 m | inherited from DeltaT cavity [MEAS] rough |
| M3 y | 0.00 m (centerline) | [EST] — confirm by tape |
| M3 z (transducer face) | -0.145 m | [MEAS]-derived via z_rail = 0.89 [EST] |
| M3 orientation | transducer face straight down | [EST] — check for vendor axis triad |

> These are the same values to enter as the M3 **mounting offsets in QINSy**
> (x = -0.23, y = 0, z = -0.145, face Down). Do **not** also duplicate them in
> the M3 software's Deployment dialog. The z value inherits the rail-top z = 0.89
> m `[EST]` anchor — when that's refined, M3 z updates in step.

The AML sound-velocity probe sits alongside the M3 (sensing tip ≈ x -0.455,
y +0.25, z -0.055 m — approximate). The full sensor offset picture, including the
hull/antenna geometry, is in
[`bizzyboat_reference_geometry.md`](../bizzyboat_project11/docs/bizzyboat_reference_geometry.md)
and the
[offsets diagram](../bizzyboat_project11/docs/bizzyboat_offsets.svg).

---

## 5. End-to-end data flow

```
                        ┌─────────────────────── gabby (Linux / ROS) ───────────────────────┐
   NTRIP caster ──────► │  ntrip_client ──► FCU (gps_rtk)                                     │
   (bizzyboat_ntrip.yaml)│        └► rtcm_relay ──► SBG (RTK in, ttyS1/PORT_E)               │
                        │                                                                    │
   AML SVS (ttyS0) ───► │  sound_speed_bridge ──► Valeport UDP ─────────────┐                │
   SBG (ttyS1/PORT_E) ─►│  zda_serial_bridge ──► $GPZDA (ttyS2) ───────────┐│                │
                        └──────────────────────────────────────────────────┼┼────────────────┘
                                                                            ▼▼
                                                        ┌──── mercat (Windows / QINSy) ────┐
                                                        │  M3 multibeam:                    │
                                                        │   • Valeport SV  ◄ UDP :20003     │
                                                        │   • $GPZDA time  ◄ serial         │
                                                        │   • nav/attitude ◄ SBG (sbgCenter)│
                                                        │  → QINSy acquisition + georef     │
                                                        └───────────────────────────────────┘
```

---

## 6. Offsets — approximate, refine this season

Every mounting offset in this guide is a **rough field measurement** from the
2026-04-22 install. They are good enough to acquire data, but the Summer Hydro
class should **verify and refine them** as a calibration exercise. Highest-value
refinements:

1. **Rail-top z anchor (0.89 m `[EST]`)** — most z values (M3 face, antennas,
   AML tip) are derived from it. Pin it down and everything downstream tightens.
2. **M3 transducer-face depth and orientation** — measure hull-floor-to-face;
   confirm strictly downward (no forward tilt) and check for a vendor axis triad.
3. **GNSS antenna phase-center heights** — once the exact Trimble model is
   identified, add the phase-center offset above the mount base.
4. **Centerline (y = 0) assumptions** — independently tape-verify y for the M3,
   the AML tip, and both Trimble pucks.
5. **SBG IMU sensing-element offset** — from the Ellipse-D datasheet, relative to
   the measured case back face (x ≈ -0.60).

When a measurement is updated, regenerate the offsets diagram:
`python3 bizzyboat_project11/docs/bizzyboat_offsets_gen.py`.

---

## 7. Known issues / open tickets

This payload is freshly integrated; a few items are still open. Check these
before drawing conclusions about bad data:

- [#163](https://github.com/rolker/unh_echoboats_project11/issues/163) — AML SVS:
  the all-NUL-bytes regression on `/dev/ttyS0` was **resolved** (#173, 2026-05-26 —
  the probe now delivers valid in-water sound speed, ~99% valid). Kept open as a
  **watch item** for occasional brief zero-dropouts at startup. The SV feed works.
- [#137](https://github.com/rolker/unh_echoboats_project11/issues/137) — M3
  intermittent missing pings (suspected ping-rate × depth correlation).
- [#156](https://github.com/rolker/unh_echoboats_project11/issues/156) /
  [#117](https://github.com/rolker/unh_echoboats_project11/issues/117) — SBG vs
  CUAV ellipsoidal-Z disagreement; `ros_standard` topic behavior.
- [#76](https://github.com/rolker/unh_echoboats_project11/issues/76),
  [#77](https://github.com/rolker/unh_echoboats_project11/issues/77),
  [#155](https://github.com/rolker/unh_echoboats_project11/issues/155) — payload
  bring-up, physical install/offsets, and URDF consolidation.

---

## See also

- [BizzyBoat Operator Manual](bizzyboat_operator_manual.md) — running the boat;
  **the home for the AML sound-velocity *device* details and the NTP / time-sync
  architecture** (this guide only covers the *forwarding paths* into the M3).
- [Hydro payload install log](../bizzyboat_project11/docs/hydro_payload_install_log.md)
  — the running measurement + bring-up record this guide summarizes.
- [Reference geometry](../bizzyboat_project11/docs/bizzyboat_reference_geometry.md)
  and [offsets diagram](../bizzyboat_project11/docs/bizzyboat_offsets.svg) — the
  full hull/sensor offset picture.
- **Marine-autonomy framework guide** (`unh_marine_autonomy`,
  `docs/how_the_stack_works.md`) — how the autonomy stack itself works.

---

*Season-scoped: this guide describes the **2026** loaner payload. When the M3 and
SBG return, archive (don't silently delete) this document and confirm the durable
docs no longer reference the borrowed topics.*
