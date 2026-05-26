---
issue: 171
---

# Issue #171 — Operator annunciator misses battery/LVD, sound-speed, and FCU-error status

## Plan Authored
**Status**: complete
**When**: 2026-05-26 10:30 -04:00
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))

**Plan**: `.agent/work-plans/issue-171/plan.md` at `c9b6b98`
**Mode**: field-execution prep — config to be verified/tuned/committed on the operator station during a deployment, then reconciled via PR
**Phases**: single

### Open questions
- [ ] Battery threshold values: 23.0/21.5 (FCU params) vs #171's ~22.5/21.5 — tune in the field
- [ ] Battery indicator mechanism: diagnostics+value_key (needs rqt_operator_tools#35 deployed) vs topic-source fallback (works now) — decide at field time by what's deployed
