---
issue: 389
---

# Issue #389 — Coverage tile transmission: revisit end-to-end

## Issue Review
**Status**: complete
**When**: 2026-07-31 18:40 +00:00
**By**: Claude Code Agent (Claude Sonnet)

**Issue**: #389
**Comment**: (best-effort post follows this entry; not recorded inline)
**Scope verdict**: well-scoped

### Summary

Issue asks to revisit the coverage-tile transmission process end-to-end and evaluate options after the 2026-07-23 BizzyBoat deployment where level-11 tiles were too large to pass through udp_bridge (operator raised `maximum_bytes_per_second` on the VPN connection in the field as a workaround; not saved to config). The problem recurred on 2026-07-29 (#398), confirming this is a systematic failure, not a one-off.

**Current state confirmed from source** (`bizzyboat.yaml`, `operator.yaml`):
- `maximum_packet_size: 1000` (both boat and operator nodes) → heavy fragmentation of large GridMap tiles
- `coverage_tiles` routed **VPN only** (cap 1.2 MB/s, line 268), not on wifi (cap 1.5 MB/s)
- `coverage_tiles: {queue_size: 2, period: 0.5}` → rate-limited to 2/s
- Operator workaround raised VPN `maximum_bytes_per_second` to 1500000 (from 1200000) — not saved

### Scope Assessment

**Well-scoped?** Yes. The issue correctly frames this as a bounded end-to-end investigation of a concrete transport failure with a root cause already narrowed (fragmented large tiles + VPN-only routing + tight cap). The candidate options are listed; plan-task's job is to evaluate/profile and select. A single PR should be able to hold the resulting config changes.

**Right repo?** Yes — all of the relevant configuration lives in `unh_echoboats_project11` (`bizzyboat_project11/config/bizzyboat.yaml` and `operator.yaml`).

**Dependencies**: Related to #350 (live coverage pipeline wiring, already closed). Also related to #398 (2026-07-29 recurrence, separate deployment issue). No blocking upstream issues.

### Principle Alignment

| Principle | Status | Notes |
|---|---|---|
| Human control and transparency | OK | Issue explicitly avoids pre-selecting the fix; asks for principled evaluation — operator remains in the loop |
| Enforcement over documentation | Watch | If a design decision is made (e.g., "always add wifi route for tile topics"), document the reasoning in config comments so future agents don't revert it silently |
| Capture decisions, not just implementations | Action needed | Multiple valid solution paths exist (rate cap, routing, fragmentation, tile detail). The chosen approach and rationale should be recorded — either a brief ADR or substantive config comment block — so the tradeoff survives to the next operator/agent |
| A change includes its consequences | Action needed | `bizzyboat.yaml` and `operator.yaml` are documented as a "pair" (see comment at line 351 of bizzyboat.yaml): any coverage-tile routing or rate change must be applied consistently to both. If wifi route is added, link budget impact on shared video streams must be assessed |
| Only what's needed | Watch | Five candidate solutions are listed; avoid implementing all of them — profile actual tile sizes first, then pick the minimum set of changes that resolves the failure |
| Improve incrementally | OK | Scope is bounded; config changes are reviewable |
| Test what breaks | Watch | Coverage tile transport is hard to unit-test; implementation should include profiling steps and a field-verification plan (next deployment). At minimum, document what to check after deploy |
| Workspace vs. project separation | OK | Config work entirely within the project repo |

### ADR Applicability

| ADR | Triggered | Notes |
|---|---|---|
| ADR-0001 (Adopt ADRs) | Watch | If the chosen fix involves a non-obvious tradeoff (e.g., raising `maximum_packet_size` changes fragmentation behavior across all topics, not just coverage tiles), record the decision. A config comment is acceptable for simple parameter changes. |
| ADR-0008 (ROS 2 conventions) | OK | Parameter changes use existing udp_bridge param names (`maximum_bytes_per_second`, `maximum_packet_size`, `period`) — no new conventions introduced |

### Consequences

- If `maximum_packet_size` changes: must update **all** udp_bridge configs across the repo (currently set in `bizzyboat.yaml` AND `operator.yaml` AND `remote.yaml` — all at 1000). Change to `maximum_packet_size` applies globally per node, not per topic/connection.
- If wifi route added for `coverage_tiles`: operator.yaml also needs the inbound `coverage_requests` mirrored on wifi (these two configs are a stated pair). Also assess: wifi already carries ffmpeg video streams (1.5 MB/s cap shared); adding tile delivery there needs a budget check.
- If VPN cap raised: assess what else shares the 1.2 MB/s budget (sidescan images, video streams, costmap window, etc.) to ensure no starvation.
- If `period` tuning or queue changes: confirm interaction with CAMP's request-driven pattern (tiles are silent until CAMP requests them, per the config comment).

### Recommendations

- **Profile before fixing**: before choosing a solution, measure actual level-11 tile sizes from a recent deployment bag (or reconstruct from the 2026-07-23 session). The 2026-07-23 log notes tiles were not arriving; a tile-size estimate drives the choice between raising the rate cap vs. changing packet size vs. reducing tile detail.
- **Persist the workaround as an interim step**: raising VPN `maximum_bytes_per_second` from 1200000 to 1500000 (matching the wifi cap) is low-risk and immediately prevents the recurrence. Commit this as a separate, clearly-labelled interim change while the deeper investigation runs.
- **Evaluate wifi routing for coverage_tiles explicitly**: the log notes tiles are VPN-only; adding the wifi route (which has the same 1.5 MB/s cap but a different physical path) gives redundancy and avoids single-route failure. Needs `operator.yaml` + `bizzyboat.yaml` changes in sync.
- **Do not raise `maximum_packet_size` without measuring the impact on other topics**: at 1000 bytes, all topics fragment. Raising this globally changes fragmentation behavior for safety-critical topics (command, heartbeat) too. Isolate the tile-specific problem first.

### Actions
- [ ] Capture the decision rationale for whichever fix approach is chosen (config comment or ADR)
- [ ] Update both `bizzyboat.yaml` and `operator.yaml` together for any coverage-tile routing or rate changes
- [ ] Profile actual tile sizes from deployment data before selecting the final fix
- [ ] Document the field-verification plan (what to check at next deployment to confirm the fix held)

## Plan Authored
**Status**: complete
**When**: 2026-07-31 19:10 +00:00
**By**: Claude Code Agent (Claude Sonnet)

**Plan**: `.agent/work-plans/issue-389/plan.md` at `a39c86b`
**Branch**: feature/issue-389 at `a39c86b`
**Phases**: single

### Open questions
- [ ] Should `period: 0.5` (2 tiles/s) stay or tighten to `period: 1.0` for safety margin — tradeoff vs. live operator responsiveness?
- [ ] Should WiFi coverage tile delivery be conditional on link quality (site-specific), or unconditional (default-on when WiFi up)?

## Plan Review
**Status**: complete
**When**: 2026-07-31 19:07 +00:00
**By**: Claude Code Agent (Claude Opus)
<!-- Independence: the ## Plan Authored entry shares the name "Claude Code Agent"
     (all workspace agents do), but this is a fresh-context, independently-dispatched
     review by a different model (Opus vs the Sonnet planner). Treated as independent;
     no author-self-review annotation. -->

**Plan**: `.agent/work-plans/issue-389/plan.md` at `ea2cbc7`
**PR**: PR-less (`--issue` mode)
**Verdict**: approve-with-suggestions

### Findings
- [ ] (suggestion) Principles Self-Check cells contradict the revised approach — still cite "both config files updated together", "WiFi budget impact", "0.5 period / ≤2 tiles/s", and "WiFi route is additive redundancy" (all cut/changed) — `plan.md:87`, `plan.md:89`
- [ ] (suggestion) review-issue's "profile actual tile sizes" action is deferred to field verification rather than done pre-implementation; the `period: 1.0` choice stays unvalidated until the next deployment, so step 4 is load-bearing — `plan.md:63`, `plan.md:50`

### Verified against source (no finding — recorded so downstream needn't re-check)
- `coverage_tiles` publishes `marine_interfaces::msg::SonarVisualizationTile` (cube_bathymetry_node.cpp:396), **not** a GridMap — the plan's comment correction (`plan.md:45`) is accurate.
- GGGS tile is a fixed 960×960 cells (`cellColumnCount()` "always 960"), depth = int16 → 960×960×2 B ≈ 1.75 MB worst case — the plan's link-budget upper bound (`plan.md:13`) is validated, not merely asserted.

### Next step
Lifecycle: **Plan Review** → **implement** → **review-code**. Verdict is
approve-with-suggestions; the two suggestions are non-blocking (finding 1 is a
plan-doc consistency cleanup the implementer can fold in while editing; finding 2
is a field-verification note). Implementation may proceed against
`bizzyboat_project11/config/bizzyboat.yaml`.

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-07-31 19:23 +0000
**By**: Claude Code Agent (Claude Opus)
**Verdict**: approved

**Branch**: feature/issue-389 at `17ce3e7`
**Mode**: pre-push
**Depth**: Standard (reason: config touching a shared VPN link budget + a documented file-pair consequence)
**Must-fix**: 0 | **Suggestions**: 1
**Round**: 1 | **Ship**: recommended — no must-fix; change is twice-field-proven, arithmetic sound, plan-adherent, operator.yaml correctly unchanged by design

Config-only change (`bizzyboat.yaml`): VPN `maximum_bytes_per_second` 1200000→1500000, `coverage_tiles period` 0.5→1.0, plus link-budget/rationale/field-check comments. Verified: YAML parses (yamllint absent, python yaml.safe_load OK); link-budget arithmetic sound (960×960×2 = 1,843,200 B ≈ 1.75 MiB > 1,500,000 B cap); issue refs consistent (#389/#287/cube_bathymetry#112) and match plan; `coverage_tiles` present in both `topics_list` and `topics`; operator.yaml advertises `coverage_requests` (inbound request path) and is unaffected by this outbound-only tile-rate/cap change. Two fresh-context Claude adversarial lenses (A logic, B systemic) corroborated; their comment-enrichment "must-fix" items and speculative CAMP-ingest/burst concerns dropped by the silence filter (already covered in-config / answered by field evidence). Local specialist skipped (--no-local, workspace#590); Copilot off (default).

### Findings
- [x] (suggestion) Optional: add explicit "don't lower `period` below 1.0 without raising cap / merging cube#112" guard line — `bizzyboat_project11/config/bizzyboat.yaml:356` (implemented pre-publish, commit `5c0a082`)

## Integrated Review
**Status**: complete
**When**: 2026-07-31 16:05 -04:00
**By**: Claude Code Agent (Claude Fable 5)

**PR**: #403 at `5c0a082`
**Sources**: 2 (Copilot R1 @ `5c0a082`, CI rollup)
**Cross-source confirmations**: 0
**CI**: all-pass (build-and-test green 2m58s)

All three Copilot comments valid, all documentation-precision class, fixed
in commit `7fc81af`:

### Findings
- [x] (suggestion, Copilot) link-budget comment conflated MiB/MB and
  understated worst case — now 1,843,200 B (~1.84 MB) in bytes against the
  1,500,000 B/s cap — `bizzyboat_project11/config/bizzyboat.yaml`, plan.md
- [x] (suggestion, Copilot) `queue_size` incorrectly framed as part of the
  offered-load arithmetic — reworded (buffers only, rate unchanged) —
  `.agent/work-plans/issue-389/plan.md`
- [x] (suggestion, Copilot) implemented guard-line suggestion still unticked
  in the pre-push entry — ticked with the implementing commit noted —
  `.agent/work-plans/issue-389/progress.md`

### False positives
- (none)

## Integrated Review
**Status**: complete
**When**: 2026-07-31 16:35 -04:00
**By**: Claude Code Agent (Claude Fable 5)

**PR**: #403 at `95b77ab`
**Sources**: 2 (Copilot re-review @ `95b77ab` — suppressed comments only, CI rollup)
**Cross-source confirmations**: 0
**CI**: all-pass (build-and-test green 3m33s)

No visible comments; three suppressed. One valid (fixed), two won't-fix.

### Findings
- [x] (suggestion, Copilot suppressed) plan.md "Estimated Scope" still said
  "two config files" — stale after the WiFi cut; corrected to one —
  `.agent/work-plans/issue-389/plan.md`

### False positives
- (Copilot suppressed) asks to rephrase the Issue Review entry's
  "Current state" snapshot (GridMap wording, pinned line number) — that
  entry is a point-in-time record of what the review phase found; the
  timeline is append-only and the corrected facts live in plan.md and the
  config comments. Rewriting history would falsify the record.
- (Copilot suppressed) Issue Review consequences note lists bizzyboat
  configs but not izzyboat's for a hypothetical `maximum_packet_size`
  change — same append-only rationale; this PR deliberately does not touch
  `maximum_packet_size`, and the caution about its global effect is
  carried in plan.md ("affects all topics globally").
