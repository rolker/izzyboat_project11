---
issue: 396
---

# Issue #396 — bag recording: log AML sound-speed raw sentence topic in the main deployment bag

## Issue Review
**Status**: complete
**When**: 2026-07-29 08:03 -04:00
**By**: Claude Code Agent (Claude Sonnet)

**Issue**: #396
**Comment**: (best-effort post follows this entry; not recorded inline)
**Scope verdict**: well-scoped

### Actions
- [ ] Before merging, verify rolker/marine_tools#75 (PR #76) has actually merged and the `raw` topic is live on the driver — as of this review PR #76 is still **open** (not merged), so implementation should either wait for the merge or explicitly note the dependency ordering in the PR body.
- [ ] Confirm whether the raw sentence topic should also be added to `sonar_logger`'s record list (`bizzyboat_project11/config/bizzyboat.yaml` line ~685 already records the parsed `/bizzy/sensors/sound_speed/sound_speed` in *both* the main `logger` and `sonar_logger` sections for bathy sound-speed correction). The issue only asks for the main bag; confirm this is an intentional scope limit (raw bytes are a diagnostic-only artifact, not needed for the bathy correction pipeline) rather than an oversight, and note it explicitly in the PR if sonar_logger is deliberately excluded.

## Plan Authored
**Status**: complete
**When**: 2026-07-29 08:07 -04:00
**By**: Claude Code Agent (Claude Sonnet)

**Plan**: `.agent/work-plans/issue-396/plan.md` at `04c9a3a`
**Branch**: feature/issue-396 at `04c9a3a`
**Phases**: single

### Open questions
- [ ] No open questions — plan is review-plan-ready.

## Plan Review
**Status**: complete
**When**: 2026-07-29 08:45 -04:00
**By**: Claude Code Agent (Claude Opus)

**Plan**: `.agent/work-plans/issue-396/plan.md` at `04c9a3a`
**PR**: PR-less (`--issue` mode; branch `feature/issue-396`)
**Verdict**: approve-with-suggestions

Both Issue Review actions are discharged by the plan: the marine_tools#75 /
PR #76 dependency ordering is stated (plan.md:16-20, PR-body requirement at
plan.md:47-49), and the `sonar_logger` exclusion is confirmed deliberate and
recorded in the consequences table (plan.md:41-43, 76). Independently
verified against source: `bizzyboat.yaml:571` (main `logger`) and `:685`
(`sonar_logger`) are the correct anchors; marine_tools PR #76 publishes an
**always-on, unconditional** bare-relative `raw` from `_handle_reading()` for
**both** the `aml` and `regex` parsers — so BizzyBoat's `parser: 'regex'`
config (`launch/sound_speed_launch.py`) is covered and the plan's "no launch
changes" claim holds. Precedent check confirms the consequences table: #270
(commit `8accf34`) added the Garmin scalars as a config-only 6-line change
with no doc updates, and no bag-contents inventory exists in `docs/`.
izzyboat has no sound-speed probe, so there is no platform-parity
consequence; the sim launch does not run the recorder.

### Findings
- [ ] (suggestion) Consequences table omits the deployment/rebuild row — the config only takes effect after gabby pulls **and rebuilds** `bizzyboat_project11` (ament `install(DIRECTORY config/)` copies YAML; symlink-install does not propagate data files), and the topic only exists after marine_tools#76 merges **and** `sound_speed_bridge` is rebuilt on gabby. Add a row so the field-side action isn't lost — `plan.md:74-77`
- [ ] (suggestion) Have the added YAML comment name the driver-version dependency, not just the issue numbers — until #76 lands and gabby rebuilds, the entry records silently nothing, and a field reader seeing an empty topic should not mistake it for a probe/driver fault. In-file precedent for annotating a topic that records nothing: the commented-out `/bizzy/sensors/deltat/soundings` at `bizzyboat.yaml:648-649` — `plan.md:34-39`
- [ ] (suggestion) Verification is under-specified ("live/bag smoke check") — state a checkable acceptance criterion instead: after the gabby rebuild, `ros2 bag info` on a new main bag shows `/bizzy/sensors/sound_speed/raw` (`std_msgs/UInt8MultiArray`) with a nonzero message count while the probe is streaming — `plan.md:64`
- [ ] (suggestion) Note in the plan that izzyboat needs no parity change (no sound-speed probe; `izzyboat.yaml` has `logger`/`sonar_logger` blocks but no `sound_speed` entry) so the omission reads as verified rather than unconsidered — `plan.md:74-77`
- [ ] (note, no action) `std_msgs/UInt8MultiArray` carries no header/stamp, so raw-vs-parsed correlation relies on rosbag2 receive time. Settled driver-side in marine_tools#76; out of scope here.
- [ ] (note) The skill's author-self-review heuristic compares only the agent-name portion of `## Plan Authored` (`Claude Code Agent`), which every agent in this workspace shares. This review is a fresh-context sub-agent on a different model (Opus vs. the planner's Sonnet), so no self-review annotation was applied.

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-07-29 09:10 -04:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: changes-requested

