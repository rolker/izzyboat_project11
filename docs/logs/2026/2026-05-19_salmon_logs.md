# BizzyBoat deployment log — salmon — 2026-05-19

**Host**: salmon
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Deployment**: [#135](https://github.com/rolker/unh_echoboats_project11/issues/135) — "Deployment 2026-05-19: Starlink-only operation + OTH survey test" (git-bug `e3c373a`; created dev-side 2026-05-19T11:01:22-04:00; no GitHub bridge configured field-side at write-time, so the GH link was added dev-side at wrap-up)

## Summary

_(user-curated, filled in at wrap-up)_

## Lessons Learned

_(user-curated, filled in at wrap-up)_

## 1. Pre-flight: git-bug visibility on salmon

**2026-05-19T11:24-04:00** — Operator asked to verify git-bug for the
deployment workflow. `git-bug` v0.10.1 installed at
`/usr/local/bin/git-bug`. Workspace is field-mode on this host (origin
`git@gitcloud:field/ros2_agent_workspace.git`). Deployment-log
convention expects the dev-opened deployment issue to be readable via
git-bug, since salmon has no `gh` CLI / GitHub credentials.

**2026-05-19T11:25-04:00** — Ran `make sync` from workspace root. Clean
except two remote-ahead repos picked up:

- `udp_bridge` — fast-forward `e6670ed..788f200` (issue-9/15 work plans
  + resend constants + connection rate-limit tests)
- `camp` — fast-forward `ea2e83e..0083095` (issue-50 progress and
  `src/camp/nav_source.cpp` edits)

Both relevant to today's deployment scope (Starlink-only validation of
the post-2026-05-01 fixes).

**2026-05-19T11:27-04:00** — In
`layers/main/platforms_ws/src/unh_echoboats_project11`, ran `git-bug bug`
— **empty list**. `git ls-remote origin 'refs/bugs/*'` showed 200+ bug
refs on the gitcloud remote, so the data exists. Triggered `git-bug
pull`: fetch succeeded (439 objects transferred from gitcloud), but the
merge step failed with:

```
No identity is set.
To interact with bugs, an identity first needs to be created using
"git bug user new" or adopted with "git bug user adopt"
: merge error: No identity is set.
```

Result: no bugs surfaced. Today's deployment issue invisible
field-side, which is the failure mode the deployment-log convention
relies on git-bug to prevent.

## 2. Root cause: identity setup scoped to workspace only

**2026-05-19T11:30-04:00** — Read
`/home/field/project11/.agent/scripts/git_bug_setup.sh`. The script
`cd`s to `ROOT_DIR` (workspace root) at line 37 and only operates
there. No iteration over project repos. Each gitcloud project repo
maintains its own `refs/bugs/*` and `refs/identities/*`, so the
workspace-level identity doesn't carry over — every project repo under
`layers/main/*_ws/src/` was missing a git-bug identity, and `git-bug
pull` cannot merge fetched bug refs without one.

Two pre-existing gates in the script, both correct as-is for field mode:

- **Identity creation** needs only the local `git config user.name`
  + `user.email`. `Field User <field@ccom.unh.edu>` is set globally on
  salmon. **No `gh` credentials needed.**
- **GitHub bridge** step is guarded by `[[ "$remote_url" ==
  *"github.com"* ]]` (line 88 in the old script). For gitcloud-origin
  repos the bridge step is skipped cleanly; `gh` not being installed on
  salmon is irrelevant for the gitcloud-origin repos. (It does mean the
  workspace repo can't get a bridge here either, but the workspace is
  also gitcloud-origin on salmon, so the same guard applies.)

The gap is identity-only, scoped to project repos.

## 3. Patch: per-repo loop in `git_bug_setup.sh`

**2026-05-19T11:34-04:00** — Refactored
`/home/field/project11/.agent/scripts/git_bug_setup.sh`:

- Factored the per-repo logic into `setup_repo_gitbug()` (inner steps
  unchanged: identity create/adopt → conditional bridge → `git-bug pull`).
