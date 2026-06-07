# 2026-06-05 — salmon log (BizzyBoat outing, backfilled)

Host: salmon
Side: field (operator station)

> **Backfilled 2026-06-07 (echoboats#174).** No live agent log was written on
> this day. This record is reconstructed from the durable operator-log sidecar
> `~/data/logs/operator/2026-06-05/operator_log.jsonl` (Pilot entries). Times are
> EDT, converted from the entry `ts_ns`. Bags: operator `operator/2026-06-05/`
> (incl. screenshooter `operator_2026-06-05.mp4`, 333 frames).

## Timeline (operator notes)

**2026-06-05 11:32:04 EDT** — Pilot: "Boat is in the water."

**2026-06-05 12:57:14 EDT** — Pilot: "Twice I noticed the boat drift away from the
hover. I did not figure out why the first time, but the second time, I noticed
whitecaps were triggering the e stop making it drift." **Whitecaps are
false-triggering the collision-monitor e-stop**, dropping the hover and letting
the boat drift. Sea-surface perception **false positive** — the complementary
failure mode to the 2026-06-03 lobster-pot false *negative* (buoy absent from the
costmap; only the e-stop sensor caught it). Filed
[unh_marine_perception#31](https://github.com/rolker/unh_marine_perception/issues/31)
(cross-links perception#26; also flags the hover + reflex-e-stop interaction as a
nav-side question — a reflex stop during active hover drifts instead of
re-acquiring station).

**2026-06-05 13:33:04 EDT** — Pilot: "so, gabby's ethernet port did not activate
when the garmin was plugged into them, but mercat's did so going try testing via
mercat." **Garmin GCV-10 sidescan: gabby NIC did not link; mercat did** — testing
moved to mercat. gabby is the intended Linux/ROS host for the sidescan driver, so
this blocks the on-boat integration path. Likely a gabby-side NIC
config/negotiation/cabling issue, not a Garmin fault. Filed
[unh_echoboats_project11#229](https://github.com/rolker/unh_echoboats_project11/issues/229).

**2026-06-05 14:31:20 EDT** — Pilot: "camp locked up." CAMP **hang/lockup**
(distinct from the 2026-06-03 trackline-removal crash, camp#65, which
auto-respawned). Added as a dated occurrence to the intermittent-GUI-hang
investigation [camp#52](https://github.com/rolker/camp/issues/52) (see also
echoboats#166). No backtrace / Qt-heartbeat capture taken at the time.

**2026-06-05 14:46:35 EDT** — Pilot: "boat recovered." End of on-water ops.

## Issues encountered

- Whitecaps false-trigger the e-stop → hover drift → perception#31 (NEW).
- Garmin sidescan: gabby NIC no link → echoboats#229 (NEW).
- CAMP lockup → camp#52 / echoboats#166 (new occurrence; no capture).

## Carry-forward

- perception#31 is the highest-signal new finding — a sea-surface perception
  false-positive found on water and recorded nowhere but the bag. Pairs with the
  06-03 false-negative; both feed the pre-class shakedown (echoboats#228).
- The Garmin NIC blocker (echoboats#229) sits on the parallel sidescan driver
  effort, not the June survey path.
