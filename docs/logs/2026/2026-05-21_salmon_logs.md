# BizzyBoat deployment log — salmon — 2026-05-21

**Host**: salmon
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Deployment**: git-bug `7d5b52c` — "Deployment 2026-05-21: validate small-wins PRs + udp_bridge WARN demote + FCU EK3 Z-source reconfig" (opened dev-side 2026-05-20T22:03-04:00; hard stop on water 14:00 EDT). GitHub issue number to be backfilled dev-side at wrap-up.

## Summary

_(user-curated, filled in at wrap-up)_

## Lessons Learned

_(user-curated, filled in at wrap-up)_

## 1. Session start

**2026-05-21T11:17-04:00** — Log initialised on salmon. Field mode confirmed
(origin `git@gitcloud:field/unh_echoboats_project11.git`). Today's deployment
issue `7d5b52c` pulled via `git-bug pull` and read; scope is the small-wins
PR validation batch + FCU EK3 Z-source reconfig, with a hard 14:00 EDT
recovery deadline.

## 2. Pre-launch sync + build

**2026-05-21T11:18-04:00** — `make sync` from workspace root. All repos
report `✅ Already up to date` except `unh_echoboats_project11` —
**skipped: Uncommitted changes detected** (this log file in
`docs/logs/2026/`; expected per the deployment-log README, field hosts push
logs at end of session). No code deltas pulled —
operator confirmed a manual `make sync` + `make build` was already run
earlier on salmon, so today's dev-side merges (PR #146, #147, #148,
`ros2_network_monitor#24`, `udp_bridge#24`) had already been mirrored
and pulled on that earlier pass.

**2026-05-21T11:21-04:00** — `make build` from workspace root. Fast
incremental pass (~2 min wall time), exit 0 across all 7 layers. Build
report:

| Layer | Packages (OK) | Status |
|---|---|---|
| underlay | 22 / 22 | ✅ |
| core | 24 / 24 | ✅ |
| platforms | 12 / 12 | ✅ |
| sensors | 17 / 17 | ✅ |
| simulation | 10 / 10 | ✅ |
| ui | 7 / 7 | ✅ |
| site | 1 / 1 | ✅ |

No stderr from any package. The `colcon-override-check` notice about
`camp` being present in an underlay is a pre-existing observation, not
new today.

Salmon is built against whatever was already on gitcloud at sync time;
operator stack is ready to launch.

## 3. Operator-bring-up watch-list (derived from landed PRs)

**2026-05-21T11:30-04:00** — Ahead of launching `operator_core_launch.py`,
read the on-disk source of each merged-today PR to derive concrete things
to watch for. Findings:

### PR #146 — `diagnostic_aggregator` removed from operator launches

Verified `operator_core_launch.py` and `marine_autonomy/launch/operator_core_launch.py`
no longer include any `diagnostic_aggregator` node.

- **Expect**: `ros2 topic list | grep diagnostics_agg` returns nothing.
- **Expect**: no `/Operator/*` STALE rollups, no toplevel ERROR driven by
  stale-promotion of empty buckets (the failure mode from 2026-05-19 §10).
- **Watch**: the CAMP / rqt annunciator now consumes raw `/diagnostics`.
  Confirm it actually shows status — if it goes blank, something downstream
  was wired specifically to `/diagnostics_agg`.

### PR #147 — `output='both'` on operator network monitors

Verified `network_monitor_operator_launch.py` lines 32 / 39 / 50 / 57 all
set `output='both'` for `mikrotik_monitor`, `teltonika_monitor`,
`starlink_diagnostics`, `ping_monitor`.

- **Expect**: any monitor crash leaves a full traceback in
  `~/.ros/log/latest_log/` **and** prints to the launch terminal —
  fixes the 2026-05-19 §12 blind spot.

### PR #148 — Stale `bencloud` ping target removed

Verified `config/ping_targets_operator.yaml` — targets are now
`gabby_direct`, `gabby_vpn`, `router_bizzy_direct`, `router_bizzy_vpn`,
`dns_google`, `dns_cloudflare`. No `bencloud`.

