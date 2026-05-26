---
issue: 162
---

# Issue #162 — Battery annunciator stays green at <BATT_LOW_VOLT — threshold-to-color mapping broken

## Integrated Review
**Status**: complete
**When**: 2026-05-26 10:36 -04:00
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))

**PR**: #179 at `3303189`
**Sources**: 1 (Copilot R1 @ `3303189`)
**Cross-source confirmations**: 0
**CI**: all-pass (copilot-pull-request-reviewer: success)

No prior local-review timeline existed for #162 (no `progress.md` before this
entry), so the single Copilot review is the only review source.

### Findings
- [ ] (deployment-dependency, triage) PR #179's config depends on the
  rqt_annunciator engine change in `rolker/rqt_operator_tools#35` (PR #36),
  which is **OPEN / unmerged**. The `value_key` + `thresholds` + `{:.2f} V`
  keys are only understood by the #36 engine. #179 must not merge/deploy
  before #36 lands and a rebuilt `rqt_operator_tools` is on the operator
  station — otherwise the row falls back to pre-#36 behavior (and Copilot's
  format-on-string failure could become real on the old engine). — `bizzyboat_project11/config/bizzyboat_annunciator.yaml`

### False positives
- (Copilot) `bizzyboat_annunciator.yaml:40` — claimed `{:.2f}` format on the
  `diagnostic_msgs/KeyValue.value` string "may error out (Unknown format code
  'f' for str)". The consuming engine
  (`rqt_annunciator/config_model.py::evaluate_diagnostic`, `has_thresholds`
  path used by this row) converts the selected KeyValue to float at
  `val = float(selected)` — returning ERROR + `Voltage?` flag if non-numeric —
  *before* `self.format.format(val)` applies `{:.2f}` to the float. That format
  call is additionally wrapped in `try/except (ValueError, TypeError,
  IndexError, KeyError)` → `str(val)` fallback. Tested in
  `test_config_model.py` with `value_key='Voltage'`, `_KV('Voltage','22.4')`
  (a string) and `{:.2f}` format. With the #36 engine the failure mode cannot
  occur. (Copilot's caveat "unless the engine explicitly converts to float" is
  satisfied by the engine.)
