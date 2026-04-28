# Plan: BizzyBoat — switch nav source to FCU EKF3-fused topics

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/91

## Context

`mru_transform` and `platform_sender` on BizzyBoat consume three raw FCU
topics: `mavros/global_position/raw/fix` (forward-antenna NavSatFix),
`mavros/imu/data` (EKF3 attitude — already CG-referenced), and
`mavros/global_position/raw/gps_vel` (antenna ENU velocity). The position
and velocity inputs sit at the **forward GPS antenna phase center**, not
at base_link / CG. With `GPS_POS1 = (+0.835, 0, +0.89 ENU)` (per
`bizzyboat_fcu_custom.param`) the reported XY is biased ~0.84 m forward
of CG in a heading-dependent way; RTK noise is cm-class so the lever
arm dominates absolute position error.

ArduPilot's EKF3 already lever-arm-corrects every measurement back to
the body origin (CG on BizzyBoat, per the configured `GPS_POS*` /
`INS_POS*` offsets). Switching `mru_transform`'s inputs to EKF3-fused
topics stops double-handling the lever arm without changing the
`/bizzy/odom` contract or the TF tree. This is **config-only**:
`mru_transform`'s `updateVelocity`
(`mru_transform/src/mru_transform.cpp:246`) is already transform-aware
on its TwistStamped input — it looks up `base_frame_ ← header.frame_id`
via tf2 and rotates linear velocity + covariance into base_frame.

IzzyBoat is intentionally out of scope for this PR — it uses the same
three raw topics and will mirror once BizzyBoat is field-validated.

## Approach

1. **Edit `bizzyboat_project11/config/bizzyboat.yaml`.** Swap three topic
   names in two `mru_transform`-pattern blocks (`platform_sender.nav.sources.mru`
   at lines 23–26 and `/**/mru_transform.sensors.mru` at lines 41–44).
2. **Decide udp_bridge forwarding** (open question — see below). Either
   update lines 137–138 and 200–201 to forward the EKF3-fused topics so
   CAMP shoreside reflects the same nav source the boat is using, or
   leave them as raw and add a comment explaining the divergence.
3. **Field-validate on next gabby session** (separate field step, not
   in the PR diff):
   - `ros2 topic hz /bizzy/mavros/local_position/velocity_body` and
     `/bizzy/mavros/global_position/global` — confirm ≥ 20 Hz. If
     lower, bump `SR0_POSITION` (or matching SR-stream param) on the
     FCU. Capture before/after rates.
   - `ros2 topic echo --once` on each new topic to confirm
     `header.frame_id` resolves in the bizzy TF tree:
     - `velocity_body.header.frame_id` should be `base_link` or a
       statically-related body frame (mru_transform rotates into
       base_frame so non-base_link is fine, but verify it resolves).
     - `global_position/global.header.frame_id` should be `base_link`
       or empty so `mru_transform`'s position handler treats it as
       already-at-CG (no double lever-arm correction).
   - Compare `/bizzy/odom` to a recorded 2026-04-27 known-good track —
     position should shift by the GPS1 lever arm (~0.84 m forward of
     where it was) in the heading-correlated direction.
   - CAMP visualization: confirm boat icon position matches RTK truth
     within RTK noise (sub-decimeter), not the previous ~0.84 m offset.
4. **Mark PR ready and merge** once field-validation passes.

## Files to Change

| File | Change |
|------|--------|
| `bizzyboat_project11/config/bizzyboat.yaml` | Three topic-name swaps in two `mru_transform` config blocks. Optional: matching swaps in two `udp_bridge` blocks pending the open question. |

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
| `mru_transform` nav inputs (boat side) | `udp_bridge` source topics (operator side) for consistency in CAMP | **Open question** — decision deferred to user |
| `mru_transform` nav inputs | mavros plugin allowlist (#87) — `local_position` plugin must remain loaded | Out of scope here, but noted in #87; this PR depends on `local_position` being kept |
| BizzyBoat config | IzzyBoat config (same three raw-topic pattern) | **Out of scope** — IzzyBoat is a deliberate follow-up, mirrored after field validation |
| `/bizzy/odom` semantics (lever-arm) | Any consumer that learned to compensate for the antenna offset (e.g., calibration scripts, costmap params with hand-tuned offsets) | None known — workspace grep confirmed no consumers reading `BatteryState.percentage`-style derived fields; nav consumers (Nav2, helm_manager, CAMP) all treat `/bizzy/odom` as ground truth |

## Open Questions

1. **udp_bridge forwarding to operator (raw vs. fused).** Update lines
   137–138, 200–201 to also use the EKF3-fused topics (consistent with
   boat-side autonomy), or leave as raw and accept that CAMP shoreside
   sees a different nav source than the boat is acting on? Lean toward
   updating, but flagging because it expands the diff and we lose the
   raw fix as a shoreside diagnostic signal.
2. **`SR_POSITION` rate.** If `local_position/*` publishes below 20 Hz,
   we'll bump it during field-validation. Should that bump be captured
   in `bizzyboat_fcu_custom.param` (this PR) or in a separate field-mode
   commit on gitcloud? Probably the latter — the FCU param file is
   field-applied, not a code edit.
3. **IzzyBoat timing.** After BizzyBoat field-validation passes, mirror
   to IzzyBoat as a follow-up commit on this branch (single PR for
   both), or open a separate IzzyBoat-only issue/PR?

## Estimated Scope

Single small PR — three lines × two blocks (six lines total) in
`bizzyboat.yaml`, possibly six more lines if we update udp_bridge
forwarding, plus a field-validation walkthrough. Implementation is
~10 minutes; the gating cost is the next gabby session for validation.