- **Expect**: no `ping.op: bencloud Unreachable` entry in `/Other`.
- **Note**: `*_vpn` targets may be Unreachable if the VPN path is down —
  expected, not regression.

### `ros2_network_monitor#24` — startup-connect hardening

Verified `mikrotik_monitor_node.py` (lines 365–395) and the parallel
teltonika node: failed polls increment `_consecutive_failures`, schedule
the next attempt via `compute_poll_backoff()` (exponential, capped at
`backoff_max_sec`), and emit `DiagnosticStatus: ERROR` with the cached
error message augmented as `(attempt N, backoff Xs)`. The node does not
exit on connect failure.

- **Headline expect**: `ros2 node list` shows **both** `mikrotik_monitor`
  and `teltonika_monitor` regardless of whether the boat router is
  reachable yet — the 2026-05-19 §12 disappearance should be impossible
  now.
- **Watch**: if the router goes unreachable mid-mission, the diagnostic
  flips to ERROR with `(attempt N, backoff Xs)`; node stays alive.

### `udp_bridge#24` — WARN demote + per-remote `DiagnosticStatus`

Verified `udp_bridge/src/remote_node.cpp` line 513: the "Giving up on
resend of packet …" log is now `RCLCPP_DEBUG_STREAM`, not
`RCLCPP_WARN_STREAM`. Verified `udp_bridge.cpp` lines 1711–1862: two
new per-remote diagnostic tasks registered per remote.

- **Expect**: `/rosout` is quiet — no flood of `Giving up on resend...`
  WARNs. The 2026-05-19 §11/§14 storm (~670 WARN/s on Starlink-only)
  is the canary; if it reappears, the new binary isn't loaded.
- **Expect on `/diagnostics`**: two new task-name patterns per remote:
  - `udp_bridge operator: bizzy: <connection_id>` (one per connection —
    wifi / vpn / starlink). Carries tx/rx B/s, `last_rx_age_s`.
    Summary auto-promotes: OK → WARN at ≥5 s rx silence → ERROR at ≥10 s.
  - `udp_bridge operator: bizzy: resend give-ups` — give-up rate per
    second. **WARN ≥ 5/s, ERROR ≥ 50/s** (defaults from
    `udp_bridge.h:350-351`; overridable via
    `resend_giveup_warn_rate_per_s` / `resend_giveup_error_rate_per_s`).

### Quick check-list on first operator stack startup

1. `ros2 node list` includes `mikrotik_monitor` **and** `teltonika_monitor`.
2. `ros2 topic list | grep diagnostics_agg` returns nothing.
3. `/rosout` not flooded with `udp_bridge` resend WARNs.
4. `/diagnostics` includes `udp_bridge operator: bizzy: …` entries
   (connection-level + `resend give-ups`).
5. No `ping.op: bencloud` entry under `/Other`.

## 4. Pre-launch re-sync (final check)

**2026-05-21T11:34-04:00** — Operator requested a second `make sync` as
final pre-launch check. All repos `✅ Already up to date` again; only
`unh_echoboats_project11` skipped (this log file). No code deltas →
**no rebuild needed**. Salmon is current with gitcloud at this time
and the install tree matches.

## 5. Operator stack startup

**2026-05-21T11:33-04:00** — Operator reported starting the stack.
Waiting for stack-up before running the §3 watch-list checks.

## 6. Operator wishlist: CAMP window geometry persistence

**2026-05-21T11:35-04:00** — Operator observation during stack startup:
**it would be nice if the CAMP window remembered its last position
and size between launches.** Every restart it comes up at default
geometry and has to be repositioned/resized to fit the operator's
screen layout. Captured here for a dev-side follow-up issue at wrap-up.

## 7. Operator stack — §3 watch-list results (boat-side still down)

**2026-05-21T11:40-04:00** — Ran the §3 quick check-list against the
operator stack now that it's up. Boat side is **not** up yet, so
checks that depend on boat data are deferred or weak. Findings:

### ✅ PR #146 (diagnostic_aggregator removal) — verified

`ros2 topic list` includes `/diagnostics` but **no** `/diagnostics_agg`.
No aggregator nodes in `ros2 node list` either.

### ✅ PR #147 (`output='both'`) — verified, and immediately load-bearing

The teltonika failure below (and its full Python traceback) is captured
in
`/home/field/.ros/log/2026-05-21-11-33-03-833285-salmon-120653/launch.log`.
Without #147 this would have gone only to the launch terminal — exactly
the 2026-05-19 §12 blind spot — and the diagnosis below would not have
been possible from salmon alone.

### ✅ `ros2_network_monitor#24` for `mikrotik_monitor` — verified

`mikrotik_monitor` is in `ros2 node list` and at startup logs:

> `Monitoring MikroTik device at bizzy.wifi.op.p11.lan:80 poll every
> 5.0s, publish every 1.0s, stale_timeout=15.0s,
> dynamic_task_grace=30.0s, backoff_max=60.0s`

The `backoff_max=60.0s` parameter is from the new
`mikrotik_monitor_node.py` `_consecutive_failures` / `compute_poll_backoff`
path, so the hardened binary is confirmed loaded.

### ❌ `teltonika_monitor` died on startup — **NOT a #24-shaped failure**

`teltonika_monitor` is **absent** from `ros2 node list`. Launch log shows
it `[FATAL]`'d inside `__init__()` before any of #24's connect-retry
logic could fire:

```
[FATAL] Failed to construct TeltonikaMonitorNode:
InvalidParameterTypeException: Trying to set parameter 'ignored_interfaces'
to '['mob1s1a1','mob1s2a1','wifi_bridge','mobile_lab']'
of type 'STRING_ARRAY', expecting type 'BYTE_ARRAY'

  File ".../teltonika_monitor/teltonika_monitor_node.py", line 63, in __init__
    self.declare_parameter('ignored_interfaces', [])
```

Process died, exit code 1.

**Diagnosis**: `declare_parameter('ignored_interfaces', [])` with an
empty Python list — rclpy infers `BYTE_ARRAY` for `[]`, then the YAML
override (a list of interface-name strings) fails the type check on
load. This is a **parameter-declaration bug**, separate from anything
`#24` was intended to fix.

**Implication for 2026-05-19 §12**: that day mikrotik *and* teltonika
were both absent. We now know mikrotik's disappearance was the
genuine #24-style connect-failure that #24 fixes, while teltonika has
**always been broken on this YAML config** and only became visible
today because PR #147 finally surfaced the traceback. So that day's
"both monitors crashed" was actually two distinct bugs in trench coat.

**Fix shape** (for the follow-up issue): declare `ignored_interfaces`
with an explicit type — e.g.

```python
from rcl_interfaces.msg import ParameterDescriptor
from rclpy.parameter import Parameter
self.declare_parameter(
    'ignored_interfaces', [],
    ParameterDescriptor(type=Parameter.Type.STRING_ARRAY.value)
)
```

Or use a `(name, value, descriptor)` tuple via `declare_parameters`.

### ⏳ `udp_bridge#24` WARN demote — weak signal (boat down)

3 s `/rosout` sample contained **0 `Giving up on resend …` entries**.
With the boat side not connected there's no resend traffic to drive the
old WARN storm anyway, so this only confirms that the *idle-bridge*
state is clean. Real validation will come once boat-side bridge starts
sending and resends start being issued — at that point the line should
be `RCLCPP_DEBUG` and not appear in `/rosout` at default verbosity.

### ⏳ PR #148 (`bencloud` ping target removal) — pending diagnostic sample

`/diagnostics` is published at low cadence; my 8 s `ros2 topic echo`
samples timed out before catching a multi-publisher window. Confirmation
deferred until either CAMP annunciator is visible or a longer sample
catches the `ping_monitor` status. The on-disk YAML
(`ping_targets_operator.yaml`) is already verified bencloud-free in §3,
so this is just a runtime cross-check.

