---
issue: 342
---

# Issue #342 — Retrofit M3 bag: TF offset + integer-second clock-skew correction

## Issue Review
**Status**: complete
**When**: 2026-06-27 00:00 +00:00
**By**: Claude Code Agent (Claude Sonnet)

**Issue**: #342
**Comment**: (best-effort post follows this entry; not recorded inline)
**Scope verdict**: well-scoped

### Actions
- [ ] Unit tests required (as specified): integer-second rounding, histogram (including ambiguous-band WARN at ±0.3–0.7 s), `bizzy/m3` TF translation rewrite, storage format + QoS preservation, and original recoverable from backup.
- [ ] Capture the PPS/integer-second correction rationale in the script docstring (why `round(offset)` is correct: PPS disciplines the sub-second fraction, whole-second jumps from mercat Windows clock drift).
- [ ] Handle both rosbag2 mcap bag directories and bare `.mcap` files — confirm sidescan precedent and adjust accordingly for the bare-file path.

## Plan Authored
**Status**: complete
**When**: 2026-06-27 00:00 +00:00
**By**: Claude Code Agent (Claude Sonnet)

**Plan**: `.agent/work-plans/issue-342/plan.md` at `132d60c`
**Branch**: feature/issue-342 at `132d60c`
**Phases**: single

### Open questions
- [ ] For bare `.mcap` output in the in-place path: confirm that `SequentialReader` can validate a freshly-written bare `.mcap` (open + read one message) without ROS middleware; if not, use file-size > 0 as the "fully written" heuristic instead. Implementer should test on a real boat bag before committing.

## Plan Review
**Status**: complete
**When**: 2026-06-27 20:53 +00:00
**By**: Claude Code Agent (Claude Opus)

**Plan**: `.agent/work-plans/issue-342/plan.md` at `132d60c`
**PR**: PR-less (--issue mode)
**Verdict**: approve-with-suggestions

### Findings
- [ ] (must-fix) Timing correction never names which topic(s) carry M3 detections — `stream()`/`correct_stamp` have no topic filter; sidescan precedent hardcodes targets (SONAR dict) and no M3 topic is defined in this repo's config. Pin the exact topic name(s). — `plan.md:48-54`
- [ ] (suggestion) No dedicated storage-format + QoS preservation test, though review-issue action #1 requires it; `test_stream_passthrough` checks message bytes, not round-tripped TopicMetadata/storage_id. — `plan.md:90`
- [ ] (suggestion) Bare-`.mcap` SequentialReader-validation open question is unresolved; it gates the in-place/backup atomicity guarantee — track before relying on in-place mode. — `plan.md:131-134`

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-06-27 21:25 +00:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: changes-requested

**Branch**: feature/issue-342 at `387d7e9`
**Mode**: pre-push
**Depth**: Deep (reason: 707 lines of new code ≥ 200; plan.md is a project-repo governance trigger)
**Must-fix**: 1 | **Suggestions**: 8
**Round**: 1 | **Ship**: continue — one real correctness gap on the default in-place path (bare `.mcap` → directory); address then re-review

Tests: 19/19 pass locally (pytest, jazzy sourced). Static analysis run (flake8 ament profile; package registers no lint test, so not CI-caught). Copilot off (not opted in). Reviewed against local `origin/jazzy` (fetch failed offline).

### Findings
- [x] (must-fix) Default in-place mode silently installs a *directory* bag at a bare `.mcap`'s original filename (verified: `.mcap` URI → rosbag2 directory bag); guard output-form ≠ input-form or require `--out` for bare files — `retrofit_m3_bag.py:260-266,308-327`
- [x] (suggestion) `validate_written` degrades to `size>0` on any reader exception; in destructive in-place mode a validation exception should abort, not fall back — `retrofit_m3_bag.py:158-178,321`
- [x] (suggestion) Two-rename in-place swap is non-atomic; SIGINT between renames leaves the bag only at `.orig` and the re-run guard then refuses — add rollback + recovery hint — `retrofit_m3_bag.py:311,326-327`
- [x] (suggestion) Input reader `rd` not released before the in-place rename (works on Linux; release for robustness) — `retrofit_m3_bag.py:317-327`
- [x] (suggestion) `AMBIG_HI=0.7` is dead (frac maxes at 0.5); behavior correct but constant + docstring "|frac| in [0.3,0.7]" mislead — `retrofit_m3_bag.py:89,102`
- [x] (suggestion) Stale `.tmp` from a SIGKILLed run blocks all future runs with no auto-clean/--force — `retrofit_m3_bag.py:309-312`
- [x] (suggestion) Histogram under `--offset N` records the forced value, undercutting its "validates the PPS assumption" claim — `retrofit_m3_bag.py:100,191`
- [x] (suggestion) Banker's-rounding direction at exactly n+0.5 untested; `test_correct_stamp_ambiguous_band` discards `n` — `test_retrofit_m3_bag.py:70-75`
- [x] (suggestion) flake8 ament profile (not run in this package's CI): unused `import os` (F401), plus D401/D403 docstring nits on test helpers — `test_retrofit_m3_bag.py:16,93,165`

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-06-27 21:41 +00:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: approved

**Branch**: feature/issue-342 at `adafe2a`
**Mode**: pre-push
**Depth**: Deep (reason: 795 lines of new code ≥ 200; plan.md is a project-repo governance trigger)
**Must-fix**: 0 | **Suggestions**: 1
**Round**: 2 | **Ship**: recommended — all 9 Round-1 findings resolved; 0 must-fix; remaining item is doc-only

Round-1 closure verified: bare-`.mcap`→bare-`.mcap` form preserved (`inplace_paths` + `_swap_in_place` single-segment extraction, `test_inplace_bare_mcap_stays_bare`); `validate_written` now fail-closed (no `size>0` fallback); in-place swap has try/except rollback from backup; `del rd` before swap; single `AMBIG_THRESHOLD=0.3`; `--force` for stale `.tmp`; histogram records measured `n`; `test_correct_stamp_half_rounds_to_even` + `test_storage_and_metadata_preserved` added. Tests: 22/22 pass (pytest, jazzy sourced; now CI-registered via `ament_add_pytest_test`). Static analysis: `ament_flake8` clean. Two disjoint-lens Claude Adversarial passes (A logic, B systemic/safety) found no new actionable bugs — flagged items (`del wr` finalization on Windows/networked FS, the inherent SIGKILL window in the FS swap, stale-`.orig` handling) are inapplicable to this Linux-only manual tool, already mitigated, or inherent-and-acceptable given the mandatory backup. Copilot off (not opted in). Reviewed against local `origin/jazzy` (94a9ea5; fetch failed offline — branch is pure additions, base unchanged).

### Findings
- [ ] (suggestion) `plan.md:148-151` still describes `validate_written` falling back to a `size>0` heuristic; the implementation intentionally dropped that fallback (Round-1 finding #2). Doc-only — update the plan to match the shipped fail-closed behavior. — `.agent/work-plans/issue-342/plan.md:148-151`
