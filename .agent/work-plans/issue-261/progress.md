---
issue: 261
---

# Issue #261 — BizzyBoat sim-aware core bringup for the Massabesic sim (no config duplication)

## Local Review
**Status**: complete
**When**: 2026-06-13 12:30 -0400
**By**: Claude Code Agent (Claude Opus 4.8 (1M context))
**Verdict**: approved (after fix)

**PR**: #264 at `c0510f2`
**Mode**: post-PR
**Depth**: Standard (reason: governance-relevant launch/config wiring)
**Must-fix**: 1 | **Suggestions**: 0

### Findings
- [x] (must-fix) Dead `chart_layer.tide_invalidate_threshold` override — sibling-scope from nav2, moot at chart-less Massabesic; removed — `config/bizzyboat_sim.yaml`
- Static nits (D100/I201/yaml-seq-indent) dropped: not enforced by package (no ament lint hooks) and match sibling style (`core_launch.py`, `ben_sim.yaml`).
- Copilot Adversarial unavailable (monthly quota exceeded); static + Claude adversarial were the gate.
