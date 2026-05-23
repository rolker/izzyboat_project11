# BizzyBoat deployment log — salmon — 2026-05-22

**Host**: salmon
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Deployment**: git-bug `1e4fe7d` — "Deployment 2026-05-22: battery drain to LVD + perception #14 in-water + costmap-over-Starlink" (opened 2026-05-22T15:17-04:00, edited 15:31).

## Summary

_(user-curated, filled in at wrap-up)_

## Lessons Learned

_(user-curated, filled in at wrap-up)_

## 1. Session start

**2026-05-22T16:18-04:00** — Log initialised on salmon. Field mode confirmed
(origin `git@gitcloud:field/unh_echoboats_project11.git`). Today's deployment
issue `1e4fe7d` pulled via `git-bug pull` and read; scope is battery-discharge
characterization to LVD trip (primary), `unh_marine_perception#14` in-water
validation, costmap-over-Starlink dynamic test, PR #153 boat-logger topic
verification, mercat NTP + AML SVS June-4 deadline items, and a 4:3
OAK preview+video FoV A/B already applied gabby-side.

**Salmon pre-deploy state**:

- `make sync` completed cleanly; the only code deltas pulled on salmon were
  `unh_echoboats_project11` (commit `ac77860`, restore `oak_aft_ffmpeg` to vpn)
  and `seafloor_echoboat_project11` (`bf4da10`, multi-instance config restored
  per gabby's field commit on the `#14` fix).
- No operator stack running yet (`ros2 node list` empty; no
  `operator_core_launch` / `camp` / rqt processes).
- No prior 2026-05-22 salmon log; this is the first scribe entry.

Standing by for operator bring-up. Watch-list for first-stack-up (carried
from yesterday's §10 baseline + today's added scope):

1. PR #153 topics surfaced operator-side if forwarded: `/bizzy/tide_estimate`,
   `/bizzy/mllw_offset`, `/bizzy/mhhw_offset` (boat-side bag is the
   load-bearing verify; operator visibility depends on udp_bridge
   `topics_list`).
2. `udp_bridge` per-remote DiagnosticStatus stays clean once boat-side
   bridge connects — yesterday's baseline: tx ~4–7 kB/s, rx ~210–400 kB/s,
   `resend give-ups` < 2/s background.
3. Phase 3 — when operator dynamically adds `local_costmap/costmap` to the
   vpn `topics_list` via `rqt_udp_bridge`, watch for the topic appearing on
   the operator side and for udp_bridge diagnostic level holding under the
   added load. Note any latency or rate observations vs the wifi baseline.
4. `#157` activation race — note time of first
   `Activating controller_server` vs first successful
   `Server controller_server connected with bond`. Operator-side only sees
   this through forwarded `/rosout`; record what's visible.

## 2. CAMP + udp_bridge dropped — restart called

**2026-05-22T16:30-04:00** — Operator reported CAMP unresponsive and lots of
red on the diagnostic surface. Quick probes before the restart call:

- `ros2 node list` was **missing both** `/operator/camp` and
  `/operator/udp_bridge` (yesterday's stack had both — see
  `2026-05-21_salmon_logs.md` §7). All other expected nodes present
  (`mikrotik_monitor`, `teltonika_monitor`, `ping_monitor`,
  `starlink_diagnostics`, `johnny5_node`, 3 rqt nodes, `rosbag2_recorder`,
  the `/bizzy/*` operator-side boat-control nodes).
- `ros2 topic info -v /operator/udp_bridge/bridge_info` → **Publisher count: 0**
  (rosbag2 + rqt still subscribed as orphans). Same for
  `/operator/udp_bridge/remotes/bizzy/bridge_info`. Confirms the bridge
  node itself died, not just a publish hiccup.
- `/diagnostics` had only 6 unique tasks (1 mikrotik wlan1 "Not running",
  2 ping ERROR on `gabby_direct` / `router_bizzy_direct`, 3 ping STALE on
  `dns_*` / `router_bizzy_vpn`). Yesterday's §10 baseline had ~30+ tasks
  including 11 `router.bizzy` teltonika, 11 `wifi.bizzy` mikrotik, 6
  `starlink.bizzy`, 6 `ping.bizzy`, plus the new udp_bridge per-remote
  diagnostics — **all of those are absent today**, consistent with the
  bridge being down (no boat-side diagnostic forwarding).
- The two "real" operator-side ERRORs (`gabby_direct`,
  `router_bizzy_direct`) are downstream of the bridge being down — with
  the bridge dead, the operator router's WiFi-to-boat path goes idle and
  pings to the boat-direct addresses fail. The `gabby_vpn` ping was still
  OK (~57 ms), so the VPN path itself is fine. The STALE entries are the
  ping_monitor's own publish cadence falling behind its 30 s threshold
  while the rest of the system is degraded.

Operator chose **restart the stack** rather than dig further. Captured
because:

- Launch log persists in `~/.ros/log/latest_log/` (the directory name is a
  timestamped run, not overwritten on next launch) — tracebacks from
  whatever killed CAMP + udp_bridge will still be available post-restart
  for triage at a calmer moment.
- Coupled death of CAMP + `/operator/udp_bridge` is suspicious. They
  launch together via `operator_core_launch.py`; either one died and the
  other was killed by `on_exit=Shutdown()` cascade, or both fell to a
  common cause (e.g. memory pressure, a parent launch process restart).
  Worth a follow-up read of the launch log post-restart.

**Probable culprit to check post-restart** (low priority unless it
recurs): nothing in the operator-side launches has changed since
yesterday's clean session, so a transient cause is most likely. Bridge
death in the middle of a deployment hasn't been seen in the salmon log
history; if it shows up again today, escalate to a follow-up issue.

## 3. Post-restart state — stack healthy, but WiFi to boat is down

**2026-05-22T16:38-04:00** — Operator restarted the stack. CAMP +
`/operator/udp_bridge` both back in `ros2 node list`. Bridge has both
`wifi` and `vpn` connections to `bizzy` registered. Diagnostic surface
expanded from 6 unique tasks pre-restart → **14 tasks** (boat-side
families now flowing: `router.bizzy`, `wifi.bizzy`, `starlink.bizzy`,
`ping.bizzy`).

### Headline: WiFi to boat is completely down

Symmetric confirmation from both sides:

| Diagnostic | Level | Message |
|---|---|---|
| `mikrotik_monitor: bizzy.wifi.op: interface/wlan1` | WARN | Not running *(operator-side WiFi interface down — same as pre-restart)* |
| `mikrotik_monitor: wifi.bizzy: connection` | ERROR | Connection error to `http://wifi.bizzy.p11.lan:80/rest/system/resource`: `[Errno 113]` (no route to host) |
| `ping_monitor: ping.op: gabby_direct` | ERROR | Unreachable (100% packet loss) |
| `ping_monitor: ping.op: router_bizzy_direct` | ERROR | Unreachable (100% packet loss) |
| `ping_monitor: ping.bizzy: salmon_direct` | ERROR | Unreachable (100% packet loss) — boat → salmon WiFi path also dead |
| `ping_monitor: ping.bizzy: router_op_direct` | ERROR | Unreachable (100% packet loss) — boat → operator router WiFi path also dead |

VPN path is healthy (yesterday's anchor: `gabby_vpn` ~57 ms). All boat-side
traffic is flowing over VPN — including the diagnostic forwarding that's
populating this very table.

### `udp_bridge#24` first real ERROR trip in the field

`udp_bridge: udp_bridge operator: bizzy: resend give-ups` ::
**give-up rate 66.04/s — exceeds ERROR threshold (50/s default)**.

Compare to 2026-05-21 baselines (yesterday's §10/§11/§13):

| Sample | give-up rate | Level | Notes |
|---|---|---|---|
| 2026-05-21 12:18 | ~0/s instantaneous (lifetime 59,282) | OK | Post-startup baseline |
| 2026-05-21 12:41 | ~1.8/s background | OK | Boat in water, all paths healthy |
| **2026-05-22 16:38** | **66.04/s** | **ERROR** | WiFi path dead — every wifi-bound packet given up on |

This is the first time `#24`'s ERROR-rate trip has actually fired in
salmon log history. Two things to note:

- The demote-to-DEBUG is doing its job: `/rosout` is quiet despite
  the 66/s give-up rate. Pre-#24, this would be a ~13× larger spam
  storm than the 2026-05-19 §14 670 WARN/s firehose
  (proportionally). The new diagnostic-summary surface flags the
  problem cleanly without log spam — the design works as intended.
- The 66/s rate is consistent with the bridge being configured to send
  on **both** wifi and vpn, with wifi failing every send. If wifi is
  going to stay down (intentional or not), removing the wifi
  `connection_id` from the boat-side `topics_list` would zero out the
  give-ups; the bridge would only send over the working VPN path.

### Other Non-OK entries (cosmetic / preexisting)

| Diagnostic | Level | Notes |
|---|---|---|
| `mavros: Mount` | WARN | "Can not diagnose in this targeting mode" — preexisting, cosmetic |
| `starlink: starlink.bizzy: alerts` | WARN | `'active: install_pending'` — preexisting Starlink-side alert, not blocking |
| `mikrotik_monitor: wifi.bizzy: system` | STALE | `no successful poll yet` — downstream of the WiFi ERROR above |
| 4× `ping_monitor` STALE entries | STALE | Self-staleness — per-target poll cadence > 30 s threshold; same pattern as yesterday |

### Bridge-coupled-death pre-restart (recap for §2 follow-up)

Worth noting for post-mission triage: the `~/.ros/log/<prev>` directory
from the pre-restart session is still on disk. If we want a root cause
on the simultaneous CAMP + `/operator/udp_bridge` death, that's where
to look — `launch.log` should have either a traceback or a SIGKILL
indication. Deferred: no immediate value during the mission; high value
post-mission if recurrence happens.

### Open question for operator

WiFi-to-boat being down is either:

1. **Intentional** — early-onset Starlink-only / VPN-only mode, similar
   to the 2026-05-19 §11 deployment shape. In that case the resend
   give-up ERROR will persist until the wifi `connection_id` is
   removed from the boat-side `topics_list` (could be done via
   `rqt_udp_bridge` at runtime).
2. **Unintentional** — operator wlan1 came up "Not running" on stack
   restart and we hadn't noticed it pre-restart either (it's also
   listed in §2's pre-restart probe). Could be operator-router WiFi
   needs a kick; or boat-router WiFi-end (the AP) is the side that's
   down. Either way, until restored, the bridge sits at ERROR-rate.

Awaiting operator decision.

## 4. WiFi investigation — boat-side WiFi router is dead, not the link

**2026-05-22T16:47-04:00** — Following operator request to look into the
WiFi issue. The §3 symptom set (operator wlan1 "Not running" + 100% packet
loss on every WiFi-routed ping in both directions) could be explained by
either a propagation issue across the water or by the boat WiFi router
itself being down. Tracked it down to the latter.

### DNS topology check (salmon side)

```text
$ getent hosts wifi.bizzy.p11.lan wifi.vpn.bizzy.p11.lan
172.16.20.3     wifi.bizzy.p11.lan
(no entry)      wifi.vpn.bizzy.p11.lan
```

The boat WiFi router has a direct-route entry (`172.16.20.3`, only
reachable when wlan1 is up) but **no VPN alias**. Compare to the boat
cellular router which does have a VPN alias:

```text
$ getent hosts router.vpn.bizzy.p11.lan gabby.vpn.bizzy.p11.lan
192.168.21.1    router.vpn.bizzy.p11.lan
192.168.21.5    gabby.vpn.bizzy.p11.lan
```

Cellular router ping over VPN: ~62 ms RTT (healthy). So the VPN backbone
is fine, the WiFi router just has no VPN-side alias in salmon's
`/etc/hosts`. Worth a follow-up to add one — without it salmon can never
query the WiFi router's API when WiFi is down, which is the most common
failure mode.

### Smoking gun: ping from gabby (boat-side LAN)

`ssh field@gabby.vpn.bizzy.p11.lan 'ping -c 2 wifi.bizzy.p11.lan'`:

```text
2 packets transmitted, 0 received, 100% packet loss
```

Gabby is wired to the same LAN as the boat WiFi router (172.16.20.x).
Gabby pinging `172.16.20.3` and getting 100% packet loss means the WiFi
router is **dead from inside the boat itself**. That's also the source
of the `mikrotik_monitor: wifi.bizzy: connection` ERROR forwarded over
the bridge — it's gabby's mikrotik_monitor publishing it, failing to
reach its target on the local subnet.

### Conclusion

The boat-side WiFi router (`wifi.bizzy.p11.lan`, `172.16.20.3`) is the
single point of failure. Possible causes:

- Powered off (PDU output dropped, blown fuse)
- Frozen — needs a power-cycle
- Wiring problem (Ethernet to gabby pulled, antenna disconnected,
  power lead loose)
- Firmware crash / network config wiped

It is **not** a range or RF propagation problem; gabby would still see
the router on the wired LAN side regardless of how far the boat is from
salmon.

### Knock-on effects

- Operator-side wlan1 "Not running" — symptom; cleared by either bringing
  the boat WiFi router back, or removing wlan1 from the operator
  router's monitoring scope.
- `udp_bridge` give-up rate at 66/s — every wifi-bound resend is failing.
  Will persist at ERROR until the wifi `connection_id` is removed from
  the boat-side `topics_list` or the WiFi router is restored.

### Options

1. **Power-cycle the boat WiFi router** — most likely fix if it's just
   frozen. Requires physical access or remote PDU control.
2. **Run Starlink/VPN-only for today** — remove `wifi` `connection_id`
   from the boat-side `topics_list` (yaml edit on gabby's
   `bizzyboat.yaml` `/**/udp_bridge:` block, or runtime via
   `rqt_udp_bridge`). Drops give-up rate to ~0 and clears the bridge
   ERROR; bridge keeps running on VPN/Starlink only. Today's mission
   scope already includes a Phase 3 Starlink load test, so this would
   amount to bringing that forward.

### Follow-up tracker entries

- **Add `wifi.vpn.bizzy.p11.lan` host alias** so salmon can query the
  boat WiFi router's API when WiFi is down (today's case). Likely
  belongs in whatever DNS / `/etc/hosts` source `gabby.vpn.bizzy.p11.lan`
  came from. File at wrap-up.
- **Investigate boat WiFi router (`172.16.20.3`) cause of death** —
  whether power, firmware, or something else. Once it's recovered,
  capture `link-downs` counter + `last reboot reason` from the router
  itself for the issue.

## 5. WiFi recovery — physical fix on the boat

**2026-05-22T16:56-04:00** — Operator reported: "wifi was unplugged on
the boat, replugged in." So the §4 diagnosis (boat WiFi router dead,
not the link) was right — the failure mode was physical: power lead
or Ethernet to the boat WiFi router had come unplugged. Restored by
replug.

### Recovery dynamics

| Signal | At-replug snapshot (16:46) | ~40 s after replug | Trend |
|---|---|---|---|
| Ping RTT salmon → `gabby.bizzy.p11.lan` (WiFi-direct) | 1.5–177 ms, 0% loss (link settling) | **1.4–118 ms, avg 25 ms**, 0% loss | stable |
| `mikrotik_monitor: bizzy.wifi.op: interface/wlan1` | cleared | cleared | OK |
| `mikrotik_monitor: wifi.bizzy: connection` | cleared (gabby can poll the WiFi router again) | cleared | OK |
| `ping_monitor: ping.op: gabby_direct` / `router_bizzy_direct` | cleared | cleared | OK |
| `ping_monitor: ping.bizzy: salmon_direct` / `router_op_direct` | cleared | cleared | OK |
| `udp_bridge: bizzy: resend give-ups` rate | 1095/s | **617/s** | halving ~every 30 s |
| Lifetime `give_ups_total` (post-recovery sample) | — | **364,293** | one-time backlog from the WiFi-down period |

The udp_bridge ERROR persists transiently because the bridge is draining
a resend backlog over the WiFi link as it comes back. The
`give_ups_total` of ~364 k accumulated during the ~10–15 minutes wifi
was down (rate was 66/s on the §3 sample at 16:38, much higher in the
first post-replug seconds as the queue caught up) — that's the
one-time cost of the outage. As the bridge clears its window the rate
should land back near the 1–2/s background we saw 2026-05-21 §11 once
nominal flow resumes.

### Remaining non-OK at re-sample (all cosmetic / preexisting)

- `mikrotik_monitor: wifi.bizzy: interface/{ether2,3,4,5}` WARN
  "Not running" — unused Ethernet ports on the boat WiFi router; same
  shape as yesterday's §10 baseline (likely 4 of yesterday's "11
  wifi.bizzy mikrotik tasks").
- `mavros: Mount` WARN — preexisting cosmetic.
- `starlink: starlink.bizzy: alerts` WARN `'active: install_pending'`
  — preexisting Starlink-side alert; not blocking.

### Notes for wrap-up

- The §4 follow-up to **add a `wifi.vpn.bizzy.p11.lan` host alias**
  becomes more interesting in light of today's incident — had it been
  in place, the operator-side mikrotik_monitor could have polled the
  boat WiFi router's status over VPN even when the WiFi link was
  down, which would have told us "router unreachable from operator AND
  from boat-side gabby" much faster than the ssh-to-gabby fallback I
  used. File at wrap-up.
- The boat WiFi router being on a single un-secured cable that can
  un-plug accidentally is itself a finding — worth a follow-up on
  physical-mount / strain-relief / cable-tie at next opportunity.
  Won't file as a workspace issue today since it's a hardware-ops
  concern; flagging here for the operator.

## 6. Costmap freezing in rviz — `costmap_updates` not bridged

**2026-05-22T17:19-04:00** — Operator reported rviz showing a few costmap
frames then freezing. Root-caused to a missing bridge topic.

### Probe

`ros2 topic hz` over a 6 s window:

| Topic | Pub count | hz | Notes |
|---|---|---|---|
| `/bizzy/local_costmap/costmap` | 1 | (silent in window) | bridge-republished, latched full grid |
| `/bizzy/local_costmap/costmap_updates` | **0** | (no publisher) | **not bridged at all** |
| `/bizzy/local_costmap/published_footprint` | 1 | 2.89 Hz | bridged, flowing |

### Diagnosis

nav2 splits costmap output across two topics:

- `costmap` — full `OccupancyGrid`, published with TRANSIENT_LOCAL
  durability, only on substantive change / startup / resize.
- `costmap_updates` — `OccupancyGridUpdate` streaming deltas at the
  costmap publish rate.

rviz subscribes to both and overlays the deltas on the latched full grid.
If only `costmap` is forwarded — which is the case in `bizzyboat.yaml`'s
`topics_list` (see §"Files referenced" below) — rviz sees the initial
latched grid, then a sparse republish from the bridge's `period: 3.0`
re-emit, and **never sees the deltas**. To a human watching rviz this
reads exactly as "a few frames, then frozen".

Note `published_footprint` worked because it's an ordinary
`PolygonStamped` stream, no updates-topic counterpart.

### Fix shape

Add `costmap_updates` to the bridge's topics list. In `bizzyboat.yaml`
(boat-side `bizzyboat_project11/config/bizzyboat.yaml`), the
`/**/udp_bridge:` block currently has (lines 63–73 / 110–111):

```yaml
topics_list:
  - local_costmap                              # → local_costmap/costmap
  - local_costmap_footprint                    # → local_costmap/published_footprint
…
local_costmap: {source: local_costmap/costmap, period: 3.0}
local_costmap_footprint: {source: local_costmap/published_footprint}
```

…and is missing a `costmap_updates` entry. Proposed addition:

```yaml
topics_list:
  - local_costmap
  - local_costmap_updates
  - local_costmap_footprint
…
local_costmap_updates: {source: local_costmap/costmap_updates}
```

(No `period` clamp — updates should flow at native rate so rviz tracks
the costmap as it actually changes; the bridge's bandwidth budgeting
should already absorb this since updates are sparse deltas.)

Today this is on the **wifi** `topics_list` only (line 72 area). The
already-planned Phase 3 deliverable from the deployment issue is to
also wire `local_costmap` (the full grid) onto **vpn** dynamically; the
`local_costmap_updates` addition belongs in both lists for symmetry.

### Runtime workaround (no boat-side rebuild required)

`rqt_udp_bridge` can add `bizzy/local_costmap/costmap_updates` at
runtime on whichever `connection_id` is preferred. This unfreezes rviz
for the rest of today's mission without touching `bizzyboat.yaml`.

### Follow-ups for wrap-up

- **`bizzyboat.yaml` — add `local_costmap_updates` to bridge `topics_list`
  on wifi (and on vpn for Phase 3 symmetry)**. Without it rviz's costmap
  display is non-functional any time the costmap is actually changing,
  which is most of the mission. Pair with the planned `local_costmap`
  vpn addition into a single small PR. Note `costmap_updates` use
  `OccupancyGridUpdate`, not the full `OccupancyGrid`, so the
  per-message size is small — should be safe to forward at native rate
  on both connections.
- Same gap likely exists on any other `*_costmap` exposed through the
  bridge (e.g. `global_costmap` if/when added) — audit the
  `topics_list`s at wrap-up rather than discovering the gap one costmap
  at a time.

### Files referenced

`layers/main/platforms_ws/src/unh_echoboats_project11/bizzyboat_project11/config/bizzyboat.yaml`:

- L63–73 — wifi `topics_list` (the costmap entry lives here)
- L110–111 — `local_costmap` / `local_costmap_footprint` topic-mapping
  definitions
- L286 — operator-side bag also records only `local_costmap/published_footprint`,
  not `costmap` or `costmap_updates` — flagged for the wrap-up audit too
  (operator-side bag is dev-machine analysis material; boat-side bag is
  the load-bearing one for costmap analysis, but if we want operator-rviz
  reproducibility we may want operator-side recording of both costmap
  topics).

## 7. Battery annunciator is missing on the operator side

**2026-05-22T19:26-04:00** — Operator checked the battery annunciator
against the §"battery context" anchors (mean voltage now 22.71 V,
below the 23.0 V WARN line documented in
`bizzyboat_project11/docs/bizzyboat_hardware.md` and matching the FCU
`BATT_LOW_VOLT 23.0` setting). Expected yellow. **Annunciator stayed
green / off.** Tracked down two compounding gaps.

### Gap 1 — ~~operator-side annunciator config has no Battery row~~ (RETRACTED)

**Initial claim was wrong.** Operator exported the running annunciator
config to `/tmp/aconf`; it's actually `bizzyboat_annunciator.yaml`, not
`bizzyboat_operator_annunciator.yaml`. The running 13-row config does
include a Battery indicator:

```yaml
- name: Battery
  source: diagnostics
  diagnostic_name: 'mavros: Battery'
```

…along with Cell Signal, Starlink, UDP WiFi/VPN, GPS, RTK, NTRIP, FCU,
Comms, Nav Stack, Mission. Annunciator is **correctly configured** for
battery monitoring.

My earlier grep landed on `bizzyboat_operator_annunciator.yaml` (which
does only have 9 network/path indicators and no Battery) and I
assumed that was the loaded file. It is not. The two yaml files in
the repo:

- `bizzyboat_annunciator.yaml` — 13 rows, includes critical-systems
  (Battery, GPS, RTK, NTRIP, FCU, etc.) — **this is the one running on salmon today**.
- `bizzyboat_operator_annunciator.yaml` — 9 rows, network/path only —
  apparently not loaded; either legacy or a stale rename. Worth a
  wrap-up cleanup pass to confirm which is canonical.

### Gap 2 — `mavros: Battery` DiagnosticStatus isn't being published

Even if the operator-side YAML did reference `mavros: Battery`, it
would show STALE — `/diagnostics` has no `mavros: Battery` task
anywhere on the bus today. Full mavros-related task list from a
fresh sample:

```text
[WARN ] mavros: Mount       :: Can not diagnose in this targeting mode  (cosmetic)
[ERROR] mavros: System      :: …
```

That's all. No `mavros: Battery`, no `mavros: GPS`, no
`mavros: Heartbeat`, no `mavros: FCU connection`, etc. The raw battery
data is fine — `/bizzy/mavros/battery` is publishing
(`voltage: 22.706`, `current: 0.01`) — but the diagnostic side is
silent. Either mavros's `sys_status` / `battery_status` plugins
aren't loaded, or they're loaded but not pushing DiagnosticStatus,
or the `/diagnostics` updater rate has dropped sub-second and got
clipped from my capture window (unlikely — yesterday's §10 baseline
showed the mavros plugins did publish to `/diagnostics`).

**`mavros: System` at ERROR** is suspicious in this context — if the
FCU connection is degraded, the battery_status plugin may have gone
silent as a side effect. Worth a closer read of `mavros: System`'s
message field next time anyone looks (didn't capture full payload in
this pass — small follow-up, not blocking).

### Follow-ups for wrap-up

- **`mavros: Battery` (and family) DiagnosticStatus not publishing** —
  **the only real bug behind today's symptom**. Annunciator is
  correctly wired (Gap 1 retracted); it stays green because there's
  no DiagnosticStatus to colour from. Verify the mavros plugin list
  on the boat actually loads the battery / sys / gps plugins. The
  historical baseline (yesterday's §10 saw mavros tasks flowing)
  makes today's silence a regression candidate. Cross-check the
  boat-side `mavros_node.launch` / `mavros_blacklist.yaml` for any
  change between 2026-05-21 and today that could have dropped the
  plugins. The 4-instance perception fix and FCU EK3 reconfig
  committed yesterday were on different layers, but worth a
  `git log` sweep on `bizzyboat_project11`'s mavros configs.
  `mavros: System` ERROR observed in the same sample is suspicious —
  capture its full message field at next opportunity.
- **Clean up the two annunciator YAMLs** — `bizzyboat_annunciator.yaml`
  is loaded; `bizzyboat_operator_annunciator.yaml` is apparently
  unused. Either delete the unused one, or repurpose / rename so the
  intended canonical file is unambiguous. Low priority — cosmetic
  cleanup, doesn't affect runtime.

## 8. CAMP froze again — solo kill this time, rest of stack survived

**2026-05-22T19:37-04:00** — Operator reported CAMP unresponsive a second
time. Different shape from §2:

| Signal | §2 (16:30) | §8 (19:37) |
|---|---|---|
| `/operator/camp` in `ros2 node list` | absent | **still present** |
| `/operator/udp_bridge` in `ros2 node list` | absent | **still present** |
| CAMP process | already gone | alive (PID 202726), GUI hung |
| Parent `operator_core_launch.py` | (not checked) | alive (PID 202706) |
| Recovery path | full stack restart | solo kill of CAMP |

This was a GUI hang, not a process death — same signature as the rviz
hang earlier (§"rviz kill" — SIGTERM ignored, went down on SIGKILL).

### Solo kill outcome

- `kill 202726` (SIGTERM) — ignored.
- `kill -9 202726` (SIGKILL) — process exited.
- After kill: `/operator/camp` gone from node list; `/operator/udp_bridge`
  **still in node list**; parent `operator_core_launch.py` still alive;
  CAMP did **not** auto-restart.

### Update to §2's open question

§2 left open whether CAMP + udp_bridge died together via an
`on_exit=Shutdown()` cascade or fell to a common cause. The solo-kill
result here resolves it: **CAMP's `on_exit` is not `Shutdown()` and not
`Restart`** — when CAMP dies alone, the rest of the stack keeps running
and CAMP stays gone until manually relaunched. So §2's coupled CAMP +
udp_bridge death was driven by a **common cause** (something that took
out both at once), not by CAMP's own `on_exit` policy. The
pre-restart `~/.ros/log/<2026-05-22T??:??:??-salmon-…>` directory is
still the right place to look for the common-cause traceback when
triage time allows.

## 9. Brief stack degradation observed between CAMP kill and recovery

**2026-05-22T19:37-04:00** — In the diagnostic sample taken just after
the solo CAMP kill (before CAMP came back), the `/diagnostics` surface
shifted in ways worth recording.

### Changes vs. pre-kill (§3/§5 reference baseline)

| Diagnostic | Pre-kill / earlier sample | Post-kill sample | Notes |
|---|---|---|---|
| `udp_bridge: bizzy: wifi` | OK | **WARN** "tx failures/drops" | was clean after §5 wifi recovery |
| `udp_bridge: bizzy: vpn` | OK | **WARN** "tx failures/drops" | **first time VPN-side is WARN today** |
| `udp_bridge: resend give-ups` | dropping (617/s → settling) | WARN 22.09/s | trending up again |
| `mavros: System` | ERROR (no message field captured) | **ERROR "Sensor health"** | message field now populated — degraded sensor |
| All `mavros: Battery/GPS/RTK/NTRIP/Heartbeat` annunciator rows | STALE (per §7) | still STALE | unchanged — that's the §7 gap, not new |

### Interpretation

- Killing CAMP shouldn't degrade boat-side bridge tx — CAMP is a pure
  consumer of bridge data, not a producer. **Both** bridge legs going
  WARN simultaneously points at a boat-side / link-side cause, not a
  consequence of the kill.
- The `mavros: System` message field becoming `"Sensor health"` is
  notable. mavros's `sys_status` plugin emits "Sensor health" when the
  FCU's `SENSOR_HEALTH_BITS` go non-OK — often correlated with low
  battery as some sensors (e.g. magnetometer noise, EKF flags) start
  failing at low voltage. We're currently at 22.7 V mean (§"battery
  context" anchors), which is consistent.
- The 22 s window between samples is too short to say whether the
  degradation correlates with anything specific (CAMP kill vs. a
  separate boat-side event). Worth a post-mission cross-reference
  against the boat-side bag.

### Video display

Cameras were never actually lost — `/bizzy/sensors/cameras/oak_*/image_raw/ffmpeg`
all streamed steadily at ~5.0 Hz throughout (verified during the
diagnostic probe). What the operator perceived as "lost videos" was the
CAMP camera-grid widgets going away with CAMP. Restored when CAMP came
back.

### State at recovery

**2026-05-22T19:37-04:00** — Operator reported "all are back now" — CAMP
relaunched, video panels restored, annunciator reds reverted. No
re-sample taken (operator-time precious). Trust the qualitative
"all back" call.

### Follow-ups for wrap-up

- **CAMP GUI hangs (×2 today, both ignored SIGTERM)** — pattern. Could
  be Qt event-loop blocking on a slow ROS callback (perhaps the
  `BridgeInfo` topic deserialize path? both hangs were after the
  bridge had been under sustained load). Worth attaching a debugger or
  enabling Qt event-loop tracing at next opportunity. The two
  `~/.ros/log/<run>-salmon-…/launch.log` directories from today's
  pre-restart + the parent launch's current dir should both be
  preserved for triage; today's CAMP hang #2 didn't kill the launch
  parent so its log is in the *current* `latest_log` directory and
  will keep accumulating until session end.
- **`mavros: System` "Sensor health"** — capture full payload + which
  bits are unhealthy next time it's WARN/ERROR. If it correlates with
  voltage, that's a useful operational signal (worth surfacing on the
  annunciator as a dedicated row, not buried in `mavros: System`).
- **Both-bridge-legs simultaneous WARN** is new today. Hard to act on
  without more samples, but if it recurs near LVD trip, that becomes
  a battery-induced-degradation anchor point.

## 10. Wrap-up snapshot

**2026-05-22T20:26-04:00** — Operator advised recovery. State captured
on salmon at wrap-up time.

### Stack state at wrap-up

`ros2 node list` shape:

- `/operator/camp` ✅ (back after the §8 solo restart)
- `/operator/udp_bridge` ✅ (survived the §8 CAMP-only kill, plus
  yesterday's `udp_bridge#24` per-remote diagnostics)
- `/mikrotik_monitor`, `/teltonika_monitor`, `/ping_monitor`,
  `/starlink_diagnostics` ✅
- `/molab/johnny5/johnny5_node` ✅ (pre-existing 401 WARNs unchanged)
- `/rosbag2_recorder` ✅
- 3 rqt nodes ✅
- `/bizzy/{command_bridge_sender,joint_state_publisher,joy_node,joy_to_helm,robot_state_publisher}`
  ✅

Boat-side still up: `/bizzy/marine/heartbeat` publishing,
`piloting_mode: autonomous`, `marine_autonomy_standby: false`.
Operator presumably winding down the stack from here.

### Battery at wrap-up

`/bizzy/mavros/battery`: **`voltage: 22.708 V`**, `current: 0.01 A`,
mavros `percentage: -0.01` (unconfigured placeholder).

Cross-deployment drain summary (operator-side view; gabby log is the
load-bearing voltage timeline):

| Deployment | Voltage start | Voltage end-of-day | Session duration |
|---|---|---|---|
| 2026-05-19 | (per dev log) | (per dev log) | — |
| 2026-05-21 | (per dev log) | 26.05 V (per today's deploy issue) | ~2 h 46 m (bag) |
| 2026-05-22 | 25.25 V | **22.71 V** | ~8 h 20 m (sessions combined) |

So today drained about 2.5 V of nominal pack over an 8-ish-hour
session, ending well below the documented 23.0 V `BATT_LOW_VOLT` /
hardware WARN threshold (§"battery context" anchors) — squarely in
the WARN band, ~1.2 V above the 21.5 V ERROR threshold. **LVD trip
was not reached on the operator-side view** — boat heartbeat still
publishing at wrap-up.

This is the §"primary mission" deliverable (battery characterization
to LVD) being partially met: 3-sample discharge data captured, but
LVD itself was not tripped today. Worth confirming on the boat-side
log whether boat reached LVD or whether the operator pulled the
mission before LVD condition.

### Operator bag(s) — two shards today

The mid-mission stack restart (§"§2 → §3" recovery) split the bag:

| Bag | Duration | Path | Size | Status |
|---|---|---|---|---|
| Pre-restart | **15,773 s ≈ 4 h 22 m** (12:06:48 → 16:29:41 EDT) | `/home/field/data/logs/operator/2026-05-22/bags/operator_2026-05-22T12.06.47/` | **106 MiB**, mcap, single shard | finalized |
| Post-restart | ~3 h 55 m so far (16:31:19 → still recording at wrap-up time) | `/home/field/data/logs/operator/2026-05-22/bags/operator_2026-05-22T16.31.19/` | 153 MiB (live; no metadata yet) | active until stack shutdown |

Pre-restart bag message counts:

```text
/diagnostics ........................................ 222,268
/tf ................................................. 390,799
/operator/udp_bridge/bridge_info ......................   6,250
/operator/udp_bridge/remotes/bizzy/bridge_info ........   6,162
/operator/udp_bridge/{,remotes/bizzy/}topic_statistics  24,778 (12321 + 12457)
/rosout ..............................................     60
/tf_static ...........................................      2
/bizzy/marine/command ................................      0
/bizzy/piloting_mode/manual/helm .....................      0
```

Same operator-side topic set as yesterday — no camera or costmap
data on the salmon bag by design; analysis-side material comes
from the boat-side bag on gabby.

**Bag-size cross-deployment comparison** (operator-side):

| Deployment | Operator bag size | Duration | Bytes / sec | Notes |
|---|---|---|---|---|
| 2026-05-19 | 296 MB | ~2 h | ~41 kB/s | pre-`#24` (670 WARN/s into /rosout) |
| 2026-05-21 | 99 MB | ~2 h 46 m | ~10 kB/s | post-`#24`; #24 WARN-demote validated |
| 2026-05-22 (pre-restart) | 106 MiB | 4 h 22 m | ~7 kB/s | continuing the `#24` benefit; also helped by WiFi-down period producing fewer per-remote-bridge stats |
| 2026-05-22 (post-restart, partial) | 153 MiB (incomplete) | ~3 h 55 m | ~11 kB/s | mid-session restart added some startup overhead |

Today's per-second rate is in the same ballpark as 2026-05-21 — the
`#24` demote benefit is durably holding; the multi-day numbers now
support yesterday's "headline #24 evidence" framing.

### Today's salmon-side findings (recap, for dev integration)

Numbered per the log sections:

| § | Finding | Disposition |
|---|---|---|
| 2 | CAMP + `/operator/udp_bridge` died together pre-restart | Cause-unknown, see §8 update — was common-cause, not `on_exit` cascade. `~/.ros/log/<pre-restart-run>` retained for triage. |
| 3 | Post-restart stack healthy; first real-world `udp_bridge#24` ERROR-rate trip at 66/s with WiFi dead; demote-to-DEBUG keeps `/rosout` quiet | `#24` design works as advertised. |
| 4 | Root cause of WiFi-down: boat WiFi router unreachable from gabby — physical / power issue, not propagation | Confirmed via ssh-to-gabby ping. |
| 5 | Operator-side fix: replug on boat → wifi recovers in <1 min; give-up rate drains from 1095/s → 22/s in ~50 min as backlog clears (lifetime total 364 k cost of the outage) | Recovered cleanly. |
| 6 | rviz costmap freezes after a few frames | `bizzyboat.yaml` bridge `topics_list` forwards `local_costmap/costmap` but not `local_costmap/costmap_updates`. Audit `*_costmap` more broadly. |
| 7 | Battery annunciator stays green at 22.7 V mean | Annunciator config correctly references `mavros: Battery`; `mavros: Battery` (and family) DiagnosticStatus not publishing today — regression vs. 2026-05-21 §10. `mavros: System` was ERROR with `"Sensor health"` message at one point. |
| 8 | CAMP froze a second time, GUI-only hang (process still alive, SIGTERM ignored, SIGKILL needed) | Solo kill worked; resolves §2's open question — `on_exit` is not `Shutdown` / not `Restart`. §2's coupled death was common-cause, not cascade. |
| 9 | Brief diagnostic shifts during §8 CAMP hang window: both `udp_bridge: bizzy: {wifi,vpn}` legs WARN simultaneously (first VPN-side WARN today), `mavros: System` "Sensor health" detail | Cause unclear; CAMP kill shouldn't cause boat-side bridge tx degradation, so points at boat-side / link-side coincidence. Worth a post-mission cross-reference vs boat-side bag. |

### Files touched on salmon today

- `docs/logs/2026/2026-05-22_salmon_logs.md` — this file. Pending push
  at session close per convention.
- No code changes were made from salmon today.

### Pending on operator (salmon-side)

- **Push this log to gitcloud at session close** (per
  `2026-05-21_salmon_logs.md` convention).
- The top-of-log `## Summary` and `## Lessons Learned` sections stay
  as placeholders here — those get integrated into the dev log at
  wrap-up, not into per-host logs.

### Pending for dev-side wrap-up

(Consolidated for the dev-side wrap-up PR. Reconcile via
`/import-field-changes` only the ones that landed as field commits;
the rest are issue-worthy follow-ups.)

- **No field commits on salmon today** — only the log file. The
  field commits today are gabby-side (perception multi-instance config,
  4:3 OAK A/B, possibly others — gabby log will say).
- **Follow-up issues** (from this log's findings, ordered by value):
  1. `mavros: Battery` (and family) DiagnosticStatus not publishing —
     regression vs. 2026-05-21 §10 baseline. Highest-value because it
     prevents battery monitoring via the annunciator, which is itself
     the operator's primary visibility into the drain-mission.
  2. `bizzyboat.yaml` bridge `topics_list` missing
     `local_costmap_updates` → rviz can't render incremental costmap
     updates. Bundle with the planned Phase 3 costmap-on-vpn PR.
     Audit other `*_costmap` topics for the same gap.
  3. Add `wifi.vpn.bizzy.p11.lan` host alias so operator-side
     `mikrotik_monitor` can poll the boat WiFi router via VPN when
     wifi is down (today's incident showed why this matters).
  4. CAMP GUI-hang pattern (×2 today, both ignored SIGTERM). Likely
     Qt event-loop blocking on a slow callback. Attach a debugger /
     enable event-loop tracing at next opportunity. Two
     `~/.ros/log/<run>-salmon-…/launch.log` directories preserve
     state for triage.
  5. `mavros: System` "Sensor health" — capture full payload + which
     bits are unhealthy next time it surfaces, ideally with a
     concurrent voltage anchor. If it tracks voltage, worth a
     dedicated annunciator row.
  6. Both-bridge-legs simultaneous WARN (`wifi` + `vpn`) — observed
     once today during the §9 window. Insufficient samples; flag for
     recurrence at next deployment.
  7. Boat WiFi router physical cable strain-relief / cable-tie
     (hardware-ops, not workspace issue).
  8. Annunciator YAML cleanup — `bizzyboat_operator_annunciator.yaml`
     apparently unused; `bizzyboat_annunciator.yaml` is the live one.
     Either delete or rename so canonical file is unambiguous.
  9. **`~/screenshooter.bash` uses UTC for day rollover** — script at
     `/home/field/screenshooter.bash` (Val's original 2018 tool, not in
     a project11 repo; lives in `$HOME` on the operator host) calls
     `date -u "+%Y-%m-%d"` on lines 103 / 113 / 125. UTC midnight
     during DST is 20:00 EDT, so a typical late-afternoon field
     session that runs past 20:00 EDT gets split into two day-dated
     output files:
     ```text
     operator_2026-05-22.mp4 — 358 MiB, finalized at 20:08 EDT (= 00:08 UTC May 23)
     operator_2026-05-23.mp4 —  19 MiB, started 20:27 EDT, still growing at wrap-up
     ```
     The script's `encode_day` did run on the UTC-previous-day at the
     boundary (the 358 MiB mp4 is intact); the bug is just that "the
     previous day" is the UTC previous day, not the local field-day,
     so the local field session's screenshots are scattered across two
     output buckets. Fix is local: switch `date -u` to `date` (local
     time) on those three lines, or use a configurable rollover hour
     (e.g. 04:00 local) to avoid the rare local-midnight case too.
     Doesn't affect any salmon-side ROS data — purely an output-naming
     issue for the post-mission screenshot mp4s. Worth a quick local
     fix at next opportunity; not workspace-tracked since the tool
     isn't in a project11 repo.
- **Verify before June 4 items**: deferred to dev log — mercat NTP
  capture and AML SVS bag verification were boat-side tasks not
  exercised from salmon today.
- **Pre-restart `~/.ros/log/<run>-salmon-…/launch.log` directory** —
  preserve for §2 common-cause triage. Also keep the post-restart
  log dir (which will close out when the operator stops the stack)
  for §8 CAMP-hang triage.

## 11. Stack shutdown — post-restart bag finalized

**2026-05-22T20:44-04:00** — Operator shut the operator stack down
between §10 and this section: `ros2 node list` returns 0 nodes and
the boat-side heartbeat is no longer publishing through the bridge.
The post-restart bag finalized cleanly as a result.

### Post-restart bag — final numbers

`ros2 bag info /home/field/data/logs/operator/2026-05-22/bags/operator_2026-05-22T16.31.19/`:

```text
Files:             operator_2026-05-22T16.31.19_0.mcap
Bag size:          153.9 MiB
Duration:          14186.498s  ≈  3 h 56 m 26 s
Start:             2026-05-22T16:31:20.397 EDT
End:               2026-05-22T20:27:46.896 EDT
Messages:          736,335
```

So today's combined operator-side capture (across the two bags):

| Bag | Duration | Size | Messages |
|---|---|---|---|
| `operator_2026-05-22T12.06.47/` | 4 h 22 m 53 s | 105.9 MiB | 650,319 |
| `operator_2026-05-22T16.31.19/` | 3 h 56 m 26 s | 153.9 MiB | 736,335 |
| **Total** | **~8 h 19 m** | **~260 MiB** | **1,386,654** |

Restart-window gap between bags: **16:29:41 → 16:31:20 ≈ 1 m 39 s** —
the time between bag #1 stopping (with the stack shutdown that
followed §2) and bag #2 starting (after the §3 restart). Small enough
that no significant operator-side telemetry was lost during the
transition.

Updates the §10 cross-deployment table: the **2026-05-22 totals are
~260 MiB / ~8 h 19 m ≈ 8.7 kB/s** — between yesterday's 10 kB/s
post-`#24` baseline and the headline today, the `#24` demote benefit
is durably holding across multi-day comparison.

### Encoder still running

The §"§12 (next)" manual local-day screenshot encode was still in
progress at stack-shutdown time (frame ~196 / 447 at last sample,
~0.55× wall-clock, so ETA a few more minutes from 20:43-04:00). The
encode is fully independent of the ROS stack — it just walks PNGs on
disk — so a stack shutdown doesn't affect it. Output will appear at
`operator_2026-05-22_local.mp4` when the atomic `.tmp` → `mv` lands.

## 12. Manual local-day screenshot encode (side-quest to wrap-up #9)

**2026-05-22T20:41-04:00** — Per operator request, encoded the local
EDT-day 2026-05-22 screenshots into a single combined mp4 (rather
than waiting for the screenshooter fix to land). One-off bash script
written at `/tmp/encode_local_2026-05-22.sh` mirroring
`~/screenshooter.bash`'s `encode_day()` ffmpeg pipeline (same x265 /
yuv444p / fps=2 / crf=22 / preset=medium), but built the input file
list from the **union of both UTC-bucketed raw dirs**:

```text
~/data/logs/operator_raw/screenshots/2026-05-22/  422 PNGs (16:06:46 → 23:59:20 UTC)
~/data/logs/operator_raw/screenshots/2026-05-23/   25 PNGs (00:00:26 → 00:28:29 UTC)
                                          total: 447 PNGs (12:06:46 → 20:28:29 EDT)
```

Sort is alphabetic on the UTC-stamped filenames, which is chronological
order by construction — no reordering needed across the UTC midnight.

Output paths (atomic via `.tmp` → `mv` per the original encode_day
pattern):

```text
~/data/logs/operator/2026-05-22/screenshots/operator_2026-05-22_local.mp4   ← combined
                                            operator_2026-05-22_local.log
                                            operator_2026-05-22_local.csv
```

Existing `operator_2026-05-22.mp4` (358 MiB, UTC-day only) and
`operator_2026-05-23.mp4` (still being written) were not touched. The
local-day file is what dev-side analysis should pick up; the
UTC-bucketed pair are kept in place for now (don't strictly need them,
but harmless and they let us reconstruct the rollover artifact if the
wrap-up issue needs an example).

Encode launched in background (PID 230535 at script start) via `nohup … &` /
`disown` so the operator could keep wrapping up; took roughly the
expected few minutes for 447 frames at x265 medium.

The script `/tmp/encode_local_2026-05-22.sh` is ephemeral (lives in
`/tmp`, gone on next reboot). If a similar mp4-recovery becomes a
recurring need (any time a deployment runs past 20:00 EDT during DST),
the screenshooter follow-up (§10 wrap-up #9) should land that fix in
the source script instead of re-running this side-quest.

### Encoder result

**2026-05-22T20:50-04:00** — Encoder exited cleanly. Final output:

| Field | Value |
|---|---|
| Output | `~/data/logs/operator/2026-05-22/screenshots/operator_2026-05-22_local.mp4` |
| Size | **361 MiB** (377,873,862 B) |
| Frames in mp4 | 446 (one less than the 447 input PNGs — likely a duplicate-timestamp dedupe by ffmpeg's concat demuxer; not material for the analysis use case) |
| Encode wall-time | 367.9 s ≈ 6 min 8 s |
| Encoder rate | 1.21 fps (encode) at `medium` x265 preset, yuv444p |
| Avg QP | 18.55 |
| Atomic move | `.tmp` → `.mp4` successful (no `.tmp` orphan) |

Cross-check against the UTC-bucketed pair: 361 MiB combined vs
358 MiB (May-22 UTC bucket) + 19 MiB (May-23 UTC bucket, partial) =
377 MiB raw concat — the difference (~16 MiB / 4%) is x265 finding
more inter-frame correlation across the previously-split boundary
during the single combined encode. Cosmetic but worth noting: the
single encode is also marginally smaller than the sum, not just more
correctly organized.

---
**Authored-By**: `Claude Code Agent`
**Model**: `Claude Opus 4.7 (1M context)`
