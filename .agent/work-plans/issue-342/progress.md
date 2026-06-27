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
