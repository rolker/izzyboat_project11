---
issue: 122
---

# Issue #122 — Field import: unh_echoboats_project11 (2026-05-01)

## External Review
**Status**: complete
**When**: 2026-05-18 20:25
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))

**PR**: #123 — 1 Copilot review (4 inline comments) + 1 self-review
(conversation, multi-specialist). Triage covered both rounds.
2 valid must-fix + 2 false positives + 3 optional suggestions.
**CI**: no CI configured on this repo.

### Actions
- [x] **Merge jazzy in** (8 commits behind: PRs #125, #127 + the README
  field-session-logging guardrails). Clean merge, no conflicts.
- [x] **Fix** Copilot #3 (`docs/logs/2026/2026-05-01_salmon_logs.md:6`)
  and #4 (`docs/logs/2026/2026-05-01_gabby_logs.md:6`): replace
  `**Deployment**: TBD` with `**Deployment**: [#121](link)` matching
  the spec in `docs/logs/README.md:51` and the markdown link style
  used by the existing 2026-04-27, 2026-04-29, and 2026-05-01 dev
  logs (commit `aa8c894`).
- [x] **Reply + resolve** Copilot #1 (`bizzyboat.yaml:167` topics_list
  asymmetry) and #2 (`bizzyboat.yaml:195` aft `_info` mapping). Both
  are false positives: the asymmetry is pre-existing on jazzy, and
  `topics:` is a lookup pool that's not 1:1 with `topics_list`.
  Replies posted; threads resolved via GraphQL `resolveReviewThread`.
- [x] **Suggestion 3** — expose `zda_min_utc_status` /
  `zda_require_utc_sync` as launch args in
  `bizzyboat_project11/launch/zda_launch.py` + wrap typed
  substitutions (`baud`, `min_utc_status`, `require_utc_sync`) with
  `ParameterValue(value_type=...)` so rclpy's strict typing is
  honoured without relying on launch-side YAML coercion (commit
  `f7d43c5`).
- [x] **Suggestion 4** — drop dead starboard/port `_info`/`_raw`
  mappings from the VPN `topics:` block; they were never in
  `topics_list`. Replace with brief comments noting the uplink-budget
  rationale (commit `94ad894`).
- [x] **Suggestion 5** — PR body refreshed: added "Review-cycle
  follow-ups" section documenting `aa8c894` / `f7d43c5` / `94ad894`;
  refreshed cross-repo dependency table to reflect today's merges of
  `marine_tools#9` and `camp#51`. Body has no QoS-rule statement to
  invert (the inversion the self-review flagged must have been in an
  earlier body that already got cleaned up).
- [ ] **Blocked on** [`rolker/udp_bridge#16`](https://github.com/rolker/udp_bridge/pull/16)
  (another agent is finishing review/merge). Once that merges,
  final review pass through this PR + take out of draft + merge.

### Cross-repo dependency status
- [`rolker/marine_tools#9`](https://github.com/rolker/marine_tools/pull/9): ✅ merged 2026-05-18
- [`rolker/udp_bridge#16`](https://github.com/rolker/udp_bridge/pull/16): in progress (other agent)
- [`rolker/camp#51`](https://github.com/rolker/camp/pull/51): ✅ merged 2026-05-18
