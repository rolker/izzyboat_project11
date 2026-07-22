---
issue: 380
---

# Issue #380 — Refine camera-mast URDF correction (pitch + roll) from 2026-07-20 recorded camera data

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-07-22 12:50 -0400
**By**: Claude Code Agent (Claude Fable 5)
**Verdict**: approved

**Branch**: feature/issue-380 at `df49a3b`
**Mode**: pre-push
**Depth**: Deep (reason: 889 changed lines / 13 files)
**Must-fix**: 0 | **Suggestions**: 7
**Round**: 1 | **Ship**: recommended — no must-fix; all 7 suggestions applied pre-push

### Findings
- [x] (suggestion) Repro block missing refine.py/plots2.py steps — `docs/analysis/2026-07-20/README.md` (applied)
- [x] (suggestion) refine.py hard-coded residuals not marked as manual snapshots — `scripts/refine.py` (applied)
- [x] (suggestion) Twist-mode divisor /2 vs /4 inconsistency — `scripts/solve.py` (applied)
- [x] (suggestion) elevation_hist.png had no generator script — `scripts/plots2.py` (applied)
- [x] (suggestion) Dead placeholder lines — `scripts/verify.py` (applied)
- [x] (suggestion) Deployment note: gabby rebuild+relaunch required or change is a silent no-op — `docs/analysis/2026-07-20/README.md` (applied)
- [x] (suggestion) flake8 F841/F401 unused var+imports — `scripts/latlon.py`, `scripts/refine.py` (applied)

## Integrated Review
**Status**: complete
**When**: 2026-07-22 13:38 -0400
**By**: Claude Code Agent (Claude Fable 5)

**PR**: #384 at `5098b5c`
**Sources**: 2 (Copilot R1 @ `5098b5c`, Local Review (Pre-Push) @ `5098b5c`)
**Cross-source confirmations**: 0 (Copilot's 4 findings all new; the 7 pre-push findings were applied before push)
**CI**: build-and-test pending at triage time (hosted runners degraded); ADR-0018 local attestation available

### Findings
- [x] (valid, Copilot) dead `if False` branches in timestamp packing — `docs/analysis/2026-07-20/scripts/geometry.py` (fixed in bf58f5b)
- [x] (valid, Copilot) unconditional `sys.argv[1]` → IndexError without usage — `docs/analysis/2026-07-20/scripts/verify_urdf.py` (fixed in bf58f5b)
- [x] (valid, Copilot) mast-comment reads as contradicting new per-camera trims — `bizzyboat_project11/urdf/bizzyboat.urdf.xacro` (clarified in bf58f5b)
- [x] (valid, Copilot) hard-coded user-specific bag path — `scripts/latlon.py` + `scripts/extract.py` (CAMERA_CAL_BAG env var, bf58f5b)

### False positives
- (none)

## Integrated Review
**Status**: complete
**When**: 2026-07-22 13:51 -0400
**By**: Claude Code Agent (Claude Fable 5)

**PR**: #384 at `38509bc`
**Sources**: 1 (Copilot R2 @ `38509bc`); CI build-and-test PASS @ `38509bc`
**Cross-source confirmations**: 0
**CI**: all-pass

### Findings
- [x] (valid, Copilot) latlon.py: no diagnostic when earth->map transform absent (Tem=None TypeError) — fixed
- [x] (valid, Copilot) extract.py: np.stack/caminfo crash on cameras with no frames — fail-fast added
- [x] (valid, Copilot) extract.py: KeyError without context on missing /tf_static frame — fail-fast added

### False positives
- (Copilot) geometry.py:63 dead `if False` branches — stale re-flag: removed in bf58f5b, verified absent at 38509bc
- (Copilot) verify_urdf.py:19 unconditional sys.argv[1] — stale re-flag: usage check added in bf58f5b, present at lines 14-16

## Integrated Review
**Status**: complete
**When**: 2026-07-22 14:16 -0400
**By**: Claude Code Agent (Claude Fable 5)

**PR**: #384 at `edf5057`
**Sources**: 1 (Copilot R3 @ `edf5057`, "generated 1 comment"); CI build-and-test PASS @ `edf5057`
**Cross-source confirmations**: 0
**CI**: all-pass

### Findings
- [x] (valid, Copilot) verify.py run(): slice step sub//4 is 0 for sub 1-3 -> ValueError — clamped to >=1

### False positives
- (Copilot, re-anchored threads) verify_urdf.py argv / latlon.py Tem / extract.py 2x fail-fast — all four are open threads carried forward from R1/R2; fixes verified present at edf5057 (bf58f5b, edf5057)
