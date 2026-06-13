---
issue: 257
---

# Issue #257 — BizzyBoat: record + bridge Garmin sidescan nadir_depth and water_temperature

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-06-13 11:10 -04:00
**By**: Claude Code Agent (Claude Fable 5)
**Verdict**: approved
**Branch**: feature/issue-257 at `dc7514f`
**Mode**: pre-push
**Depth**: Standard (config-only, boat deployment; sole gate — Copilot quota exhausted until end of June 2026)
**Must-fix**: 0 | **Suggestions**: 1 (flagged for operator decision)

Fresh-context adversarial review of the config diff. Verified list↔map consistency
(wifi 51/51, vpn 38/38, zero mismatch), source paths resolve to the real driver
topics (cross-checked vs node.py publishers and the sonar_logger absolute paths),
no duplicate keys, QoS best_effort matches, YAML valid, recorder script bash -n clean.

### Findings
- [ ] (suggestion) WiFi sidescan imagery adds ~150 KB/s (~10% of the 1.5 MB/s budget) alongside the camera streams; the bridge's drop-fairness under saturation isn't expressed in config. Kept full-rate (operator explicitly wants live imagery; safety topics are tiny). Flagged in the PR for Roland's link-budget call — easy knob is a per-topic `period` on the wifi imagery if margin is tight.

Out of scope (pre-existing): the sonar_logger comment says "GCV-20" while the fleet uses GCV-10/20 — unrelated to this diff.
