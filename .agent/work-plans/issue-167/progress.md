---
issue: 167
---

# Issue #167 — Comprehensive cross-deployment power-usage analysis (2026-05-19 → 21 → 22 single charge cycle)

## External Review
**Status**: complete
**When**: 2026-05-25 16:49 -0400
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))

**PR**: #176 at `cea7bfb`
**Reviews**: 2 Copilot review(s), 4 inline comments — **4 valid, 0 false positives**; 0 human, 0 conversation
**CI**: none substantive (draft PR; only Copilot-reviewer runs)

### Actions
- [x] **BATT_MONITOR (line 13):** doc says `4` (inherited); `bizzyboat_fcu_custom.param` + 2026-05-21 live snapshot = `3` (voltage-only, `BATT_CURR_PIN -1`). Update to "`BATT_MONITOR 3` (was `4` inherited from IzzyBoat)".
- [x] **Internal contradiction (line 64):** "Power model / limits" bullet still cites "~10× SOC dependence"; reconcile with corrected §B (mild; R_int ≈ stable; PWM-dominant).
- [x] **R_int clarity (line 31):** note 12.9 mΩ = steady-state (0.864 V @ 67 A, used by `power.py`) vs the 2026-04-27 log's 25 mΩ = peak transient sag (1.7 V @ 67 A).
- [x] **(minor) Dangling ref (line 7):** make `bizzyboat_performance.md` a link to PR #172.