- Driver loops over workspace root plus every match of
  `layers/main/*_ws/src/*/` via bash glob.
- Existence check uses `[ -e "$repo_dir/.git" ]` so worktrees (where
  `.git` is a file pointing into the linked repo) and regular repos
  are both handled.
- Bridge step keeps its github.com origin guard. For non-GitHub origins
  the loop logs "Non-GitHub origin — skipping bridge step." and proceeds
  to the pull, which works over plain git transport once identity
  exists.
- Smoke test stays workspace-scoped (one summary line, not per-repo).

Edit applied in-tree on salmon — workspace is field-mode on this host,
so AGENTS.md field-mode rules permit direct edits to `main`.

## 4. Verification across all overlay project repos

**2026-05-19T11:35-04:00** — Re-ran
`/home/field/project11/.agent/scripts/git_bug_setup.sh`. Workspace
identity already existed (idempotent). **40 project repos processed**
across `core_ws`, `platforms_ws`, `sensors_ws`, `simulation_ws`,
`site_ws`, `ui_ws`, and `underlay_ws`. Each produced:

```
Creating git-bug identity: Field User <field@ccom.unh.edu>
<identity hash>
ℹ️  Non-GitHub origin — skipping bridge step.
Pulling git-bug data from origin...
✅ git-bug sync complete.
```

No failures. Workspace smoke test reported `38 open issues cached`.

**2026-05-19T11:36-04:00** — Confirmed in
`layers/main/platforms_ws/src/unh_echoboats_project11`:

- `git-bug user` now lists 3 identities — `Field User` just created
  here, plus `Matthew Diakonov (m13v)` and `Claude Code Agent`
  inherited from prior gitcloud history.
- `git-bug bug status:open` → **34 open bugs**.
- `git-bug bug status:closed` → **48 closed bugs**.
- Today's deployment issue **`e3c373a`** — "Deployment 2026-05-19:
  Starlink-only operation + OTH survey test" — visible with full body
  (scope, hosts, pre-launch checklist, carry-forward items from
  2026-05-01).

This unblocks the field side of the deployment-log workflow: salmon
(and gabby on first sync) can now read the deployment issue without
GH access.

## 5. Field commit and push

**2026-05-19T11:37-04:00** — Sourced
`.agent/scripts/set_git_identity_env.sh "Claude Code Agent"
"roland+claude-code@ccom.unh.edu" "Claude Opus 4.7 (1M context)"`,
then committed the script change as a field change on the workspace's
`main` and pushed:

- Commit: `236f2d7` — `git_bug_setup: configure identity + sync across
  all overlay project repos` (author `Claude Code Agent
  <roland+claude-code@ccom.unh.edu>`).
- Push: `5add5e2..236f2d7  main -> main` on
  `gitcloud:field/ros2_agent_workspace.git`.

## 6. Workspace build after sync

**2026-05-19T11:47-04:00** — `make build` from workspace root. ~11
minutes wall time, exit 0 across every layer. Build report:

| Layer | Packages (OK) | Notes |
|---|---|---|
| underlay | 22 / 22 | stderr only from audio_capture, audio_play, geodesy, norbit_driver, r2sonic (warnings) |
| core | 24 / 24 | stderr from manda_coverage, marine_autonomy, marine_charts, marine_nav_behavior_tree, marine_nav_bt_task_navigator, marine_nav_crabbing_path_follower, udp_bridge |
| platforms | 12 / 12 | stderr from mru_transform |
| sensors | 17 / 17 | stderr from cube_bathymetry, depthai_marine, marine_radar_layer, marine_radar_tracker, marine_tools, sea_surface_segmentation, simrad_halo_radar |
| simulation | 10 / 10 | clean |
| ui | 7 / 7 | stderr from camp, rqt_marine_radar, rqt_udp_bridge, rviz_sonar_image |
| site | 1 / 1 | clean |

