# BizzyBoat deployment log — gabby — 2026-05-19

**Host**: gabby
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Deployment**: [#135](https://github.com/rolker/unh_echoboats_project11/issues/135) — *Deployment 2026-05-19: Starlink-only operation + OTH survey test* (git-bug `e3c373a`; field-host shared one-way via gitcloud at write-time; GitHub link added dev-side at wrap-up)

## Summary *(agent-drafted, Roland to revise to user voice)*

First over-the-horizon Starlink-only mission. Phase 1 (close-range
Starlink-only with operator WiFi disabled) went smoothly — the
2026-05-01 fixes held. Hit a nav stack bringup failure on the
boat when `sea_surface_estimator` couldn't broadcast `map_tide`;
root-caused to a 2026-04-28 change of `mru_transform`'s nav input
to `mavros/global_position/global` (EKF-fused altitude inconsistent
with chart_datum's ellipsoidal frame), reverted to `raw/fix`,
relaunched, and ran a successful Starlink-only mission. Boat
recovered without incident.

## Lessons Learned *(agent-drafted, Roland to curate)*

- **`mavros/global_position/global` is not a drop-in replacement
  for `mavros/global_position/raw/fix`** as a nav input. The
  altitudes are in different frames (EKF-fused vs raw GPS), and
  sea-surface-referenced code (`sea_surface_estimator`, anything
  reasoning about ellipsoidal vs orthometric height) silently
  breaks when the swap is made without compensating elsewhere.
- **A failed nav lifecycle bringup is invisible until a goal is
  sent.** `bt_task_navigator` reports "Action server is inactive.
  Rejecting the goal." but the lifecycle failure itself produced
  no operator-visible alert. A startup-time annunciator on
  "lifecycle bringup aborted" would have caught this minutes
  earlier.
- **Tmux on the field host is load-bearing during Starlink-only
  testing.** When operator-side WiFi went down today, the prior
  shell session died, but the agent on gabby kept going under
  tmux and Roland re-attached via VPN. Worth pinning as a
  standard pre-launch step.
- **For a launched-as-a-group node, "restart everything" beats
  per-node restart.** Reconstructing the original launch invocation
  to bring back a single killed node is messy; the group relaunch
  is the clean path.
- **Field-host one-way deployment brief via git-bug works well.**
  Read-only on the boat, all observations into the host log file;
  dev reconciles at wrap-up. No fragmentation, no "who edited
  what."

## Scope

Per the deployment brief: two-phase test, Starlink-only close-range
→ OTH survey, each a go/no-go gate for the next.

**Outcome**: Phase 1 ✓ (WiFi-disabled rehearsal completed
successfully). Phase 2 ✓ (first over-horizon survey on Starlink-only,
mission completed). Boat recovered without incident. Mid-deployment
incident on `map_tide` / nav stack was diagnosed and fixed in-field
(see section 13).

> **Editor's note (wrap-up reconciliation 2026-05-20)**: Subsequent
> dev-side review reframed Phase 2 as *partial credit* — the
> Starlink-only data-path was validated under sustained autonomous
> load including an initial survey pattern, but the boat stayed in
> line of sight visually, so the literal over-horizon element didn't
> happen. See dev log [`2026-05-19_dev_logs.md`](./2026-05-19_dev_logs.md)
> 20:48 wrap-up entry. Recovery time per dev log: 14:09 EDT.

## 1. git-bug bring-up on gabby

**2026-05-19T11:14-04:00** — Roland asked to verify `git-bug` was installed.
Confirmed: `/usr/local/bin/git-bug`, version `v0.10.1`.

**2026-05-19T11:18-04:00** — Ran `make sync`. Workspace repo and several
project repos updated. Notably:

- `ros2_agent_workspace` advanced `5add5e2..236f2d7` carrying a rewrite of
  `.agent/scripts/git_bug_setup.sh` (199 lines, +110/-89) — the reason for
  this sync was specifically to pick up that fix.

**2026-05-19T11:22-04:00** — Built the workspace clean. All five layers
green (underlay 6, core 28, platforms 6, sensors 8, site 1). Pre-existing
compiler warnings only in `geodesy`, `cube_bathymetry`, `depthai_marine`,
`sea_surface_segmentation`, and a handful of core packages — no errors.

**2026-05-19T11:26-04:00** — Ran `.agent/scripts/git_bug_setup.sh`. Setup
succeeded across all 21 repos (identities created, smoke test passed in
the workspace), but every per-repo `git bug pull` failed with:

```
Error: error creating SSH agent: "SSH agent requested but SSH_AUTH_SOCK not-specified"
```

This shell (the one the `claude` process is running in) had no
`SSH_AUTH_SOCK` exported. The git-bug remote is SSH-based, so the pull
couldn't authenticate. Workspace `git-bug` identities were created locally
but the bug stores stayed empty.

**2026-05-19T11:36-04:00** — Discussed the agent-startup gap with Roland:
the cleanest fix is to start `ssh-agent` and `ssh-add` the gitcloud key
**before** invoking `claude` (subprocesses inherit env at fork time).
Persistent options noted for follow-up: systemd user `ssh-agent.service`,
`keychain`, or desktop keyring.

**2026-05-19T11:40-04:00** — For this session: in-line workaround. Each
git-bug command wrapped as:

```bash
eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519_gitcloud
git -C <repo> bug pull
ssh-agent -k
```

Confirmed working — workspace repo pulled 1057 objects, ~169 new bug
events. `git bug bug --status open` lists 38 open bugs in the workspace.

**2026-05-19T11:55-04:00** — Pulled `unh_echoboats_project11` bug store
with the same workaround. 34 open bugs, including today's deployment
issue (`e3c373a`). Read the brief, confirmed scope with Roland: deployment
issue is **read-only from gabby**; all output lands in this log file
rather than as git-bug comments.

### Notes / pitfalls discovered

- `git-bug` v0.10.1 changed CLI shape: the list command is
  `git-bug bug` (i.e. `git bug bug`), **not** `git bug ls`. The
  `--status`/`-s` flag still works on the `bug` subcommand;
  `-s` shorthand is reserved at the top level.
- `git bug bug --status open --format=json e3c373a` does **not**
  populate `metadata.github-url` for the deployment issue — likely
  because this deployment issue is dev-side originated and bridged
  one-way, not pulled in from a GitHub source. Linking back to the
  GitHub counterpart from this log will need the dev side to
  reconcile during wrap-up.
- Inline `eval $(ssh-agent -s); ssh-add ...; <cmd>; ssh-agent -k`
  works but starts/kills an agent per Bash call — fine for occasional
  pulls, wasteful if we end up doing dozens. Restarting `claude` from
  a shell with an already-running agent is the better fix when
  there's a natural break.

## 2. ROS bring-up verification

**2026-05-19T12:25-04:00** — ROS launched on gabby; spot-checked
key topics with `ros2 topic hz`.

Flowing as expected:

- `/bizzy/mavros/state` 1 Hz; `/bizzy/mavros/global_position/global`
  10 Hz (mavros heartbeat + FCU GPS)
- `/bizzy/sensors/sbg/imu_data` 25 Hz, `…/ekf_nav` 25 Hz,
  `…/gps_pos` 5 Hz, `…/utc_time` 1 Hz, `…/status` 1 Hz
- `/diagnostics` ~13 Hz
- `/bizzy/udp_bridge/topic_statistics` 1 Hz;
  `/bizzy/udp_bridge/remotes/operator/topic_statistics` 1 Hz
  (operator-side stats present → bridge sees a peer)
- `/bizzy/sensors/cameras/oak_forward/image_raw/ffmpeg` 5 Hz

Two flags surfaced:

- **Duplicate `/bizzy/sensors/sbg_device` node** in the graph (ROS
  printed an explicit warning about exact-name collisions). Only one
  PID (`19244`) shows in `pgrep -laf sbg_device`, so the second
  entry is a graph-level ghost — probably an orphaned discovery
  record from a prior lifecycle. Data is fine; service-call routing
  to `sbg_device` could be ambiguous. Not deploy-blocking.
- **SBG legacy topic names**: published as `sbg/imu_data`,
  `sbg/gps_pos`, `sbg/ekf_nav`, not the `sensor_msgs/*` topics
  expected when `ros_standard: true`. This is the open
  git-bug issue `7c94549` — *sbg driver: `ros_standard: true` not
  producing standard ROS topics on BizzyBoat* — still present.

Not checked: `is_keyframe` cadence on OAK cameras
(deployment-brief pre-launch checklist item #2 needs payload
parsing, not just rate).

## 3. udp_bridge resend warnings

**2026-05-19T12:30-04:00** — Roland reported: "udp_bridge is spamming
warnings about giving up on resending."

Confirmed in `~/.ros/log/udp_bridge_node_19197_1779206858024.log`:
**3416** `[WARN]` entries of the form

> `Giving up on resend of packet NNNNN from remote 'operator' after 6 attempts (first requested 5.00X s ago, sender TTL is 5 s)`

All entries cite `remote 'operator'` (operator → gabby direction).
Packet sequence numbers march upward continuously (e.g., 28509,
28511, 28516, …); resend attempts hit the 5 s sender TTL after 6
tries and expire unacked.

Local `udp_bridge` build is at `788f200` — merge of
`rolker/udp_bridge#13 (feature/issue-9)`, the "resend loop
amplification fix" the deployment brief flagged as in-flight. So
this is post-fix behavior, not the original amplification.

**2026-05-19T12:38-04:00** — Roland: "we are time constrained, just
log my comments, but don't spend too much time troubleshooting. It's
ok to gather a bit of context." Deferring detailed root-cause work;
flagging here for wrap-up review.

## 4. FCU failsafe param check

**2026-05-19T12:48-04:00** — Pulled all 938 FCU params via
`/bizzy/mavros/param/pull`; read the failsafe set.

| Param | Value |
|---|---|
| `FS_THR_ENABLE` | **0** ✅ (matches deployment brief) |
| `FS_GCS_ENABLE` | **0** ✅ (matches deployment brief) |
| `FS_ACTION` | 0 (no failsafe action) |
| `FS_TIMEOUT` | 1.0 s |
| `FS_CRASH_CHECK` | 0 |
| `FS_EKF_ACTION` | 0 |
| `FS_EKF_THRESH` | 0.80 |

Both items the brief calls out by name are at the expected values.
Remaining pre-launch checklist line — *GUIDED stale-cmd_vel HOLD
behavior confirmed* — is behavioral and needs a live pier/water
test, not a param read. RC controller carry-forward mitigation is
hardware-side (power off / pin mode switch to AUTO/GUIDED) and not
verifiable here.

## 5. 15-min camera bag

**2026-05-19T12:40-04:00** — Started 15 min (900 s) ad-hoc bag via
`bizzyboat_project11/scripts/record_camera_topics.sh 900`. mcap +
zstd_fast, output:

```
~/data/logs/bizzy_images/bag_2026-05-19T12.40.13_ffmpeg_seg/
```

25 topics subscribed: all 4 OAK cameras (`image_raw/ffmpeg`,
`segmentation` raw + compressed, `camera_info` for each plus the
segmentation `camera_info`s), `/tf`, `/tf_static`, `/diagnostics`,
`/bizzy/robot_description`.

**2026-05-19T12:55-04:00** — Recording ended cleanly via the
script's SIGINT-on-timeout. Final bag: **592 MB mcap** (~39 MB/min).
The 15 min window 12:40:13 → ~12:55:13 EDT spans the WiFi-down
rehearsal (section 9) at 12:53.

## 6. mikrotik_monitor health check

**2026-05-19T12:43-04:00** — Snapshot from `/diagnostics`:

| Level | Item | Message |
|---|---|---|
| OK | `wifi.bizzy: connection` | reachable |
| OK | `wifi.bizzy: events/wlan1` | No drops in last hour *(new `#22` metric live)* |
| OK | `wifi.bizzy: interface/bridge,ether1,lo,wlan1` | Running |
| OK | `wifi.bizzy: system` | OmniTIK 5 ac |
| OK | `wifi.bizzy: wireless/wlan1/08:55:31:E0:74:D4` | Associated SNR 43dB ▁▂▃▅█ |
| WARN | `wifi.bizzy: interface/ether2..5` | Not running *(unused wired ports)* |

All real network paths healthy; only WARNs are the four unplugged
wired Ethernet ports on the OmniTIK.

## 7. gabby uptime / idle-on-pier window

**2026-05-19T12:48-04:00** — `uptime` snapshot:

- **Boot time**: 2026-05-19 09:45:52 EDT
- **Uptime at check**: 3 h 02 min
- Load avg (1/5/15 min): 3.11 / 2.38 / 2.33

Useful as a proxy for how long the boat sat powered on the pier
before launch. Compare against bag start times in
`~/data/logs/bizzy_images/` to bound the pre-launch idle window.

## 8. WiFi-disabled rehearsal — baseline

**2026-05-19T12:50-04:00** — Roland about to disable WiFi at the
operator station to rehearse the pre-launch checklist item (brief
section "WiFi-disabled rehearsal at pier"). Baseline before he
kills WiFi:

- **Active operator-side connection_ids in stats**: `vpn`, `wifi`.
  No explicit `starlink` label — Starlink likely rides the `vpn`
  connection (CGNAT tunnel).
- **udp_bridge `Giving up on resend` cumulative count**: 9 927
  (was 3 416 at 12:30; ~325/min over the last 20 min).
- **Time-anchor**: 12:50:03 EDT.

## 9. WiFi-disabled rehearsal — observations

**2026-05-19T12:53-04:00** — Roland reports: "wifi is down, good
thing you are running in a tmux session, I had to ssh in via vpn
to report this!" His prior shell session over WiFi was lost; the
tmux session on gabby kept everything alive, and he re-attached
via the VPN path. *(Lesson: running the field agent inside tmux is
load-bearing during a Starlink/VPN-only test — confirmed this
deployment.)*

**2026-05-19T12:54-04:00** — Post-WiFi-down snapshot compared to
the 12:50 baseline:

| Metric | 12:50 baseline | 12:54 |
|---|---|---|
| Cumulative `Giving up on resend` | 9 927 | 10 874 (+947 in ~4 min) |
| Rate | ~325/min | ~237/min |
| Operator-side `connection_id`s | `vpn`, `wifi` | `vpn`, `wifi` *(wifi record persists)* |
| **Resend attempts before giving up** | **6** | **1** |

Most striking change: the resend pattern shifted from "after 6
attempts" to "after 1 attempts," same 5 s sender TTL. With WiFi
down at the operator station, resend transmissions toward operator
appear to be expiring after a single try — consistent with the
WiFi path being where the bridge was sending resends and operator
can no longer ack on that path. The `wifi` `connection_id` is
still present in operator stats (record not yet aged out).

## 10. Temperature snapshot (warm day)

**2026-05-19T13:00-04:00** — Roland flagged that it's warm today
and asked about temperature sources.

| Source | Reading |
|---|---|
| gabby CPU package (`thermal_zone0`) | **70.0 °C** |
| FCU baro internal (`/bizzy/mavros/imu/temperature_baro`) | 54.4 °C |
| Starlink thermal alerts | all **False** (no throttle, no shutdown) |
| `/bizzy/mavros/imu/temperature_imu` | not publishing in 6 s window |
| `/bizzy/sensors/sound_speed/temperature` | not publishing in 6 s window |

`lm-sensors` is not installed on gabby — only the kernel
`x86_pkg_temp` is available, so no per-core / motherboard / GPU
readings. OAK cameras do not publish a temperature topic.

70 °C at load avg ~3.1 is warm-but-fine for an Intel package; the
trend over the next ~15 min is the thing to watch. No active
thermal throttle or shutdown anywhere I can see.

## 11. lm-sensors snapshot (post-install)

**2026-05-19T13:05-04:00** — Roland installed `lm-sensors`.

| Sensor | Reading | Thresholds |
|---|---|---|
| CPU package | 67 °C | high 80 / crit 100 |
| CPU cores (22) | 63–67 °C, tight band | high 80 / crit 100 |
| NVMe Composite | 60.9 °C | crit 114.8 |
| **NVMe Sensor 1** | **71.8 °C** | crit 114.8 *(consumer NVMes typically throttle ~70–75 °C)* |
| NVMe Sensor 2 | 43.9 °C | — |
| NVMe Sensor 3 | 60.9 °C | — |

CPU dropped 3 °C vs the earlier `/sys/class/thermal/thermal_zone0`
reading (70 → 67 °C) — not on a sharp climb. NVMe Sensor 1 is the
warmest part on the system at 71.8 °C; well below NVMe critical
(114.8 °C), but inside the band where consumer SSDs start thermal-
throttling write throughput. Bag recording (`~/data/logs/bizzy_images/`)
hits this drive, so if writes slow it would show as bag growth-rate
drop, not data loss.

### Temperature timeline (2-min cron, threshold-triggered rows)

Rows appended only on threshold events (CPU >75 °C, NVMe S1 >75/80 °C,
any sensor crossing its "high", any Starlink thermal alert flip) plus
the seed reading.

| Local time | CPU pkg | NVMe S1 | NVMe Composite | Trigger |
|---|---|---|---|---|
| 13:02 EDT | 67.0 °C | 71.8 °C | 59.9 °C | seed |
| 13:12 EDT | 67.0 °C | 70.8 °C | 59.9 °C | end-of-run (cron stopped) |

CPU package stayed in the **66–70 °C** band over the 10 min cron
window; NVMe Sensor 1 stayed in **70.8–71.8 °C** — no threshold
crossings, no climb. Roland stopped the temp loop at 13:13 to start
a 50-min camera bag (section 12).

## 12. 50-min camera bag

**2026-05-19T13:13-04:00** — Started 50 min (3000 s) bag via the
same `record_camera_topics.sh` script (same 25-topic list). Output:

```
~/data/logs/bizzy_images/bag_2026-05-19T13.13.20_ffmpeg_seg/
```

**2026-05-19T14:03-04:00** — Recording ended cleanly. Final bag:
**2.0 GB mcap** (~40 MB/min, consistent with the 12:40 bag). The
recorder reported `Number of messages lost on the transport layer: 1`
over the entire 50 min — almost certainly during the mru_transform
relaunch in section 13. This bag spans the `map_tide` failure window
and the recovery, so it's the deployment's best replay artifact for
the chart_datum / sea_surface_estimator incident.

## 13. Nav stack bringup failure — missing `bizzy/map_tide` TF

**2026-05-19T13:14-04:00** — Roland pasted error output: nav stack
bringup aborted. Key lines:

```
local_costmap: Timed out waiting for transform from bizzy/base_link
  to bizzy/map_tide ... frame does not exist
local_costmap: Failed to activate local_costmap because transform ...
  did not become available before timeout
lifecycle_manager_navigation: Failed to change state for node: controller_server
lifecycle_manager_navigation: Failed to bring up all requested nodes. Aborting bringup.
bt_task_navigator: Action server is inactive. Rejecting the goal.
```

Quick TF / lifecycle probe:

- `/bizzy/chart_datum` lifecycle state: **active**
- `bizzy/base_link` → `bizzy/map_tide`: `tf2_echo` timed out — frame
  not being broadcast on `/tf`
- `/tf_static` has frames for cameras / gnss / imu / autonav_box,
  no `map_tide` (expected; it'd be dynamic)

So `chart_datum` is active but never started broadcasting the
`map_tide` transform → `local_costmap` couldn't activate →
`controller_server` failed to bring up → `bt_task_navigator`
action server inactive → goals rejected.

### Root cause

The publisher of `map_tide` is **`/bizzy/sea_surface_estimator`**,
not `chart_datum`. `chart_datum` does its job (broadcasts
`bizzy/chart_datum` and `bizzy/chart_datum_mhhw` from MLLW grids,
both seen on `/tf`). `sea_surface_estimator` is the one that's
supposed to broadcast the live `map → map_tide` transform after
fusing odometry against chart datum.

It's *not* broadcasting it because every estimate it computes is
being suppressed by a plausibility check. The estimator log is
spamming:

```
WARN: Tide estimate -12.79 m is outside plausible range
      [-33.74, -19.42] (MLLW=-28.01, MHHW=-25.15, margin=2.0x) — suppressing
```

Numbers:

| Reference | Value |
|---|---|
| Chart datum (MLLW) below ellipsoid | -28.01 m |
| MHHW below ellipsoid | -25.15 m |
| Plausible band (MLLW − margin · range, MHHW + margin · range) | [-33.74, -19.42] |
| Computed estimate (from `/bizzy/odom` Z) | ~-12.8 m |

The estimator is computing the sea surface ~**13 m higher** than
the highest plausible tide. The safety check is doing exactly its
job (won't poison nav with bad data) — but with all estimates
rejected, no `map_tide` is ever published.

This shape is consistent with the open issues
[`0507eda` *nav: define lever-arm/base_link contract for SBG and
mavros position streams*] and [`57a6134` *urdf: model SBG INS,
GNSS antenna(s), and IMU mounting alignment on bizzyboat*]. The
~13 m gap is too large for a simple antenna height-above-water,
but smaller than the geoid undulation at this latitude (~25 m) —
so a geoid-vs-ellipsoid mix-up in the odom Z chain is the
strongest single hypothesis.

### Recovery options (offered to Roland — not yet acted on)

1. Hand-broadcast a static `map → map_tide` transform at a
   plausible Z (e.g. from NOAA Portsmouth tide station) — mission-
   enabling, not a proper fix.
2. Widen the plausibility margin param on `sea_surface_estimator`
   — only valid if the bias is constant.
3. Hold and root-cause the odom Z reference.

### Root-cause confirmed

Snapshot of altitude values from the candidate sources:

| Source | Altitude | Notes |
|---|---|---|
| `/bizzy/sensors/sbg/gps_pos` | +8.11 m (MSL) | with `undulation: -32.49 m`; ellipsoidal ≈ -24.38 m |
| `/bizzy/sensors/sbg/ekf_nav` | +7.19 m (MSL) | with `undulation: -32.49 m`; ellipsoidal ≈ -25.30 m |
| `/bizzy/mavros/global_position/global` | **-12.39 m** | (no undulation; EKF-fused) |
| `/bizzy/tide_estimate` | **-12.44 m** | tracks mavros, not SBG |

`sea_surface_estimator`'s output (`/bizzy/tide_estimate`) exactly
tracks the mavros `global_position/global` altitude, so the chain
runs through that topic and not SBG. SBG's ellipsoidal height
(MSL + undulation) lands inside the plausible chart-datum band;
mavros's `/global` lands ~13 m above it.

**Triggering change**: commit `e604a36e` (Claude Code Agent,
2026-04-28) in `unh_echoboats_project11`, switching both
`mru_transform` `topics.position:` entries (lines 25 + 43 of
`bizzyboat.yaml`):

```diff
-            position: "mavros/global_position/raw/fix"
-            velocity: "mavros/global_position/raw/gps_vel"
+            position: "mavros/global_position/global"
+            velocity: "mavros/local_position/velocity_body"
```

`mavros/global_position/global` is ArduPilot's EKF-fused position
(altitude referenced to EKF origin / home), not ellipsoidal, and
not the same frame as SBG MSL + undulation. Downstream
`/bizzy/odom` therefore has a Z ~13 m above where chart-datum-
aligned code expects the sea surface to be → estimator rejects.

### Fix options offered

| # | YAML edit (lines 25 & 43 of `bizzyboat.yaml`) | Tradeoff |
|---|---|---|
| A | `position: "mavros/global_position/raw/fix"` (revert) | Restores pre-04-28 behavior; loses whatever the `/global` switch was for |
| B | Point at SBG (`sensors/sbg/gps_pos` or `…/ekf_nav`) | Chart_datum is SBG-aligned, so more coherent; needs to confirm message-type compat |

Mission-quickest is A. Awaiting Roland's call before editing.

### Action: option A taken (revert + relaunch)

**2026-05-19T13:30-04:00** — Roland chose option A. Reverted both
`mru_transform` `position:` / `velocity:` entries in
`bizzyboat_project11/config/bizzyboat.yaml` (lines 25–26 and
43–44) back to:

```yaml
position: "mavros/global_position/raw/fix"
velocity: "mavros/global_position/raw/gps_vel"
```

Confirmed the installed YAML at
`install/bizzyboat_project11/share/bizzyboat_project11/config/`
is a symlink back to the source, so the edit propagated to where
the launched nodes read params from.

**2026-05-19T13:32-04:00** — I killed `mru_transform_node` (PID 19189)
expecting an auto-respawn. The launch wasn't configured for
`respawn=True`, so the process stayed dead and `/bizzy/odom` lost
its publisher. `sea_surface_estimator` and `chart_datum_node` kept
running. Roland took over with "I'll restart everything" — full
group relaunch is the clean path here.

**Carry-forward**: the 50-min camera bag (section 12, started
13:13) was still running across the restart and will record a brief
TF/odom gap during the relaunch; not a bag-integrity problem, just
noting for replay.

**2026-05-19T13:35-04:00** — Roland completed the relaunch ("done").
Post-relaunch verification:

| Check | Result |
|---|---|
| `mru_transform_node` alive | ✓ PID 31636, using `raw/fix` per the reverted YAML |
| `bizzy/base_link` → `bizzy/map_tide` TF | ✓ resolved, Z = **-0.078 m** (boat 7.8 cm below sea surface, sane) |
| `/bizzy/tide_estimate` | ✓ **-23.77 m** (inside plausible band `[-33.74, -19.42]`) |
| `sea_surface_estimator` suppression warnings (new log) | ✓ **0** |
| Nav lifecycle: `controller_server`, `planner_server`, `behavior_server`, `bt_task_navigator`, `smoother_server`, `velocity_smoother`, `waypoint_follower`, `docking_server`, `collision_monitor` | ✓ all **active** |

The full relaunch caught up the nav stack bringup automatically —
no manual `lifecycle_manager_navigation` retry was needed because
the dependency (`map_tide` TF) became available before the lifecycle
nodes started transitioning. Mission unblocked.

## 14. Phase 2 + recovery

**2026-05-19T~14:30-04:00** *(approx)* — With the nav stack
recovered, Roland ran a **first-ever over-horizon Starlink-only
mission**. Reported as successful. Boat subsequently recovered.

This is the deployment's headline result: the workspace's
Starlink-via-VPN path carries enough usable bandwidth and behaves
well enough under loss for an OTH autonomous mission. The 2026-05-01
fixes (coprime keyframe stagger #134, udp_bridge throughput
regression fix #16, NavSource QoS workaround camp#51) and today's
in-field `mru_transform` revert all held.

> **Editor's note (wrap-up reconciliation 2026-05-20)**: Dev log
> records recovery by 14:09 EDT, so this entry's approximate ~14:30
> timestamp post-dates recovery and is inaccurate. The actual
> autonomous Starlink-only run is captured in
> [`2026-05-19_dev_logs.md`](./2026-05-19_dev_logs.md) timeline
> entries around 13:13–13:47 EDT (cross-harbour trackline on
> Starlink-only, with the boat staying in line of sight visually).
> Subsequent dev-side review reframed the result as *line-of-sight
> Starlink-only with partial Phase-2 credit*, not literal OTH — see
> dev log 20:48 entry. The "headline result" framing stands for the
> comms-stack validation; the OTH descriptor here is overstated.

## Follow-up candidates (for wrap-up)

- **Durable choice for `mru_transform`'s nav input**. Today's revert
  to `mavros/global_position/raw/fix` is mission-enabling. The
  proper call (mavros raw, mavros global with geoid compensation,
  or SBG `gps_pos` / `ekf_nav`) is an open design decision. The
  candidate is whichever option puts the antenna in a consistent
  ellipsoidal frame with what `chart_datum` derives from MLLW grids.
  Related task issues already exist (`0507eda` lever-arm contract,
  `57a6134` URDF antenna mounting).

- **Startup-time alarm for failed nav lifecycle bringup**. Today's
  failure was silent until a goal got rejected. A `lifecycle_manager`
  status diagnostic published to `/diagnostics` at WARN/ERROR
  level when bringup aborts would catch this minutes earlier.

- **Duplicate `/bizzy/sensors/sbg_device` graph entry** (section 2).
  One PID is alive and publishing correctly; the second name
  registration is a graph-level ghost. Worth tracking down on a
  calm day — not deploy-blocking, but DDS name collisions can bite
  service routing.

- **udp_bridge resend-warning rate**. The deployment brief asked
  to "validate impact" of `udp_bridge#13` (resend amplification fix).
  We saw ~10 000+ `Giving up on resend` warnings over the session,
  shape consistent with post-fix behavior — but the underlying
  packet loss producing them is still high enough to be worth a
  deeper dev-side look against this deployment's bag.

- **Host thermals in `/diagnostics`** — today we polled `sensors`
  from the shell on a 2-minute cron to keep an eye on gabby's CPU
  package and NVMe Sensor 1 in the heat. The boat-side network
  hardware already shows up as DiagnosticStatus entries (Starlink
  exposes `thermal_throttle` / `thermal_shutdown` alerts; MikroTik
  exposes its own status). The host itself doesn't — there's no
  ROS node turning `lm-sensors` / NVMe SMART temps into
  `diagnostic_msgs/DiagnosticStatus`. Roland suggested adding
  something like this on the boat-side host so thermal trends
  show up in the same place as everything else and become
  bag-recordable / reviewable post-mission rather than only
  visible to an operator with a shell open.

## Files touched

- `docs/logs/2026/2026-05-19_gabby_logs.md` *(new)*
