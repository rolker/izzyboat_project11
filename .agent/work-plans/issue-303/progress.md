---
issue: 303
---

# Issue #303 — Bizzyboat sidescan URDF grazing tilt (#185 Stage 2)

## Plan Authored
**Status**: complete
**When**: 2026-06-21 00:00 +00:00
**By**: Claude Code Agent (Claude Sonnet)

**Plan**: `.agent/work-plans/issue-303/plan.md` at `af04e2e`
**Branch**: feature/issue-303 at `af04e2e`
**Phases**: single

### Open questions
- [x] Verify call sites of `garmin_sidescan` — only `bizzyboat.urdf.xacro`, uses keyword args; safe.
- [ ] Confirm marine_sidescan_mosaic (#200) depends only on `+X` forward (not `+Z` horizontal) before merging.

## Plan Review
**Status**: complete
**When**: 2026-06-21 06:20 +00:00
**By**: Claude Code Agent (Claude Opus)

**Plan**: `.agent/work-plans/issue-303/plan.md` at `af04e2e`
**PR**: PR-less (`--issue` mode; `gh` unauthenticated — issue context read from plan's captured Context)
**Verdict**: approve-with-suggestions

Mechanism verified independently: port rpy `${-pi/2 - g}` → child `+Z=[0,cos g,−sin g]`, `+X=[1,0,0]`;
for `g=62.5°` → `[0,0.462,−0.887]` (matches plan's TF check; +X-forward preserved, so #200 heading
extraction is safe). Single caller (`bizzyboat.urdf.xacro:268`, keyword args) confirms the defaulted
param is non-breaking. Scope/file-targeting/ADR-0008/REP-103 all good. Independent review (plan
authored by Sonnet, reviewed by Opus) — no self-review annotation despite shared agent name.

### Findings
- [ ] (must-fix) Reconcile contradictory default derivation before writing header — Context says sidescan fires "20–30° below horizontal" but sets default to 62.5° via `90 − fan/2`; `fan/2`=27.5° is the horizontal-aligned reading. Differ by 35°. — `plan.md:11`
- [ ] (suggestion) Open question on #200 depending only on `+X` (not `+Z` horizontal) still unchecked; confirm before merge — `plan.md:105`
- [ ] (suggestion) Documented TF check uses `name:=sidescan`; deployed frame is `bizzy/garmin_sidescan_port` — use real frame name — `plan.md:57`

## Implementation
**Status**: complete
**When**: 2026-06-21 07:10 +00:00
**By**: Claude Code Agent (Claude Opus)

**Plan**: `.agent/work-plans/issue-303/plan.md` (followed, with the 3 review must-fixes folded in)
**Branch**: feature/issue-303 at `7ed439e`
**Phases**: single

### What changed
- `bizzyboat_project11/urdf/sensors/sidescan.xacro`:
  - Added `grazing_deg:=62.5` param to the `garmin_sidescan` macro.
  - `_port` rpy `${-pi/2} 0 0` → `${-pi/2 - grazing_deg * pi / 180} 0 0`.
  - `_starboard` rpy `${pi/2} 0 0` → `${pi/2 + grazing_deg * pi / 180} 0 0`.
  - `_down` unchanged; +X forward preserved on both side channels.
  - Removed the PLACEHOLDER header; documented the 62.5° rationale (90 − fan/2,
    half-fan off nadir → inner fan edge at nadir, clean tiling vs `_down`), the
    ~20–30° side-imaging alternative, and a manual `tf2_echo` check.
- `.agent/work-plans/issue-303/plan.md`: synced to match (self-consistent 62.5
  rationale, real-frame TF check, resolved #200 open question).

### Verification
No xacro unit-test harness exists; verified by rendering the macro under ROS 2
Jazzy xacro:
- `_to_garmin_sidescan_port` rpy = `-2.661627…` = `-(π/2 + 62.5°)` ✓
- `_to_garmin_sidescan_starboard` rpy = `+2.661627…` ✓
- `_to_garmin_sidescan_down` rpy = `π 0 0` (unchanged) ✓
- port child +Z in `bizzy/base_link` = `[0, 0.462, -0.887]` (62.5° depression) ✓
- port child +X = `[1, 0, 0]` (forward) ✓
The documented `tf2_echo bizzy/base_link bizzy/garmin_sidescan_port` is the
manual field check (matches the rendered values above).

### Review must-fixes folded in
1. Reconciled the contradictory rationale — header + plan now state 62.5° as
   half-fan-off-nadir (inner fan edge at nadir); 20–30° is named only as an
   alternative, never as the default's justification.
2. TF check now uses the real frame names produced by the macro
   (`bizzy/base_link` → `bizzy/garmin_sidescan_port`), not the placeholder
   `name:=sidescan` / `bizzy/sidescan_port`.
3. #200 open question resolved: #200 reads the +Z boresight via
   `ecefPoseToGeoBeam` and +X stays forward, so it consumes the tilted
   boresight directly — no breakage.

### Open questions
- None remaining (both prior questions resolved).

### Next step
Code review of `feature/issue-303` (commit `7ed439e`), then PR.
