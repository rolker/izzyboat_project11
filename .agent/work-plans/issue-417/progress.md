---
issue: 417
---

# Issue #417 — bizzyboat: enable helm capability-curve regulation + planner minimum_turning_radius 3 m

## Local Review (Pre-Push)
**Status**: complete
**When**: 2026-08-05 17:17 +00:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: approved

**Branch**: feature/issue-417 at `37aa020`
**Mode**: pre-push
**Depth**: Standard (reason: safety-relevant nav/helm config, cross-layer coupling to unh_marine_autonomy helm; small diff, no Deep trigger)
**Must-fix**: 0 | **Suggestions**: 2
**Round**: 1 | **Ship**: recommended — no Must-fix; capability_curve array validated against curvature_regulation.h contract, 3.0 m radius achievable (native at 1 kt, regulated to ~0.95 m/s from transit), helm feature #292 already merged to unh_marine_autonomy jazzy

### Findings
- [ ] (suggestion) Reversion banner "Nothing else to undo … the helm cap in config/bizzyboat.yaml" under-lists the new `capability_curve_*` block also added to bizzyboat.yaml; add it to the servo-reinstall reversion cross-reference. Residual risk is over-conservative turns only (regulation is monotone-safe, never widens the arc), not a hazard — `bizzyboat_project11/config/nav2_overlay.yaml:434-436`
- [ ] (suggestion, optional) No CI/mechanism catches a config-vs-helm-binary mismatch (capability_curve_* declared in unh_marine_autonomy; ROS silently ignores undeclared overrides); coupling is documented + mirrors accepted depth_costs pattern. Optional: pre-launch helm-binary capability check on gabby — cross-repo, `bizzyboat_project11/config/bizzyboat.yaml:32`

### Verification performed
- Parameter contract: `capability_curve_enabled` / `capability_curve_v_omega_max` / `capability_curve_margin` names match the helm consumer exactly (`unh_marine_autonomy/helm_manager/src/helm_manager.cpp:69-72`); `capability_curve_pivot_speed` intentionally unset (defaults 0.05).
- Curve validity: array `[0.0,0.28,0.15,0.26,0.55,0.38,1.05,0.40,1.55,0.20,2.15,0.20]` passes every rule in `curvature_regulation.h::validateCurvatureConfig` — 12 values (even), starts at v=0.0, v strictly ascending, finite/non-negative, margin 0.8 ∈ (0,1].
- Data consistency: the six band-center ω values match the measured p95 yaw-rate table in `nav2_overlay.yaml:454-461` and the pivot p95 0.280 at `nav2_overlay.yaml:499`.
- Turn-radius math: for k=1/3, margin-scaled feasibility f(x)=0.8·ω(x)−k·x is positive at low speed and crosses zero at x*≈0.95 m/s (segment [0.55,1.05]); x* > pivot_speed so curvature is preserved, not sacrificed. 3.0 m native at 1 kt survey speed (commanded ω≈0.17 < λ≈0.30 → passthrough); regulated down from transit speed preserving v/ω=3.0.
- Dependency landed: helm capability-curve feature (#292 / PR#293, ADR-0012) is an ancestor of `origin/jazzy` in unh_marine_autonomy — code dependency merged; remaining risk is gabby build/deploy ordering, which both files document.
- Static: yamllint unavailable on host; both YAMLs parse via yaml.safe_load; changed lines covered by the file's own line-length/colons/indentation disable directives.
- Local Adversarial skipped: Ollama not reachable (localhost:11434).

### Next step
Lifecycle: **Local Review** → (address 2 suggestions or accept) → push / open PR → **triage-reviews**. Verdict is approved (0 must-fix); suggestions are optional hardening.
