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
