# BizzyBoat / hydrography roadmap

What we're aiming for, and what's deferred. Scope is BizzyBoat plus the
sensor payload (M3 sonar, SBG, SVS) bound for the June 2026 field
hydrography class.

This document is the **carry-over mechanism between deployments**.
Items here are durable direction; specific bounded work belongs in
GitHub task issues (referenced from here when relevant).

## End goal

**Fully autonomous survey round-trips.** Plan a survey from the
operator station; boat transits to the area, runs survey lines, returns
to the pier — all without user intervention.

## Forcing function

**Field hydrography class — June 2026.** Students plan surveys, monitor
execution, configure sonar software, and measure offsets. The system
must be reliable and novice-friendly by then.

## Active threads (have task issues)

Cross-references — the roadmap is not the source of truth for any
specific task; the linked issue is. Listed here so the threads are
visible from one place.

### Sensor payload integration (M3 + SBG + SVS on mercat)

- [`unh_echoboats_project11#76`](https://github.com/rolker/unh_echoboats_project11/issues/76) — mercat bring-up + data flow + NTRIP strategy + NTP
- [`unh_echoboats_project11#77`](https://github.com/rolker/unh_echoboats_project11/issues/77) — physical install, offsets, URDF, SVG diagram
- [`rolker/marine_tools#1`](https://github.com/rolker/marine_tools/issues/1) — QINSy → ROS bridge for coverage / sounding feedback

### Camera obstacle avoidance

- [`rolker/unh_marine_perception#6`](https://github.com/rolker/unh_marine_perception/issues/6) — `SeaSurfaceLayer::matchSize()` segfault (blocker)
- [`rolker/unh_marine_perception#7`](https://github.com/rolker/unh_marine_perception/issues/7) — end-to-end OAK→costmap validation (blocked on #6)

### Navigation reliability

- [`rolker/unh_marine_navigation#23`](https://github.com/rolker/unh_marine_navigation/issues/23) — TF extrapolation on multi-line survey goals

### Class-ready operator UI

- [`rolker/rqt_operator_tools#2`](https://github.com/rolker/rqt_operator_tools/issues/2) — operator logbook (Phase 1 landed, not field-tested)
- [`rolker/rqt_operator_tools#29`](https://github.com/rolker/rqt_operator_tools/issues/29) — pre-launch checklist (form factor TBD)
- [`unh_echoboats_project11#18`](https://github.com/rolker/unh_echoboats_project11/issues/18) — student-facing operating documentation

### FCU configuration

- [`unh_echoboats_project11#55`](https://github.com/rolker/unh_echoboats_project11/issues/55) — FCU battery params recalibration (field-gated, PR [#56](https://github.com/rolker/unh_echoboats_project11/pull/56) ready)

## Deferred / lower priority — no current issue

These items are explicitly not on deck. Promote to a task issue when
they become relevant.

### Navigation polish

- **Hover v5** (range-aware taper for faster excursion recovery) —
  v4 is sufficient for current use; revisit only if v4's behavior
  becomes a real ergonomics problem
- **Hover vectored-thrust parameter** — works well enough with v4 cliff

### Networking

- **DNS-over-HTTPS on RUTX11** — exploration item, not urgent
- **WiFi bridge: static routes → default gateway approach** — current
  static-route setup works; cleaner default-gateway redesign deferred
- **IzzyBoat WireGuard return path fix** — IzzyBoat is parked, fix
  this before next IzzyBoat deployment

### Testing

- **Formal WiFi range test** — 2026-04-21 field data shows graceful
  degradation well past the old "300 m limit" and range comparable to
  or better than 2025 IzzyBoat (see memory `project_wifi_range.md`).
  A dedicated controlled range test is out of class-prep scope.

### Hardware oddities

- **Forward USB camera** publishes a black image — root cause unknown,
  USB camera has not been needed for any field work. Revisit if it
  becomes load-bearing.

## What's not on this roadmap

- Specific bug fixes — those are task issues
- Specific deployments — those get their own deployment issues
- Anything that's on deck for the **next** deployment — that goes in
  the next deployment issue's body, not here

## How this roadmap stays useful

- At deployment start: planner reads this + open task issues → picks
  the next deployment's scope
- At deployment wrap-up: items that came up but aren't bounded enough
  for a task issue and aren't going to be done next time → land here
- Periodically: if "deferred" items have been sitting more than a
  couple of months without any pull toward them, they're probably
  dropped, not deferred. Edit them out.

This document was seeded from the milestone content of
[`unh_echoboats_project11#57`](https://github.com/rolker/unh_echoboats_project11/issues/57)
(BizzyBoat field ops umbrella) when that issue was closed in favor of
the per-deployment convention. See
[`unh_echoboats_project11#92`](https://github.com/rolker/unh_echoboats_project11/issues/92)
for the close-out rationale.
