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

**Remaining:** `/review-code` on PR #185; live `ros2 launch` smoke test (4 sea_surface
layers + reflex polygons + gating intact) before deploy. Depends on the composition
mechanism in seafloor PR #29 (`instance_params` arg).
