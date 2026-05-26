---
issue: 169
---

# Issue #169 — Data analysis umbrella for #160 (2026-05-22 deployment) — standard checklist + sub-issue tracker

## Integrated Review
**Status**: complete
**When**: 2026-05-26 00:51 -0400
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))

**PR**: #177 at `419e9ac`
**Sources**: 1 — Copilot (R1 @ `3c9eecf`, R2 @ `419e9ac`); no prior local timeline (PR didn't go through plan-task/review-code)
**Cross-source confirmations**: 0
**CI**: all-pass (copilot-pull-request-reviewer: success)

### Findings
- [x] (low, Copilot R2) Broken relative link `bizzyboat_power.md` → should be `../bizzyboat_project11/docs/bizzyboat_power.md` — `docs/roadmap.md:160`
- [x] (low, Copilot R1) §8 header says milestone snapshots + annunciator correlation "remain", but §8.D/§8.F are present and ✅ — `docs/analysis/2026-05-22/findings.md:51`
- [x] (low, Copilot R2) §6.2 delegation note ("leaving XTE-per-direction to #164, not duplicating") contradicts §12 (which performed it) and #164 being closed — `docs/analysis/2026-05-22/findings.md:171`
- [x] (low, Copilot R2) Stale note "`docs/roadmap.md` is not edited here / separate PR on your word" — the roadmap IS edited in this PR (commit `419e9ac`) — `docs/analysis/2026-05-22/findings.md:397`
- [x] (low, Copilot R2) §1 power caveat says ±~20%; inconsistent with `bizzyboat_power.md`/#167 which use ±30% — `docs/analysis/2026-05-22/findings.md:43`

### Findings
- [x] (low, Copilot R2) Broken relative link `bizzyboat_power.md` → should be `../bizzyboat_project11/docs/bizzyboat_power.md` — `docs/roadmap.md:160`
- [x] (low, Copilot R1) §8 header says milestone snapshots + annunciator correlation "remain", but §8.D/§8.F are present and ✅ — `docs/analysis/2026-05-22/findings.md:51`
- [x] (low, Copilot R2) §6.2 delegation note ("leaving XTE-per-direction to #164, not duplicating") contradicts §12 (which performed it) and #164 being closed — `docs/analysis/2026-05-22/findings.md:171`
- [x] (low, Copilot R2) Stale note "`docs/roadmap.md` is not edited here / separate PR on your word" — the roadmap IS edited in this PR (commit `419e9ac`) — `docs/analysis/2026-05-22/findings.md:397`
- [x] (low, Copilot R2) §1 power caveat says ±~20%; inconsistent with `bizzyboat_power.md`/#167 which use ±30% — `docs/analysis/2026-05-22/findings.md:43`

### False positives
- (none)

## Integrated Review
**Status**: complete
**When**: 2026-05-26 10:02 -04:00
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))

**PR**: #177 at `73360cc`   (round 2)
**Sources**: 2 — Copilot R3 @ `73360cc`; prior Integrated Review round 1 @ `419e9ac`
**Cross-source confirmations**: 0 (live findings are Copilot-only at head; no `Local Review` entry at `73360cc`)
**CI**: all-pass (copilot-pull-request-reviewer: success)

### Findings
- [ ] (low, Copilot R3) §8 ERROR table verdict + §8.C prose label this run's 534 resend give-ups "structural ~30% resend", but §7 measured **0.7% of wire this deployment** (the ~30% is the prior 2026-05-01/05-18 calibration) — qualify so §8 doesn't contradict §7 — `docs/analysis/2026-05-22/findings.md:60,89`
- [x] (low, Copilot R3) Dev-log "Post-mission analysis" calls the no-auto-failsafe "by design" (settled), but findings §8.A kept "intentional config vs oversight" as an open question — *resolved 2026-05-26*: Roland confirmed the battery failsafe is **intentionally disabled** for the drain test; closed the open question in §8.A + §10 register + §Open questions, dev-log "by design" is now accurate — `docs/analysis/2026-05-22/findings.md:73`, `docs/logs/2026/2026-05-22_dev_logs.md:277`

### Resolved in prior round (verified at `73360cc`)
- All 5 round-1 findings (above, @ `419e9ac`) confirmed fixed in current code; the head-SHA review did not re-raise them.

### False positives
- (none)
