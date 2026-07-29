# Plan: bag recording: log AML sound-speed raw sentence topic in the main deployment bag

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/396

## Context

`marine_tools#75` (PR [#76](https://github.com/rolker/marine_tools/pull/76))
adds a bare-relative `raw` publisher (`std_msgs/UInt8MultiArray`) to
`sound_speed_bridge`, carrying each framed sentence's raw bytes exactly as the
AML SVS probe emitted them — including parse failures and garbage, which are
the key diagnostic cases for field sound-speed RCA. Under BizzyBoat's launch
namespace this resolves to `/bizzy/sensors/sound_speed/raw`.

PR #76 is approved and heading to merge in a parallel pipeline (confirmed at
the Issue Review checkpoint), so this issue's implementation does not need to
block on the merge landing first — but the PR body must state the dependency
so a reviewer can confirm topic existence before/at merge time.

The parsed `/bizzy/sensors/sound_speed/sound_speed` topic is already recorded
in **both** record lists in `bizzyboat_project11/config/bizzyboat.yaml`:
main `logger` (line 571) and `sonar_logger` (line 685, for bathy sound-speed
correction). The operator has confirmed (Issue Review checkpoint) that the raw
sentence topic is diagnostic-only and must go **only** into the main `logger`
list — deliberately excluded from `sonar_logger`, since raw bytes are not an
input to the bathy correction pipeline.

Bandwidth is negligible: short ASCII sentences at probe rate, same reasoning
already applied to the Garmin water-temperature/nadir-depth scalars (#270).

## Approach

1. **Add the new topic to the main `logger` record list** in
   `bizzyboat_project11/config/bizzyboat.yaml`, immediately after the existing
   `/bizzy/sensors/sound_speed/sound_speed` entry (line 571), with a short
   comment explaining what it carries and pointing at marine_tools#75/#76 —
   mirroring the comment style already used for the neighboring sound-speed
   and Garmin entries (lines 567–576).
2. **Do not touch `sonar_logger`** — leave its record list as-is. The
   exclusion is deliberate (raw bytes are diagnostic-only, not a bathy
   correction input) and will be called out explicitly in the PR body so it
   reads as an intentional scope limit, not an oversight.
3. **No launch, code, or message-type changes** — this is a pure
   config-file addition; `bizzyboat_project11` doesn't need to know the
   topic's type, only its name, for `ros2 bag record`.
4. **PR body**: state the `marine_tools#75`/PR #76 dependency (driver-side
   publisher) and explicitly note the `sonar_logger` exclusion and why, per
   the operator's Issue Review decisions.

## Files to Change

| File | Change |
|------|--------|
| `bizzyboat_project11/config/bizzyboat.yaml` | Add `/bizzy/sensors/sound_speed/raw` to the main `logger` topics list (after line 571), with an explanatory comment; no change to `sonar_logger`. |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| Only what's needed | Single topic, negligible bandwidth (short ASCII sentences), matches existing scalar-logging precedent (#270). No new tooling or process. |
| A change includes its consequences | Comment added references marine_tools#75/#76 so future readers can trace the topic's origin; `sonar_logger` exclusion is documented in-PR rather than left as a silent gap. |
| Workspace vs. project separation | Config-only change to a project repo (`unh_echoboats_project11`); no workspace-repo changes needed. |
| Test what breaks | Config-only change with no new code path — verification is topic-existence on the driver (post-merge of marine_tools#76) plus a live/bag smoke check, not a unit test. |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| ADR-0008 (ROS 2 conventions) | Marginal | No new package/node/message; topic name and type are already settled on the driver side (marine_tools#75/#76). This change only adds an existing topic to a record list. |

## Consequences

| If we change... | Also update... | Included in plan? |
|---|---|---|
| Main `logger` record list | `sonar_logger` record list | No — deliberately excluded per operator decision (raw bytes are diagnostic-only, not a bathy sound-speed correction input); stated explicitly in the PR body. |
| Main `logger` record list | Any docs describing the main bag's contents | No dedicated bag-contents doc found in this repo beyond inline YAML comments; the added comment is the documentation. |

## Open Questions

- [ ] No open questions — dependency ordering and scope (main-logger-only,
  `sonar_logger` excluded) were both settled at the Issue Review checkpoint
  by the operator; plan is review-plan-ready.

## Estimated Scope

Single PR, single-line config change (plus a comment) — no breakdown needed.
