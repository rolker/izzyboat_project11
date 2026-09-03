---
issue: 484
---

# Issue #484 — bizzyboat bridge config: coverage_catalog needs durability: transient_local, or the latched catalog is relayed VOLATILE

## Issue Review
**Status**: complete
**When**: 2026-09-03 13:22 -04:00
**By**: Claude Code Agent (Claude Sonnet)

**Issue**: #484
**Comment**: (best-effort post follows this entry; not recorded inline)
**Scope verdict**: well-scoped

### Verification performed (source-checked, not taken on faith)

- `bizzyboat_project11/config/bizzyboat.yaml` — confirmed `coverage_catalog` appears
  exactly twice, at line 284 (wifi connection, under boat-side `udp_bridge` node
  `name: bizzy`, config block starting line 153) and line 542 (vpn connection).
  Neither sets `durability`, and `grep -c durability` over the whole file returns
  0 — no topic in it sets the key anywhere. Claims accurate.
- `udp_bridge/doc/qos_design.md` (§ Durability, § "How configuration works") and
  `udp_bridge/include/udp_bridge/qos_resolution.h` — confirmed: default is
  `VOLATILE` on both ends; per-topic opt-in via
  `remotes.<remote>.connections.<connection>.topics.<topic>.durability`; an
  unrecognized string falls through to `durability_volatile()` (the `else`
  branch in `resolveDestinationPublisherQos`/`resolveSourceSubscriptionQos`) —
  confirms the "typo fails silently to VOLATILE" caveat.
- `cube_bathymetry_node.cpp` — confirmed `tile_catalog_publisher_` is created
  with `rclcpp::QoS(1).transient_local().reliable()`, with a comment describing
  the catalog as the transient_local "COMPLETE snapshot" driving anti-entropy
  reconciliation. **The issue's cited line numbers are stale** (it says `:515`
  and `:459`; current source has the publisher creation at line 640 and the
  nearby late-joiner comment around line 477-483, line 459 is now unrelated
  draft-tile-persistence logging). Content claim is correct; line citations
  have drifted — note for whoever writes the fix PR, don't copy the line
  numbers verbatim into a commit message.
- `udp_bridge/src/udp_bridge.cpp::publishItem` — confirmed the destination
  publisher is found-or-created once into a `publishers_` map keyed by topic
  (phase 1/2/3 lookup, `try_emplace`), matching the "created once and cached,
  QoS fixed by the first message, config change does not re-create it" claim.
  Cross-checked against `operator.yaml`: the boat (`bizzyboat.yaml`, node
  `bizzy`) is the *sender* of `coverage_catalog`; the operator-station
  `udp_bridge` process is the *receiver* that caches the destination
  publisher — so it is the operator-side bridge process that needs the
  restart after this config change ships, not the boat-side one. Worth
  spelling out explicitly in the fix PR / rollout note, since it's the kind
  of detail that's easy to get backwards on deployment day.