All "stderr" entries are compiler warnings (unused-parameter etc. in
`camp/src/camp/*`); nothing fatal, no error escalations. Picks up the
post-sync code in `udp_bridge` (resend constants + rate-limit tests +
remote-node resend) and `camp` (`nav_source.cpp` QoS edits from
PR #51) without changes to the rest of the tree.

Workspace is ready for the deployment-issue pre-launch checks (OAK
cadence bench-verify, sustained `iperf3 -u -t 600 -b 5M`, WiFi-disabled
rehearsal).

## 7. Operator-side ROS nodes started

**2026-05-19T11:57-04:00** — Operator reported operator-side ROS
nodes started on salmon. Verified via `ros2 node list` /
`ros2 topic list`:

- **Operator stack**: `/operator/camp`, `/operator/diagnostic_aggregator`,
  `/operator/udp_bridge`.
- **Operator-side boat-control nodes** (run on salmon, drive `bizzy` via
  `udp_bridge` — namespaced under `/bizzy` by convention):
  `/bizzy/command_bridge_sender`, `/bizzy/joy_node`, `/bizzy/joy_to_helm`,
  `/bizzy/joint_state_publisher`, `/bizzy/robot_state_publisher`.
- **Network / support**: `/mikrotik_monitor`, `/ping_monitor`,
  `/starlink_diagnostics`, `/molab/johnny5/johnny5_node`,
  `/rosbag2_recorder` (recording active).
- **rqt panels**: three rqt nodes alive
  (`/rqt_gui_cpp_node_48863`, `/rqt_gui_cpp_node_48866`,
  `/rqt_gui_py_node_48863`).
- Operator `udp_bridge` has registered **one remote**: `bizzy`
  (`/operator/udp_bridge/remotes/bizzy/{bridge_info,topic_statistics}`).

`ros2 topic echo --once /bizzy/marine/heartbeat` timed out at 3 s — no
boat-side heartbeat received yet. Topic exists in the operator
namespace (bridge has it registered) but no data has flowed.
Consistent with operator-only startup.

## 8. Pre-restart re-sync

**2026-05-19T12:06-04:00** — Operator flagged that the running ROS
stack predates the `make build` (pre-sync `udp_bridge` + `camp`
binaries). Plan: restart with the new build before bringing the boat
side up.

Re-ran `make sync` from workspace root as a final pre-launch check.
All repos `✅ Already up to date` except:

- `unh_echoboats_project11` — **skipped: Uncommitted changes
  detected.** That's this log file in `docs/logs/2026/`. Expected per
  README convention (field hosts push logs at end of session); not a
  blocker.

No code deltas, so no rebuild needed before restart. Pre-launch
checklist item *"`make sync` on dev; field hosts pulled latest from
gitcloud"* is satisfied for salmon.

**2026-05-19T12:07-04:00** — Belt-and-braces `make build` re-run.
Fast incremental pass (~1 min), all 7 layers ✅, no stderr — confirms
the install tree matches the current source. Stack is ready to be
relaunched on the new binaries.

## 9. Boat deployed; operator stack relaunched on new build

**2026-05-19T12:20-04:00** — Operator reported boat is deployed.
Verified state on salmon:

- **Operator stack restarted**: `launch_ros` PID 48850 → 57526; rqt
  PIDs also new (57546/57547 vs 48863/48866). So the operator side is
  now running on the post-`make build` install (with `udp_bridge`
  resend + rate-limit changes and `camp` NavSource QoS workaround in
  effect).
- **Boat heartbeat flowing**: `ros2 topic echo --once
  /bizzy/marine/heartbeat` returns a fresh message — was timing out
  at 11:57.
- **First heartbeat values**:
  - `piloting_mode`: **standby**
  - `marine_autonomy_standby`: `true`
  - `connected`: `true`
  - `armed`: `true`
  - `guided`: `true`
  - `mode`: **LOITER** (FCU mode)
- **Node-list delta vs 11:57**: `/mikrotik_monitor` not present in
  the current node list (was running pre-restart). Not investigating
  further unless operator flags it.

Bridge link to `bizzy` is healthy enough to deliver heartbeat;
end-to-end UDP-bridge → CAMP path is exercised.

## 10. Diagnostics snapshot (post-deploy)

**2026-05-19T12:26-04:00** — Operator confirmed CAMP shows green;
captured `/diagnostics_agg` for cross-reference. Toplevel reports
**ERROR**; 86 status entries total, 64 OK.

**ERROR (3)**
- `/Boat` — "Error" (rollup)
- `/Other` — "Error" (rollup)
- `/Other/ping_monitor: Ping: ping.op: bencloud` —
  **Unreachable (100% packet loss)**

**WARN (9)**
- `/Boat/MAVROS/mavros: Mount` —
  *"Can not diagnose in this targeting mode"*
  (drives `/Boat/MAVROS` rollup → Warning; everything else under
  MAVROS is OK)
- `/Other/mikrotik_monitor: wifi.bizzy: interface ether{2,3,4,5}` —
  **Not running** (×4)
- `/Other/ping_monitor: ping.bizzy: dns_google` — **25% packet loss**
- `/Other/teltonika_monitor: router.bizzy: interface mob1s2a1` — Down
- `/Other/teltonika_monitor: router.bizzy: mwan3 mob1s2a1` — notracking
- `/Other/teltonika_monitor: router.bizzy: mwan3 wan1` — notracking

**STALE (9)** — `/Boat/{MikroTik,Ping,Starlink,Teltonika}` and the
parallel `/Operator/*` set. The `/Operator/*` buckets exist in the
aggregator config but receive no input: the actual monitor nodes
(`mikrotik_monitor`, `ping_monitor`, etc.) publish under `/Other`
instead. (Pre-existing aggregator-config issue, not new today.)

**MAVROS happy-data sanity check** (from the same snapshot):
- Battery 28.49 V, 0.0 A
- GPS 3D fix, 38 sats visible, EPH 0.39 m / EPV 0.70 m
- Heartbeat 1.0 Hz, 1129 since startup
- FCU mode LOITER, ArduPilot, System ACTIVE
- MAVROS Router 309 114 routed / 0 dropped; FCU endpoint rx 9988 B/s

**Cross-reference to today's Phase 1 scope** (Starlink-only, WiFi
disabled at operator):
- `wifi.bizzy ether2-5 Not running` — consistent with WiFi disabled.
- `teltonika mob1s2a1 Down`, `mwan3 notracking` — consistent if
  cellular isn't being used today.