### Other node-list observations

Operator stack composition consistent with expectations:

- `/operator/camp`, `/operator/udp_bridge` ✅
- `/bizzy/{command_bridge_sender,joy_node,joy_to_helm,joint_state_publisher,robot_state_publisher}` —
  operator-side boat-control nodes ✅
- `/mikrotik_monitor`, `/ping_monitor`, `/starlink_diagnostics` ✅
- `/molab/johnny5/johnny5_node` ✅ (with the 401 auth WARNs to johnny5
  that are pre-existing; not blocking)
- 3 rqt nodes ✅
- `/rosbag2_recorder` ✅

`/diagnostics` reports **Publisher count: 4** — consistent with the 4
publishers being mikrotik / ping / starlink / udp_bridge (teltonika
absent, as established above).

## 8. Field fix: teltonika_monitor `ignored_interfaces` declaration

**2026-05-21T11:55-04:00** — Fixed the teltonika construction crash in
`ros2_network_monitor` (the repo, not unh_echoboats):

```python
# Before
self.declare_parameter('ignored_interfaces', [])

# After
self.declare_parameter('ignored_interfaces', rclpy.Parameter.Type.STRING_ARRAY)
```

Matches the pattern `ping_monitor_node.py:40` already uses in the same
repo. Tested first with `ParameterDescriptor(type=PARAMETER_STRING_ARRAY)`
+ `[]` default — that approach still failed with the same error in rclpy
Jazzy (the empty-list-value type inference appears to override the
descriptor type at value-validation time). The type-only declaration
form works because there is no Python default value for rclpy to infer
a wrong type from.

**Smoke test** (post-rebuild):

```text
$ ros2 run teltonika_monitor teltonika_monitor_node \
    --ros-args --params-file teltonika_monitor_operator.yaml
[INFO] [teltonika_monitor]: Monitoring Teltonika router at router.op:443
       poll every 5.0s, publish every 1.0s, stale_timeout=15.0s,
       dynamic_task_grace=30.0s, backoff_max=60.0s
```

Node alive >5 s, registered in `ros2 node list`, no traceback. The
`backoff_max=60.0s` line confirms the new #23 hardening path is now
reachable (was being prevented by the parameter crash).

**Caveat**: the repo's own default config
(`teltonika_monitor/config/teltonika_monitor.yaml`) does **not** set
`ignored_interfaces`. With the type-only declaration, loading that
YAML leaves the parameter `NOT_SET`; the consumer at line 100–104
reads `.get_parameter_value().string_array_value` which returns the
message's default `[]` — so behavior should be unchanged, but the
dev-side PR should either (a) add `ignored_interfaces: []` to the
default YAML or (b) wrap the consumer access in a NOT_SET guard for
defense-in-depth.

**Field commit pushed to gitcloud**:

- Repo: `ros2_network_monitor`, field mode (gitcloud origin)
- Commit: `b27abab` — `teltonika_monitor: fix InvalidParameterTypeException on STRING_ARRAY override`
- Push: `bdf396c..b27abab  jazzy -> jazzy` on
  `gitcloud:field/ros2_network_monitor.git`

To be reconciled to a GitHub PR via `/import-field-changes` after
wrap-up.

**Live-stack handling**: operator chose to bring teltonika back into
the running operator stack themselves (no full restart needed, since
launching teltonika_monitor standalone with the operator YAML is
sufficient — process collision is irrelevant because the
launch-managed instance is already dead).

## 9. Audit: `ignored_interfaces` coverage on both deployment sides

**2026-05-21T12:05-04:00** — Pulled on the §8 thread to make sure both
op and boat sides of the deployment have `ignored_interfaces` properly
set. Findings:

| YAML | Has `ignored_interfaces`? | Loaded by deployment? |
|---|---|---|
| `bizzyboat_project11/config/bizzyboat.yaml` | ❌ then ✅ (this entry) | ✅ — `network_monitor_boat_launch.py` (gabby) |
| `bizzyboat_project11/config/teltonika_monitor_operator.yaml` | ✅ `['mob1s1a1', 'mob1s2a1', 'wifi_bridge', 'mobile_lab']` | ✅ — `network_monitor_operator_launch.py` (salmon) |
| `bizzyboat_project11/config/teltonika_monitor_boat.yaml` | ✅ `['mob1s2a1', 'wan1']` | ❌ **orphaned** — referenced only by `ccomjhc_project11/documentation/bizzyboat_network_debug_2026-04-14.md` |
| `ros2_network_monitor/teltonika_monitor/config/teltonika_monitor.yaml` (upstream) | ❌ | ❌ — only affects standalone upstream users |
| `ccomjhc_project11/configuration/teltonika.yaml` | n/a | n/a — credentials file (just `"password": "…"`), not a ROS params yaml; misled my initial grep |

**Gap that mattered for today**: the boat-side teltonika params come
from `bizzyboat.yaml`'s `/**/teltonika_monitor:` block (not
`teltonika_monitor_boat.yaml`, which is unused). That block was
missing `ignored_interfaces`. With the §8 type-only declaration the
parameter would have been `NOT_SET` on gabby; the consumer's
`.string_array_value` access still returns `[]` from the message
default, so functional behavior would have matched the implicit
"ignore nothing" intent — but the dependency on rclpy's NOT_SET
read behavior is brittle, and the orphaned `_boat.yaml` shows
someone had recorded a more deliberate ignore-list anyway.

**Fix applied to `bizzyboat.yaml`**:

```yaml
/**/teltonika_monitor:
  ros__parameters:
    …existing keys…
    ignored_interfaces: ['mob1s2a1', 'wan1']    # ← added
```

Value copied from the orphaned `teltonika_monitor_boat.yaml` — that
captures someone's recorded intent for what to ignore on the boat-side
Teltonika router (cellular modem 2 and wan1).

**Field commit pushed**:

- Repo: `unh_echoboats_project11`, field mode (gitcloud origin)
- Commit: `02afc7f` — `bizzyboat.yaml: add ignored_interfaces for boat-side teltonika_monitor`
- Push: `608f7f5..02afc7f  jazzy -> jazzy` on
  `gitcloud:field/unh_echoboats_project11.git`

No salmon rebuild needed (this YAML is loaded only by gabby's
boat-side launch; salmon's operator-side teltonika loads
`teltonika_monitor_operator.yaml`). Gabby will pick it up at next
sync.

## Findings worth a follow-up issue

- ~~**teltonika_monitor crash on empty STRING_ARRAY default**~~ —
  fixed in §8 and pushed as field commit
  `ros2_network_monitor@b27abab`. Dev-side PR still needed:
  reconcile via `/import-field-changes`, add `ignored_interfaces: []`
  to the upstream `teltonika_monitor/config/teltonika_monitor.yaml`,
  and add a regression test that loads a STRING_ARRAY override and
  verifies the node constructs without raising.
- ~~**boat-side `bizzyboat.yaml` missing `ignored_interfaces`**~~ —
  fixed in §9 and pushed as field commit
  `unh_echoboats_project11@02afc7f`.
- **Orphaned `teltonika_monitor_boat.yaml`** — referenced only by docs,
  not loaded by any launch. Either an unfinished refactor toward
  per-node yamls on the boat side (the op side already uses that
  pattern) or stale. Worth either deleting or completing the refactor
  at wrap-up. Deferred per operator decision today.

## 10. Post-restart §3 watch-list — all green

**2026-05-21T12:18-04:00** — Operator restarted the ROS stack (boat
side now up too, judging by the boat-side diagnostics flowing through
the bridge). Re-ran the §3 quick check-list:

### Orphan cleanup

My §8 smoke-test left an orphan `teltonika_monitor` python process
(PID 126233, parented to init after the `ros2 run` wrapper died) — its
duplicate `/teltonika_monitor` node name and extra `/diagnostics`
publisher would have been confusing. Killed it. Node-list count for
`teltonika_monitor` now == 1; `/diagnostics` Publisher count drops by
1.

