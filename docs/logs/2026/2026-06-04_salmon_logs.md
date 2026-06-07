# 2026-06-04 — salmon log (BizzyBoat outing, backfilled)

Host: salmon
Side: field (operator station)

> **Backfilled 2026-06-07 (echoboats#174).** No live agent log was written on
> this day. This record is reconstructed from the durable operator-log sidecar
> `~/data/logs/operator/2026-06-04/operator_log.jsonl` (Pilot entries) plus the
> dev-side bag analysis already captured in
> [`2026-06-03_dev_logs.md`](2026-06-03_dev_logs.md). Times are EDT, converted
> from the entry `ts_ns`. Bags: main `bizzyboat/2026-06-04T13-43-04+00-00`;
> operator `operator/2026-06-04/`.

## Timeline (operator notes)

**2026-06-04 10:25:53 EDT** — Pilot: "not following line properly." Line-following
deficiency on survey paths. Root-caused dev-side to cross-track PID over-commanding
yaw 3–4× hull capability → undamped overshoot closing into 360° loops on
planner-generated paths. Tracked at
[unh_marine_navigation#66](https://github.com/rolker/unh_marine_navigation/issues/66)
(top roadmap priority; not location-specific — expected to reproduce elsewhere).

**2026-06-04 10:38:46 EDT** — Pilot: "way over corrected for avoid obstacle."
Obstacle-avoidance over-correction (avoider-in-loop weave). Data point for
[unh_marine_navigation#63](https://github.com/rolker/unh_marine_navigation/issues/63).

**2026-06-04 13:33:01 EDT** — Pilot: "Velocity smoother was disabled." Operator
disabled the cmd_vel velocity_smoother mid-run to test its effect on the weave —
"didn't seem to help." Dev-side verification (analysis `~/data/logs/analysis/2026-06-04/`):
while in-loop, `cmd_vel_smoothed` yaw ≈ `cmd_vel_nav` yaw (median diff 0.000 rad/s)
— the smoother is near-transparent on yaw, so the weave originates upstream
(controller/avoider), not the smoother. NB: the ±1.0 rad/s yaw clamp lives *in*
the smoother, so bypassing it removed the clamp (raw nav yaw ±2.4 reached the
command), tending to make the weave sharper. Posted to nav#63. Confirms the
smoother (re-enabled seafloor#36) is not the weave source.

## Issues encountered

- Line-following 360° loops → nav#66 (root-caused, top priority).
- Obstacle-avoidance over-correction weave → nav#63 (smoother ruled out as source).

## Notes

The full cmd_vel-chain analysis for this outing lives in the 2026-06-03 dev log
(written when the bags were pulled and analyzed). This salmon backfill captures
the operator-voice timeline that was otherwise only in the bag sidecar.