- `ping.bizzy: dns_google 25% loss` — boat's outbound DNS path lossy.
- `ping.op: bencloud Unreachable` — operator-side, not in today's
  scope. **Looks like a stale monitor target on the operator config;
  pending operator confirmation.**

Operator reports the CAMP view is green — the toplevel ERROR is
driven by stale-promotion of categories that haven't been re-bucketed
into `/Boat/*` post-restart, plus the `bencloud` monitor.

## 11. udp_bridge resend-give-up warning storm

**2026-05-19T12:30-04:00** — Operator reported `udp_bridge` is
spamming warnings. Sampled `/rosout` for ~6 s and captured **5386
distinct WARN entries** from `operator.udp_bridge`, all of the same
template:

> `Giving up on resend of packet NNNNNN from remote 'bizzy' after 5
> attempts (first requested ~5.00 s ago, sender TTL is 5 s)`

Packet numbers sampled span at least 983046–983094 with gaps,
indicating both sequential give-ups (e.g. 983046–983057 contiguous)
and sporadic singletons (983070, 983093, 983094…). Same template,
varying packet IDs.

This is from the **new resend tracking code** just deployed
(`udp_bridge` commit range
`e6670ed..788f200` from this session's `make sync`, which added
`udp_bridge/include/udp_bridge/resend_constants.h` plus
`udp_bridge/test/test_remote_node_resend.cpp` and the resend logic in
`src/remote_node.cpp`). The text reports that resend requests issued
by the operator side for missing packets are reaching the sender's
5 s TTL window before they can be delivered — so the sender drops
them after 5 attempts.

