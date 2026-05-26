# BizzyBoat deployment log — gabby — 2026-05-26

**Host**: gabby
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7 (1M context))
**Mode**: field (gitcloud origin)
**Deployment**: git-bug `20a49fc` — *Deployment 2026-05-26: validate raised yaw cap (1.0) + planner radius (1.5)* (GitHub link added dev-side at wrap-up)

> **Summary** and **Lessons Learned** for this deployment live in
> [`2026-05-26_dev_logs.md`](2026-05-26_dev_logs.md), not here —
> per-host logs capture scribe-grade detail, the dev log carries the
> at-a-glance summary and the durable operator-level take-homes.

## 1. Session start — sync, build, deployment-issue retrieval

**2026-05-26T11:24-04:00** — Roland prompted pre-deployment prep on
gabby. Ran `make sync` (twice). All 17 workspace repos clean on their
default branches; first pass fast-forwarded several, second pass
"already up to date". Notable code pulls into `jazzy`:

- `unh_marine_perception` → `401385c` (`sea_surface_segmentation`
  reflex/projection rework, issue-17 bag fixtures)
- `udp_bridge` → `09d43ed` (publish_queue + QoS work, issue-10)
- `unh_marine_navigation` → `063bbdc` (behavior-tree
  `set_controller_speed`, crabbing path follower, issue-26)