- `udp_bridge` test suite (`test_qos_resolution.cpp`,
  `test_qos_matching_integration.cpp`) — confirmed durability *resolution*
  (parsing) is unit-tested (`DestinationTransientLocal`,
  `DestinationUnrecognizedDurabilityFallsBackToVolatile`), but the QoS
  *matching* integration tests cover only reliability, not durability, and
  there is no latch-delivery test. `rolker/udp_bridge#79` ("QoS matching
  integration tests cover reliability but not durability — no negative-match
  test, no latch-delivery test") is open and matches the issue's "filed
  separately" claim exactly — confirmed, not just asserted.
- `unh_echoboats_project11#467` (2026-08-26 Appledore deployment issue,
  CLOSED) — exists, confirming the field-evidence provenance.
- No project `PRINCIPLES.md` and no parameter table in this repo's
  `.agents/README.md` — this is a config-value edit to an already-documented
  `udp_bridge` parameter, not a new node parameter or new package interface,
  so no doc-consequence gap here.

### Scope Assessment

**Well-scoped?** Yes — a two-key addition (`durability: transient_local`) at
two call sites in one file, one repo, no code changes. Verifiable entirely by
reading source (done above); acceptance is a bench/field observation, not a
design decision.
**Right repo?** Yes — deployment-specific bridge config belongs in
`unh_echoboats_project11`, not the workspace or `udp_bridge` itself (whose
mechanism needs no change).
**Dependencies**:
- `rolker/unh_marine_autonomy#363` and `rolker/camp#220` — both downgraded a
  consumer to `VOLATILE` as a field workaround and are correctly left *out*
  of this issue's scope (different repos), but the issue's own "will not
  announce itself" warning is accurate: a `TRANSIENT_LOCAL` publisher still
  matches a `VOLATILE` subscriber, so nothing will force those reverts once
  this lands. Recommend the fix PR link both explicitly as tracked
  follow-ups so they don't silently become permanent (this is exactly what
  camp#220's PR framed as "a permanent accepted tradeoff" already risks).
- `rolker/udp_bridge#79` — open, tracks the missing matching/latch-delivery
  test coverage; correctly not blocking this config fix.

### Principle Alignment

| Principle | Status | Notes |
|---|---|---|
| Human control and transparency | OK | Issue is evidence-based (source line refs, field measurements); rationale is clear |
| A change includes its consequences | Watch | The coupled-repo reverts (autonomy#363, camp#220) are a real consequence of this fix landing but are explicitly out of this issue's scope; recommend cross-linking, not folding in |
| Only what's needed | OK | Minimal, config-only diff; follows the file's existing per-entry inline-comment convention (every other exceptional entry in this file carries a rationale comment — the fix should too) |
| Test what breaks | Action needed | The issue itself flags "Verification owed": nobody has exercised a latched catalog crossing the bridge with this parameter set — it's traced in source, not observed. Given this is safety/deployment-relevant boat config and AGENTS.md's Quality Standard ("fix it completely... check the lifecycle transition"), the fix's acceptance criteria should include an explicit bench or field check (a late-joining subscriber actually receiving the retained catalog), not just a source-level trace, before this is called done |
| Workspace vs. project separation | OK | Correctly placed in the project repo |

### ADR Applicability

| ADR | Triggered | Notes |
|---|---|---|
| 0008 — ROS 2 conventions | No | Value-only config edit, not a package/launch structural change; the udp_bridge `durability` parameter itself is already documented in `udp_bridge/doc/qos_design.md` |

### Consequences

- No package/doc updates needed in `udp_bridge` (parameter already exists and
  is documented) or in this repo's `.agents/README.md` (no parameter table
  section exists here to update).
- The fix PR should state explicitly, as a rollout step: the **operator-station**
  `udp_bridge` process (not the boat-side one) needs a restart to pick up the
  new destination-publisher QoS, since its publisher is cached on first
  arrival per-topic.
- Recommend adding a short inline comment at both edit sites (line 284, 542)
  following this file's existing convention, referencing #484 and the
  transient_local rationale, since every other special-cased entry in this
  file already carries one.

### Recommendations

- Cross-link `unh_marine_autonomy#363` and `camp#220` from the fix PR as
  tracked follow-ups for the coupled reverts.
- Include a bench/field verification step (late-joining subscriber receives
  the retained catalog) in the PR's test plan — closes the "verification
  owed" gap the issue itself names.
- Double-check the exact string `transient_local` (not `transient-local`) at
  both sites — the issue calls out this typo class as reproducing the
  original bug silently; a quick `grep durability` post-edit is cheap
  insurance.

### Actions
- [ ] Verify the fix's PR test plan includes a bench/field observation of
      latched delivery, not just a source trace (Test what breaks — Action
      needed)
- [ ] Cross-link unh_marine_autonomy#363 and camp#220 as follow-ups in the
      fix PR (coupled-repo reverts consequence)
- [ ] Note in the PR/rollout that the operator-station udp_bridge process
      (not the boat-side one) needs restarting for the QoS change to take
      effect


## Plan Authored
**Status**: complete
**When**: 2026-09-03 13:27 -04:00
**By**: Claude Code Agent (Claude Sonnet)

**Plan**: `.agent/work-plans/issue-484/plan.md` at `06ee6d1`
**Branch**: feature/issue-484 at `06ee6d1`
**Phases**: single

### Open questions
- [ ] No open questions — plan is review-plan-ready.

## Plan Review
**Status**: complete
**When**: 2026-09-03 13:32 -04:00
**By**: Claude Code Agent (Claude Sonnet)

**Plan**: `.agent/work-plans/issue-484/plan.md` at `06ee6d1`
**PR**: PR-less (--issue mode)
**Verdict**: approve-with-suggestions

### Evaluation

| Dimension | Verdict | Notes |
|---|---|---|
| Scope | Good | Two-key config diff at two verified call sites; appropriately sized for a single PR |
| Issue alignment | Good | Addresses the exact bug (unset durability defaults to VOLATILE, breaking transient_local relay) and folds in all three review-issue action items |
| File targeting | Good | Independently re-counted: `coverage_catalog` appears in the `topics:` dict at exactly two connections — wifi (line 284) and vpn (line 542). A third connection (`cell`, line 622) also relays other topics but does **not** carry `coverage_catalog` (verified by grep over its full topics_list/topics block) — the plan's "two call sites" claim is correct, not an undercount. `operator.yaml` (the reverse-direction config) does not retransmit `coverage_catalog` either. |
| Consequences | Good | Coupled reverts (autonomy#363, camp#220) correctly cross-linked rather than folded in; udp_bridge#79 correctly left out of scope |
| Documentation & instruction impact | Good | Non-silent; correctly frames the "receiving bridge caches QoS, must restart" note as a candidate, not an applied edit |
| Principle alignment | Needs work (minor) | See findings 1-2 below — "Enforcement over documentation" and "Human control and transparency" are both touched by gaps that are cheap to close |
| ADR compliance | Good | 0008 correctly assessed not triggered — value-only config edit |
| ROS conventions | Good | `durability: transient_local` mechanically verified end-to-end against `udp_bridge/include/udp_bridge/qos_resolution.h` and `udp_bridge.cpp` (`addSubscriberConnection`/`updateLocalSubscriptions`): setting it on either connection also flips the boat-side *source* subscription to transient_local (`sub.durability` takes the strongest per-topic setting across remotes, `udp_bridge.cpp:1875-1880`), so the fix correctly reaches both the source subscription and the destination publisher from a single per-connection key. Config-only is genuinely sufficient — no code change needed. |

### Findings

1. **(suggestion) [Principle alignment — Enforcement over documentation]** The plan's only protection against the exact silent-fallback bug this issue is about (`durability: transient-local` or any other typo silently resolves to VOLATILE, per `qos_resolution.h`'s `else` branch) is a manual post-edit `grep` by the implementer. There is no lasting, automated check in this repo or `udp_bridge` that a `durability` value is one of the recognized strings — a future edit to these same two lines (or a new topic needing the same treatment) can reintroduce this exact bug with no signal. This doesn't need to block the plan (it's a two-line diff, and `udp_bridge#79` already tracks the matching/latch-delivery test gap at the mechanism level), but the plan should at least name this as a residual gap rather than treating the one-time grep as sufficient closure — a one-line note that "no automated durability-string validation exists; a future edit to this file carries the same silent-fallback risk" would be enough to keep it visible rather than quietly resolved.
2. **(suggestion) [Principle alignment — Human control and transparency]** The plan states the rollout requirement (operator-station bridge restart) explicitly but never states a rollback step. Given this is safety-relevant boat config and the review prompt specifically asked "what if this makes things worse on the water" — the answer is almost certainly "revert the two config lines and restart the operator-station bridge again," and it costs one sentence in the PR body to say so rather than leaving it implicit. Risk here is low (a low-rate, small, queue_size-2 catalog message; transient_local is not expected to change bandwidth materially), but stating it costs nothing and matches the plan's own standard of being explicit about the restart requirement.

Neither finding is must-fix — both are cheap, low-risk additions to the PR body/plan that close a genuinely open (if minor) transparency/enforcement gap. Implementation should not be blocked on them, but they're worth folding into the PR description when it's written.

### Summary

The plan is well-scoped, source-verified (independently re-checked, not just trusted), and correctly limits itself to the two config sites that actually carry `coverage_catalog`. The mechanism trace confirms config-only is sufficient — durability set on either connection also fixes the boat-side source subscription, not just the destination publisher. Two small transparency/enforcement gaps (residual silent-typo risk, no stated rollback) are worth a sentence each in the PR body but do not block implementation.

### Recommended Actions

- [ ] When writing the PR body, add one sentence acknowledging the residual silent-fallback-typo risk (no automated durability-string validation exists in this repo or `udp_bridge`)
- [ ] When writing the PR body, add one sentence stating the rollback step (revert the two config lines, restart the operator-station bridge)
