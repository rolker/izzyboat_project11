---
issue: 455
---

# Issue #455 — operator.yaml: raise the helm admission floor on the uplinks

## Implementation
**Status**: complete
**When**: 2026-08-24 14:58 -04:00
**By**: Claude Opus

**Issue**: #455
**Branch**: `feature/issue-455` (3 commits; published as PR #456 after operator confirmation)

### What changed

`admission_floor_bytes_per_second: 32768.0` added to every operator→boat
uplink connection, with the rationale inline in the config:

| File | Connections |
|---|---|
| `bizzyboat_project11/config/operator.yaml` | `wifi`, `vpn`, `cell` |
| `izzyboat_project11/config/operator.yaml` | `wifi`, `vpn` |

Two commits:

- `a8e059b` — **whitespace only**. Both files indent their `topics_list:`
  sequence items at the same column as the key. That parses identically but
  the repo's own yamllint hook (default `indentation` rule) rejects it, so
  neither file could be committed at all without `--no-verify`. Verified
  pre-existing: bare `HEAD` fails the same check. `yaml.safe_load` of both
  files asserted equal to the HEAD version before committing.
- `c393503` — the admission floor itself.

### FINDING: the value must be a float, not the integer in the issue text

The issue's snippet says `admission_floor_bytes_per_second: 32768`. Applied
literally that **breaks the bridge**. `udp_bridge.cpp:544` declares the
parameter with a `double` default (`kDefaultAdmissionFloorBytesPerSecond`),
and rcl parses a bare `32768` in YAML as an integer, so `on_configure`
throws and the node never leaves `unconfigured`. Reproduced directly:

```
[ERROR] [udp_bridge]: Original error: parameter
  'remotes.bizzy.connections.wifi.admission_floor_bytes_per_second' has
  invalid type: ... is of type {double}, setting it to {integer} is not allowed.
[WARN]  [udp_bridge]: Callback returned ERROR during the transition: configure
```

Committed as `32768.0`, and the config carries a comment saying why. Anyone
hand-applying this on a field host from the issue text must use the float.

### Verification

- Both edited files `yaml.safe_load` clean; repo yamllint config passes.
- **Parameter proven live, not just spelled right.** Ran the real
  `udp_bridge_node` against each committed file and read the parameter back
  through `ros2 param get` after a successful `configure`:
  `remotes.bizzy.connections.{wifi,vpn,cell}.admission_floor_bytes_per_second`
  → `Double value is: 32768.0` on all three, lifecycle `Transitioning
  successful`. Same readback for `remotes.izzy.connections.{wifi,vpn}` →
  32768.0 (that node's `configure` then failed on `Temporary failure in name
  resolution` for `mystique_ib` — izzy's hosts are not in DNS on the dev
  machine — which is after the parameter read and unrelated to this change).
- Parameter path confirmed against source, not the issue:
  `remotes.<remote>.connections.<connection>.admission_floor_bytes_per_second`
  (`udp_bridge.cpp:543`). This is a declared-parameter tree, so a
  misspelling is silently ignored — hence the live readback rather than a
  visual check.
- Rate-limit headroom re-checked from source: no operator-side connection
  sets `maximum_bytes_per_second`, so all five fall back to
  `Connection::default_rate_limit = 50000` B/s (`connection.h:243`). The
  floor is applied as `min(admission_floor, data_rate_limit)`
  (`connection.cpp:~265`), so 32768 sits ~35 % under the cap and AIMD
  backoff still has range. **No connection has a lower explicit limit**, so
  32768 is safe on all of them.

### Assessed and deliberately NOT changed

- **`bizzyboat_project11/config/operator_no_wifi.yaml`** — needs no change,
  and adding one would be wrong. It is a delta that only shortens
  `connections_list` to `[vpn, cell]`; the connection blocks themselves come
  from `operator.yaml`, so it inherits the new floor automatically.
- **Boat-side configs (`bizzyboat.yaml`, `izzyboat.yaml`)** — out of scope
  per the issue, and the exposure is genuinely different, not merely
  unmeasured. (a) Their connections set explicit caps (bizzy wifi 1500000,
  vpn 1500000, cell 300000 B/s), so the floor is 0.5–2.7 % of the cap rather
  than 16 %, and there is far more backoff range below it. (b) The downlink
  is never quiet — it carries continuous telemetry (heartbeat, mavros, tf,
  costmaps, video), so it does not have the idle-decay exposure that makes
  the operator uplink's floor load-bearing. (c) `updateAdmissionControl`
  cannot mark an idle connection congested at all (`sent_bps > 0` gate), so
  what drives the operator uplink toward the floor is *low-but-nonzero*
  traffic with poor delivery feedback — again not the boat side's regime.
  If a boat-side floor is ever wanted, it needs its own measurement and its
  own issue; raising it there interacts with real congestion control on a
  link that is routinely at cap.
- **`lr30_project11/config/operator.yaml`** — confirmed by reading it: one
  connection (`default`), `topics_list: [command]` only, no helm topic. It
  is also in a separate repo. Left alone; not changed "for consistency".
- **izzy judgement**: its structure matches bizzy closely enough to apply
  the same change — same `/izzy/piloting_mode/manual/helm` advertisement on
  both connections, same absence of a rate limit. Differences: two
  connections rather than three (no cell), and it sets an explicit
  `return_host` where bizzy derives it in the launch file. Neither bears on
  the floor. Izzy's helm rate has *not* been measured; the config comment
  says so, so 32768 there is carried-over sizing, not a measured value.

### Before deploying

- **The bridge reads this at connection setup.** `ros2 param set` at runtime
  will not apply it (same failure mode logged for `maximum_bytes_per_second`
  on 2026-08-20). The operator station's udp_bridge must be **restarted**
  after syncing; a `param get` reading 32768.0 on a running node is not
  evidence it is in effect. Check `effective_rate_limit` / the admission
  counters in `bridge_info` instead, over a window rather than one sample.
- Config is symlink-installed, so no rebuild is needed — but a plain `git
  pull` on the operator host is enough only if that host is not one of the
  ones whose history was rewritten (see the 08-24 note about `reset --hard`).
- This is the stopgap, not the fix. `rolker/unh_marine_autonomy#352`
  (rate-limit `joy_to_helm` to 20 Hz) brings peak helm to ~3.4 kB/s, under
  even the old default floor; it needs on-water verification and lands on
  its own schedule. Expect the floor to become redundant, not wrong, when it
  does.