**Branch**: feature/issue-396 at `4d63eec`
**Mode**: pre-push
**Depth**: Standard (reason: 162 changed lines across 3 files, plus `.agent/work-plans/issue-396/plan.md` project-repo override trigger)
**Must-fix**: 1 | **Suggestions**: 4
**Round**: 1 | **Ship**: continue — one mechanical comment correction plus a doc-consequence gap; expect approval next round

Specialists: Static Analysis (clean — yamllint under the project's own hook
args finds nothing on changed lines); Governance; Plan Drift; Claude
Adversarial Lens A + Lens B (both run). Local Adversarial skipped: request
timed out (900 s limit; the GPU was serving a concurrent local review).
Copilot Adversarial off (default).

Independently verified against source: the bare-relative `raw` publisher in
marine_tools PR #76 resolves to `/bizzy/sensors/sound_speed/raw` under
`sound_speed_launch.py`'s `PushRosNamespace('sensors/sound_speed')` inside
`core_launch.py`'s boat namespace; the entry sits in the correct `/**/logger`
block (consumed by the `rosbag2_transport` recorder at
`perception_launch.py:246-262`) with correct indentation and no duplicate;
`sonar_logger` is untouched as intended; `all_topics: false` with an explicit
list skips a not-yet-existing topic non-fatally and subscribes later via the
discovery loop. Bandwidth checked: the probe runs ~25 Hz (not "a few Hz"),
~32 B/sentence → roughly 9 MB/h pre-compression under `zstd_fast` — still
negligible beside the four compressed OAK streams, so the plan's conclusion
holds even though its rate assumption was low. No udp_bridge relay, no
bag-analysis consumer, no sensitive content in the raw sentences.

