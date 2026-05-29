# BizzyBoat deployment log — salmon — 2026-05-29

**Host**: salmon
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Side**: field
**Deployment**: git-bug `5617368` — "Deployment 2026-05-29: validate graded sea-surface costmap (perception #22)" (opened 2026-05-29T11:47-04:00, last edited 2026-05-29T12:32-04:00).
**Started**: 2026-05-29 12:45 -04:00

## `/start-deployment` first-activation on salmon

- Config: `.agents/deployment.yaml` discovered at `unh_echoboats_project11/.agents/`.
- Side detection: `field_mode.sh` resolved field mode (origin `git@gitcloud:field/unh_echoboats_project11.git`). Clean.
- `issue_sync.field_pull` (`git bug pull gitcloud`) **failed again** — same drift as 2026-05-28 salmon log noted. The remote in this repo is `origin`, not `gitcloud`. Worked around with `git bug pull origin` (15 objects, 4 bug refs updated). The deployment.yaml hotfix to switch the config commands from `gitcloud` → `origin` still hasn't landed.
- `field_list_open` returned single open deployment issue (`5617368`). Clean.
- Three-state detection → **activate first time** for salmon (issue present, no prior `2026-05-29_salmon_logs.md`).
- Tree state: on `jazzy`, in sync with `origin/jazzy`, clean.
- Issue title in canonical form; `## Logs` section present in body. No edits attempted (field side is read-only on the issue).
- **TODO for next dev-side `/start-deployment` run**: stamp `[salmon log](docs/logs/2026/2026-05-29_salmon_logs.md)` under the deployment issue's `## Logs` section (only `dev log` is currently linked there).

## Pre-launch checks

### 2026-05-29 12:57 -04:00 — operator-bridge data sanity from salmon
- 62 topics visible from salmon. Segmentation `/compressed` from all 4 cameras (aft / forward / port / starboard) + camera_info present.
- Initial probe showed only `/bizzy/local_costmap/published_footprint` — no costmap occupancy, no plan, no `sea_surface_*`. Flagged the costmap absence (operator-bridge gap, not a stack-down condition — boat-side autonomy nodes are not visible to salmon by design).
- Operator added the costmap to the operator bridge; costmap now flowing to salmon. Plan / `sea_surface_*` not (re)checked post-fix.

### 2026-05-29 15:19 -04:00 — CAMP (operator app) frozen on salmon
- Operator report: "camp seems frozen" / "camp is frozen". **Agent misread as "costmap" for several turns** before operator clarified ("it's not the topics, it's camp, the application that is frozen"). Probes below were therefore on the wrong target.
- Misdirected ROS probes (kept for record): `hz` on `/bizzy/local_costmap/costmap_windowed` over 5s → 0 msgs; then `published_footprint` also 0 msgs over 4s. Both topics exist; neither flowing during the window. **Not the user's symptom** — CAMP is an operator-side application on salmon, not a ROS topic. Whether the local_costmap node is actually wedged is unconfirmed and unrelated to the operator's report.
- Mitigation: operator asked diagnose-vs-restart; agent recommended restart (low confidence on diagnosing an unfamiliar GUI freeze from outside; restart is faster than any external probe).
- Follow-up if CAMP refreezes: check `journalctl --user`, its stderr, and whether the process is CPU-pegged.

### 2026-05-29 16:30 -04:00 — CAMP freeze post-mortem (post-restart analysis)
- CAMP identity: `CCOMAutonomousMissionPlanner`, built at `layers/main/ui_ws/install/camp/`. Launched as ROS 2 node `__node:=camp __ns:=/operator`. Prior PID 138488 (from the 12:14:42 launch), current PID 156187 (restarted 15:22:34).
- Per-node log `~/.ros/log/CCOMAutonomousMissionPlanner_138488_*.log` was misleadingly sparse (7 lines, 790 bytes). Real output went to `~/.ros/log/2026-05-29-12-14-42-213786-salmon-138470/launch.log` (the combined launch log).
- Death certificate: `process has died [pid 138488, exit code -9, cmd ...]` at epoch 1780082549.96 = **15:22:29 EDT**. Exit code -9 = **SIGKILL** → operator force-killed; a clean shutdown signal wouldn't take. Consistent with "frozen / unresponsive".
- Last activity before SIGKILL:
  - 15:07:23 — last `QGeoCoordinate` update (still alive).
  - **15:15:43** — last log line was `Message Filter dropping message: frame 'bizzy/base_link' at time 1780082142.038 for reason 'the timestamp on the message is earlier than all the data in the transform cache'`. ~4 min gap before operator noticed at 15:19.
  - Same `bizzy/base_link` TF cache miss reappeared on the restarted instance at 15:23:52 (line 1 of its log) → not a one-shot, this is an ongoing TF / clock state.
- Other suggestive signals from the session:
  - 15:02:59 — `[ERROR] [rmw_zenoh_cpp]: SubscriberCallback triggered over 0/bizzy/marine/heartbeat/...` (Zenoh-side anomaly on heartbeat).
  - Post-restart at 15:22:35/45 — Zenoh: `Scouting delay elapsed before start conditions are met` and `Didn't receive DeclareFinal for interest ... Timeout(10s)`. Discovery/interest layer unhappy.
- Negative findings (ruling out): no OOM kill (dmesg clean), no `journalctl --user` entries for CAMP. Not a kernel-side or systemd-side event.
- Working hypothesis (not proven): TF cache miss on `bizzy/base_link` (likely clock skew salmon ↔ gabby, or a transient TF publisher reset) caused a Qt-thread-bound TF wait or message-filter callback to stall; flaky Zenoh discovery state may have compounded. The GUI thread wedged → SIGKILL required.
- Suggested follow-up when quiet: `ros2 run tf2_ros tf2_echo bizzy/map bizzy/base_link` for stability; `ros2 topic hz /bizzy/tf` to look at fan-in cadence; compare salmon vs gabby `chronyc tracking` for clock drift.

## Wrap-up

### 2026-05-29 16:32 -04:00 — boat recovered, session wrap
- Operator: "boat has been recovered, let's wrap up."
- `/wrap-up-deployment` skill not yet built (tracked under workspace #495) — hand-rolled close: committing + pushing this log only. Not closing the deployment issue.
- Open items to carry into wrap-up / next deployment:
  - **Costmap verification gap**: never confirmed end-to-end that the graded sea-surface costmap (perception #22) actually marked dim buoys on the costmap. Operator-side bridge work + CAMP freeze ate the window. The fix is shipped + the bridge is updated, but the deployment's "must-verify" checklist on issue 5617368 is still unchecked.
  - **CAMP freeze cause**: hypothesis (TF cache miss on `bizzy/base_link` + Zenoh discovery flakiness) is unproven. Suggested probes documented above for a quieter window.
  - **deployment.yaml drift**: `issue_sync.field_pull` still says `gitcloud` when the repo's remote is `origin`. Worked around (again) this session — same as 2026-05-28. Worth a v2 hotfix to the config.
  - **Issue body `## Logs` section**: still only links the dev log. Next dev-side `/start-deployment` should stamp `salmon log` and any `gabby log` that exists.
