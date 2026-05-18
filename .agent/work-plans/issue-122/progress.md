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
- [ ] **Deferred (optional)** suggestions from the self-review:
  expose `min_utc_status` / `require_utc_sync` as launch args in
  `bizzyboat_project11/launch/zda_launch.py`; clean up dead
  starboard/port VPN `_info`/`_raw` mappings for symmetry; tighten
  PR body framing of the QoS rule (consistency with udp_bridge#16 /
  camp#51 wording).
- [ ] **Blocked on** [`rolker/udp_bridge#16`](https://github.com/rolker/udp_bridge/pull/16)
  (another agent is finishing review/merge). Once that merges,
  optional final pass through this PR + take out of draft + merge.

### Cross-repo dependency status
- [`rolker/marine_tools#9`](https://github.com/rolker/marine_tools/pull/9): ✅ merged 2026-05-18
- [`rolker/udp_bridge#16`](https://github.com/rolker/udp_bridge/pull/16): in progress (other agent)
- [`rolker/camp#51`](https://github.com/rolker/camp/pull/51): ✅ merged 2026-05-18
