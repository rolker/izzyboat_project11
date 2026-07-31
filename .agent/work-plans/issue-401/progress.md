---
issue: 401
---

# Issue #401 — Roadmap: OTH sections stale — costmap display, concurrent links, OTH validation are delivered

## Integrated Review
**Status**: complete
**When**: 2026-07-31 17:20 -04:00
**By**: Claude Code Agent (Claude Fable 5)

**PR**: #402 at `bc61522`
**Sources**: 2 (Copilot R1 @ `bc61522`, CI rollup)
**Cross-source confirmations**: 0
**CI**: all-pass (build-and-test + copilot-review green)

### Findings
- [x] (suggestion, Copilot, verified against operator.yaml) roadmap says the
  safety-critical uplink is "pinned to the cell path" — the config carries
  `command`/`joystick_helm` redundantly on wifi+vpn+cell; only the cell
  *tunnel* is WAN-pinned (router-level). Reword the #145 bullet to say
  redundant carriage across all three paths — `docs/roadmap.md:140`

### False positives
- (none)

## Integrated Review
**Status**: complete
**When**: 2026-07-31 17:50 -04:00
**By**: Claude Code Agent (Claude Fable 5)

**PR**: #402 at `523cb21`
**Sources**: 2 (Copilot re-review @ `523cb21` — suppressed only, CI rollup)
**Cross-source confirmations**: 0
**CI**: all-pass (build-and-test green 3m46s)

### Findings
- [x] (suggestion, Copilot suppressed) roadmap conflated the two #389 field
  workarounds — 07-23 was a max-data raise, 07-29 a return-rate override to
  1.5 MB/s per the gabby log; bullet now names both — `docs/roadmap.md:164`

### False positives
- (none)
