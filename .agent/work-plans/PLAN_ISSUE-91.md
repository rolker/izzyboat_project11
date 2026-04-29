# Plan: BizzyBoat — switch nav source to FCU EKF3-fused topics

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/91

## Context

`mru_transform` and `platform_sender` on BizzyBoat consume three raw FCU
topics: `mavros/global_position/raw/fix` (forward-antenna NavSatFix),
`mavros/imu/data` (EKF3 attitude — already CG-referenced), and
`mavros/global_position/raw/gps_vel` (antenna ENU velocity). The position
and velocity inputs sit at the **forward GPS antenna phase center**, not
at base_link / CG. Per `bizzyboat_fcu_custom.param`,
`GPS_POS1 = (+0.835, 0.0, -0.89)` in ArduPilot's body/NED convention
(Z down, so the antenna is +0.89 m above the body origin); the reported
XY is biased ~0.84 m forward of CG in a heading-dependent way, and RTK
noise is cm-class so the lever arm dominates absolute position error.

ArduPilot's EKF3 already lever-arm-corrects every measurement back to
the body origin (CG on BizzyBoat, per the configured `GPS_POS*` /
`INS_POS*` offsets). Switching `mru_transform`'s inputs to EKF3-fused
topics stops double-handling the lever arm without changing the
`/bizzy/odom` contract or the TF tree. This is **config-only**:
`mru_transform`'s `updateVelocity` (in the
[`rolker/mru_transform`](https://github.com/rolker/mru_transform) repo,
`src/mru_transform.cpp:246`) is already transform-aware on its
TwistStamped input — it looks up `base_frame_ ← header.frame_id` via
tf2 and rotates linear velocity + covariance into base_frame.

IzzyBoat is intentionally out of scope for this PR — it uses the same
three raw topics and will mirror once BizzyBoat is field-validated.

## Approach

1. **Edit `bizzyboat_project11/config/bizzyboat.yaml`.** Swap three topic
   names in two `mru_transform`-pattern blocks (`platform_sender.nav.sources.mru`
   at lines 23–26 and `/**/mru_transform.sensors.mru` at lines 41–44).
2. **Add fused-topic feeds to both udp_bridge blocks alongside raw**
   (parallel-feed pattern, matching `seafloor_echoboat_project11/echoboat_project11/config/echo.yaml`):
   keep `mavros_position` (raw) and `mavros_velocity` (raw) as-is;
   add new labels `mavros_position_ekf` (sourced from
   `mavros/global_position/global`) and `mavros_velocity_body`
   (sourced from `mavros/local_position/velocity_body`) to both the
   `topics:` definitions and the `topics_list:` arrays in each udp_bridge
   block (boat-side wifi remote ~lines 116–143 + vpn ~lines 144–202). Raw remains a
   shoreside diagnostic for GPS quality / RTK status / EKF3 health
   (raw vs. fused divergence as an unhealthy-EKF tripwire); fused is
   what autonomy-aligned operator tooling should subscribe to going
   forward.
3. **Field-validate on next gabby session** (separate field step, not
   in the PR diff):
   - `ros2 topic hz /bizzy/mavros/local_position/velocity_body` and
     `/bizzy/mavros/global_position/global` — confirm ≥ 10 Hz. (10 Hz
     is the marine-vehicle floor — at peak 1.75 m/s that's 17.5 cm
     per sample, well within sub-meter XTE goals; the 2026-04-24
     dynamics analysis already showed sub-meter XTE on the existing
     ~5–10 Hz pipeline.) If lower, bump `SR0_POSITION` on the FCU.
     Capture before/after rates.
   - `ros2 topic echo --once` on each new topic to confirm
     `header.frame_id` resolves in the bizzy TF tree:
     - `velocity_body.header.frame_id` should be `base_link` or a
       statically-related body frame (mru_transform rotates into
       base_frame so non-base_link is fine, but verify it resolves).
     - `global_position/global.header.frame_id` should be `base_link`
       or empty so `mru_transform`'s position handler treats it as
       already-at-CG (no double lever-arm correction).
   - Compare `/bizzy/odom` to a recorded 2026-04-27 known-good track —
     today's position is at the forward GPS antenna, so after the
     switch the reported position should shift ~0.84 m **aft** (back
     toward CG) in the heading-correlated direction.
   - CAMP visualization: confirm boat icon position matches RTK truth
     within RTK noise (sub-decimeter), not the previous ~0.84 m offset.
4. **Mark PR ready and merge** once field-validation passes.

## Files to Change

