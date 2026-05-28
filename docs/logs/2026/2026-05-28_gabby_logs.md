# 2026-05-28 — gabby log (BizzyBoat deployment)

**Mode**: field (gitcloud origin)
**Deployment**: git-bug `6445516` — *Deployment 2026-05-28: validate nav2
config-split cutover + 240 footprint* (GitHub link to be added dev-side at
wrap-up; first end-to-end trial of `/start-deployment` skill,
[ros2_agent_workspace#501](https://github.com/rolker/ros2_agent_workspace/issues/501)).
**Host**: gabby
**Started**: 2026-05-28 12:16 -04:00
**Dev-side wrap-up TODO**: stamp this log's path under the deployment issue
body's `## Logs` section (field-side is read-only, per memory + skill 4b).

## 1. git-bug cache trust on session start [start-deployment trial]

**2026-05-28T12:16-04:00** — Ran `/start-deployment` on gabby. Skill found
the project config (`unh_echoboats_project11/.agents/deployment.yaml`,
just landed via PR #194) and routed to field-side three-state detection.
First attempt at the configured `field_pull` failed:

```bash
$ git bug pull gitcloud
Error: unable to resolve URL for remote: <nil>
```

Two compounding issues, both pre-existing not skill-introduced:

1. **No `gitcloud` git remote on this repo** (or any of the 17 workspace
   repos on gabby). The `add_remote.py --remote gitcloud …` setup that
   creates the `gitcloud` alias was never run here. On field hosts `origin`
   already points at the gitcloud URL, so the alias would be a duplicate,
   but the deployment.yaml's commands assume it exists.
2. **No `SSH_AUTH_SOCK` in the claude shell** — same prior-session gap
   recorded in `2026-05-19_gabby_logs.md:84` and reinforced in
   `2026-05-26_gabby_logs.md:38`. Even if the remote name resolved,
   `git bug pull` would fail at SSH auth.

**Initial mis-routing**: the skill's three-state detection consulted the
local git-bug cache (which had not been refreshed since 2026-05-26 11:44)
and saw the **closed-since** 5/26 issue (`20a49fc`) as still open, with
no 5/28 issue present. That routed to "resume ongoing" against the
wrong deployment.

**Fix applied** — documented in `2026-05-26_gabby_logs.md:38-67`
two-step:

```bash
git -C <repo> fetch origin 'refs/bugs/*:refs/bugs/*' 'refs/identities/*:refs/identities/*'
rm -rf <repo>/.git/git-bug/cache
git -C <repo> bug bug --label deployment --status open
```

Plain `git fetch` works without `SSH_AUTH_SOCK` (uses `~/.ssh/config`
IdentityFile directly); the cache reindex on first `git bug bug` after
removal picks up all the new refs. Open count surfaced today's issue
(`6445516`) and dropped the now-closed 5/26.

**Skill trial meta-observations** (for `/start-deployment` v2):

- **Field-side `field_pull` is broken as written for this repo.** The
  yaml's `git bug pull gitcloud` needs (a) the `gitcloud` remote alias
  to exist and (b) an SSH agent. Neither is guaranteed on a gabby
  claude shell. The skill currently runs `field_pull` before consulting
  the cache, so on failure it silently falls through to a stale-cache
  read instead of warning that issue state may be untrustworthy.
- **Recommended v2 behavior**: either the skill or the yaml command
  should use the plain-git two-step that survives both missing-remote
  and missing-SSH-agent (`git fetch origin 'refs/bugs/*…' && rm cache`),
  or it should pre-flight check `SSH_AUTH_SOCK` and the remote name
  before claiming the local view is fresh. A silent fall-through to a
  multi-day-stale cache is the highest-impact failure mode here: it
  causes the three-state detection to give a confidently wrong answer.
- **Workspace-side follow-up**: `add_remote.py --remote gitcloud …`
  hasn't been run on gabby (and likely the other field hosts). Worth
  adding to the field-host onboarding checklist, or making it a
  pre-condition the skill verifies.
- **Where the skill did help**: the urgency contract was loaded
  immediately and shaped subsequent triage (sterile cockpit kept the
  troubleshooting tight; mitigate-before-diagnose said "fix the local
  view enough to proceed, leave a workspace-side cleanup for wrap-up").
  Three-state detection routed correctly once the cache was fresh.
- **Where the skill stumbled**: the stale-cache path. See above.
- **Missing workspace doc**: `.agents/deployment.yaml` references
  `.agent/knowledge/field_mode_hotfix.md` — that file doesn't exist
  in the workspace. Wrap-up follow-up.

**Carry-forward operational state after fix**: cache fresh, 5/28 issue
read, urgency contract loaded, ready for on-boat verification work
(deployment issue §1-5: 240 footprint, rig/reflex via cutover, nav2
clean bring-up, plus the marine_nav PR test plan in issue comment #2).

## 2. Stack bring-up — mru→/global startup race recurrence

**2026-05-28T12:27-04:00** — Operator started the nav stack. All
operational nodes present in the graph (~110 nodes incl. 4 OAK cameras
and `oak_forward/segments_to_pointcloud_reflex`, so the
[seafloor#29](https://github.com/rolker/seafloor_echoboat_project11/pull/29)
+ [#185](https://github.com/rolker/unh_echoboats_project11/pull/185) rig+reflex
cutover **is intact** on this build — addresses deployment issue
must-verify #2 at the build/graph level; on-water functional verification
still pending).

**2026-05-28T12:28-04:00** — Nav2 lifecycle partial-activation, stable
across two checks 12s apart (not transient mid-launch):

| Node | State |
|---|---|
| `controller_server` | active [3] |
| `smoother_server` | active [3] |
| `local_costmap` | active [3] |
| `planner_server` | **inactive [2]** |
| `behavior_server` | **inactive [2]** |
| `collision_monitor` | **inactive [2]** |
| `global_costmap` | **unconfigured [1]** |

**2026-05-28T12:29-04:00** — Confirmed the upstream cause: `map_tide`
frame does **not** exist (`tf2_echo map_tide base_link` → `Invalid frame
ID "map_tide" ... frame does not exist`). This is the documented
[[project-mru-global-startup-race]] signature: with `mru_transform`
configured against `mavros/global_position/global`, the Nav2 lifecycle
can lose the startup race for `map_tide` TF, leaving global_costmap
unable to configure and stalling the cascade.

**Recommended action — operator full relaunch of the nav launch group.**
Per memory, this fix has worked previously once the upstream chain
(mavros / mru_transform / chart_datum) reaches steady-state, which they
have by now (mavros, mru_transform, chart_datum all present in the
graph). Not attempting a single-node restart from here — `ros2 launch`
groups don't auto-respawn and per-node restart is messy
([[feedback-dont-kill-launched-nodes]]).

**Must-verify #3 (nav2 clean bring-up) currently FAILING** — needs
re-launch + re-check before any on-water work.

## 3. Correct diagnosis — stale perception build, NOT the mru→/global race

**2026-05-28T12:33-04:00** — Operator pushed back ("not seeing errors in
the launches"). Re-investigated; the §2 mru→/global attribution was
**wrong**. Memory matched the symptom but the cause is different this
time.

**Concrete evidence:**

| Artifact | mtime | Contains `SeaSurfaceRelayLayer`? |
|---|---|---|
| `unh_marine_perception/sea_surface_segmentation/src/sea_surface_relay_layer.cpp` | 2026-05-28 12:06 | yes (source, just pulled today) |
| `sensors_ws/install/sea_surface_segmentation/share/.../costmap_plugins.xml` | 2026-05-28 (symlink-installed) | yes (advertises class) |
| `sensors_ws/install/sea_surface_segmentation/lib/libsea_surface_layer.so` | **2026-05-22 15:33** | **NO** (`nm -D` shows only `SeaSurfaceLayer` symbols) |

**Smoking gun in `~/.ros/log/planner_server_27036_*.log`:**

```
[INFO]  [bizzy.global_costmap.global_costmap]: Using plugin "sea_surface_relay"
[ERROR] [bizzy.global_costmap.global_costmap]: Caught exception in callback for transition 10
[ERROR] Original error: MultiLibraryClassLoader: Could not create object of class type
        sea_surface_layer::SeaSurfaceRelayLayer as no factory exists for it.
[WARN]  Callback returned ERROR during the transition: configure
[FATAL] Lifecycle node global_costmap does not have error state implemented
```

**Why "no errors in launches"**: launch's `ExecuteProcess` just spawns
the node; configure-time pluginlib failures emit to the node's own
rosout log under `~/.ros/log/<launch_id>/`, NOT to the launch console.
Lifecycle_manager treats global_costmap as "ERROR" and silently stops
cascading further activations — no exception thrown out to launch.
[start-deployment trial] — worth surfacing this in skill v2: a
post-launch lifecycle-state check would catch this in ~10 seconds.

**Chain of changes that produced the skew:**

1. `seafloor_echoboat_project11#34` / PR #35 (merged 2026-05-28 10:52) —
   added `sea_surface_relay` to `global_costmap`'s plugin list in
   `nav2_params.base.yaml`. *Config-only, but creates the demand for
   the new plugin class.*
2. `unh_marine_perception` (sea_surface_segmentation) — added the
   `SeaSurfaceRelayLayer` source + manifest entry. Pulled fresh today
   by `make sync`.
3. **Missing step**: rebuild `sea_surface_segmentation` so the `.so`
   actually contains the new class. `make sync` doesn't build.

**Fix:**

```bash
cd /home/field/project11/layers/main/sensors_ws
./build.sh sea_surface_segmentation
```

Then operator re-launches the nav group. Re-verify all 7 nav2
lifecycle nodes report `active`.

**Secondary observation** (will resolve with primary fix, noting for
completeness): planner_server log also warns "No inflation layer found
in costmap configuration" — that's the global_costmap plugin chain
aborting at the failed `sea_surface_relay` configure, before reaching
`inflation_layer`. Same root cause.

## 4. Rebuild + relaunch

**2026-05-28T12:44-04:00** — Operator approved rebuild. Ran from
sensors_ws:

```bash
colcon build --symlink-install --packages-select sea_surface_segmentation
```

Clean in 37s (stderr was PCL `CMP0144`/FLANN_ROOT policy warnings,
unrelated). `libsea_surface_layer.so` mtime updated to 12:44; size
16.4 MB → 25.9 MB; `nm` confirms full `SeaSurfaceRelayLayer` symbol
set now present (registerPlugin, onInitialize, updateBounds,
updateCosts, gridCallback, dtors). Symlink-install means no further
copy step.

Awaiting operator relaunch of the nav group; will re-check 7 nav2
lifecycle nodes all `active` after.

## 5. Second stale-build hit — `SetTaskFailed` BT node

**2026-05-28T12:45-04:00** — Operator relaunched after the
sea_surface_segmentation rebuild. global_costmap configured cleanly
this time (`Using plugin "sea_surface_relay"` followed by chart-layer
grid loads `US2EC04M.000` / `US5PSMCC.000` / `US4NH1BD.000` /
`US3EC10M.000` and a tide-offset publication `6.04338 m` — sea_surface
fix confirmed working).

New blocker further down lifecycle:

```
[bt_navigator-6] [ERROR] Exception when loading BT: Error at line 116:
   -> Node not recognized: SetTaskFailed
[bt_navigator-6] [ERROR] Error loading XML file:
   …/marine_nav_bt_task_navigator/share/.../behavior_trees/run_tasks.xml
[lifecycle_manager-10] [ERROR] Failed to change state for node: bt_task_navigator
[lifecycle_manager-10] [ERROR] Failed to bring up all requested nodes. Aborting bringup.
```

`SetTaskFailed` is the new BT action introduced by **PR #37 (issue #25)**
on `unh_marine_navigation` — one of the 5 marine_nav PRs in the
deployment issue's comment #2 test plan. Same stale-build class as §3:
`run_tasks.xml` (symlink-installed) references it, but
`libmarine_nav_behavior_tree_bt_plugins.so` was last built 4/08 and
the symbol wasn't there.

**Sweep across `marine_nav_*` packages:**

| Package | Source mtime | Install/build .so mtime | Action |
|---|---|---|---|
| marine_nav_behaviors | 5/28 12:06 | 4/08 | rebuild |
| marine_nav_behavior_tree | 5/28 12:06 | 5/27 14:34 | rebuild (§3 fix lives here) |
| marine_nav_bt_task_navigator | 5/27 14:30 | 5/27 14:34 | already current |
| marine_nav_crabbing_path_follower | 5/26 | 5/27 14:33 | already current |
| marine_nav_interfaces | — | 5/27 | already current |
| marine_nav_tasks | 3/27 | 5/27 | already current |
| marine_nav_utilities | 5/27 14:30 | 5/27 | already current |

**Rebuild ran:**

```bash
cd /home/field/project11/layers/main/core_ws
colcon build --symlink-install --packages-select marine_nav_behavior_tree \
    marine_nav_behaviors marine_nav_bt_task_navigator \
    marine_nav_crabbing_path_follower
```

Result: `marine_nav_behavior_tree` 20.5 s + `marine_nav_behaviors` 9.8 s
(real compiles); `marine_nav_bt_task_navigator` 1.7 s +
`marine_nav_crabbing_path_follower` 1.7 s (configure-only, no source
delta from 5/27 build). `nm` confirms `SetTaskFailed` (constructor,
providedPorts, tick, dtors) now present in
`libmarine_nav_behavior_tree_bt_plugins.so`.

**[start-deployment trial] meta-observation**: this is the **second**
stale-build hit in the same session. The pattern — `make sync` pulls
fresh source + symlink-installs data files (XML/YAML), but doesn't
rebuild — has now bitten twice. Worth proposing for skill v2: either
post-sync staleness check ("these N packages have install older than
source"), or fold a build pass into the `/start-deployment` pre-flight.
The current fail-mode is fully silent at launch (errors in node log,
not console), and the lifecycle stall reads identically to the
mru→/global TF race from memory — easy to misattribute, which I did.

Awaiting second relaunch.

## 6. Lifecycle clean — Must-verify #3 satisfied

**2026-05-28T12:54-04:00** — Operator relaunched. All 8 nav2 lifecycle
nodes report `active [3]`:

| Node | State |
|---|---|
| controller_server | active |
| planner_server | active |
| behavior_server | active |
| smoother_server | active |
| global_costmap | active |
| local_costmap | active |
| collision_monitor | active |
| bt_task_navigator | active |

`/bizzy/mavros/state` confirms `connected: true` (FCU up).

`tf2_echo map_tide base_link` silently times out at 8 s but no longer
emits the prior `Invalid frame ID "map_tide"` — the frame is registered
in the TF tree (would otherwise be an explicit error within ~1 s);
the echo just isn't printing within budget, almost certainly rmw_zenoh
discovery / buffer-warm latency. Global costmap is active and chart
grids loaded with a tide-offset publication (§5), which it couldn't do
without a usable `map_tide`. Not chasing further; will surface if
planning misbehaves.

**Deployment issue Must-verify status:**
- [x] **#3 — nav2 comes up cleanly** (Collision Monitor + costmaps + planner all active).
- [ ] **#1 — 240 footprint re-tune** — pending on-water survey-path planning.
- [ ] **#2 — rig + reflex intact after the cutover** — graph-level presence
  confirmed in §2 (4 OAK cameras + `oak_forward/segments_to_pointcloud_reflex`);
  on-water reflex behavior verification pending.

## 7. costmap_window silent at startup — transient_local + zenoh race

**2026-05-28T12:58-04:00** — Operator asked whether windowed costmaps
were getting to the boat. Survey found:

- `/bizzy/local_costmap/costmap_windowed` was **not publishing** (5 s
  `topic hz` returned zero messages).
- `udp_bridge` stats had no entry for it (the bridge config in
  `bizzyboat.yaml` does list it on both VPN throttled `period: 2.0`
  and WiFi unthrottled — `local_costmap_windowed: {source:
  local_costmap/costmap_windowed}` — but with no source publication
  there was nothing to forward).
- `costmap_window` node was `active [3]` per lifecycle, but
  `ros2 node info` showed **zero data subscribers** (only
  `/parameter_events`). Its source (in
  `marine_nav_utilities/src/costmap_window_node.cpp`) creates a
  subscription to relative `costmap` (resolves to
  `/bizzy/local_costmap/costmap`) at construction, with
  `reliability_best_available()` + `durability_best_available()`.
- `/bizzy/local_costmap/costmap` publisher (from `local_costmap` node)
  is `TRANSIENT_LOCAL` + `RELIABLE` + KEEP_LAST(1) — the latched
  single-grid pattern.
- `marine_nav_utilities` is NOT stale (built 5/27, source 5/27) — not
  a stale-build issue this time.

**Operator workaround**: added a `udp_bridge` subscription to
`/bizzy/local_costmap/costmap` as a debug. That added a *second*
subscriber on the source topic, which woke rmw_zenoh's discovery
exchange, the latched message got delivered to both subscribers, and
the cropper finally started producing.

**After workaround — verified end-to-end:**

| Path | Rate |
|---|---|
| `/bizzy/local_costmap/costmap_windowed` (local) | **1.38 Hz** |
| udp_bridge VPN (throttled, `period: 2.0` → ~0.5 Hz) | 0.47 Hz, 18 KB/s success |
| udp_bridge WiFi (unthrottled) | 1.35 Hz, 53 KB/s success |

**Diagnosis**: classic transient_local + zenoh discovery race —
the publisher's transient_local cached message didn't reach the
single-subscriber path on startup, leaving costmap_window silent
indefinitely until *something else* subscribed and shook discovery.
Same race **family** as the deployment-issue PR #45 hover-publisher
fix (`marine_nav_behaviors`, #42 — guard against DDS type-discovery
race) — this codebase has now seen it on two separate publishers.

**Stability** of the workaround: once the dual-subscriber wake-up
happened, both subscriptions should remain matched until a node
restarts. A relaunch of the nav group would re-roll the race; the
udp_bridge sub on `local_costmap/costmap` (if kept) keeps the
shaker present.

**Follow-up candidates (post-deployment)**:
- Open an issue on `marine_nav_utilities` (or feed into the existing
  `unh_marine_navigation` race-family track from #42) to harden
  `costmap_window_node`'s subscription against this — e.g., explicit
  reliability + transient_local match, or a one-shot wake-up.
- Or: keep the operator-side `local_costmap/costmap` subscription
  as a permanent bridge entry (it's already useful per the 5/26 log
  observation about subscribers on local_costmap), with a config-side
  comment noting it doubles as the discovery shaker for
  `costmap_window`.

[start-deployment trial] — meta-note: the cropper-silent fault was
fully silent (zero messages, no log entry, lifecycle `active`).
A topic-hz pre-flight on the operator-relevant bridge-out topics
(`costmap_windowed`, `collision_pointcloud`, `published_footprint`,
nav `cmd_vel_nav`, etc.) would catch this class in `<30 s` and could
be a useful skill addition.

## 8. Launch — boat in water

**2026-05-28T13:17-04:00** — Operator: boat is in the water.

Snapshot at launch:
- `/bizzy/mavros/state` — `connected: true, armed: true, guided: true,
  mode: LOITER, system_status: 4` (MAV_STATE_ACTIVE; holding position).
- `/bizzy/mavros/battery` — **28.56 V**, current 0.01 A (LOITER, no
  commanded thrust). Clear of annunciator thresholds (warn 23.0, error
  21.5).

Phase: launch → underway. Scribe mode.

## 9. Ad-hoc 45 min camera recording

**2026-05-28T13:25-04:00** — Operator: record video for 45 min.
Launched `bizzyboat_project11/scripts/record_camera_topics.sh 2700`
(established pattern; ad-hoc, not a logger-YAML change — see 5/26 §9).
Background process bh6p83353.

**2026-05-28T14:10-04:00** — Recording completed clean (exit 0, full
2700 s window). Recorder shutdown sequence in output (Pausing → cache
flush → Recording stopped → Event publisher exit). Final:
`~/data/logs/bizzy_images/bag_2026-05-28T13.25.54_ffmpeg_seg/`,
**2.9 GiB** (single 3.01 GB mcap + 27 KB metadata.yaml). Slightly
smaller than 5/26's 3.1 GiB / 60 min (≈ 51 MB/s in both cases —
consistent FFMPEG-stream bitrate).

## 10. Small-obstacle (mooring buoys) not marking in costmap

**2026-05-28T13:30-04:00** — Operator: an obstacle in the front camera
isn't registering in the costmap. Narrowed: *small obstacles like
mooring buoys aren't making it*, but the chain itself looks intact —
oak_forward publishes `segmentation` + `segmentation/camera_info`,
local_costmap (multi-source SeaSurfaceLayer) is subscribed to all
4 cameras, `/bizzy/sea_surface/lethal_grid` topic exists.

**Follow-on observation from operator**: *small obstacles do show up
on the costmap when farther away — suggesting they project to larger
areas the costmap picks up.*

That observation localizes it to **per-cell water-pixel dilution at
close range**. SeaSurfaceLayer's marking params aren't set in either
config file (BizzyBoat overlay or seafloor base) — running at C++
defaults from `sea_surface_segmentation/src/occupancy_buffer.hpp`:

| param | default | role |
|---|---|---|
| `hit_log_odds` | 0.85 | added per obstacle-pixel observation |
| `miss_log_odds` | −0.40 | added per water-pixel observation |
| `clamp` | 5.0 | bound on accumulated log-odds |
| `lethal_threshold` | 1.0 | log-odds ≥ this → lethal |
| `decay_half_life_s` | 30.0 | unobserved evidence half-life |
| `maximum_range` | 150.0 (overlay) | obstacle range cutoff |

Close-range geometry concentrates many buoy-and-water pixels into the
same 1–2 cells; even modest segmentation noise gives e.g.
`3 hit × 0.85 − 7 miss × 0.40 = −0.15` and the cell stays free.
Distance spreads buoy pixels across one cell each, giving nearly-pure
hit votes — matches the "works far, fails close" pattern.

**Tuning #1 applied (live, no relaunch)** — most targeted fix for the
dilution mode:

```bash
ros2 param set /bizzy/local_costmap/local_costmap \
    sea_surface_layer.miss_log_odds -0.10
# verify → Double value is: -0.1
```

Plugin validator accepted. Existing accumulated log-odds in cells
aren't reset; effect kicks in on the next segmentation frames.

Tradeoff: clearing of formerly-lethal cells slows down (less water-
pixel pressure to bias them free). Decay_half_life_s = 30 s still
bounds it — not a permanent stamp. If close-range marking still
doesn't catch up to buoys, escalation candidates are
`lethal_threshold 1.0 → 0.5` and then `hit_log_odds 0.85 → 1.2`,
both also live-settable. Pulsing one at a time so any phantom marks
(wakes, glare) are attributable.

## 11. Hover location appears latched at first hover point

**2026-05-28T13:33-04:00** — Operator: *"Can't seem to change the
hover location, it seems to be stuck at the first hover point."*

No troubleshooting from this side yet — recording the observation.

Cross-reference (not asserted): same class of pattern as
[5/26 §10 stale-mission issue](./2026-05-26_gabby_logs.md) (new
trackline sent, mission_manager kept executing the prior task),
related to git-bug `7709673` *"Discuss: when to clear stale mission
on GUIDED mode entry."* Whether this hover-latch is the same
mechanism or distinct (e.g. HoverTask not preempting on a re-sent
Hover override) needs replay against the recorded session.

Evidence-availability note: `marine/status/mission_manager` and
`behavior_tree_log` are in the deployment recorder's topic list, so
the `Current Nav Task` / BT-execution transitions across these
hover sends are captured for offline replay. `follow_path` /
`run_tasks` `_action/status` UUIDs are still in the transient_local
rosbag gap (5/26 §8) → may not be able to correlate exact goal IDs
offline.

## 12. SeaSurface tuning #1 — partial: large obstacles in, small still out

**2026-05-28T13:37-04:00** — Operator (after the §10 `miss_log_odds
-0.40 → -0.10` tweak settled): *"A sailboat is showing up, but not
the mooring balls."*

The sailboat is large enough that even at close range its hit pixels
dominate the per-cell vote; mooring balls remain below threshold.
Tuning #1 alone is **insufficient for mooring-ball-scale targets**.
Escalation candidates (per §10):

- `sea_surface_layer.lethal_threshold 1.0 → 0.5` — lets a single
  decent hit cross to lethal. Best next try.
- `sea_surface_layer.hit_log_odds 0.85 → 1.2` — last resort; biggest
  false-positive risk (wakes, glare, sunlit chop).

## 13. Hover workaround — slow tight survey pattern

**2026-05-28T13:38-04:00** — Operator: *"Doing a slow tight survey
pattern to simulate a hover."*

Workaround for the §11 hover-latch — survey lines are dispatchable
where hover re-targeting isn't right now.

## 14. SeaSurface tuning #2 declined — likely upstream issue

**2026-05-28T13:39-04:00** — Offered `lethal_threshold 1.0 → 0.5` as
the next pulse. Operator declined: *"Not sure how that would help."*

On reflection, the operator's instinct is reasonable. Post-§10 the
math is forgiving:
- 1 hit + 5 misses per frame = `0.85 − 0.50 = +0.35` per frame
- At ~5 Hz over a 5 s dwell that's ~+8.75 log-odds → well over the
  current threshold of 1.0, let alone 0.5

So if a buoy still isn't marking on a slow survey, the limiter is
**not** lethal_threshold. The most likely upstream causes:
- Segmentation model not classifying mooring-ball pixels as non-water
  at this range/lighting (false-negative in the model itself).
- Per-frame projection landing on different cells each frame (IMU /
  GPS jitter, TF chain noise) so accumulation never sticks to one
  cell.
- Mooring-ball pixels falling under whatever ground-plane validity
  filter the projection uses (waterline geometry — buoys sit ON the
  surface; if the projection treats only above-waterline pixels as
  obstacles, a low ball might be culled).

Confirming any of these needs a look at `oak_forward/segmentation`
output (topic echo on the Image — would prompt) or the cropped lethal
grid in `sea_surface/lethal_grid` for live coverage. Not pursued from
this side without operator go-ahead — boat is currently driving the
survey.

## 15. SeaSurface tuning — buoys flicker on/off, clearing too aggressive

**2026-05-28T13:45-04:00** — Operator: *"Buoys are showing up
occasionally but disappearing quickly."*

That ruled out the segmentation-false-negative hypothesis from §14 —
the model IS classifying buoys at least intermittently. The
remaining failure mode is **active clearing** by water-classified
frames. Post-§10 at miss=−0.10, the cell loses 0.10 log-odds per
water frame × ~5 Hz = 0.50/s. A buoy mark at +1.2 log-odds drops
below the 1.0 threshold in ~0.4 s, fully cleared in ~2.4 s — matches
the observed flicker.

**Tuning pulse #2 applied** (continuing on the same lever):

```bash
ros2 param set /bizzy/local_costmap/local_costmap \
    sea_surface_layer.miss_log_odds -0.02
# verify → Double value is: -0.02
```

At miss=−0.02, the per-frame water-pixel penalty is 5× smaller; a
mark at +1.2 now takes ~10 s to drop to threshold instead of 0.4 s,
giving intermittent re-hits a chance to refresh the cell before it
clears.

Held in reserve (operator's call when this lands): `clamp 5.0 → 10.0`
to give confident cells more "headroom" before clearing —
independent lever, can stack with miss=−0.02.

Watch-out: tradeoff curve gets steeper as miss approaches 0 — any
false-positive marks (wake, glare) stick around longer. `decay_half_
life_s = 30 s` still bounds it.

## 16. SeaSurface tuning — −0.02 too noisy, settled at −0.06

**2026-05-28T13:48-04:00** — Operator: *"That made lots of noise show
up, especially around the edge of the costmap."*

Predicted-tradeoff materialized: at miss=−0.02 phantom marks built up
faster than they cleared, and edge cells (sparse-observation regions
at the rolling-window boundary) accumulated false-positive evidence
with too little clearing pressure. Clamp=10 follow-up cancelled —
direction was wrong, not under-pushed.

Reverted to miss=−0.10 (the §10 working point); operator then
requested *"go back half way."* Set to **−0.06** as the midpoint
between the noisy −0.02 and the buoy-flickering −0.10. Live value
verified.

Current SeaSurface tuning state on the boat:

| param | live value | default |
|---|---|---|
| `sea_surface_layer.miss_log_odds` | **−0.06** | −0.40 |
| `sea_surface_layer.hit_log_odds` | 0.85 | 0.85 |
| `sea_surface_layer.lethal_threshold` | 1.0 | 1.0 |
| `sea_surface_layer.clamp` | 5.0 | 5.0 |
| `sea_surface_layer.decay_half_life_s` | 30.0 | 30.0 |
| `sea_surface_layer.maximum_range` | 150.0 | (overlay) |

None of these are persisted to the config files — a relaunch of the
nav group resets to default −0.40. Wrap-up follow-up: if −0.06 (or
whatever final value settles) ends up the keeper, lift it into
`nav2_overlay.yaml`'s `sea_surface_layer:` block.

## 17. Collision avoidance firing repeatedly (pointcloud-fed, not costmap)

**2026-05-28T13:43-04:00** — Operator: *"Collision avoidance might
be kicking in."* Confirmed from `~/.ros/log/collision_monitor*.log`:
**331 state transitions** total; the last ~25 entries (within
seconds of the read) show stop / slowdown firing every 0.2-1.5 s
in rapid alternation.

**Structural correction**: the §10/§15/§16 SeaSurfaceLayer tuning
**does not affect collision avoidance** — different input path.
- Costmap path: `oak_forward/segmentation` → `SeaSurfaceLayer` →
  `local_costmap` / `sea_surface/lethal_grid` → planner.
- CA path: `oak_forward/segmentation` →
  `oak_forward/segments_to_pointcloud_reflex` →
  `collision_monitor/pointcloud` → `CollisionSlowdown` /
  `CollisionStop` polygons → cmd_vel scaling/zeroing.

So the SeaSurfaceLayer `miss_log_odds` adjustments have been tuning
the planner's view, not the safety-stop reflex. The CA churn is
driven by the *reflex pointcloud* being noisy — pointcloud points
crossing into the forward `[[20,3],[20,-3],[0,-3],[0,3]]`
slowdown polygon (`min_points: 4`) and the stop polygon
(`min_points: 5`).

Cross-reference: this may also be implicated in §11 (hover-latch).
If CA is repeatedly zeroing `cmd_vel`, the hover/goto position-
control loop can't actually translate to the new target — boat
sits while perceptual triggers fire.

Levers (all live-settable, not applied without operator sign-off):
- `/bizzy/collision_monitor` `CollisionSlowdown.min_points` 4 → 8+
  (reject sparse phantoms; trigger only on clusters)
- `/bizzy/collision_monitor` `CollisionStop.min_points` 5 → higher
- Polygon `min_height`/`max_height` ±2 m → tighter band if sky/glare
  points are leaking in
- `segments_to_pointcloud_reflex` filtering — need to inspect its
  param surface to find the right knobs

Held — operator deciding (offered: (a) bump min_points on Slowdown
+Stop, (b) hold, (c) inspect reflex node params first).

## 18. Goto failed after retries → mission resumed [PR #37 territory]

**2026-05-28T13:44-04:00** — Operator: *"My goto seems to have
failed after a few tries and it's resuming the mission."*

This matches the **expected** behavior of deployment-issue PR #37
(`unh_marine_navigation` #25 — `RecoveryNode` + `SetTaskFailed`):
> *After 3 exhausted retries the line is recorded `failed` (camp
> heartbeat shows `status: failed` on that task) — NOT silently
> marked done. The MISSION continues: subsequent lines run normally.*

Not asserted as definitively-the-new-behavior — that needs offline
BT-log replay to confirm `RecoveryNode` invocation, `Wait` action,
and the 3-retry path. The recorder is capturing `behavior_tree_log`
and `marine/status/mission_manager`, so the evidence is in the bag.

Plausibly mechanistically linked to §17: if CA was zeroing cmd_vel
repeatedly during the goto, `SimpleProgressChecker` would have
flagged "no 0.5 m progress in 10 s," `FollowPath` would `ABORT`,
RecoveryNode would invoke `Wait`, retry, repeat — exhaust → task
failed → mission resumes. The new path (PR #37) is the right
result; the *triggering condition* (CA-induced progress stall) is
the underlying noise problem.

Same cross-reference applies to §11 hover-latch — earlier "hover
stuck at first point" may have been goto-style position requests
failing via the same path, with the mission-resume falling back to
whatever the prior task was.

## 19. SeaSurface tuning #3 — lethal_threshold pulse

**2026-05-28T13:46-04:00** — Operator approved the threshold drop
(separately from the CA discussion in §17, which remains untouched).

```bash
ros2 param set /bizzy/local_costmap/local_costmap \
    sea_surface_layer.lethal_threshold 0.8
# verify → Double value is: 0.8
```

Math after this + §16: a single full hit (0.85) per cell now exceeds
threshold (0.8) immediately. Marginal-evidence buoys (1-of-2 case
from the prior message) should mark on their first reliable hit.

Updated live SeaSurface tuning state:

| param | live value | default |
|---|---|---|
| `sea_surface_layer.miss_log_odds` | −0.06 | −0.40 |
| `sea_surface_layer.lethal_threshold` | **0.8** | 1.0 |
| `sea_surface_layer.hit_log_odds` | 0.85 | 0.85 |
| `sea_surface_layer.clamp` | 5.0 | 5.0 |
| `sea_surface_layer.decay_half_life_s` | 30.0 | 30.0 |
| `sea_surface_layer.maximum_range` | 150.0 | (overlay) |

Held in reserve: `hit_log_odds 0.85 → 1.2` (last resort, highest
phantom risk) and `clamp 5.0 → 10.0` (persistence headroom).

CA-side: **no changes**, per operator direction.

## 20. Survey line abandoned with buoy in path [PR #37 / PR #40 validation]

**2026-05-28T13:48-04:00** — Operator: *"I moved the survey pattern
so one of the buoys, the one that shows up better, is in the path.
Seems like the boat gave up on the line and jumped to the next one."*

Direct on-water cause-and-effect: the §19 `lethal_threshold = 0.8`
pulse made the marking decisive enough for the better-imaged buoy to
persist as a lethal cell. With a lethal cell on the planned line,
the planner can't form a route that re-acquires the line through it
within line-following tolerance — line aborts, mission advances.

**This is also the expected new behavior validation for two
deployment-issue PRs:**
- **PR #37 / unh_marine_navigation #25** — *"no more silent done-on-
  fail."* Pre-fix: failed line silently marked done; mission moves
  on as if nothing happened. Post-fix: line is recorded `failed`,
  mission continues. Operator observed exactly that progression.
- **PR #40 / unh_marine_navigation #28** — *"line-transition zero-
  cmd window bounded."* If the planner exhausted at the (now
  bounded) 4 retries instead of stalling at 20, that route gets
  surfaced rather than degrading silently.

Distinguishing which mechanism actually fired (planner exhausted vs.
FollowPath ABORT via SimpleProgressChecker → RecoveryNode → 3-retry
exhaustion → SetTaskFailed) requires:
- Camp heartbeat showing the line `status: failed` (not `done`).
- BT log in the launch dir: `RecoveryNode` invoked? `Wait` ran
  (~5 s)? `ComputePathThroughPoses` retry count?
- `marine/status/mission_manager` `Current Nav Task` transition.

All of those are in the deployment recorder's topic list — captured
in this session's bag for offline replay.

Phantom-risk side-check: at threshold = 0.8 + miss = −0.06, are
there any wake/glare false-positives also persisting along the
planned lines (i.e., spurious lethals that would similarly abort
*other* lines)? Worth a quick visual look in CAMP's costmap view if
the boat now skips multiple consecutive lines without an obvious
real obstacle on each.

## 21. Dark skies degrading buoy segmentation [environmental]

**2026-05-28T13:51-04:00** — Operator: *"The dark skies seem to be
making buoys harder to detect as obstacles."*

Direct upstream finding — confirms the §14 segmentation-false-
negative hypothesis as the dominant limiter for small targets
today, *under these conditions*. Implications:

- The §10 / §16 / §19 SeaSurfaceLayer tuning has been compensating
  downstream for an upstream input shortage. There's a hard limit
  to that compensation: if the segmentation model outputs zero non-
  water pixels for a given buoy in a given frame, no log-odds
  adjustment can produce a mark. We've already pushed
  `miss_log_odds` and `lethal_threshold` near the noise floor; the
  remaining levers (`hit_log_odds`, `clamp`) primarily amplify
  whatever signal IS coming through — diminishing returns, growing
  phantom risk.
- Wake/glare false positives go DOWN under dark skies (less reflected
  glint), but so does true-positive coverage. Net: the current
  tuning that produced noise in brighter conditions may be more
  tolerable now — but small-buoy coverage stays partial.

**Wrap-up follow-ups for the dev session:**
- Quantify segmentation hit-rate per buoy class vs. ambient light in
  the recorded bag (`oak_*/segmentation` + `image_raw/ffmpeg` →
  classify per-pixel + correlate with diagnostic sun/sky exposure).
  Likely a training-data gap on the segmentation model — overcast /
  low-contrast conditions under-represented.
- Check whether the OAK forward camera's auto-exposure / gain is
  saturating or compressing under low ambient — if so, exposure
  tuning may be cheaper than a model retrain.
- Re-baseline SeaSurfaceLayer tuning under each lighting regime
  (clear / overcast / dusk) and document keeper values in
  `nav2_overlay.yaml` rather than running at C++ defaults that
  weren't tuned for any of these conditions.

## 22. Goto into buoy-rich area — boat orbiting, not failing

**2026-05-28T13:55-04:00** — Operator: *"Tried a goto to an area
with more buoys, but seems stuck going around a buoy."*

Planner log says it's NOT the planner: last `ComputePath` failure /
retry / cancel was at 1779989216 (~20 min ago, a manual goal cancel).
Recent planner output is just tide-offset updates from global_costmap
(now 1.74 m, dropping ~0.05 m over the last 5 min as the tide ebbs).
No `STATUS_ABORTED`, no `Plan not found`, no Smac retry exhaustion.

So the planner is producing routes successfully — the "stuck" is
downstream. Most consistent reading given the running state:

- Buoy-rich area genuinely has many real lethal cells from buoys
  that ARE marking.
- §19 `lethal_threshold = 0.8` is keeping marginal hits stickier —
  more cells flagged in the dense area than would be at default 1.0.
- §16 `miss_log_odds = −0.06` makes those marks decay slowly under
  intermittent (dark-sky-§21) coverage.
- §17 collision_monitor is still at default `min_points` 4/5 with
  the reflex pointcloud feeding it. In a buoy-rich region with the
  costmap marks persisting, the reflex pointcloud also has more
  enduring "obstacles" in the slowdown/stop polygons — boat keeps
  getting throttled to 30 % or stopped.
- Net behavior: planner produces a detour, controller starts
  executing, CA chops cmd_vel before forward progress completes,
  planner re-plans on the moved frame and produces a slightly
  different detour, boat crab-orbits the same buoy.

Three levers to consider (held — operator's call):
- (a) **Revert §19** `lethal_threshold 0.8 → 1.0` (back to default).
  Fewer marginal cells → less cluttered local picture for planner
  *and* less reflex-pointcloud-feeding density. Cost: §20's
  desirable "buoy stops a line" demo regresses for marginal targets.
- (b) **CA tuning** per the §17 offer — bump
  `CollisionSlowdown.min_points` 4 → 8+, possibly
  `CollisionStop.min_points` 5 → 8+. Less CA churn, more
  forward progress; cost: small real obstacles need more cluster
  density to trigger.
- (c) **Pull the goto** (operator-side action) — try a different
  goto target / different area / move on. Validation of (a) or
  (b) is post-deployment work; live ops only needs the boat to be
  drivable.

## 23. Manual nudge clear of paralyzing target

**2026-05-28T13:54-04:00** — Operator escalated: *"Boat seems mostly
paralyzed by a close target."* → *"Just nudged it with the USB
controller."* Operator-driven mitigation via MANUAL — boat moved
clear of the close-target CA-trigger geometry.

No autonomous-stack changes. CA still at default `min_points` 4/5
per operator direction. The §22 observation pattern — paralysis at
close range from CA polygon trigger storm in dense buoy/dark-sky
conditions — is now a logged wrap-up follow-up candidate (alongside
the wider CA-tuning + reflex-node-tuning discussion from §17, §22).

## 24. Transit to pier — planner routing around obstacles cleanly

**2026-05-28T13:57-04:00** — Operator: *"Transit back to the pier
shows planning around obstacles, looks good!"*

Positive validation data point. Current cumulative tuning
(miss=−0.06, lethal_threshold=0.8, hit/clamp/decay at default,
CA untouched) is producing clean obstacle-avoidance routes at
transit speeds in less-dense regions — the typical operational
case. The dense-buoy paralysis (§22 / §23) is an edge case
specific to:
- Close-range targets entering CA polygons before forward motion
  clears them,
- Dense obstacle field amplifying CA polygon triggers,
- Dark-sky-degraded segmentation (§21) generating partial-coverage
  marks that compound,

— rather than a baseline behavior of the deployment build.

## 25. Recovery

**2026-05-28T14:09-04:00** — Operator: *"Recovered."* Boat out of
the water. Gabby uptime 1 day, 5h 38m. Phase: underway → recovery.

§9 ad-hoc 45 min recording (started 2026-05-28T13:25:54) is in
`~/data/logs/bizzy_images/bag_2026-05-28T13.25.54_ffmpeg_seg/`,
about ~2 min remaining to its clean SIGINT-flush termination at
14:10:54.

**Tuning persistence note for next relaunch**: the live SeaSurface
tunings from §10 (`miss_log_odds −0.06`) and §19
(`lethal_threshold 0.8`) are in-process only — a nav-group relaunch
resets to C++ defaults (miss=−0.40, threshold=1.0). Lifting any
final keeper values into `nav2_overlay.yaml`'s
`sea_surface_layer:` block is a wrap-up follow-up — captured under
§16 already; flagging again here so it's not forgotten across the
phase change.

No Summary / Lessons sections per per-host log convention — those
land in the dev log at wrap-up.