### Findings
- [x] (must-fix) YAML comment overstates what `raw` captures and gives a misleading absence rule: the driver publishes only on a `\r\n`-framed line (`RegexParser.feed`, marine_tools `parsers.py`), so unframed "wrong-baud garbage" — including the documented all-NUL fault ([#163](https://github.com/rolker/unh_echoboats_project11/issues/163)), the flagship sound-speed failure in the operator manual — yields **zero** raw messages. Paired with "if this topic is absent from a bag, suspect an older driver on gabby, not a probe fault", a field diagnostician is actively misled in exactly the RCA scenario the topic was added for. Reword to drop/qualify the garbage claim and state the real discriminator: topic **absent** = old driver or bridge not running; topic **present with zero messages** = probe silent or emitting unframed bytes (#163). Cross-pass confirmed (Lens A + Lens B + lead) — `bizzyboat_project11/config/bizzyboat.yaml:571-577`
- [x] (suggestion) Consequence missed: two in-repo places enumerate the sound-speed topic set as `(sound_speed, temperature, fluid_pressure)` and go stale once `raw` lands — `docs/bizzyboat_2026_field_season_guide.md:211-212` and `bizzyboat_project11/launch/sound_speed_launch.py:45-46`. The plan's "no docs to update" holds for bag-contents inventories (none exist) but not for these enumerations.
- [x] (suggestion) Cross-reference the new bag topic from the operator manual's #163 all-NUL known-issue bullet (`docs/bizzyboat_operator_manual.md:228-230`) — that fault is the motivating case, and the manual is where a field reader looks first.
- [x] (suggestion) File a `marine_tools` follow-up: without an idle-timeout or size-based flush of unframed buffer bytes, `raw` cannot capture the unframed-stream failure mode, so issue #396's "RCA from the bag alone" goal is only partly met. Track the gap rather than lose it. (deferred: already filed as [rolker/marine_tools#77](https://github.com/rolker/marine_tools/issues/77) — byte-stream tap; related [#78](https://github.com/rolker/marine_tools/issues/78) parser buffer cap. No `marine_tools` work in this pass; the gap is now recorded in `plan.md` Context and the YAML comment.)
- [x] (suggestion) Plan text is stale on the dependency gate: `plan.md:16-20` says marine_tools PR #76 is "approved and heading to merge", but it is still **open** as of this review. Refresh the plan and make sure the PR body carries the ordering gate plus the deliberate `sonar_logger` exclusion (both still owed at push time).

## Implementation
**Status**: complete
**When**: 2026-07-29 09:57 -04:00
**By**: Claude Code Agent (Claude Opus)

**Branch**: feature/issue-396 at `a942c56`
**Addressed**: `## Local Review (Pre-Push)` (2026-07-29 09:10 -04:00, branch at `4d63eec`) — 1 must-fix, 4 suggestions
**Commits**: `82f1a9c`, `c0e69dd`, `74d1d55`, `a942c56`

Ground truth applied per the operator's cross-repo confirmation from the
`marine_tools` review: the driver's `raw` topic publishes **only** framed
sentences; an unframed stream (wrong baud, the #163 all-NUL fault) yields
**zero** messages, not garbage payloads. The rewritten comment therefore drops
the "wrong-baud garbage" claim and the "not a probe fault" guidance, and states
the real discriminator instead.

### Actions
- [x] (must-fix) Rewrote the YAML comment: `raw` carries framed sentences only;
  unframed streams (wrong baud, #163 all-NUL) publish zero messages; absence
  rule split into topic-missing (old driver build / bridge not running) vs.
  topic-present-with-zero-messages (probe silent or output not framing — which
  includes the #163 fault). Points at `marine_tools#77` for the byte-stream gap
  — `bizzyboat_project11/config/bizzyboat.yaml:572-582` (`82f1a9c`)
- [x] (suggestion) Refreshed the two stale sound-speed topic enumerations to
  include `raw`, with the driver-build caveat in the guide —
  `docs/bizzyboat_2026_field_season_guide.md:211-215`,
  `bizzyboat_project11/launch/sound_speed_launch.py:45-46` (`c0e69dd`)
- [x] (suggestion) Cross-referenced the new bag topic and its absence rule from
  the operator manual's #163 all-NUL known-issue bullet —
  `docs/bizzyboat_operator_manual.md:228-237` (`74d1d55`)
- [x] (suggestion) Follow-up for unframed-byte capture — `plan.md` Context
  (deferred: already filed as rolker/marine_tools#77, byte-stream tap; related
  rolker/marine_tools#78, parser buffer cap. No `marine_tools` changes made
  here per operator instruction; both are now referenced from the plan and the
  YAML comment.) (`a942c56`)
- [x] (suggestion) Refreshed the stale dependency-gate text in `plan.md`: PR
  rolker/marine_tools#76 is still **open** (verified via `gh` this pass), not
  "approved and heading to merge"; recorded why landing first is safe
  (`all_topics: false` + explicit list skips a missing topic non-fatally), and
  restated that the PR body still owes the ordering gate and the deliberate
  `sonar_logger` exclusion — `plan.md:20-31, 66-70` (`a942c56`)

### Verification
- pre-commit hooks (incl. `yamllint`) passed on every commit; no `--no-verify`.
- Parsed `bizzyboat.yaml` with PyYAML: `/**/logger` `record.topics` contains
  `/bizzy/sensors/sound_speed/raw` (76 topics, `all_topics: false`);
  `/**/sonar_logger` does **not** (17 topics) — the deliberate exclusion holds.
- `gh` confirms rolker/marine_tools#76 OPEN, #77 and #78 OPEN.
- Not pushed — the host performs pushes.

### Next step
Re-review the fixes:
`.agent/scripts/dispatch_subagent.sh --mode in-process --issue 396 --skill review-code`

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-07-29 10:30 -04:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: changes-requested

**Branch**: feature/issue-396 at `1a7e9d7`
**Mode**: pre-push
**Depth**: Standard (reason: 4 substantive files across config + launch + two operator-facing docs; `.agent/work-plans/issue-396/plan.md` project-repo override trigger)
**Must-fix**: 2 | **Suggestions**: 8
**Round**: 2 | **Ship**: recommended — both must-fixes are precise file:line corrections with obvious fixes (one paren typo, one decision-rule completion); no design question remains, so address-findings then push rather than a third full round

Specialists: Static Analysis (clean — yamllint under the project's own hook
args passes; the only flake8 hits in `sound_speed_launch.py` are I201/D103 on
untouched lines 20/24); Governance (relayed by host: APPROVE, 0 must-fix, 2
suggestions — `sonar_logger` reciprocal comment, operator-manual cross-repo
breadcrumb); Plan Drift (lead-run); Claude Adversarial Lens A + Lens B (both
run, both substantive). Local Adversarial skipped: operator-directed skip at
~21 min against the 1500 s cap with zero output; the GPU pass produced nothing
and was killed to free the device (same class of skip as Round 1's timeout).
Copilot Adversarial off (default).

Round-1 carry-over: all five Round-1 findings verified fixed at `1a7e9d7`. The
must-fix comment rewrite (`82f1a9c`) correctly drops the "wrong-baud garbage"
claim and states the absent-vs-empty discriminator; the two stale enumerations
(`c0e69dd`) and the #163 cross-reference (`74d1d55`) landed as described. The
Round-2 must-fixes below are **new surface created by that rewrite** — the
decision rule it introduced is now the thing being reviewed — not regressions.

Independently verified against source this round: `marine_tools` PR #76 is now
**MERGED** (`780b59f`, 2026-07-29T14:17Z) — the plan's dependency gate is
satisfied; the merged `node.py` creates `self._raw_pub` (`UInt8MultiArray`,
bare-relative `raw`, RELIABLE depth-10, matching its siblings) in `__init__`
and publishes on every framed reading including NaN/parse-failure ones;
`RegexParser.feed` frames only on the configured terminator and skips
whitespace-only lines; PyYAML parse confirms main `logger` = 76 topics
(`all_topics: false`, no duplicates, contains the new topic) and `sonar_logger`
= 17 topics without it. Clean checks, no action: no credential/PII exposure in
AML sentences; bandwidth negligible; `raw` correctly absent from all three
`udp_bridge` topic maps (lines 248/406/487 relay only `sound_speed`); izzyboat
parity a verified no-op.

### Findings
- [x] (must-fix) Unbalanced parenthesis introduced by the enumeration edit: the `(` opening the topic list is never closed — the trailing `)` belongs to the `#396` link. Mechanically counted 5 `(` vs 4 `)` over lines 209-217. Fix by closing the list before the em-dash clause, or split into two sentences (which also discharges suggestion 4) — `docs/bizzyboat_2026_field_season_guide.md:211-216`
- [x] (must-fix) The absence/zero-message decision rule is presented as exhaustive but omits a cause in **each** branch, and both omissions point a field diagnostician at the wrong subsystem — the exact failure mode Round 1's must-fix was raised against. (a) **"Topic absent"** omits *the recorder config on gabby being stale* — `bizzyboat_project11` needs its own pull+rebuild (ament `install(DIRECTORY config/)` copies YAML; symlink-install does not propagate it), independent of the driver rebuild. With #76 merged today and gabby carrying neither rebuild, this is now the **most likely** near-term cause, and the reverse deploy order (marine_tools rebuilt, bizzyboat_project11 not) makes the topic live-but-unrecorded and silently invisible. (b) **"Topic present with zero messages"** omits the host-side serial fault — all four publishers are created in `__init__` *before* the serial thread starts, and `_serial_loop` catches `SerialException`/`OSError` and retries forever, so a wrong/missing device or permission failure yields exactly zero messages and reads as "probe silent or unframed". The discriminator is already in the same bag: `/diagnostics` is recorded in this very `logger` list (`bizzyboat.yaml:509`) and the node emits `Serial not connected (<device>)` at ERROR. Add both causes, and cite the `/diagnostics` cross-check so "RCA from the bag alone" is actually true. Cross-pass confirmed (Lens A + Lens B) — `bizzyboat_project11/config/bizzyboat.yaml:577-582`, `docs/bizzyboat_operator_manual.md:233-237`
- [x] (suggestion) `\r\n` framing is attributed to "the driver", but it is a per-deployment launch parameter, not a driver property: `RegexParser` defaults `line_terminator='cr'` and the first-class `AMLParser` frames on a bare `\r`. It is `\r\n` here only because `sound_speed_launch.py:63` sets `regex_line_terminator: 'crlf'`. If the probe is retuned or `parser: 'aml'` is selected, the diagnostic rule silently becomes wrong. Qualify once — `bizzyboat_project11/config/bizzyboat.yaml:574`, `docs/bizzyboat_operator_manual.md:235`, `docs/bizzyboat_2026_field_season_guide.md:214`
- [x] (suggestion) The reading table omits the single most diagnostically valuable state the topic exists to capture: **`raw` has messages while parsed `/bizzy/sensors/sound_speed/sound_speed` is NaN** → the probe is framing sentences whose content the `regex_pattern` rejects (verified: `_parse` returns NaN with `raw_bytes` intact on both a regex miss and a decode failure). Tell the operator to pair `raw` against the parsed topic rather than treat message presence as a health verdict — `docs/bizzyboat_operator_manual.md:233-234`
- [x] (suggestion) The deliberate `sonar_logger` exclusion is documented only in the main-logger comment ~120 lines away. A future agent adding sound-speed diagnostics to the sonar bag will be reading the `sonar_logger` sound-speed entry and will read the omission as an oversight. Add a reciprocal half-line there. Cross-source confirmed (Lens B + Governance) — `bizzyboat_project11/config/bizzyboat.yaml:697`
- [x] (suggestion) The refreshed enumeration groups `raw` with `temperature` and `fluid_pressure`, implying comparable behavior. Under BizzyBoat's regex pattern those two have no named groups, so they are advertised and permanently silent, whereas `raw` publishes on every framed sentence. Splitting `raw` into its own clause fixes this and must-fix 1 together — `docs/bizzyboat_2026_field_season_guide.md:211-213`
- [x] (suggestion) Add a pre-survey check rather than relying only on an after-the-fact absence rule: `ros2 topic list | grep sound_speed/raw` on gabby before trusting the bag for RCA. The absence rule only helps once the data is already lost — `docs/bizzyboat_operator_manual.md:230-232` (deferred: operator-directed scope hold at the Round-2 disposition — the four cheap suggestions were named explicitly and this was not among them. A pre-survey topic check belongs with the manual's broader pre-survey checklist, not bolted onto the #163 known-issue bullet; leaving it for a dedicated pass.)
- [x] (suggestion) Governance (relayed): add the cross-repo breadcrumb to the operator manual so the `marine_tools` origin of the topic is traceable from the field-facing doc. (deferred: operator-directed scope hold — not among the four suggestions dispositioned for this pass. Partly served already: the manual's rebuild branch now names the driver build explicitly, and the field season guide carries the `rolker/marine_tools#75` reference.)
- [x] (suggestion) Plan internal inconsistency: Approach step 3 still asserts "No launch, code, or message-type changes — this is a pure config-file addition", which its own Files-to-Change table (now four files, including a launch-comment edit and two docs) contradicts. Reword step 3 — `.agent/work-plans/issue-396/plan.md:63-65`
- [x] (suggestion) Dependency gate is now satisfied — `marine_tools` PR #76 merged (`780b59f`, 2026-07-29), superseding the plan's "still open" text. Update the plan Context and the owed PR-body gate, and restate the deployment consequence as a **paired** gabby rebuild (`marine_tools` + `bizzyboat_project11` together) rather than two independent queue entries: the marine_tools-only order is the one that fails silently — `.agent/work-plans/issue-396/plan.md:26-31, 102`

### Next step
Address the findings, then re-review or push:
`.agent/scripts/dispatch_subagent.sh --mode in-process --issue 396 --skill address-findings`

## Implementation
**Status**: complete
**When**: 2026-07-29 10:34 -04:00
**By**: Claude Code Agent (Claude Opus)

**Branch**: feature/issue-396 at `5da388f`
**Addressed**: `## Local Review (Pre-Push)` Round 2 (2026-07-29 10:30 -04:00, branch at `1a7e9d7`) — 2 must-fix, 8 suggestions
**Commits**: `921be12`, `a5d8f6b`, `0b36c39`, `5da388f`

Host disposition for this pass: fix both must-fixes, apply four named
suggestions (framing attribution, the missing reading-table state, the
reciprocal `sonar_logger` note, the plan Approach-step-3 scope claim), restate
the deployment consequence for the now-**merged** `marine_tools` PR #76
(`780b59f`, 2026-07-29) as one **paired** gabby rebuild, and defer the rest
without expanding scope.

### Actions
- [x] (must-fix) Closed the unbalanced parenthesis by splitting the enumeration
  into two bullets — `sound_speed` / `temperature` / `fluid_pressure` in one,
  `raw` in its own, which also discharges the "raw grouped with permanently
  silent topics" suggestion. Paren count re-verified balanced (6/6) —
  `docs/bizzyboat_2026_field_season_guide.md:208-218` (`921be12`)
- [x] (must-fix) Completed both branches of the absence/zero-message decision
  rule in the YAML comment and the operator manual. **Absent** now leads with
  the stale recorder config on gabby (`bizzyboat_project11` needs its own
  pull+rebuild, independent of the driver; ament copies `config/`), then the
  pre-passthrough driver build, then bridge-not-running — with the explicit
  warning that a driver-only rebuild leaves the topic live but unrecorded.
  **Present with zero messages** now includes the host-side serial fault
  (wrong/missing device, permissions — publishers exist before the serial
  thread connects and it retries forever), discriminated via `/diagnostics` in
  the same bag (`Serial not connected (<device>)` at ERROR) —
  `bizzyboat_project11/config/bizzyboat.yaml:572-593`,
  `docs/bizzyboat_operator_manual.md:228-252` (`a5d8f6b`)
- [x] (suggestion) Attributed `\r\n` framing to the launch parameter
  `regex_line_terminator: 'crlf'` in all three places, noting the parser's own
  default is a bare `\r` (as is `parser: 'aml'`), so the rule is re-checked if
  the parser config changes — `bizzyboat.yaml:574-576`,
  `docs/bizzyboat_operator_manual.md:250-252`,
  `docs/bizzyboat_2026_field_season_guide.md:216-218`
  (`921be12`, `a5d8f6b`)
- [x] (suggestion) Added the highest-value reading state: `raw` present with
  messages while the parsed `.../sound_speed` is **NaN** → the probe is framing
  sentences the `regex_pattern` rejects; the manual now tells the operator to
  pair the two topics rather than read message presence as a health verdict —
  `docs/bizzyboat_operator_manual.md:233-237`, mirrored in
  `bizzyboat.yaml:592-593` (`a5d8f6b`)
- [x] (suggestion) Added the reciprocal exclusion half-line at the
  `sonar_logger` sound-speed entry so a future agent reads the omission as
  deliberate — `bizzyboat_project11/config/bizzyboat.yaml:707-709` (`0b36c39`)
- [x] (suggestion) Reworded Approach step 3 to match the four-file reality: the
  functional change is config-only, with three accompanying documentation-only
  edits (launch comment + two docs), none behavioral —
  `.agent/work-plans/issue-396/plan.md:64-70` (`5da388f`)
- [x] (suggestion) Dependency gate updated to **satisfied**: `marine_tools`
  PR #76 merged (`780b59f`, 2026-07-29). Plan Context and the owed PR-body item
  now say so, and the deployment consequence is restated as one **paired**
  gabby rebuild (`marine_tools` + `bizzyboat_project11` together), calling out
  that the driver-only order is the silently-failing one —
  `.agent/work-plans/issue-396/plan.md:26-32, 71-73, 105` (`5da388f`)
- [x] (suggestion) Re-grouped `raw` out of the `temperature` / `fluid_pressure`
  clause in the guide, noting those two are advertised but permanently silent
  under BizzyBoat's regex — folded into the must-fix 1 split —
  `docs/bizzyboat_2026_field_season_guide.md:210-213` (`921be12`)
- [x] (suggestion) Pre-survey `ros2 topic list | grep sound_speed/raw` check
  (deferred: operator-directed scope hold — not among the four suggestions
  dispositioned for this pass; belongs with the manual's broader pre-survey
  checklist rather than the #163 known-issue bullet.)
- [x] (suggestion) Governance cross-repo breadcrumb in the operator manual
  (deferred: operator-directed scope hold; partly served already — the manual's
  rebuild branch names the driver build, and the field season guide carries the
  `rolker/marine_tools#75` reference.)

### Verification
- pre-commit hooks (incl. `yamllint`) passed on every commit; no `--no-verify`.
- PyYAML re-parse of `bizzyboat.yaml`: main `/**/logger` = 76 topics,
  `all_topics: false`, no duplicates, contains
  `/bizzy/sensors/sound_speed/raw`; `/**/sonar_logger` = 17 topics and does
  **not** contain it — the deliberate exclusion still holds.
- Parenthesis balance re-counted over the edited guide block: 6 open / 6 close.
- No code or launch-behavior changes in this pass — docs, YAML comments, and
  plan text only.
- Not pushed — the host performs pushes.

### Next step
Round 2 recommended Ship; no Round 3 planned. Host proceeds to the publish
checkpoint (push + PR). The PR body still owes: dependency gate satisfied
(`marine_tools` PR #76 merged `780b59f`), the deliberate `sonar_logger`
exclusion, the paired gabby rebuild, and the
[`rolker/marine_tools#77`](https://github.com/rolker/marine_tools/issues/77)
framing-coverage follow-up link.
