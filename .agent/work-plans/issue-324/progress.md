---
issue: 324
---

# Issue #324 — bridge rqt_boat_state panel topics to operator

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-06-24 13:20 +00:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: approved

**Branch**: feature/issue-324 at `72d9dd9`
**Mode**: pre-push
**Depth**: Light (reason: 1 config file, +36 lines, no override-trigger/Deep triggers)
**Must-fix**: 0 | **Suggestions**: 3
**Round**: 1 | **Ship**: recommended — no must-fix findings; only optional cell-link throttling suggestion

### Findings
- [ ] (suggestion) `mavros_rc_in`/`mavros_rc_out` (~10 Hz) added unthrottled to the minimal 300 KB/s cell link; consider a `period:` cap — `bizzyboat_project11/config/bizzyboat.yaml:366-370,395-399`
- [ ] (suggestion) Same RC streams unthrottled on wifi/vpn — consistent and within budget, noted for completeness — `bizzyboat_project11/config/bizzyboat.yaml:116-120,250-254`
- [ ] (suggestion) On-water: confirm mavros `rc_io` plugin is publishing `mavros/rc/in`+`mavros/rc/out`; if inactive the entries forward nothing (harmless)
