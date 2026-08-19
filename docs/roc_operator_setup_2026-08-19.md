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

## Remaining before the survey

- Dockside/pre-departure rehearsal from the ROC: full bridge load from pandy
  plus a concurrent RDP session to mercat, watching udp_bridge resend rates
  against the vpn/cell budgets.