**Cross-reference to deployment scope**: the issue body lists
[`rolker/udp_bridge#13`](https://github.com/rolker/udp_bridge/pull/13)
("resend loop amplification fix") as in-flight. The merged code
includes `resend_constants.h` and the `remote_node` resend logic;
whether that PR specifically is merged or is still in flight against
this baseline is **pending operator confirmation**. Either way, the
warning storm is worth capturing as Starlink-only baseline behavior
to feed back into the post-deployment review.

Not investigating root cause unless the operator asks. Recording as
field observation.

## 12. mikrotik_monitor: working on boat side, missing on operator side

**2026-05-19T12:45-04:00** — Operator asked whether `mikrotik_monitor`
is working. Two distinct answers:

### Boat-side: working fine

The boat-side `mikrotik_monitor` is publishing fresh diagnostics that
arrive at salmon via `udp_bridge` (which is why no node matching
`mikrotik` appears in operator-side `ros2 node list` — the node runs
on gabby and its `/diagnostics` topic forwards through the bridge).
Sampled at 2026-05-19T16:43:03+00:00 (≈12:43 EDT):

- Target: `MikroTik OmniTIK 5 ac`, RouterOS 7.22 stable, uptime
  2h57m, CPU load 5 %, `connection: reachable`
- `events/wlan1`: no drops in the last hour (`drops_last_5min = 0`,
  `drops_last_60min = 0`)
- `wireless/wlan1/08:55:31:E0:74:D4`: **Associated, SNR 35 dB,
  signal-strength −73 dBm @ HT40-3** — link healthy
- `interface/{bridge,ether1,lo,wlan1}`: Running ✅
- `interface/ether{2,3,4,5}`: Not running (unused router ports)

### Correction to §10

§10 attributed `wifi.bizzy ether2-5 Not running` to "WiFi disabled at
the operator station". That was **wrong**: `wifi.bizzy` is the
**boat-side** MikroTik (the OmniTIK 5 ac on the boat), and ether2-5
are just its unused LAN ports — normal for this router model. The
Phase 1 "WiFi disabled at operator" condition isn't visible via
`mikrotik_monitor` on this run because the operator-side mikrotik
monitor isn't running (see below).

### Operator-side: declared but not running

**2026-05-19T12:48-04:00** — Investigated why operator-side
`mikrotik_monitor` and `teltonika_monitor` are absent from the node
list. Findings:

- Launch invocation: `ros2 launch bizzyboat_project11
  operator_core_launch.py` (PID 57526, started 12:08 EDT from pts/5).
  Resolved via `ps -ef | awk '$2=="57526"'`.
- `operator_core_launch.py` includes
  `network_monitor_operator_launch.py`, which declares **4 monitor
  nodes**: `mikrotik_monitor`, `teltonika_monitor`,
  `starlink_diagnostics`, `ping_monitor`.
- Of those 4 in the running tree of PID 57526:
  - ✅ `starlink_diagnostics` (PID 57750)
  - ✅ `ping_monitor` (PID 57755)
  - ❌ `mikrotik_monitor` — absent, no matching PID
  - ❌ `teltonika_monitor` — absent, no matching PID
- Sanity checks rule out missing-install / unreachable-target:
  - Executables present:
    `sensors_ws/install/mikrotik_monitor/lib/mikrotik_monitor/mikrotik_monitor_node`
    and the parallel `teltonika_monitor_node`.
  - Target host `bizzy.wifi.op.p11.lan` (172.16.20.4) is reachable
    from salmon, <1 ms RTT, 0 % loss.
  - `/rosout` retained buffer has **no** entries from either node
    name — they appear to have died before publishing, or their
    messages aged out of the buffer.
  - `journalctl --user` shows nothing because they're not run as
    user-services.

Stdout/stderr from these processes went to the launch terminal
(`pts/5`) — `output='screen'` in the Node declaration. The actual
crash reason (likely an exception during connect/auth against the
RouterOS box, but **not verified**) would be visible there. Operator
will check pts/5 console / scrollback.

**Effect on diagnostics tree**: the `/Operator/MikroTik`,
`/Operator/Teltonika`, `/Operator/Ping`, `/Operator/Starlink`
aggregator buckets are STALE in §10 because no operator-side
publishers are providing input to them — separate config issue noted
in §10, but the two missing monitors here would not have helped even
if running (they publish under `/Other`, not `/Operator/*`).

## 13. Phase 1: WiFi-down test — baseline captured

**2026-05-19T12:50-04:00** — Operator announced they are about to
disable WiFi at the operator station (Phase 1 of today's scope:
Starlink-only operation). Captured pre-test baseline from
`/operator/udp_bridge/remotes/bizzy/topic_statistics`:

- Active connection seen in stats: **`connection_id: wifi`**.
- `/bizzy/local_costmap/costmap`: published on boat at
  **1.485 msg/s (3.80 MB/s)**; arriving on operator via WiFi at
  **0.334 msg/s (855 kB/s, 65 fragments/msg, success 21.4 kB/s)** —
  ~78 % drop on this large fragmented topic even on the WiFi path.
- `/bizzy/local_costmap/published_footprint`: published 5.108 msg/s
  (551 B/s); arriving via WiFi 5.108 msg/s (552 B/s) — clean.
- Heartbeat flowing, FCU LOITER, armed/guided/standby all true.
- Toplevel diagnostics still ERROR (unchanged from §10).
- `udp_bridge` resend-give-up warning storm (§11) still in progress.

Standing by to capture post-WiFi-down snapshot for comparison once
operator signals the cutover.

## 14. Post-WiFi-down: heartbeat alive, bridge stats stalled

**2026-05-19T12:53-04:00** — Operator reported WiFi at salmon is now
down (Phase 1 cutover). Snapshot taken in the first 60 s after the
cutover:

**Data plane (Starlink) is alive for small low-rate topics:**

- Boat heartbeat: **11 messages in 10 s, exactly 1.000 s spacing**
  (clean 1 Hz) — Starlink path is delivering the small high-priority
  payloads.
- Operator-side bridge process alive: PID 57723, ELAPSED 54:01,
  STAT `Sl+` (sleeping, multithreaded, foreground), no crash.

**Bridge statistics publication has stalled:**

- `/operator/udp_bridge/topic_statistics` — **0 msgs in 10 s**
- `/operator/udp_bridge/remotes/bizzy/topic_statistics` —
  **0 msgs in 15 s**
- `/operator/udp_bridge/remotes/bizzy/bridge_info` —
  **0 msgs in 10 s**
- All three were arriving within a few seconds pre-cut. They are not
  publishing at all now.

**Resend-give-up WARN storm has accelerated:**

- ~2021 distinct WARN msgs from `operator.udp_bridge` in a 3 s live
  sample → **~670 WARN/s** (compare §11's 5386-in-6s which included
  retained buffer; the 670/s number here is live-rate).
- Template now ends `"after 6 attempts"` (was `"after 5 attempts"`
  in §11). Sender TTL still 5 s; operator side is trying one more
  attempt before giving up.
- Packet IDs jumped from ~983 k at 12:30 (§11) to ~1.97 M at 12:53
  — implies sustained ~720 packets/s on the wire over the
  intervening 23 minutes.

**Reading**: the bridge process is alive and the inbound packet path
is still working (heartbeat proves end-to-end). But the periodic
stats publish callbacks (topic_statistics, bridge_info) are not
firing — consistent with the inbound-packet / resend-tracking loop
saturating the bridge's work queue and starving the stats timer.
CAMP / rqt statistics panels would look frozen.

Not yet investigating root cause beyond observation; logging as
field finding for the post-mission review.

## 15. Boat recovered

**2026-05-19T14:10-04:00** — Operator reported boat has been
recovered. Snapshot from salmon at recovery time (mission ran roughly
12:50 → 14:10 EDT, ≈1h20m on-water phase including the Starlink-only
test):

**Heartbeat still flowing (1 Hz, 5/5 in 5 s)** — boat still powered
up. Latest state:

- `piloting_mode = autonomous`  *(was `standby` at deployment §9)*
- `mode = MANUAL`  *(was `LOITER`)*
- `armed = true`  *(unchanged)*
- `guided = false`  *(was `true`)*
- `connected = true`
- `marine_autonomy_standby = false`  *(was `true`)*

Mode transitions consistent with manual takeover for recovery.

**Bridge statistics still stalled** — `topic_statistics` 0 msgs in
5 s. The stats-publication stall first observed in §14
(post-WiFi-down) has persisted for the entire ≈1h17m of the
Starlink-only phase. Stats panels in CAMP / rqt have been frozen
that whole time.

**`udp_bridge` WARN rate dropped** — ~918 distinct WARN entries in
3 s ≈ **306/s**, compared with §14's ~670/s right after the WiFi
cutover. The "Giving up on resend" template now ends `"after 1
attempts"` (was "5" in §11, "6" in §14). Packet IDs in the WARN
samples (e.g. 1691225, 1691830) are **lower than the 1.97 M IDs
seen at 12:53 in §14**, which suggests a counter reset somewhere
during the mission — possibly a sender-side bridge restart on the
boat. Not verified from salmon.

These are anchor observations for the post-mission review; logging
them now while fresh.

## 16. Wrap-up snapshot

**2026-05-19T14:12-04:00** — Final state captured before session
wrap-up.

**Operator-side ROS bag** (recorded throughout the session):

- Path: `/home/field/data/logs/operator/2026-05-19/bags/operator_2026-05-19T12.08.34/operator_2026-05-19T12.08.34_0.mcap`
- Size: **296 MB** (one shard; mcap / zstd_fast preset)
- Recorded topics (from `operator_core_launch.py` arguments):
  `/diagnostics`, `/bizzy/marine/command`,
  `/bizzy/piloting_mode/manual/helm`,
  `/operator/udp_bridge/topic_statistics`,
  `/operator/udp_bridge/bridge_info`,
  `/operator/udp_bridge/remotes/bizzy/topic_statistics`,
  `/operator/udp_bridge/remotes/bizzy/bridge_info`,
  `/rosout`, `/tf`, `/tf_static`
- Coverage: 12:08:34 → 14:12 (~2h 4m, includes pre-deploy + on-water
  + post-recovery).
- **Note**: the bag captures `/rosout` so the udp_bridge resend WARN
  storm (§11/§14/§15) is fully replayable for the post-mission review.
  It also captures `topic_statistics` — so the stall observed in §14
  manifests there as a gap in publication, not as missing data.

**Final salmon node-list count**: 16 (same shape as §9: operator
stack + /bizzy/* operator-side control nodes + support).

**Final diagnostics toplevel**: still ERROR (unchanged from §10/§15;
driven by the stale `/Operator/*` rollups and the `ping.op: bencloud`
unreachable entry).

**Session anchor times** (for cross-correlation with gabby / dev
logs):

| Time | Event |
|---|---|
| 11:01 | Deployment issue `e3c373a` opened on dev side |
| 11:24 | git-bug discovery on salmon (pre-fix) |
| 11:37 | `git_bug_setup.sh` field commit `236f2d7` pushed |
| 11:47 | First `make build` complete |
| 12:08 | `operator_core_launch.py` started (PID 57526) |
| 12:20 | Boat heartbeat first seen at salmon |
| 12:50 | Phase 1 baseline captured (WiFi up) |
| 12:53 | WiFi-down cutover observed; bridge stats stall begins |
| 14:10 | Boat recovered, FCU → MANUAL |
| 14:12 | Wrap-up snapshot |

## Issues encountered + diagnoses

- **Pre-commit hook did not run on salmon's workspace clone.**
  `/home/field/project11/.git/hooks/pre-commit` does not exist on this
  host — `make lint` has not been run, so the workspace's
  `.pre-commit-config.yaml` (which lists `no-commit-to-branch` for
  `main`/`jazzy`/`rolling`) was never wired up. The field commit on
  `main` went through without the branch-protection check that
  AGENTS.md anticipates would block it on a host with pre-commit
  installed. Per the "Hook caveat" in AGENTS.md: field-mode workspace
  clones may need `main` removed from the hook list (or the hook
  dropped) to align with field-mode behavior. **Flagging for dev-side
  decision** rather than altering hook config here, since this would
  affect all consumers of the workspace.

- **GitHub issue number for `e3c373a` is not resolvable field-side.**
  Without a bridge ever having been configured for this issue, git-bug
  has no `metadata` blob mapping `e3c373a` to its GitHub `#NNN`.
  Workable for field reading (the title + git-bug hash are sufficient)
  but worth a follow-up: future deployment-issue creation on dev should
  ideally happen after the bridge is in place, so field hosts see the
  mapping.

## Files touched

- `/home/field/project11/.agent/scripts/git_bug_setup.sh` — full
  rewrite (110 insertions / 89 deletions on the workspace's `main`).
  Workspace repo, gitcloud origin. **Pushed** as field commit
  `236f2d7` at 11:37 (§5).
- `docs/logs/2026/2026-05-19_salmon_logs.md` — this file. Project repo
  (`unh_echoboats_project11`), gitcloud origin. **Pending push** per
  README convention.
- Operator bag:
  `/home/field/data/logs/operator/2026-05-19/bags/operator_2026-05-19T12.08.34/operator_2026-05-19T12.08.34_0.mcap`
  — 296 MB, mcap/zstd_fast. Not under version control; stays in
  `~/data/logs/` per README convention.

## Pending on operator

- **Push this salmon log to gitcloud** when ready to close the
  session.
- **Check pts/5 console scrollback** for the actual crash reason of
  operator-side `mikrotik_monitor` and `teltonika_monitor` (§12).
  Stdout/stderr from those processes went there.
- **Confirm boat-side bridge restart hypothesis (§15)**: packet IDs
  in the resend-WARN stream went from ~1.97 M at 12:53 down to
  ~1.69 M at 14:10, which only makes sense if the sender-side bridge
  on gabby was restarted at some point. Worth checking gabby's log
  for a restart event.
- **Confirm `rolker/udp_bridge#13` status** (resend-loop amplification
  fix referenced in the deployment issue) — needed to interpret the
  WARN storm severity (§11/§14).

## Pending for dev-side wrap-up

- **Reconcile `236f2d7` to GitHub** via `/import-field-changes` from
  a dev workstation. The dev-side PR will re-run the workspace's
  pre-commit set — first time this script change has seen it.
- **Open follow-up task issues** for the post-mission findings:
  - udp_bridge `topic_statistics` / `bridge_info` publication
    stalled the entire ≈1h17m of Starlink-only operation (§14/§15).
    Stats panels in CAMP / rqt were frozen the whole time.
  - "Giving up on resend… after N attempts" template — observed N
    values 5 / 6 / 1 across the session. Whether N is meaningful or
    a counter-tracking glitch worth confirming.
  - Operator-side `mikrotik_monitor` + `teltonika_monitor` crash on
    startup (§12) — likely fixable with a try/except around the
    initial connect, but root-cause from pts/5 still needed.
  - `ping.op: bencloud` Unreachable in `/Other` despite `ping` from
    salmon reaching bencloud — `ping_monitor` may be pinging a
    different target than the operator's bash shell resolves (the
    YAML uses `bencloud.wg.p11.lan`, not `bencloud`).
  - `/Operator/{MikroTik,Ping,Starlink,Teltonika}` aggregator
    buckets STALE because real monitors publish under `/Other`
    (§10/§12) — aggregator config drift.
  - Costmap had ~78 % loss on WiFi pre-cut (§13) — the bag has the
    Starlink-only data needed for direct comparison.
- **Update `docs/roadmap.md`** with anything from the above that
  isn't bounded enough for a focused issue.
- **Merge the wrap-up PR**; closing it closes the deployment issue
  `e3c373a` / its GitHub equivalent.
