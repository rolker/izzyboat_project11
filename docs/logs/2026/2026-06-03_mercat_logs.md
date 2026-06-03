# 2026-06-03 — mercat log (BizzyBoat deployment, git-bug 0cba862)

Deployment issue: `0cba862` — Deployment 2026-06-03: pier — clean-survey validation + OTH (final pre-class)
Host: mercat
Side: field
Started: 2026-06-03 17:05 +00:00

> Note: mercat's system clock is UTC (`date` reports `+00:00`). Newcastle, NH is
> EDT (−04:00) in June, so 17:05 UTC ≈ 13:05 EDT. All timestamps in this log are
> machine-measured UTC unless an entry marks otherwise.

## 2026-06-03

**2026-06-03 17:05 +00:00** — Deployment mode activated on mercat (field side) via `/start-deployment`. First activation of this host for deployment `0cba862`. Repo on `jazzy`, tree clean. git-bug refs freshly pulled from gitcloud (system-git ref fetch; `git bug pull` is non-functional on this Windows box). Field-side: issue is read-only here — dev should stamp `docs/logs/2026/2026-06-03_mercat_logs.md` under the deployment issue's `## Logs` section on its next `/start-deployment` run.

**2026-06-03 17:39 +00:00** — Boat in the water (operator-reported).

**2026-06-03 18:06 +00:00** — Sonar (M3) and QINSy coming up. Operator confirmed the sonar is receiving the **1 PPS** signal. ✓ Ticks the #205 carry-forward "Confirm M3 1PPS lock in the sonar console."

**2026-06-03 18:11 +00:00** — Survey started, then **aborted**. Operator-reported reason: "qinsy doesn't see the sng." (Survey not yet underway; QINSy missing an expected input. "sng" = SBG, per resolution below.)

**2026-06-03 18:15 +00:00** — Restarted QINSy; it can see the **SBG** (Ellipse INS position/attitude) now. Abort cause resolved by the restart — fix was QINSy-side, not the boat. *(Wrap-up note: a QINSy restart recovering the SBG suggests the I/O link was present but QINSy lost the stream on init — worth a root-cause look at wrap-up if it recurs.)*

**2026-06-03 20:03 +00:00** — QINSy **navigation display crashed** (operator-reported). Second QINSy-side instability today after the 18:11 SBG dropout — survey PC software, not the boat. *(Wrap-up: two QINSy fault events in one session — flag QINSy stability for RCA.)*

**2026-06-03 20:23 +00:00** — Operator closed the **RDP (rdesktop) session to mercat** to improve the camera feeds; "helped a bit" (partial improvement). Suggests bandwidth/resource contention between the mercat remote-desktop session and the camera streams. *(This agent session on mercat continues regardless — it runs detached from the interactive RDP session.)*

**2026-06-03 21:43 +00:00** — **Sound speed sensor reading NaN** on the QINSy annunciator (operator-reported). Boat has been in the water since ~17:39, so not an in-air artifact. NaN = QINSy holding no valid SV value (no/garbled data from the SV sensor, or sensor fault). Affects sonar ranging/beamforming if uncorrected. *(Possibly another QINSy-side I/O event given today's pattern — flag for wrap-up.)*

**2026-06-03 22:01 +00:00** — Sonar off (operator-reported).

**2026-06-03 22:15 +00:00** — **Boat recovered** (operator-reported). On-water ops for the session ended. *(Open carry-forwards: offload the QINSy data; the must-do validation backlog — nav#35, nav#58, #124, #164, #130, #209, operator-log plugin — was not reached, the day was consumed by QINSy-side faults: SBG dropout, nav-display crash, sound-speed NaN.)*

## Session summary (mercat)

**2026-06-03 22:17 +00:00** — Session close from mercat (field-side logging station; no direct ROS/QINSy access from this box). The day was dominated by **QINSy survey-PC instability**, which blocked the planned clean-survey validation:

- ✓ **M3 1 PPS lock confirmed** (18:06) — ticks a #205 carry-forward.
- ✗ **SBG not seen by QINSy** → first survey aborted (18:11); recovered by a QINSy restart (18:15).
- ✗ **QINSy nav display crashed** (20:03).
- ✗ **Sound-speed sensor NaN** on the annunciator (21:43), boat already in water since ~17:39.
- Operator closed the mercat RDP session (20:23) to relieve camera-feed contention — helped partially.
- Sonar off (22:01); boat recovered (22:15).

**Net:** no clean survey line achieved; validation backlog (nav#35, nav#58, #124, #164, #130, #209, operator-log plugin) untouched. **QINSy stability is the clear RCA theme for wrap-up** (three distinct QINSy fault events in one session). QINSy data offload remains open.

*Times are machine-measured UTC on mercat; subtract 4 h for EDT at the pier.*
