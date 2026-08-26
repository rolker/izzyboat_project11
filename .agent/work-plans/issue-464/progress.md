---
issue: 464
---

# Issue #464 — Record operator-side AIS on salmon

## Issue Review
**Status**: complete
**When**: 2026-08-26 04:23 +00:00
**By**: Claude Code Agent (Claude Sonnet)

**Issue**: #464
**Comment**: (best-effort post follows this entry; not recorded inline)
**Scope verdict**: well-scoped

### Verification of issue claims

Checked against the current tree (`platforms_ws/src/unh_echoboats_project11`,
branch `feature/issue-464`):

- `bag_recorder_operator_launch.py`'s `RECORD_TOPICS` (lines 42-57 exactly,
  as cited) lists 12 topics, none AIS-related. Confirmed.
- `operator_core_launch.py` includes `ais_launch.py` (arg `ais`, default
  `'true'`) at lines 203-211, **outside** the `GroupAction` that pushes
  `operator_namespace` (lines 157-178). `ais_launch.py` itself pushes only
  the `'ais'` sub-namespace (not `operator/ais`), per its own header comment
  explaining that double-pushing broke `ais_layer`'s subscription in the
  past. So the resulting topics are global `/ais/nmea`, `/ais/messages`,
  `/ais/contacts`, not `/operator/ais/...` — the issue's namespace claim is
  correct, and matters because `RECORD_TOPICS` takes absolute names.
- All four candidate topics exist and are correctly attributed:
  `nmea_relay` publishes relative `nmea` → `/ais/nmea` (raw `!AIVDM`);
  `ais_parser` publishes `messages` → `/ais/messages`; `ais_contact_tracker`
  publishes both `contacts` → `/ais/contacts` (`marine_ais_msgs/AISContact`)
  and `atons` → `/ais/atons` (`GeoPointStamped`), per
  `marine_ais_tools/marine_ais_tools/ais_contact_tracker.py:141,145`. The
  issue's claim that `/ais/contacts` is what `ais_layer`/CAMP consume matches
  `ais_launch.py`'s own docstring.
- The ~1.2 datagrams/s rate is documented in
  `bizzyboat_project11/config/ais.yaml`'s header comment, confirming the
  issue's "cheap to record both raw and tracked" framing.
- No boat-side conflict: `bag_recorder_operator_launch.py` is
  operator-only (salmon); the boat's own AIS bag is a separate receiver
  instance per the issue's stated non-goal, not touched by this change.
- Precedent for how `RECORD_TOPICS` entries pick up inline rationale
  comments: the file's own header attributes the existing list to
  `PLAN_ISSUE-97.md`, and `bag_recorder_operator_launch.py`'s current
  `/operator/sonar_waterfall/contacts` entry (lines 53-56) carries a
  same-shape "why this topic, why here" comment — the pattern this issue's
  AIS entries should follow.

### Scope Assessment

**Well-scoped?** Yes — a single `RECORD_TOPICS` list edit in one existing
launch file, no new nodes, no launch-graph changes. Fits one PR easily.

**Right repo?** Yes — `unh_echoboats_project11` owns both the recorder and
the AIS launch chain; this is project-specific bizzyboat/operator content,
not workspace infra.

**Dependencies**: None identified. The linked issue (unh_marine_autonomy#357,
the public web AIS layer) is informational context only — it consumes the
same live feed but has no code dependency on this recording change, and
this issue doesn't block or get blocked by it.

### Principle Alignment

