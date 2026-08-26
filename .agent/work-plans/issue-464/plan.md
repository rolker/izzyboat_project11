# Plan: Record operator-side AIS on salmon

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/464
<!-- gh issue read is unavailable in this dispatch; URL constructed from the repo's origin remote + issue number. -->

## Context

`operator_core_launch.py` includes `ais_launch.py` (arg `ais`, default
`true`) outside the `GroupAction` that pushes `operator_namespace`, and
`ais_launch.py` itself pushes only the `ais` sub-namespace — so the running
chain (`nmea_relay → ais_parser → ais_contact_tracker`) publishes at the
**global** namespace: `/ais/nmea`, `/ais/messages`, `/ais/contacts`,
`/ais/atons`. `bag_recorder_operator_launch.py`'s `RECORD_TOPICS` (12
entries) records diagnostics, operator commands, udp_bridge stats, rosout,
TF, and sonar-waterfall contacts — no AIS. An operator session with AIS on
screen (via CAMP) today leaves nothing on disk to replay.

The operator (2026-08-26, in the issue's comment thread) settled the one
open question: record `/ais/contacts` and `/ais/nmea`; do not record
`/ais/messages` or `/ais/atons`.

## Approach

1. **Add two entries to `RECORD_TOPICS`** in `bag_recorder_operator_launch.py`
   — `/ais/nmea` and `/ais/contacts` — each with an inline rationale comment,
   matching the file's existing per-topic comment convention (e.g. the
   `/operator/sonar_waterfall/contacts` entry). Rationale to capture per
   topic:
   - `/ais/nmea`: raw `!AIVDM` sentences; smallest artifact, and the parser
     and tracker can be re-run against it offline if either changes later.
   - `/ais/contacts`: the tracked, per-MMSI `marine_ais_msgs/AISContact`
     product — what CAMP draws and what a replay drives directly without
     re-running the decode chain.
2. **No code change to the AIS chain** — `ais_launch.py`,
   `ais_contact_tracker.py`, and `operator_core_launch.py` are untouched
   (non-goal, confirmed by review-issue).
3. **No boat-side change** — the boat's own `/bizzy/ais/*` bag is a
   different receiver instance and out of scope (non-goal).

## Files to Change

| File | Change |
|------|--------|
| `bizzyboat_project11/launch/bag_recorder_operator_launch.py` | Add `/ais/nmea` and `/ais/contacts` to `RECORD_TOPICS`, each with a one/two-line rationale comment. |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| Human control and transparency | Makes a previously-silent operator feed replayable; no behavior change to the running system, only what lands on disk. |
| A change includes its consequences | Per-topic rationale comments are added inline (matching the file's existing convention) rather than left implicit, per the review-issue recommendation. |
| Only what's needed | Two topics, not all four — `/ais/messages` and `/ais/atons` are deliberately excluded as reconstructible from `/ais/nmea` and not needed for replay/CAMP respectively. |
| Test what breaks | No existing test infra covers `RECORD_TOPICS` contents (confirmed by review-issue grep); consistent with the rest of this launch file's recorders. Not adding one here — same precedent as issue #458. |
| Workspace vs. project separation | Change is entirely within the project repo (`unh_echoboats_project11`), which owns both the recorder and the AIS chain. |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| N/A | No | Review-issue found no workspace ADR triggered — a topic-list edit in an existing project launch file, no new package or launch-graph restructuring. |

## Consequences

| If we change... | Also update... | Included in plan? |
|---|---|---|
| `RECORD_TOPICS` in `bag_recorder_operator_launch.py` | Nothing else — the topics already exist and are documented at their source (`ais_launch.py`'s docstring, `config/ais.yaml`'s header); no new interface is introduced. | Yes (no-op: confirmed nothing further needed) |

## Documentation & Instruction Impact

- **Stale docs** (must land in this PR): None — the recorder file has no
  separate README/API doc describing its topic list; the file's own header
  docstring already describes what it records at a high level ("aggregated
  diagnostics... operator-originated commands... rosout, and TF") and will
  need a one-clause addition ("...and operator-side AIS traffic") so it
  stays accurate once AIS is added — included as part of the `RECORD_TOPICS`
  edit commit, same file.
- **Agent-instruction candidates** (proposals only — the operator decides,
  never auto-applied): None — this follows an existing, already-documented
  convention (per-topic rationale comments in `RECORD_TOPICS`) rather than
  introducing a new pattern worth generalizing.

## Open Questions

- [ ] No open questions — the operator's 2026-08-26 comment settled the
  raw-vs-tracked topic selection (`/ais/nmea` + `/ais/contacts`); plan is
  review-plan-ready.

## Estimated Scope

Single PR — one file, ~10 added lines (2 topic entries + comments + a
one-clause docstring update).
