---
issue: 241
---

# Issue #241 — Field import: unh_echoboats_project11 battery monitoring (2026-06-09)

## Integrated Review
**Status**: complete
**When**: 2026-06-09
**By**: Claude Code Agent (Claude Opus 4.8 (1M context))

**PR**: #242 at `5b9e8e3`
**Sources**: 2 (Copilot @ `5b9e8e3`, import pre-review in issue #241 / PR #242 body)
**Cross-source confirmations**: 1
**CI**: no CI configured (copilot check success)

### Findings
- [ ] (cross-confirmed) `current_a` CSV column blank for FCU and `0`/NaN/misleading from MAVROS — no current meter on BizzyBoat; document or drop the column — `bizzyboat_project11/scripts/battery_logger.sh:18`
- [ ] (bug, Copilot) `percentage` cleaned only for NaN; out-of-range (MAVROS emits -0.01 when battery_remaining==-1) → negative/garbage remaining_pct; blank values outside [0,1] before *100 — `bizzyboat_project11/scripts/mavros_battery.sh:86`
- [ ] (nit, Copilot) grammar "An flock" → "A flock" in header comment — `bizzyboat_project11/scripts/battery_logger.sh:21`

### False positives
- None — all three Copilot comments valid.
