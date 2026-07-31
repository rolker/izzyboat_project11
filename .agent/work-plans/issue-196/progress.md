---
issue: 196
---

# Issue #196 — Capture external-charger idle/maintenance current (~6.2 A, #186) + revisit power models

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-07-31 (see commit timestamps)
**By**: Claude Code Agent (Claude Fable 5)
**Verdict**: approved

**Branch**: feature/issue-196 at `52b1f6e`
**Mode**: pre-push
**Depth**: Standard (reason: 140 changed lines, docs-only)
**Must-fix**: 1 | **Suggestions**: 5
**Round**: 1 | **Ship**: recommended — sole must-fix (AC-efficiency inconsistency, cross-pass confirmed) and all suggestions addressed in `52b1f6e` before push

### Findings
- [x] (must-fix) AC-input amps derived from output watts at implicit 100% efficiency, inconsistent with the 90% used one sentence later — `bizzyboat_project11/docs/bizzyboat_power.md` AC-draw bullet (also analysis README); restated as ~8 A wall / ~850 W out, gross-vs-net DC split
- [x] (suggestion) 20.94 V cutoff reading is from a `source=mavros` row while the method claims fcu-only — attributed in README; fcu day-min 22.24 V after 85-min gap noted
- [x] (suggestion) mid-pack ~11–15 h band silently excluded the interrupted 06-17 event (~17 h pace) — now included
- [x] (suggestion) overnight-charge rule failed 1-of-3 observed events (06-27, ~21 h) — hedged with resting-voltage go/no-go backstop in both files
- [x] (suggestion) operator manual + performance doc still stated recharge time as unknown/unnumbered — measured ~15 h + pointer added
- [x] (suggestion) bare `#186`/`#196` refs don't autolink in repo markdown — converted to full links

## Integrated Review
**Status**: complete
**When**: 2026-07-31 (see commit timestamp)
**By**: Claude Code Agent (Claude Fable 5)

**PR**: #404 at `9947539`
**Sources**: 3 (Copilot R1 @ `9947539`, Local Review (Pre-Push) @ `52b1f6e`, CI rollup)
**Cross-source confirmations**: 0 (all 6 pre-push findings were closed at `52b1f6e`; Copilot's two comments are new)
**CI**: all-pass (build-and-test ✓, copilot-pull-request-reviewer ✓)

### Findings
- [ ] (suggestion, Copilot) 6.2 A charger reading could be misread as 120 VAC input current — label it as charger-reported DC output current (assumed) — `bizzyboat_project11/docs/bizzyboat_power.md`
- [ ] (suggestion, Copilot) README cites only the dev-machine synced CSV path; the producing script `bizzyboat_project11/scripts/battery_logger.sh` writes `~/data/logs/bizzy_battery/` on gabby — cite both + the logger script — `docs/analysis/2026-07-31/README.md`

### False positives
- none
