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
