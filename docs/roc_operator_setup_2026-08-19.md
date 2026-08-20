# ROC Operator Station Setup — Shoals Survey Prep

Started 2026-08-19. Running log of the operator-side setup for the Shoals
survey, plus the task handoff to the agent working on pandy.

## Context

BizzyBoat will operate at the Shoals; the operator station moves to CCOM's
Telepresence Room ("ROC"), behind the operator RUTX11 router (WAN on the CCOM
network — the same network used for earlier lab testing, so the WireGuard
tunnels to BenCloud are already proven from there). The WiFi bridge is out of
range for this survey, so the only operator↔boat paths are the WireGuard VPN
(`vpn`, Starlink) and cell (`cell`) NETMAP paths.

Stations:

- **pandy** — primary operator station (Linux desktop, 4 monitors, full
  operator stack). New machine, identity set up below.
- **salmon** — warm standby (laptop), keeps its existing identity and
  configs untouched. Only ONE operator udp_bridge runs at a time (the boat
  learns its return path from whichever bridge advertises); failover = stop
  bridge on pandy, start salmon's.
- **Windows machine** — sonar operator, RDP client to
  `mercat.vpn.bizzy.p11.lan` (192.168.21.8). Outbound-only: plain DHCP, no
  static lease or DNS name needed. RDP screen data shares the boat's
  Starlink uplink with telemetry and sits outside the udp_bridge byte
  budgets — use conservative RDP settings (color depth, resolution) and
  watch bridge resend rates when the session is active.

## Done 2026-08-19 — pandy network identity (ccomjhc_project11 `db3103b`, `ec4a2d8`)

Static lease and fleet DNS names for pandy, deployed to both routers and
verified end-to-end (details and lease material in the private
`ccomjhc_project11` repo, `configuration/dnsmasq/`):

| Name | Address |
|------|---------|
| `pandy.op.p11.lan` / `pandy.p11.lan` | 192.168.13.144 |
| `pandy.vpn.bizzy.p11.lan` | 192.168.22.144 |
| `pandy.cell.bizzy.p11.lan` | 192.168.24.144 |
| `pandy.zt.p11.lan` | 10.242.75.122 |

Verified: resolution on both routers, pandy holding the lease, and the
gabby→pandy VPN NETMAP return path (ping, 0% loss, ~78 ms) — the path
udp_bridge return traffic uses.

Also added boat-relative `.vpn`/`.cell` shorthands for operator hosts on the
BizzyBoat router (`salmon.vpn`, `pandy.vpn`, `deadpool.vpn` + `.cell`), for
interactive use from on board. Configs must keep the canonical
`.vpn.bizzy` forms — see `dns_naming.md` rule 8 in the private repo:
operator hosts have one NETMAP address per boat, so the short names are only
unambiguous relative to the router serving them.

## Handoff — ROC config variants (agent on pandy)

Work in `bizzyboat_project11` (field-mode repo — direct commits, agent
identity, atomic; never `--no-verify`). salmon's configs are the working
standby set: **create variants, don't modify them.**

1. **`config/operator_roc.yaml`** — variant of `config/operator.yaml`: drop
   the `wifi` connection entirely; keep `vpn` and `cell` with `host:`
   unchanged (`gabby.vpn.bizzy.p11.lan` / `gabby.cell.bizzy.p11.lan`) and
   `return_host:` changed to `pandy.vpn.bizzy.p11.lan` /
   `pandy.cell.bizzy.p11.lan`. Connection ids must stay `vpn`/`cell`
   exactly — they pair with the boat's `bizzyboat.yaml`, which needs **no
   changes**.
2. **`config/ping_targets_operator_roc.yaml`** — drop the direct/wifi-path
   targets (`gabby_direct`, `router_bizzy_direct`), keep the vpn targets,
   consider adding cell targets (`gabby.cell.bizzy.p11.lan`,
   `router.cell.bizzy.p11.lan`).
3. **`config/bizzyboat_operator_annunciator.yaml`** — ROC variant removing
   WiFi-path indicators (precedent: 2026-04-29 removal of the bencloud
   indicator; see `bizzyboat_project11/docs/operator_annunciator_design.md`).
4. Check `config/network_monitor_operator.yaml` and
   `config/teltonika_monitor_operator.yaml` for wifi-path assumptions; make
   variants only if needed.
5. **Launch selection**: config paths are hard-coded in
   `launch/operator_core_launch.py` and
   `launch/network_monitor_operator_launch.py` — add a launch argument
   (e.g. `site:=roc`) or parallel launch files; pick whichever fits the
   repo's existing style.
6. Verify against source before documenting; test what's testable with the
   boat reachable over VPN (bridge up from pandy, topics flowing, resend
   rates sane). Do not run the bridge while salmon's bridge is running.

Note: ssh to the boat works as `gabby.vpn` only with key auth set up (salmon
has an ssh alias for it; pandy may need `ssh-copy-id`).