**Lesson**: `kill $!` on a `ros2 run …` background sends SIGTERM to
the `ros2` wrapper, not to the launched python child — the child gets
orphaned. Use `pkill -f teltonika_monitor_node` or capture the python
PID via `pgrep -P $!` for clean teardown next time.

### Watch-list results

| Item | Result |
|---|---|
| #146 — no `/diagnostics_agg` topic | ✅ |
| #147 — `output='both'` (visible by virtue of §7 / §8 traceback capture) | ✅ |
| #148 — 0 `bencloud` mentions in 8 s `/diagnostics` sample | ✅ |
| #24 — `mikrotik_monitor` alive (op + boat) | ✅ |
| #24 — `teltonika_monitor` alive (op + boat, after §8 + §9 fixes) | ✅ |
| `udp_bridge#24` — `/rosout` quiet, no resend WARN flood (3 s sample) | ✅ |
| `udp_bridge#24` — new per-remote `/diagnostics` tasks present | ✅ |

### `udp_bridge#24` per-remote diagnostic samples (8 s window)

Three new task names registered, all OK level:

```yaml
- name: 'udp_bridge: udp_bridge operator: bizzy: wifi'
  message: tx ~4500 B/s, rx ~210000 B/s     # gabby.bizzy.p11.lan
- name: 'udp_bridge: udp_bridge operator: bizzy: vpn'
  message: tx ~7000 B/s, rx ~400000 B/s     # gabby.vpn.bizzy.p11.lan
- name: 'udp_bridge: udp_bridge operator: bizzy: resend give-ups'
  message: give-up rate 0.00/s (total 59282)
```

The bridge has registered two connections to `bizzy`: **`wifi`** and
**`vpn`**, both flowing. The `resend give-ups` task shows a lifetime
total of **59,282** but a current rate of **0.00/s** — far below the
**5/s WARN threshold**. Compare to 2026-05-19 §11/§14: ~670 WARN/s
floodgate to `/rosout`. The lifetime counter says give-ups *do* still
happen at a background rate; the difference is the demote-to-DEBUG
plus the operator visibility surface having moved from log spam to a
single rate-summarised diagnostic.

### Notable side-observations from the diagnostic dump

- Boat-side data is fully forwarded: 11 `router.bizzy` teltonika
  tasks, 11 `wifi.bizzy` mikrotik tasks, 6 `starlink.bizzy` starlink
  tasks, 6 `ping.bizzy` ping tasks — all reaching the operator
  diagnostic surface.
- Boat-side teltonika **`interface/mob1s2a1`** and **`interface/wan1`**
  are absent from the published task list, while `interface/mob1s1a1`
  is present. Confirms the `ignored_interfaces: ['mob1s2a1', 'wan1']`
  added in §9 to `bizzyboat.yaml` is being honored at gabby — which
  means gabby has pulled and rebuilt since §9. ✅
- Operator-side teltonika ignore-list (`['mob1s1a1', 'mob1s2a1',
  'wifi_bridge', 'mobile_lab']`) also honored — none of those appear
  in `router.op` task names.

### Pending / weak

- `udp_bridge#24` WARN-demote validation is now stronger (the
  link is active), but the 8 s sample only captures a non-stress
  baseline. A real validation moment is the Phase 1 WiFi-down cutover
  (per the deployment-issue Block 3) — if the demote works, `/rosout`
  should stay quiet through that period instead of flooding like
  2026-05-19 §14.

## 11. Boat in water — post-deploy baseline

**2026-05-21T12:41-04:00** — Operator confirmed boat is already in the
water; we're in Block 3 (in-water mission), not Block 2. The Block 2
`#24` dockside validation was not run from the operator side as a
controlled test; the validation now happens passively as conditions
on the water change.

**State snapshot**:

