# BizzyBoat Hydro Payload Install Log

Detailed running log for M3 / SBG / SVS install and bring-up on mercat.
Summaries land in [`bizzyboat_deployment_log.md`](../../docs/bizzyboat_deployment_log.md)
(issue [#57](https://github.com/rolker/unh_echoboats_project11/issues/57)).

Tracking:
- [#76](https://github.com/rolker/unh_echoboats_project11/issues/76) — mercat bring-up and data flow
- [#77](https://github.com/rolker/unh_echoboats_project11/issues/77) — physical install, offsets, URDF, SVG diagram
- [rolker/marine_tools#1](https://github.com/rolker/marine_tools/issues/1) — QINSy → ROS bridge (peer/downstream)

Photos are kept locally on the operator workstation (not committed).
Measurements and observations extracted from them are recorded here.

## Hardware inventory

| Device | Model | Serial | Link | mercat port | Status |
|---|---|---|---|---|---|
| Kongsberg M3 sonar head | M3 | TBD | Ethernet (direct to mercat, isolated) | n/a | Installed |
| Kongsberg M3 topside unit | TBD | TBD | Ethernet | n/a | Installed |
| SBG GPS/IMU | TBD (Ellipse family) | TBD | Serial | TBD | Installed |
| Sound speed sensor | TBD (AML suspected) | TBD | Serial | TBD | Installed |

## Install photo index (local-only)

| Date | Subject | Tape measure visible? | Notes |
|---|---|---|---|

## Measurement log

### 2026-04-22

- **SBG survey GPS antenna baseline**: 2.05 m (tape measure, with measuring
  tape visible in photos). Wider than Cube GPS baseline of 1.67 m (y=±0.835).
  SBG antennas mounted at the existing EchoBoat survey antenna positions —
  separate from the antennas feeding the Cube autopilot.

## To refine from vendor manuals

- [ ] SBG IMU body-frame origin vs. case mechanical reference
- [ ] SBG antenna phase center vs. mount reference
- [ ] M3 transducer acoustic center vs. housing reference
- [ ] M3 mounting angle convention per vendor
- [ ] SVS sampling point vs. housing reference

## Open questions / investigations

- SVS model — pending verification from serial stream (suspected AML)
- NTRIP path for SBG — independent MACORS client, shared corrections from
  Cube chain, or routed via mercat? Tracked in
  [#76](https://github.com/rolker/unh_echoboats_project11/issues/76)
- mercat NTP — still not configured; blocking accurate timestamps for
  QINSy logging and sensor fusion
