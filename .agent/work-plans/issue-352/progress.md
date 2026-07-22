---
issue: 352
---

# Issue #352 — Version-control the incremental Massabesic store-build script

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-07-02 12:10 -04:00
**By**: Claude Code Agent (Claude Fable 5)
**Verdict**: changes-requested
**Branch**: feature/issue-352 at `1736377`
**Mode**: pre-push
**Depth**: Standard (reason: authoritative-data-product script, full semantic rework, ~200 lines)
**Must-fix**: 4 | **Suggestions**: 8
**Round**: 1 | **Ship**: continue — must-fixes include interruption-safety design gaps, worth a re-read after the fix round

### Findings
- [ ] (must-fix) 1h in-place write to live store, no staging/sentinel — interrupted run indistinguishable from complete — `build_massabesic_store.sh:153` (Lens B)
- [ ] (must-fix) partial reference layer silently treated as complete on re-run — `build_massabesic_store.sh:103` (Lens A+B cross-confirmed)
- [ ] (must-fix) legacy chart/processed store accepted as --out target → double-counted layers — `build_massabesic_store.sh:93` (Lens B)
- [ ] (must-fix) zero-bags case dies silently: grep -c exit 1 under set -e before the friendly error — `build_massabesic_store.sh:143` (Lens A)
- [ ] (suggestion) no flock — concurrent invocations interleave writes (TOCTOU) — `:93` (Lens B)
- [ ] (suggestion) anchor topic greps (name: /tf$; full detections topic); warn on mcap-without-metadata bags — `:137` (Lens A+B cross-confirmed)
- [ ] (suggestion) no free-disk preflight on a 99%-full machine — `:75` (Lens B)
- [ ] (suggestion) success banner without post-run tile-count check — `:168` (Lens B)
- [ ] (suggestion) option arms lack value guards (dangling --out dies raw under set -u) — `:55` (Lens A)
- [ ] (suggestion) bag list as scalar word-splitting; use bash array — `:129` (Lens A)
- [ ] (suggestion) provenance vocabulary: platform/sensor should be bizzyboat/kongsberg-m3 per ADR-0005/0007; unify campaign id style — `:166` (Governance F2)
- [ ] (suggestion) PR body must cover: #352 scope pivot rationale (#96 supersession), import_bag-vs-batch_regen, script-not-installed intent, retire uncontrolled ~/build_massabesic_store.sh copies (Governance F1/F3/F4)

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-07-02 12:55 -04:00
**By**: Claude Code Agent (Claude Fable 5)
**Verdict**: approved
**Branch**: feature/issue-352 at `1090133` (+ round-2 fix commit)
**Mode**: pre-push
**Depth**: Light re-read (reason: round-2 verification of mechanical fixes)
**Must-fix**: 1 (fixed in-round) | **Suggestions**: 2 (both applied)
**Round**: 2 | **Ship**: recommended — round-1 fixes verified correct; the one new must-fix (mv nesting into a tile-less reference/) fixed, guard behavior-tested; suggestions (BS-store lock+df, INT/TERM trap) applied

### Findings
- [x] (must-fix) mv nests staged reference into pre-existing empty reference/ dir → blunder gate silently absent — fixed: up-front refusal + mv -T — `build_massabesic_store.sh:186`
- [x] (suggestion) lock + disk preflight covered only the bathy store — second flock + df on --bs-out — `:108`
- [x] (suggestion) EXIT trap misses SIGINT/SIGTERM → orphaned .ref_stage dirs — trap EXIT INT TERM — `:179`
