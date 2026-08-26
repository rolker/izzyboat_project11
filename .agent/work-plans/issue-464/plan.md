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
`/ais/atons`. `bag_recorder_operator_launch.py`'s `RECORD_TOPICS` (11
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
   **Provenance of the topic selection**: the operator's decision is
   [unh_echoboats_project11#464 comment 5420582779](https://github.com/rolker/unh_echoboats_project11/issues/464#issuecomment-5420582779)
   (2026-08-26). Cited by URL because the planning dispatch had no GitHub
   read auth and could not re-read it; the host fetched it and spliced it in.

   **Deliberate asymmetry with the boat side**, to be named in the inline
   comment so a later reader does not "fix" it: the boat-side logger records
   all four `/bizzy/ais/*` topics (`config/bizzyboat.yaml`, the `/**/logger`
   record list, added 2026-08-24). The operator side records two. Both are
   defensible — the boat's bag is the vessel's own record of what it heard;
   the operator bag exists to make an operator-side session replayable, and
   the raw sentences plus the tracked product are sufficient for that.

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
| Only what's needed | Two topics, not all four. `/ais/messages` **and** `/ais/atons` are both re-derivable from `/ais/nmea` by re-running the same parser and tracker, so neither buys anything the raw feed does not already hold — the same argument applies to both, and is the whole reason for excluding them. |
| Test what breaks | No existing test infra covers `RECORD_TOPICS` contents (confirmed by review-issue grep); consistent with the rest of this launch file's recorders. Not adding one here — same precedent as issue #458. |
| Workspace vs. project separation | Change is entirely within the project repo (`unh_echoboats_project11`), which owns both the recorder and the AIS chain. |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| 0008 — Follow ROS 2 Official Conventions | Nominally | Any launch-file edit is in its scope. This one *extends* the file's existing conventions (absolute topic names in `RECORD_TOPICS`, one inline rationale comment per entry) rather than deviating from them; no new pattern is introduced. |
| Others | No | A topic-list edit in an existing project launch file — no new package, no launch-graph restructuring, no workspace-repo content. |

## Consequences

| If we change... | Also update... | Included in plan? |
|---|---|---|
| `RECORD_TOPICS` in `bag_recorder_operator_launch.py` | Nothing else — the topics already exist and are documented at their source (`ais_launch.py`'s docstring, `config/ais.yaml`'s header); no new interface is introduced. | Yes (no-op: confirmed nothing further needed) |

## Documentation & Instruction Impact

- **Stale docs** (must land in this PR): the recorder file's own header
  docstring. It enumerates what is recorded ("aggregated diagnostics...
  operator-originated commands... rosout, and TF") and goes stale the moment
  AIS is added, so it gains a clause naming the AIS feed and the fact that it
  is decoded on this host and displayed in CAMP but written nowhere until
  now. Lands in the same commit as the `RECORD_TOPICS` edit, same file.
  Nothing outside this file enumerates the operator recorder's topic list
  (checked): the only other mention is a dated field log, which is a
  historical record and must not be retrofitted.
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