| Principle | Status | Notes |
|---|---|---|
| Human control and transparency | OK | Adds visibility (a recorded feed that was previously silently unrecorded); no hidden behavior change to the AIS chain itself. |
| A change includes its consequences | Watch | The issue's "Scope" section already reasons through the one real decision (which of 4 topics) with each candidate's tradeoffs named — good. Implementation should carry that same per-topic rationale into inline comments in `RECORD_TOPICS`, matching the existing file's convention (see `/operator/sonar_waterfall/contacts`'s comment) and `PLAN_ISSUE-97.md`'s per-topic rationale for the current list. |
| Only what's needed | OK | Explicitly scoped to the recorder edit; issue calls out both non-goals (no AIS-chain change, no boat-side change). |
| Test what breaks | Watch | No test currently asserts on `RECORD_TOPICS` contents (confirmed by grep — nothing references the recorder's topic list). Not a blocker; this launch file has no existing test infra to extend, consistent with `perception_launch.py`'s recorders (see issue #458 review). |
| Workspace vs. project separation | OK | Contained entirely within the project repo. |

### ADR Applicability

No workspace ADRs are triggered by this change. It's a data-recording
scope change (topic list) in a project repo's launch file, not a new ROS 2
package, launch-graph restructuring, or a change to workspace scripts/CI.
ADR-0008 (ROS 2 conventions) is nominally in scope for any launch-file edit
but the existing file's conventions (absolute-topic `RECORD_TOPICS`,
per-entry rationale comments) are what this issue asks to extend, not
deviate from.

### Consequences

- None beyond the recorder file itself. The topics being added already
  exist and are already documented elsewhere (`ais_launch.py`'s docstring,
  `config/ais.yaml`'s header) — no README/API doc update needed since no
  interface is being introduced, only what's captured on disk.

### Recommendations

- Decide the raw-vs-tracked question explicitly in the plan (the issue
  frames it as "cheap to do both, so do it deliberately") rather than
  defaulting to just `/ais/contacts` — worth a one-line decision in the
  plan doc so a future reader sees it was considered, not overlooked.
- If `/ais/atons` is included, note in the topic's inline comment that
  it's currently only exercised by non-standard AtoN-flagged beacons (per
  `ais_contact_tracker.py`'s comment: "added to track Mesobot, which uses
  an AIS beacon that transmits as an AtoN") rather than charted
  navigation aids — avoids a future reader assuming it captures real
  buoys/lighthouses.

### Actions
- [ ] Carry per-topic rationale comments into `RECORD_TOPICS`, matching the file's existing convention.
- [ ] Make the raw-vs-tracked (nmea/messages vs. contacts/atons) inclusion decision explicit in the plan rather than defaulting.
- [ ] If `/ais/atons` is recorded, note in its comment that it currently only fires for AtoN-flagged beacons (e.g. Mesobot), not charted navigation aids.

## Plan Authored
**Status**: complete
**When**: 2026-08-26 04:40 +00:00
**By**: Claude Code Agent (Claude Sonnet)

**Plan**: `.agent/work-plans/issue-464/plan.md` at `d5bfb91`
**Branch**: feature/issue-464 at `d5bfb91`
**Phases**: single

### Open questions
- [ ] No open questions — plan is review-plan-ready.

## Plan Review
**Status**: complete
**When**: 2026-08-26 04:29 +00:00
**By**: Claude Code Agent (Claude Opus)

**Plan**: `.agent/work-plans/issue-464/plan.md` at `d5bfb91`
**PR**: PR-less (dispatched `--issue 464`; no plan PR)
**Verdict**: approve-with-suggestions

Note: `gh` is unauthenticated in this dispatch, so the issue body and its
comment thread could not be re-read. Issue-side facts were verified against
the `## Issue Review` entry above and against the tree directly; the one
item that could not be checked is finding 2 below.

### Verification performed against the tree

- `bizzyboat_project11/launch/bag_recorder_operator_launch.py:42-57` —
  `RECORD_TOPICS` is a 12-entry absolute-name list ending in the
  `/operator/sonar_waterfall/contacts` entry with its inline rationale
  comment; the plan's cited convention and target file/path are correct.
- `bag_recorder_operator_launch.py:85` — topics are passed as
  `--topics *RECORD_TOPICS`, so adding names is the whole change; absent
  publishers (e.g. `ais:=false`) are simply not recorded, no failure mode.
- `operator_core_launch.py:203-212` includes `ais_launch.py` outside the
  `operator_namespace` `GroupAction`, and `ais_launch.py` pushes only
  `PushRosNamespace('ais')` — confirming the global `/ais/nmea` and
  `/ais/contacts` names the plan uses.
- Consequences check: no doc or config outside the launch file enumerates
  the operator recorder's topic list. `docs/logs/2026/2026-08-20_pandy_link-stalls_logs.md:104`
  names some recorded topics but is a dated field log (historical record,
  not a spec to update); `bizzyboat_project11/docs/operator_annunciator_design.md:127`
  references the file, not its list. The plan's "nothing else" row holds.
- All three `## Issue Review` action items are addressed by the plan
  (inline rationale comments; explicit raw-vs-tracked decision; the
  `/ais/atons` caveat is moot since atons is not recorded).

### Findings
- [ ] (suggestion) `## Documentation & Instruction Impact` says "Stale docs: None" and then, in the same bullet, describes a required header-docstring update — the docstring update *is* the stale-doc item and should be listed as one, not under "None" — `plan.md:72-78`
- [ ] (suggestion) The operator's topic-selection decision is cited as an issue comment but the plan also records that `gh issue read` was unavailable in that dispatch; cite the comment URL/id or name the channel it actually arrived on, so the decision's provenance is checkable — `plan.md:6,20-22`
- [ ] (suggestion) Nearest precedent is unnamed: the boat-side logger already records all four `/bizzy/ais/*` topics with a rationale comment (`bizzyboat_project11/config/bizzyboat.yaml:740-751`, added 2026-08-24). The operator side deliberately records two — name that divergence in the plan and in the inline comment so a later reader doesn't "fix" the asymmetry — `plan.md:54`
- [ ] (suggestion) `/ais/atons` is excluded only as "not needed for CAMP"; it is equally re-derivable from `/ais/nmea` by re-running the parser + tracker — the same argument already used for `/ais/messages`. Saying so makes the exclusion airtight — `plan.md:54`
- [ ] (suggestion) ADR row reads "N/A | No", dropping `## Issue Review`'s nuance that ADR-0008 (ROS 2 conventions) is nominally in scope for any launch-file edit and that this change extends, not deviates from, the file's existing conventions — one line restores it — `plan.md:60-62`

No must-fix findings. Scope, issue alignment, file targeting, and
consequences all check out against the tree; the suggestions are
documentation-accuracy and reader-context items that can be folded into
the implementation commit.
