# Operator-side annunciator — design

Status: draft. Captures the rationale + scope so we can stage rollout without
losing context between deployments.

## Why a separate panel

The current `bizzyboat_annunciator.yaml` is 100 % boat-prefixed — every
indicator's `diagnostic_name` resolves under the `Boat` aggregator group
(`mavros:`, `wifi.bizzy`, `starlink.bizzy`, `ping.bizzy`, etc.).

When the boat is off, every indicator on the panel goes red/stale. The
operator can't tell from the annunciator whether the link, the boat, or
salmon itself broke. We need a second, op-prefixed panel that stays green
when the operator station is healthy regardless of the boat.

## What's already wired

`bizzyboat_project11/config/diagnostics.yaml` already declares an
`operator:` analyzer group with sub-analyzers for op-side mikrotik,
teltonika, starlink, and ping. Salmon is publishing the matching
diagnostics today (verified live via `ros2 topic echo /diagnostics`):

- `MikroTik: bizzy.wifi.op: …` — op-side WiFi bridge to boat
- `Starlink: starlink.op: {state, link, comms, alerts, obstruction, thermal}`
- `Ping: ping.op: {gabby_direct, gabby_vpn, router_bizzy_direct, router_bizzy_vpn,
  bencloud, dns_cloudflare, dns_google}`

Aggregator-side it's all there. The display side is the only thing missing.

Note: `Teltonika: router.op` is configured (the op-side teltonika monitor node
exists in `network_monitor_operator_launch.py`) but is not on the wire in the
2026-04-29 deployment. Either the op router doesn't have a Teltonika to query,
or the monitor isn't actually starting. Out of scope for the preliminary panel —
add when we know it produces.

## Tier 1 — preliminary panel (config-only)

Implemented as `bizzyboat_project11/config/bizzyboat_operator_annunciator.yaml`.
Pulls only from already-published keys, so dropping it in works the moment the
package's `config/` install runs.

| Indicator | Source key (post-prefix-strip) |
|---|---|
| Op WiFi Bridge | `MikroTik: bizzy.wifi.op: wireless/` |
| Op Starlink | `Starlink: starlink.op` |
| Ping Gabby (WiFi) | `Ping: ping.op: gabby_direct` |
| Ping Gabby (VPN) | `Ping: ping.op: gabby_vpn` |
| Ping Boat Router (WiFi) | `Ping: ping.op: router_bizzy_direct` |
| Ping Boat Router (VPN) | `Ping: ping.op: router_bizzy_vpn` |
| Internet (DNS) | `Ping: ping.op: dns_cloudflare` |
| UDP WiFi | `udp_bridge operator: bizzy: wifi` |
| UDP VPN | `udp_bridge operator: bizzy: vpn` |

The two UDP indicators currently live on the boat panel; once we add the
op panel, they belong here (they're op-bridge state, not boat state). Move
them in a follow-up commit so we don't break the boat-panel layout mid-deployment.

### What we deliberately don't include: `Ping: ping.op: bencloud`

The `bencloud` ping target in `ping_targets_operator.yaml` resolves to
`bencloud.wg.p11.lan` (the raw WireGuard mesh endpoint, `10.132.146.1`).
Salmon has no WG client of its own — its WG-bound traffic is mediated by
the op router, which NETMAPs salmon-LAN traffic onto specific WG-tunneled
subnets. Direct addressing of the `10.132.146.0/24` mesh is not exposed
to salmon-side hosts by design. So the bencloud-WG ping always reads as
"no link" from salmon, regardless of whether the WG transport is
actually healthy.

Don't add it to the annunciator until either (a) the ping target moves to
a NETMAP'd address that does land at bencloud, or (b) salmon is given a
direct WG client. Until then, "is the VPN/WG transport up?" is best
inferred indirectly from `Ping Boat Router (VPN)` (`router_bizzy_vpn` —
192.168.21.1, NETMAP'd through WG) — a successful round-trip there proves
the tunnel carries data.

## Tier 2 — small new monitors (deferred)

Useful but each needs a small new diagnostic publisher:

| Indicator | Producer needed | Why it matters |
|---|---|---|
| Joystick | watchdog on `/joy` rate (or device presence) | dead joystick = no manual override |
| Bag recorder | introspect `/events/write_split` from rosbag2 | "you weren't recording" surprise |
| Disk free | small periodic publisher reading `~/data` | recorder fills disk silently |
| chrony lock | `chronyc tracking` polled to `/diagnostics` | timestamp drift wrecks bag debrief |
| zenohd | pidfile / health probe | router crash silently breaks discovery |

These belong in a `salmon_monitor` package (or an op-side launch file with
several lightweight nodes). Not in scope for the preliminary panel.

## Architecture

- One annunciator config per panel — no plugin code change. The annunciator
  widget already takes any YAML path.
- Two annunciator widgets in the same `bizzyboat-diagnostics` rqt perspective:
  boat panel on top (where eyes default), operator panel beneath. Glance
  pattern: red on top → boat issue; red on bottom → operator/link issue;
  red on both → look first at "Internet (bencloud)" to see whether we still
  have any path off the dock.
- Aggregator config is already correct for Tier 1; no edits needed.

## What I deliberately skipped

- Don't replicate every boat indicator with an op-side wrapper. The boat
  panel handles those.
- Don't surface every salmon ROS node's heartbeat. Noise. Operator only
  cares about the few whose silent death would break the deployment.
- Don't re-engineer the annunciator widget itself for sections/dividers
  yet. Two stacked widgets is cheaper and clearer than designing a
  collapsible-section layout.

## Open questions

1. **Recorder health**: produced by a separate watchdog node, or
   introspected from inside `bag_recorder_operator_launch.py` (cleaner,
   but couples the launch to its own monitoring)?
2. **Joystick liveness signal**: device-presence (works in standby) or
   `/joy` message rate (only works while user is touching the stick)? A
   button-event count over the last 5 s splits the difference.
3. **STAT vs banner for "is recording"**: today the annunciator only does
   indicator cells. A "currently recording" banner might be a better fit —
   but a yellow STAT cell when the recorder is silent is the lazy answer
   that costs nothing.

## How to try the preliminary panel

After `colcon build --packages-select bizzyboat_project11`, in any rqt
window with the annunciator plugin loaded, point the config at:

```
$(ros2 pkg prefix bizzyboat_project11)/share/bizzyboat_project11/config/bizzyboat_operator_annunciator.yaml
```

Or before rebuild, the source-tree path:
`bizzyboat_project11/config/bizzyboat_operator_annunciator.yaml`.

The current `bizzyboat-diagnostics` perspective doesn't include this panel
yet — load it as a second annunciator widget alongside the boat one, save
the perspective if you want it to persist.