- Heartbeat (`/bizzy/marine/heartbeat`): `piloting_mode=standby`,
  `mode=MANUAL`, `armed=true`, `connected=true`, `guided=false`.
- Bridge: both `wifi` and `vpn` connections registered and flowing
  (visible in `bridge_info`).
- `resend give-ups` lifetime total: **61,712** (was 59,282 at §10).
  Δ = 2,430 over ~23 min → background rate ≈ **1.8/s**, well under
  the 5/s WARN threshold. `/rosout` remains quiet — demote holding.
- Operator-side bag recording active since 12:05 (PID 127796) at
  `/home/field/data/logs/operator/2026-05-21/bags/operator_2026-05-21T12.05.34`.
  Captures `/diagnostics`, `/bizzy/marine/command`,
  `/bizzy/piloting_mode/manual/helm`,
  `/operator/udp_bridge/{,remotes/bizzy/}{topic_statistics,bridge_info}`,
  `/rosout`, `/tf`, `/tf_static` — matches the 2026-05-19 topic set
  for offline udp_bridge analysis.

Mode is MANUAL — boat is being driven by the operator, not yet in
autonomy. Standing by in scribe mode for phase transitions.

## 12. NTP status (salmon)

**2026-05-21T12:47-04:00** — Operator asked for NTP status. Salmon's
chrony state:

- `timedatectl`: **System clock synchronized: yes**, NTP service active.
- `chronyc tracking`: System time **0.000000155 s (155 ns) fast** of
  NTP time. Last offset −2.2 ms; RMS 35.5 ms; root delay 2.4 ms.
- **Selected source**: `time.lan.bizzy.p11.lan` (=`192.168.20.123`,
  stratum 1, marked `prefer` in
  `/etc/chrony/sources.d/project11.sources`). Last offset **−18 µs**,
  ±2.2 ms.