| File | Change |
|------|--------|
| `bizzyboat_project11/config/bizzyboat.yaml` | (a) Topic-name swaps in two `mru_transform`-pattern blocks (`platform_sender.nav.sources.mru` ~23–26 + `/**/mru_transform.sensors.mru` ~41–44): position raw → fused, velocity ENU → body, orientation unchanged. (b) Add `mavros_position_ekf` and `mavros_velocity_body` parallel feeds to both udp_bridge blocks (~116–143 + ~144–202): two new entries in each block's `topics:` map and two new entries in each block's `topics_list:` array. Raw `mavros_position` / `mavros_velocity` labels kept as-is. |
| `bizzyboat_project11/config/mavros.yaml` | Add `child_frame_id: "bizzy/base_link"` to the `/**/local_position:` block. The `global_position` block already has it; `local_position` was missing it, causing `velocity_body` to publish with bare `base_link` (which doesn't resolve in the bizzy TF tree). Field-discovered during Phase-A diagnostics on 2026-04-28. |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| Quality Standard ("do it completely") | Field-validation steps are explicit, not "look fine, ship it." Topic-rate verification is a real gate, not optional. |
| Issue-first | #91 exists with full design rationale; this plan implements the proposal in its body. |
| Verify against source | Confirmed `mru_transform.cpp:246` is transform-aware before declaring config-only. Confirmed lever-arm config in `bizzyboat_fcu_custom.param` matches the issue's analysis. |
| Atomic commits | Plan-first; config swap is one logical change in one commit. |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| 0008 (Follow ROS 2 official conventions) | Yes | REP-105 says odom.twist must be in child_frame_id (body); the proposed input `velocity_body` is already body FLU at CG, and mru_transform's existing tf2-based rotation ensures REP-105 compliance regardless. |
| 0011 (Field-mode for non-GitHub origins) | Indirectly | Field-validation will happen on gabby (gitcloud-origin in field mode); any field-side hot-tweaks of bizzyboat.yaml come back via `/import-field-changes`. |

## Consequences

| If we change... | Also update... | Included in plan? |
|---|---|---|
| `mru_transform` nav inputs (boat side) | `udp_bridge` operator-side feeds | Yes — parallel-feed: raw labels kept, new fused labels added per echo precedent |
| `mru_transform` nav inputs | mavros plugin allowlist (#87) — `local_position` plugin must remain loaded | Out of scope here, but noted in #87; this PR depends on `local_position` being kept |
| BizzyBoat config | IzzyBoat config (same three raw-topic pattern) | **Out of scope** — IzzyBoat is a deliberate follow-up, mirrored after field validation |
| `/bizzy/odom` semantics (lever-arm) | Any consumer that learned to compensate for the antenna offset (e.g., calibration scripts, costmap params with hand-tuned offsets) | None known — workspace grep confirmed no consumers reading `BatteryState.percentage`-style derived fields; nav consumers (Nav2, helm_manager, CAMP) all treat `/bizzy/odom` as ground truth |

## Resolved Decisions

1. **udp_bridge forwarding** — parallel-feed pattern (raw kept, fused
   added alongside under new labels `mavros_position_ekf` and
   `mavros_velocity_body`), matching the precedent in
   `seafloor_echoboat_project11/echoboat_project11/config/echo.yaml`.
   Raw stays available shoreside as a GPS-quality / EKF3-health
   diagnostic; fused is the autonomy-aligned source for new operator
   tooling.
2. **`SR0_POSITION` rate** — if `local_position/*` publishes below
   10 Hz on the boat, bump `SR0_POSITION` in
   `bizzyboat_fcu_custom.param` on **this** branch as a follow-up
   commit, then field-apply in the same gabby session that validates
   the topic swap. Single source of truth dev-side, applied field-side
   — same pattern as #56's battery params. 10 Hz target reflects
   marine-vehicle dynamics (PR #90 / 2026-04-24), not Nav2's
   small-robot defaults.
3. **IzzyBoat timing** — open a separate IzzyBoat-only issue and PR
   *after* BizzyBoat field-validation succeeds. Keeps blast radius
   contained and the IzzyBoat mirror gated on real-world validation.

## Open Questions

None blocking implementation. Naming for the new udp_bridge labels
(`mavros_position_ekf` / `mavros_velocity_body`) is a judgment call —
position label matches echo's exact name, velocity label uses
`_body` because the salient change there is the frame contract
(ENU → body FLU), not just "EKF-fused." Easy to rename to
`mavros_velocity_ekf` for echo-symmetry if preferred.

## Estimated Scope

Single small PR — ~four edited lines (mru_transform-pattern blocks)
plus ~eight new lines (parallel-feed labels added to both udp_bridge
blocks: two `topics:` entries + two `topics_list:` entries × two
blocks), plus one added line in `mavros.yaml` (`child_frame_id` for
the local_position plugin, discovered during Phase-A field
diagnostics). Implementation is ~15 minutes; the gating cost is the
next gabby session for field validation.

## Implementation Notes

- 2026-04-28 Phase-A field diagnostics on gabby revealed that
  `mavros/local_position/velocity_body.header.frame_id` was bare
  `base_link` while every other mavros topic used `bizzy/base_link`.
  Root cause: `bizzyboat_project11/config/mavros.yaml`'s
  `/**/local_position:` block set `frame_id` but not `child_frame_id`.
  Added the missing `child_frame_id` line so the body twist publishes
  with the correctly namespaced frame_id and resolves in the bizzy
  TF tree. Without this fix, mru_transform's `lookupTransform`
  would have failed for every velocity sample and produced silent
  degradation (throttled WARN, no `/bizzy/odom.twist` updates).
