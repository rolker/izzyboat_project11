# Plan: bag recording: log AML sound-speed raw sentence topic in the main deployment bag

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/396

## Context

`marine_tools#75` (PR [#76](https://github.com/rolker/marine_tools/pull/76))
adds a bare-relative `raw` publisher (`std_msgs/UInt8MultiArray`) to
`sound_speed_bridge`, carrying each framed sentence's raw bytes exactly as the
AML SVS probe emitted them — including sentences the parser rejects, which are
the key diagnostic cases for field sound-speed RCA. Under BizzyBoat's launch
namespace this resolves to `/bizzy/sensors/sound_speed/raw`.

**Scope limit of the driver-side publisher** (confirmed against
`marine_tools` `parsers.py` during the pre-push review): `raw` emits one
message per `\r\n`-**framed** line. An unframed byte stream — wrong baud, or
the all-NUL fault of [#163](https://github.com/rolker/unh_echoboats_project11/issues/163)
— produces **zero** `raw` messages, not garbage payloads. Capturing unframed
bytes needs a separate byte-stream tap, filed as
[rolker/marine_tools#77](https://github.com/rolker/marine_tools/issues/77)
(see also `marine_tools#78`, parser buffer cap). The absence rule documented
in the YAML comment and the operator manual reflects this.

PR #76 is **merged** (`780b59f`, 2026-07-29), so the dependency gate is
satisfied: the `raw` topic exists on the driver side. This issue's
implementation never blocked on it in any case — `all_topics: false` with an
explicit list skips a not-yet-existing topic non-fatally and subscribes later
via the recorder's discovery loop. The PR body should record the gate as
satisfied (rather than as an open ordering condition) and state the deployment
consequence: **one paired gabby rebuild** of `marine_tools` and
`bizzyboat_project11` together.

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
   comment explaining what it carries — mirroring the comment style already
   used for the neighboring sound-speed and Garmin entries (lines 567–576).
   The comment must **name the driver-version dependency** (topic exists only
   with a `sound_speed_bridge` that has the `raw` publisher,
   marine_tools#75/PR #76) and give the correct absence rule: topic **absent**
   → old driver build or bridge not running; topic **present with zero
   messages** → probe silent or output not framed (this includes the #163
   all-NUL fault). (Plan-review suggestion 2, corrected by the pre-push
   review's must-fix — an absent/empty topic is *not* by itself evidence
   against a probe fault.)
2. **Do not touch `sonar_logger`** — leave its record list as-is. The
   exclusion is deliberate (raw bytes are diagnostic-only, not a bathy
   correction input) and will be called out explicitly in the PR body so it
   reads as an intentional scope limit, not an oversight.
3. **No code or message-type changes** — the functional change is the
   config-file addition alone; `bizzyboat_project11` doesn't need to know the
   topic's type, only its name, for `ros2 bag record`. The pre-push review
   passes added three accompanying **documentation-only** edits (the launch
   file's namespace comment plus the two operator-facing docs listed in Files
   to Change), so the final diff spans four files, none of them behavioral.
4. **PR body** (still owed at push time): record the `marine_tools#75`/PR #76
   dependency gate as **satisfied** (merged `780b59f`, 2026-07-29) and
   explicitly note the `sonar_logger` exclusion and why, per the operator's
   Issue Review decisions. Also link the framing-coverage follow-up
   `rolker/marine_tools#77` so the "RCA from the bag alone" gap is tracked.

## Files to Change

| File | Change |
|------|--------|
| `bizzyboat_project11/config/bizzyboat.yaml` | Add `/bizzy/sensors/sound_speed/raw` to the main `logger` topics list (after line 571), with an explanatory comment; no change to `sonar_logger`. |
| `docs/bizzyboat_2026_field_season_guide.md` | Add `raw` to the sound-speed topic enumeration (added in the pre-push-review fix pass). |
| `bizzyboat_project11/launch/sound_speed_launch.py` | Add `raw` to the namespace comment's topic enumeration (added in the pre-push-review fix pass). |
| `docs/bizzyboat_operator_manual.md` | Cross-reference the new bag topic and its absence rule from the #163 all-NUL known-issue bullet (added in the pre-push-review fix pass). |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| Only what's needed | Single topic, negligible bandwidth (short ASCII sentences), matches existing scalar-logging precedent (#270). No new tooling or process. |
| A change includes its consequences | Comment added references marine_tools#75/#76 so future readers can trace the topic's origin; `sonar_logger` exclusion is documented in-PR rather than left as a silent gap. |
| Workspace vs. project separation | Config-only change to a project repo (`unh_echoboats_project11`); no workspace-repo changes needed. |
| Test what breaks | Config-only change with no new code path — no unit test. Checkable acceptance criterion (plan-review suggestion 3): after the gabby rebuild, `ros2 bag info` on a newly recorded main bag lists `/bizzy/sensors/sound_speed/raw` (`std_msgs/UInt8MultiArray`) with a nonzero message count while the probe is streaming. Safe to land before marine_tools#76 merges: the recorder uses `all_topics: false` with an explicit list, so a not-yet-existing topic records nothing rather than failing (in-file precedent: commented-out `/bizzy/sensors/deltat/soundings`). |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| ADR-0008 (ROS 2 conventions) | Marginal | No new package/node/message; topic name and type are already settled on the driver side (marine_tools#75/#76). This change only adds an existing topic to a record list. |

## Consequences

| If we change... | Also update... | Included in plan? |
|---|---|---|
| Main `logger` record list | `sonar_logger` record list | No — deliberately excluded per operator decision (raw bytes are diagnostic-only, not a bathy sound-speed correction input); stated explicitly in the PR body. |
| Main `logger` record list | Any docs describing the main bag's contents | No dedicated bag-contents doc exists beyond inline YAML comments. **But** two places enumerate the sound-speed topic set and would go stale — `docs/bizzyboat_2026_field_season_guide.md` and `launch/sound_speed_launch.py`; both updated in the pre-push-review fix pass, along with an operator-manual cross-reference from the #163 bullet. |
| Main `logger` record list | Deployment: **one paired gabby rebuild** (`marine_tools` + `bizzyboat_project11`) | Config takes effect only after gabby pulls and rebuilds `bizzyboat_project11` — ament `install(DIRECTORY config/)` copies YAML at build time, so symlink-install does not propagate data-file edits. The topic itself needs `sound_speed_bridge` rebuilt from merged marine_tools PR #76 (`780b59f`). Treat these as a **single paired action**, not two queue entries: rebuilding only `marine_tools` makes the topic live but unrecorded (silently invisible in the bag), and rebuilding only `bizzyboat_project11` records nothing. Noted in PR body; joins the outstanding gabby-rebuild queue (plan-review suggestion 1). |
| Main `logger` record list | izzyboat equivalent config | No-op, verified: izzyboat carries no sound-speed probe, so there is no parity change to make (plan-review suggestion 4). |

## Open Questions

- [ ] No open questions — dependency ordering and scope (main-logger-only,
  `sonar_logger` excluded) were both settled at the Issue Review checkpoint
  by the operator; plan is review-plan-ready.

## Estimated Scope

Single PR, single-line config change (plus a comment) — no breakdown needed.