## Handoff status (updated 2026-08-20, agent on pandy)

1. **Superseded — done as a station-agnostic change, not an ROC variant**
   (`eaf8976`). `wifi:=false` layers `config/operator_no_wifi.yaml` (shortens
   `connections_list` to `[vpn, cell]`; udp_bridge iterates only the listed
   connections, so the `wifi` block is simply never read and nothing is
   duplicated), and `return_host` is derived from the station's short hostname
   per `dns_naming.md` rule 8, overridable via `return_host_prefix`. Named for
   the condition rather than the site because salmon has operated without wifi
   too. On salmon the derivation reproduces the previous literals exactly.
   Not yet exercised against the boat.
2. **Still open** — `ping_targets_operator.yaml` keeps `gabby_direct` and
   `router_bizzy_direct`, both unreachable from the ROC, and has no cell
   targets. Should follow the same `wifi` argument rather than becoming an
   `_roc` variant.
3. **Effectively already done, for a reason worth recording**: the annunciator's
   indicator list lives *inside the rqt perspective* as an embedded
   `config_yaml`, not in `config/bizzyboat_operator_annunciator.yaml`. Salmon's
   two live instances are already VPN-only — there are no WiFi indicators to
   remove. The repo YAML (with `Op WiFi Bridge`, `Ping Gabby (WiFi)`,
   `UDP WiFi`) is dead config; `docs/logs/2026/2026-05-22_salmon_logs.md:526`
   recorded the suspicion and line 791 has the cleanup on a backlog. The real
   ROC gaps are the stale `Op Starlink` row (no dish at the ROC) and the total
   absence of cell-path indicators.
4. **Still open** — `network_monitor_operator.yaml` points the mikrotik monitor
   at `bizzy.wifi.op.p11.lan` (unreachable from the ROC) and
   `network_monitor_operator_launch.py` hard-codes a Starlink dish at
   192.168.100.1 that the ROC does not have. `teltonika_monitor_operator.yaml`
   is fine — `router.op` resolves and answers.
5. **Done for `operator_core_launch.py`** via the `wifi` argument;
   `network_monitor_operator_launch.py` still hard-codes its config paths.
6. Untested against the boat — the bridge has not been run from pandy.

## Task: wire AIS into the operator stack

Live AIS is arriving on pandy's udp/2125 (verified 2026-08-20: ~1 sentence/s
from `10.242.80.203` over ZeroTier, 10 distinct MMSIs in 20 s, message types
1/3/18/21/24) and is being discarded — nothing is bound to the port.

CAMP will not pick it up as-is: `camp/ais/ais_manager.cpp:36` subscribes to ROS
topics of type `marine_ais_msgs/AISContact`, not UDP. The chain is three nodes
deep:

```
udp/2125 -> nmea_relay -> /ais/raw -> ais_parser -> /ais/messages
         -> ais_contact_tracker -> contacts (AISContact) -> CAMP
```

Gaps to close:

- `marine_ais_tools/launch/ais_parser_with_nmea_relay.launch.py` covers only the
  middle two nodes — it does not start `ais_contact_tracker`, so it stops one hop
  short of the topic CAMP subscribes to.
- Its shipped `config/parameters.yaml` defaults to `input_type: serial`,
  `/dev/ttyACM0`, `input_port: 0` — nothing about UDP or 2125, so parameters must
  be overridden.
- No operator launch file in the workspace includes it, and neither the tmux
  operator scripts nor salmon's crontab reference AIS. The only in-repo note on
  the UDP path, `ccomjhc_project11/documentation/notes/ais.md`, is still in ROS 1
  form.

Also reconcile the sender: `ccomjhc_project11/scripts/ais_sender.py:34-36`
hardcodes its ZeroTier destinations (`snowpetrelz`, `penguinz`, `pandora`) and
lists neither pandy nor salmon, yet pandy receives — so the deployed sender has
drifted from the committed copy.

## Remaining before the survey

- Plumb the `wifi` argument through `network_monitor_operator_launch.py` and the
  ping-target / mikrotik / Starlink configs (handoff items 2, 4, 5).
- Tweak the rqt perspectives on pandy (window placement across four monitors),
  then put them under version control — they hold the only copy of the live
  annunciator config, which has silently diverged from the repo YAML.
- Wire AIS into the operator stack (task above).
- Create `~/data` on pandy: the operator bag recorder writes
  `~/data/logs/operator/<date>/bags/` and rqt_operator_log is configured for
  `/home/field/data/logs/operator`.
- Install `git-bug` (field-side `/start-deployment`) and `python3.12-venv`
  (so `pre-commit` can run — commits from pandy have gone in unhooked so far).
- Dockside/pre-departure rehearsal from the ROC: full bridge load from pandy
  plus a concurrent RDP session to mercat, watching udp_bridge resend rates
  against the vpn/cell budgets.