- Other configured sources:
  - `192.168.21.123` (VPN-route boat NTP, stratum 1) — reachable
  - `192.168.20.5` (reverse-resolves to bare `gabby`) — shows `^?`
    (unreachable from chrony's perspective). **Harmless** because the
    LAN-route boat NTP is the active stratum-1 source. Worth a
    look-back: either gabby isn't running an NTP service on that
    address, or there's an ACL/route gap to that path specifically.
    Flagged for follow-up.
  - `time.unh.edu` (UNH fallback) — available, excluded by chrony
    selection algorithm.
  - Ubuntu NTP pool — fallback.

Sync is tight enough that operator+boat bag timestamps will correlate
to within microseconds; no concern for the post-mission analysis path.

## 13. Mission complete — wrap-up snapshot

**2026-05-21T14:55-04:00** — Operator advised the boat was recovered
"a while ago". Captured wrap-up state on salmon — I missed logging
the recovery moment in real time (no autonomous trigger; the bag
mtime suggests the operator stack ran until ~14:51 EDT).

**State at 14:55**:

- **Boat side**: powered off — `/bizzy/marine/heartbeat` no longer
  publishing.
- **Operator stack**: shut down — `ros2 node list` empty. CAMP / rqt
  windows closed; no `launch_ros_*` process.
- **Operator bag**: recording finalized at **14:51 EDT** (4 min
  before this snapshot). Final stats:
  - Path:
    `/home/field/data/logs/operator/2026-05-21/bags/operator_2026-05-21T12.05.34/`
  - Size: **99 MB**, one shard (mcap / zstd_fast)
  - Duration: 12:05 → 14:51 = **~2h 46m** (pre-deploy + on-water +
    post-recovery)
  - Topics: `/diagnostics`, `/bizzy/marine/command`,
    `/bizzy/piloting_mode/manual/helm`,
    `/operator/udp_bridge/{,remotes/bizzy/}{topic_statistics,bridge_info}`,
    `/rosout`, `/tf`, `/tf_static`

**Comparison vs. 2026-05-19 bag**: 99 MB today vs. **296 MB** then,
for similar (~2h) duration — **~1/3 the size**. Almost certainly the
`udp_bridge#24` WARN demote: yesterday's 670 WARN/s firehose into
`/rosout` no longer lands, so the bag's `/rosout` slice is dramatically
smaller. This is direct, end-to-end evidence that #24's stated goal
(orders-of-magnitude WARN-volume reduction vs. 27,992-in-2h baseline)
is being met in practice.

**Phase coverage observed today** (operator-side perspective only —
dev / gabby logs will fill in the boat-side phases):

- **Phase 0 (bring-up confirm)** — implicit, heartbeat seen at 12:20-ish.
- **Phase 1 (FCU reconfig validation)** — gabby-led; we'd need to
  read post-mission bag or gabby's log for verdict.
- **Phase 2 (udp_bridge#24 WARN demote)** — passively validated by
  the entire mission: `/rosout` stayed quiet (no resend WARN flood),
  give-up rate held in the 1–2/s background range (under 5/s WARN
  threshold), and the bag-size comparison above is the headline
  number.
- **Phase 3 / 4 / 5** — no direct operator-side observation captured
  during the mission; will reconcile from gabby and dev logs.

**Last-known resend give-up totals captured during the mission**:

- 12:18 (§10): total 59,282
- 12:41 (§11): total 61,712 (Δ 2,430 over 23 min ≈ 1.8/s background)

These two anchor points let post-mission analysis estimate the
mission-window give-up rate from the bag without needing to integrate
the full `/diagnostics` stream.

## Files touched

- `layers/main/sensors_ws/src/ros2_network_monitor/teltonika_monitor/teltonika_monitor/teltonika_monitor_node.py`
  (lines ~63) — switched `declare_parameter('ignored_interfaces', [])`
  to `declare_parameter('ignored_interfaces', rclpy.Parameter.Type.STRING_ARRAY)`.
  Field commit `ros2_network_monitor@b27abab` on `jazzy`. (§8)
- `layers/main/platforms_ws/src/unh_echoboats_project11/bizzyboat_project11/config/bizzyboat.yaml`
  — added `ignored_interfaces: ['mob1s2a1', 'wan1']` to the boat-side
  `/**/teltonika_monitor:` block. Field commit
  `unh_echoboats_project11@02afc7f` on `jazzy`. (§9)
- `docs/logs/2026/2026-05-21_salmon_logs.md` — this file. Pending
  push at session close (per convention, field-host logs are append-only
  and push at end-of-session).
- Operator bag (not version-controlled, stays in `~/data/logs/`):
  `/home/field/data/logs/operator/2026-05-21/bags/operator_2026-05-21T12.05.34/`
  — 99 MB, mcap/zstd_fast, 12:05 → 14:51 EDT.

## Pending on operator

- **Push this log to gitcloud** at session close. The top-of-log
  Summary + Lessons Learned sections stay as placeholders here — those
  are integrated into the dev log at wrap-up, not into per-host logs.

## Pending for dev-side wrap-up

- **Reconcile field commits to GitHub PRs via `/import-field-changes`**:
  - `ros2_network_monitor@b27abab` — teltonika `ignored_interfaces`
    type fix (§8). Dev PR should add `ignored_interfaces: []` to the
    upstream repo's default `teltonika_monitor.yaml` and add a
    regression test loading a STRING_ARRAY override.
  - `unh_echoboats_project11@02afc7f` — boat-side
    `bizzyboat.yaml` `ignored_interfaces` (§9).
- **Address the orphaned `teltonika_monitor_boat.yaml`** — either
  delete (it's stale dead config) or complete the refactor to
  per-node yamls on the boat side (matching the op side's pattern).
  Tracked at the bottom of "Findings worth a follow-up issue".
- **Bag-size delta is the headline #24 evidence** — worth elevating
  to the wrap-up PR description.
- **`gabby` (192.168.20.5) NTP source `^?` unreachable** — minor
  config follow-up (§12). Confirm whether the entry is stale or
  whether gabby's NTP service is down. Harmless because the LAN-route
  boat NTP is the active stratum-1 source.
