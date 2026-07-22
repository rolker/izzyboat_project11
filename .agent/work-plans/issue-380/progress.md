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