**2026-05-26T11:27-04:00** — `make build` completed: all 5 layers /
49 packages OK. Only compiler warnings (unused-parameter, sign-compare,
pedantic flexible-array-member in `udp_bridge/packet.h`, one PCL
`FindFLANN` CMP0144 CMake-policy note in `sea_surface_segmentation`);
no errors. This rebuild picked up perception `401385c`, which is the
reflex-mode precondition called out in the deployment issue (comment
#3): gabby needed to pull `jazzy` + rebuild the perception layer to
get the reflex `segments_to_pointcloud` node and its `/diagnostics`
health task present. **Reflex node should now be built on gabby** —
to be confirmed live with `ros2 topic hz /bizzy/collision_monitor/pointcloud`
once the stack is up.

**2026-05-26T11:39-04:00** — Looked for today's deployment issue;
initially not visible. `git bug bug --status open` showed the newest
deployment entry as `1e4fe7d` (2026-05-22) only. Same SSH_AUTH_SOCK
gap as prior sessions — `git-bug pull` exits with
`Error: error creating SSH agent: "SSH agent requested but SSH_AUTH_SOCK not-specified"`.
Worked around with plain git (which has working creds) to fetch the
bug refs directly:

```bash
git fetch origin 'refs/bugs/*:refs/bugs/*' 'refs/identities/*:refs/identities/*'
```

This brought down new refs (open count 38 → 45) but the
2026-05-26 issue still didn't appear. **The git-bug on-disk cache was
stale** — `.git/git-bug/cache/{bugs,identities}` was dated
2026-05-22 16:03 and `make sync` / the `git fetch` did not refresh it.
(A salmon-side agent flagged the likely stale cache.) Forced a full
reindex:

```bash
rm -rf .git/git-bug/cache && git-bug bug --status open
```

Count went 45 → 50 and today's issue surfaced:
`20a49fc` — *Deployment 2026-05-26: validate raised yaw cap (1.0) +
planner radius (1.5)*. **Takeaway for next session**: refreshing
git-bug on a field host without SSH-agent is two steps —
`git fetch origin 'refs/bugs/*:refs/bugs/*'` **then**
`rm -rf .git/git-bug/cache`; the cache does not auto-invalidate on a
bare ref fetch.

**2026-05-26T11:48-04:00** — Read the full deployment issue (4
comments). Core scope: validate the raised helm yaw cap (0.5 → 1.0
rad/s) and reduced planner min turning radius (3.0 → 1.5 m), both
field-untested; land `pid_state` (cross-track-error) recording before
launch (record-only per operator); reflex Collision Monitor Phase B
merged today (baby-stepped on-water, sim-verify **not** a hard gate per
operator correction in comment #4); opportunistic operator-annunciator
coverage (#171). Started this log.

## 2. Land `pid_state` recording (deployment issue §2)

**2026-05-26T12:00-04:00** — Stack up on gabby. Verified the
CrabbingPathFollower PID-state topic on the **live** stack rather than
guessing (the issue flagged this as a silent-failure class):

```
$ ros2 topic list | grep -i pid
/bizzy/FollowPath/pid/pid_state
$ ros2 topic info /bizzy/FollowPath/pid/pid_state
Type: control_msgs/msg/PidState
Publisher count: 1
Subscription count: 0
```

**Finding — the topic is namespaced under `/bizzy/`**, i.e.
`/bizzy/FollowPath/pid/pid_state`, **not** the global `/FollowPath/...`
the issue's source-note predicted from the alphanumeric `topic_prefix`.
The node inherits the `/bizzy` namespace, which prefixes the PID
publisher too. Publisher count 1 confirms the state publisher is live
(`activate_state_publisher: true`); subscription count 0 confirms it
was going unrecorded — exactly the gap to close.

**2026-05-26T12:02-04:00** — Added the verified topic to the `/**/logger`
→ `record:` → `topics:` list in
`bizzyboat_project11/config/bizzyboat.yaml` (grouped with the FollowPath
action items, with a comment recording the verified-live namespace).
Record-only per operator (post-mission XTE analysis of #164), not a
field monitor.

**Propagation check**: package is `ament_cmake` with
`install(DIRECTORY config ...)`, which normally *copies*. But the
install-space copy at
`platforms_ws/install/bizzyboat_project11/share/bizzyboat_project11/config/bizzyboat.yaml`
is a **symlink** back to source (the layer was built `--symlink-install`),
so the edit is already live in the install space — **no rebuild needed**.
The running logger node, however, reads the YAML at launch, so it will
**not** pick up the new topic until the logger launch group is
relaunched (not killed mid-op from here — operator relaunches).

- [ ] **In-field confirm after relaunch**: `ros2 bag info <bag>` shows
  `/bizzy/FollowPath/pid/pid_state` present — don't repeat the
  published-but-not-recorded gap (#171/#162 class).

**2026-05-26T12:10-04:00** — Relaunch-scope finding: the `logger` node is
**not** standalone — it lives inside `perception_launch.py` (top-level
`Node` in the main `GroupAction`, alongside the reflex
`segments_to_pointcloud` node and `sonar_logger`). So picking up the
`pid_state` config edit means **relaunching the whole perception group**
(DeltaT sonar + cube bathymetry, all OAK cameras, the reflex pointcloud
node, both loggers) — not a logger-only restart. Flagged to operator for
timing.

## 3. Throttle reflex pointcloud to 1 Hz on the VPN link

**2026-05-26T12:14-04:00** — Operator asked to throttle the new reflex
cloud on the VPN link. The udp_bridge config (`bizzyboat.yaml`) carries
two links: a full-rate WiFi link and the `vpn:` link (1 MB/s cap, the
OTH/Starlink budget path). `collision_pointcloud`
(`source: collision_monitor/pointcloud`) was **unthrottled on both**.

Verified `period` semantics in source before editing (`udp_bridge.cpp`
~641–649): a topic forwards only when `period >= 0`, and at most once
per `period` seconds — `period: 0`/absent = every message, `period: -1`
= never forward, so `period: 1.0` = 1 Hz. Matches the existing VPN
segmentation-overlay pattern.

Set `period: 1.0` on the **VPN** `collision_pointcloud` entry only; left
the WiFi entry full-rate. **Takes effect at udp_bridge (re)launch** —
the bridge is in a different launch group than the perception loggers.

## 4. Collision-avoidance wiring review — feed OK, **gating path bypassed**

**2026-05-26T12:12-04:00** — Operator asked whether the collision
avoidance is wired correctly. Checked against the **live** graph (stack
up), not just config. Verdict: the **feed side is correct, the gating
side is not** — as wired the Collision Monitor cannot slow or stop the
boat.

**Feed side — OK ✓**
- `collision_monitor` is running and lifecycle **active [3]**.
- Reflex cloud `/bizzy/collision_monitor/pointcloud`: publisher =
  `segments_to_pointcloud_reflex` (the perception#17 reflex node);
  subscribers (3) = `collision_monitor`, `logger`, `udp_bridge`.
- QoS matches — publisher and `collision_monitor` sub are both
  **BEST_EFFORT / VOLATILE**, so the deployment-issue worry ("a reliable
  source silently gets nothing") does **not** bite here.

**Gating side — BROKEN ✗**
The Collision Monitor sits on a **dead input** and the real autonomous
command bypasses it:
- Monitor input `cmd_vel_in_topic: cmd_vel_smoothed` → live
  `/bizzy/cmd_vel_smoothed` has **0 publishers** (only `collision_monitor`
  subscribes). Nothing feeds the monitor.
- `controller_server` is launched with remap
  `('cmd_vel', 'piloting_mode/autonomous/cmd_vel')`
  (`echoboat_project11/launch/navigation_launch.py:140`; the alternative
  `('cmd_vel', 'cmd_vel_nav')` is **commented out** at :141). So the
  controller publishes **directly** to `/bizzy/piloting_mode/autonomous/cmd_vel`,
  which `helm_manager` consumes → FCU. The monitor is not in this path.
- `velocity_smoother` is the intended middle stage but is dead: it
  subscribes `cmd_vel_nav` (**0 publishers** live) and its output is
  remapped to `piloting_mode/autonomous/cmd_vel` anyway (:234). This is
  the "deliberately disconnected filter chain" from prior cmd_vel
  troubleshooting — but the Collision Monitor (Phase B) was configured
  for the **standard** chain (controller → smoother → `cmd_vel_smoothed`
  → monitor → out), so the disconnect leaves the monitor stranded.
- Net: live `/bizzy/piloting_mode/autonomous/cmd_vel` has 9 publishers
  (`controller_server`, `velocity_smoother`, `behavior_server`×6,
  `collision_monitor`) and is consumed by `helm_manager`. The monitor is
  one parallel publisher among several, fed by nothing — so it emits
  nothing and gates nothing.

**This contradicts deployment-issue comment #2** ("runs … polygons on the
autonomous cmd_vel path") — on BizzyBoat's actual disconnected-smoother
topology it does not. Would have surfaced on-water as "boat doesn't slow
or stop"; caught at the dock instead.

**Minimal fix (smoother stays bypassed, monitor in the loop)** — a
shared-config change in `seafloor_echoboat_project11` (affects izzy too),
so flagged to operator, **not applied**:
- `controller_server` remap → `('cmd_vel', 'cmd_vel_nav')` (uncomment
  :141, drop :140); same for `behavior_server` (:180/:181).
- `collision_monitor` `cmd_vel_in_topic: cmd_vel_nav` (out stays
  `piloting_mode/autonomous/cmd_vel`).
- Result: `controller_server → cmd_vel_nav → collision_monitor →
  piloting_mode/autonomous/cmd_vel → helm_manager`.
- [ ] Lower-priority verify once gating is fixed: `base_frame_id`
  `<tf_prefix>/base_link` substitution actually resolves (monitor active
  ≠ source transforms succeeding); watch `collision_monitor_state` /
  TF "source timed out" warnings.

**2026-05-26T12:30-04:00** — Rewire applied (operator chose Option A:
bypass smoother, apply field-mode now). In `seafloor_echoboat_project11`
(field/gitcloud, `jazzy`, commit `ffbc57a`):
- `navigation_launch.py` non-composition path: `controller_server` and
  `behavior_server` cmd_vel → `cmd_vel_nav` (was the helm topic);
  `velocity_smoother` removed from `lifecycle_nodes` + its node block
  (kept deliberately disconnected, so it can't co-publish the helm topic).
- `nav2_params.yaml`: `collision_monitor.cmd_vel_in_topic` →
  `cmd_vel_nav`.
- Composition path left unchanged (unused; `use_composition=False`) with
  a TODO.
- New chain: `controller/behaviors → /bizzy/cmd_vel_nav → collision_monitor
  → /bizzy/piloting_mode/autonomous/cmd_vel → helm_manager → FCU`.

Shared config → also changes izzy + seafloor echoboat (all equally
bypassed before, so a strict improvement). **Takes effect on a nav-stack
relaunch** (config symlinked → no rebuild). Post-relaunch checks:
- [ ] `ros2 topic info /bizzy/piloting_mode/autonomous/cmd_vel` →
  publisher is **collision_monitor only** (was 9).
- [ ] `/bizzy/cmd_vel_nav` → publishers `controller_server` +
  `behavior_server`, subscriber `collision_monitor`.
- [ ] Object in the forward arc slows then stops the boat;
  `/bizzy/collision_monitor_state` transitions; clear water passes
  through unchanged.
- [ ] Manual RC override still drives with an obstacle present (monitor
  gates the autonomous branch only).

## 5. gabby uptime — battery-analysis baseline

**2026-05-26T12:12-04:00** — Recorded for future battery/draw analysis
(correlate host-on time with pack voltage):
- **Boot**: 2026-05-26 08:37:55 EDT
- **Uptime at check**: 3 h 34 min (load avg 3.63 / 3.51 / 2.69, 2 users)

So gabby has been drawing since ~08:38 EDT this morning; any LVD/voltage
trend today should be referenced against this boot time.

## 6. Post-restart verification (full stack relaunch)

**2026-05-26T12:39-04:00** — Operator restarted the whole stack (core +
perception + nav tmux windows). Verified against the live graph:

- **Collision gating fixed ✓** — `/bizzy/piloting_mode/autonomous/cmd_vel`
  publisher count is now **1 = collision_monitor** (was 9). Subscribers:
  `helm_manager` + `logger`. The monitor is the sole gate to the helm.
- **Monitor input ✓** — `/bizzy/cmd_vel_nav`: pubs = `controller_server`
  + `behavior_server`(×6); subs = `collision_monitor` + `logger`.
- **Smoother gone ✓** — `velocity_smoother` not in node list;
  `/bizzy/cmd_vel_smoothed` topic **absent entirely** (no orphan).
- **Reflex feed survived ✓** — `/bizzy/collision_monitor/pointcloud`:
  pub `segments_to_pointcloud_reflex`; subs `collision_monitor` +
  `udp_bridge` + `logger`, all BEST_EFFORT (QoS match).
- **pid_state recording ✓** — `/bizzy/FollowPath/pid/pid_state`
  subscription 0→**1** (the logger now records it; config took effect).
- `collision_monitor` lifecycle **active [3]**. New bag:
  `~/data/logs/bizzyboat/2026-05-26T16-36-35+00-00/`.

Remaining checks deferred to on-water (can't verify at the dock):
- [ ] `pid_state` actually lands in the bag — only publishes during an
  active `FollowPath`; confirm with `ros2 bag info` after a path runs.
- [ ] Object in the forward arc slows then stops the boat;
  `/bizzy/collision_monitor_state` transitions; clear water passes
  through (baby-step on-water per operator).
- [ ] Manual RC override still drives with an obstacle present.
- [ ] VPN cloud ≈ 1 Hz — measure operator-side over the VPN link.
- [ ] `base_frame_id` `<tf_prefix>/base_link` resolves — watch for
  `collision_monitor` TF / "source timed out" warnings.

## 7. Launch / in-water phase

**2026-05-26T12:42-04:00** — Boat going in the water. Stack up post-restart
(core + perception + nav), collision gating verified live at the dock (§6).
gabby uptime ~4 h since 08:37 EDT boot.

**2026-05-26T12:58-04:00** — Boat in the water. Confirming data points:
`/bizzy/mavros/state` mode **GUIDED**; GPS fix valid (`raw/fix` status 0);
collision gate still intact (`piloting_mode/autonomous/cmd_vel` single
publisher = `collision_monitor`, lifecycle active).

## 8. Collision-avoidance testing

**2026-05-26T13:16-04:00** — Operator testing collision avoidance.
Started a 1 h ad-hoc camera-video recording in parallel (see §9).
State at start of test:

- **Reflex obstacle feed healthy + live** — `/diagnostics` task
  `segments_to_pointcloud_reflex: obstacle projection feed` =
  "projecting obstacles": `camera_info_received: true`,
  `clouds_published` climbing (11576→11596 over ~6 s), `tf_lookup_failures:
  0`, `projection_frame: bizzy/base_link_level`, z=0. So the
  `<tf_prefix>/base_link` substitution **resolves** (deferred check from
  §4 — cleared). The monitor will see obstacles.
- **Tooling note**: `ros2 topic hz /bizzy/collision_monitor/pointcloud`
  reads blank — the cloud is BEST_EFFORT and (zenoh RMW) hz's default
  RELIABLE sub doesn't match. Use the diagnostic `clouds_published`
  counter, or `hz --qos-reliability best_effort`, to judge the feed.
- **No autonomous command flowing at check time** — `cmd_vel_nav` silent,
  `follow_path` status 4 (SUCCEEDED). The Collision Monitor only gates
  the autonomous path, so it will not act on a **manual** approach. To
  exercise stop/slowdown, an autonomous goal must be driving toward the
  obstacle (controller → `cmd_vel_nav` → monitor). Relayed to operator.

**2026-05-26T13:47-04:00** — Recording-coverage check during the seawall
test (operator question). Verified per-topic which recorder is subscribed:
the **logger** captures the debug chain — `collision_monitor/pointcloud`,
`collision_monitor_state`, `cmd_vel_nav`, `piloting_mode/autonomous/cmd_vel`,
`/tf` — and the **ad-hoc bag** adds `oak_forward/segmentation` (+
camera_info). Cloud is recorded BEST_EFFORT-matched (logger subscribes
best-effort), so it lands. Only gap: the danger-zone polygon topics were
unrecorded. Per operator, **added them to the logger `record:` list**
(`/bizzy/collision_monitor/slowdown_polygon` +
`/bizzy/collision_monitor/stop_polygon`, `geometry_msgs/PolygonStamped`).
**Caveat: takes effect on the next perception-group relaunch** (logger
reads the list at launch) — so this run's polygons are still only
reconstructable from config + TF; future runs capture them directly.
Note `collision_monitor_state` only publishes on action, so it's
sparse/empty during pass-through (not a recording gap).

## 9. Ad-hoc 1 h camera-video recording

**2026-05-26T13:14-04:00** — Operator: record video for an hour. Used the
established `bizzyboat_project11/scripts/record_camera_topics.sh 3600`
(ad-hoc capture, not a logger-YAML change). Records the 4 OAK
`image_raw/ffmpeg` streams + segmentation (raw/compressed) + camera_info
+ TF + diagnostics + robot_description + local_costmap, mcap/zstd_fast,
clean SIGINT flush at timeout. Confirmed "Recording..." Disk: 1.7 T free
(prior 45 min run was ~2.1 GiB). Output under `~/data/logs/bizzy_images/`.

**2026-05-26T14:14-04:00** — Recording completed clean (exit 0, full
window). Final: `~/data/logs/bizzy_images/bag_2026-05-26T13.01.29_ffmpeg_seg/`,
**3.1 GiB**.

## 10. Issue — new trackline sometimes resumes a stale mission

**Symptom (operator, ~13:59)**: running multiple tracklines at the seawall
at various speeds; sometimes on sending a **new** trackline the boat
**resumes/continues an older** one, even though camp's mission heartbeat
shows the new trackline was received. "Need to investigate."

**Live snapshot (~14:00, read-only, non-disruptive)**:
- `marine/status/mission_manager`: **`Current Nav Task: goto_override`**
  (type *goto* — NOT the new survey_line). Tasks tracked: `goto_override`
  (goto), `trackline0004` (survey_line), `done_hover` (hover).
- `follow_path/_action/status`: one ABORTED (6) + one EXECUTING (2).
- `run_tasks/_action/status`: long stack of ABORTED (6) — consistent with
  each new mission aborting the prior.
- `marine/heartbeat` at snapshot: standby / MANUAL / guided=false (between
  runs, operator on manual).

**Leading hypothesis — UNCONFIRMED, do not assert**: on GUIDED entry /
new-mission receipt, the mission_manager may advance through its existing
task list (a stale `goto_override` or a prior line) instead of cleanly
switching to the just-sent trackline. Camp shows the new line because the
MM holds it in its task set, but `Current Nav Task` is a leftover.
Directly related to git-bug **`7709673` — "Discuss: when to clear stale
mission on GUIDED mode entry."**

**Evidence availability**:
- ✅ `marine/status/mission_manager` **is recorded** (logger) → the
  `Current Nav Task` transitions are in this session's bag for offline
  replay. `behavior_tree_log` is recorded too.
- ⚠️ `follow_path`/`run_tasks` `_action/status` goal UUIDs **not recorded**
  (transient_local rosbag2 gap, §8) → can't correlate which goal_id
  actually executed offline. The QoS-override follow-up would close this.

**Recommended (dev-side, post-deployment)**: replay the mission_manager
status + `behavior_tree_log` from this bag around the reproductions; open a
follow-up issue tied to `7709673`. Capture any reproduction specifics the
operator recalls (speed, re-send timing, GUIDED toggle order).

## 11. Recovery

**2026-05-26T14:14-04:00** — Boat recovered. Stack still up at recovery.
Battery **28.14 V** — healthy, well clear of annunciator warn 23.0 /
error 21.5; no LVD drain this session (contrast the 2026-05-22 drain test).
gabby uptime **5 h 36 min** (boot 08:37:55 EDT). 1 h camera video completed
(§9).

## Files touched (this session, gabby-side, so far)

- `docs/logs/2026/2026-05-26_gabby_logs.md` — this log (new)
- `bizzyboat_project11/config/bizzyboat.yaml` —
  (1) add `/bizzy/FollowPath/pid/pid_state` to the logger `record:` list;
  (2) throttle `collision_pointcloud` to `period: 1.0` (1 Hz) on the VPN
  link only;
  (3) add `collision_monitor/slowdown_polygon` + `stop_polygon` to the
  logger `record:` list (takes effect next perception relaunch)

Cross-repo (gabby agent, **`seafloor_echoboat_project11`** @ `ffbc57a`):
- `echoboat_project11/launch/navigation_launch.py` — route
  controller/behaviors via `cmd_vel_nav`; remove `velocity_smoother` from
  active path; composition-path TODO
- `echoboat_project11/config/nav2_params.yaml` — `collision_monitor`
  `cmd_vel_in_topic` → `cmd_vel_nav`
