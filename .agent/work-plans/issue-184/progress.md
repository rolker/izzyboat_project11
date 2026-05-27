---
issue: 184
---

# Issue #184 — BizzyBoat nav2 instance overlay: sensor-rig + reflex

## Implementation Status (resume — 2026-05-26 21:44 -04:00)

The echoboats half of the seafloor#3 step-2 cutover. Branch `feature/issue-184`
@ `2a04fad`, PR #185 (draft).

**Done:**
- `bizzyboat_project11/config/nav2_overlay.yaml` — Bizzy's 4-OAK `sea_surface` rig +
  `collision_monitor` reflex response (polygons, observation_sources, reflex_cloud),
  moved out of the generic `echoboat_project11` base.
- `bizzyboat_project11/launch/nav_launch.py` — passes `model:=240` +
  `instance_params:=<overlay>` to the generic `nav2_bringup_launch.py`.

**Verified:** composed `base + 240 + this overlay` == today's `nav2_params.yaml`
(zero param diffs; Bizzy behavior preserved).

**⚠ DEPLOY-TOGETHER with rolker/seafloor_echoboat_project11#3 / PR #29** (the base
rig-agnostic reduction). Pulling one without the other drops Bizzy's rig/reflex.

**Remaining:** live `ros2 launch` smoke test (4 sea_surface layers + reflex polygons +
gating intact) before deploy — tracked on the deployment issue `unh_echoboats#186`.
Depends on the composition mechanism in seafloor PR #29 (`instance_params` arg).

## Local Review
**Status**: complete
**When**: 2026-05-27 12:10 -04:00
**By**: Claude Code Agent (Claude Opus 4.7 (1M context))
**Verdict**: approved

**PR**: #185 at `2a04fad` + working tree (boolean-consistency fixes)
**Mode**: post-PR
**Depth**: Standard (reason: deployed safety config — collision reflex + segmentation rig)
**Must-fix**: 0 | **Suggestions**: 3 (all fixed)

Both adversarial specialists ran clean. Claude (fresh-context) diffed the overlay
field-by-field against the pre-#29 monolithic `nav2_params.yaml` (`27d3de9^`) and confirmed a
**lossless restoration** — `local_costmap.plugins` re-includes `chart_layer`+`inflation_layer`
alongside the 4 sea_surface layers (critical given list-replace merge), all collision
polygon/reflex params identical, launch wiring + `<robot_namespace>` substitution ordering
correct. Copilot independently confirmed the same. Static analysis clean after the boolean fix.

### Findings
- [x] (suggestion, Copilot ×3 + yamllint) capitalized booleans (`True` / `'False'`) vs repo lowercase convention — fixed to `true` / `'false'` — `nav2_overlay.yaml`, `nav_launch.py:32`
- [ ] (note) `use_composition: 'false'` is safe — consumed via `IfCondition` (evaluator lowercases); the change is consistency-only.
