---
issue: 307
---

# Issue #307 — one-off retrofit_sidescan_bag.py for legacy bizzy sidescan bags

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-06-22 02:56 +00:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: approved

**Branch**: feature/issue-307 at `285e27b`
**Mode**: pre-push
**Depth**: Standard (reason: single new 115-line Python file; 50–199 changed lines)
**Must-fix**: 0 | **Suggestions**: 5
**Round**: 1 | **Ship**: recommended — no must-fix; happy-path correct (geometry matches URDF #305, QoS/storage preserved); 5 robustness/style suggestions are optional for a not-installed one-off

### Findings
- [ ] (suggestion) No try/finally; reader never closed and writer finalized via `del wr` — a mid-loop exception leaves a partial output bag that the startup existence-guard then blocks on re-run. Add explicit `rd.close()`/`wr.close()` in finally + remove partial output on failure (cross-confirmed Lens A + Lens B). — `bizzyboat_project11/scripts/retrofit_sidescan_bag.py:75,82,107`
- [ ] (suggestion) Silent no-op on legacy naming: if the expected sonar/tf topics are absent or lack the `bizzy/` prefix in an older bag, everything passes through and the script still prints success with `0 sonar, 0 tf` — exactly the "legacy bag" case this tool targets. Warn (or exit non-zero) when both rewrite counters are 0. — `bizzyboat_project11/scripts/retrofit_sidescan_bag.py:88-106`
- [ ] (suggestion) `sid = meta.storage_identifier or "mcap"` silently defaults to mcap; a sqlite3 legacy bag with an empty identifier would change storage format, contradicting the "storage format preserved" claim. Fail loudly or detect explicitly. — `bizzyboat_project11/scripts/retrofit_sidescan_bag.py:78`
- [ ] (suggestion) `/tf_static` messages with none of the three sidescan children are still deserialized + re-serialized (counted as `tf`) rather than passed through byte-for-byte; re-serialization is not guaranteed bit-identical. Passthrough when no child matches. — `bizzyboat_project11/scripts/retrofit_sidescan_bag.py:97-104`
- [ ] (suggestion) Static analysis: file diverges from the ament_flake8 style its sibling `scripts/` files already follow (double quotes ×47 Q000, semicolon multi-statements ×7 E702, one-line import E401, C408). No CI/pre-commit enforces it here, so non-blocking — flagged for in-directory consistency. — `bizzyboat_project11/scripts/retrofit_sidescan_bag.py`
