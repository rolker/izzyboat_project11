# BizzyBoat Network Configuration

Network architecture for BizzyBoat (EchoBoat 240). For the full setup journal,
see the private `ccomjhc_project11` repo (`documentation/bizzyboat_network_setup_2026-03-18.md`).

Sensitive details (MAC addresses, credentials, public IPs, key material) are in
the private repo (`configuration/bizzyboat_network.yaml`).

## Hardware

| Component | Model | Notes |
|-----------|-------|-------|
| Robot computer | Neousys Nuvo 9160GC, Core i7-14700, 32 GB RAM | Hostname: `gabby`, Ubuntu 24.04 Server |
| GNSS | CUAV New C-RTK 2HP | Dual antenna, centimeter position, heading |
| Network switch | Trendnet TI-PG80B | Industrial PoE+ gigabit switch (unmanaged) |
| Router | Teltonika RUTX11 | Industrial cellular router, firmware RUTX_R_00.07.21.2 |
| WiFi bridge (boat) | MikroTik OmniTIK 5 ac (RBOmniTikG-5HacD) | RouterOS 7.22, AP bridge mode |
| WiFi bridge (shore) | MikroTik SXTsq Lite5 (RBSXTsq5nD) | RouterOS 7.22, station-bridge mode |

## Network Topology

```
Shore Side                              Boat Side
──────────                              ─────────
Operator laptop (deadpool)              gabby (robot computer)
  │ 192.168.13.x                          │ 192.168.20.5
  │                                       │
Operator Router (RUTX11)               BizzyBoat Router (RUTX11)
  │ 192.168.13.1                          │ 192.168.20.1
  │                                       │
  ├── WiFi bridge ─────────────────────── ├── WiFi bridge
  │   SXTsq          172.16.20.0/24      │   OmniTIK
  │   172.16.20.2 ←→ 172.16.20.4 ~~~ 172.16.20.3 ←→ 172.16.20.1
  │                                       │
  └── VPN (WireGuard) ── BenCloud ────── └── VPN (WireGuard)
      10.132.146.5        10.132.146.1       10.132.146.6
```

## Subnets

| Subnet | Purpose |
|--------|---------|
| 192.168.20.0/24 | BizzyBoat onboard LAN |
| 192.168.13.0/24 | Operator LAN (shared with IzzyBoat) |
| 172.16.20.0/24 | WiFi bridge link |
| 10.132.146.0/24 | WireGuard VPN tunnel |
| 192.168.21.0/24 | NETMAP: BizzyBoat onboard via VPN |
| 192.168.22.0/24 | NETMAP: operator via VPN (BizzyBoat path) |
| 172.16.0.0/16 | Garmin Marine Network (isolated; mercat only) |

### Garmin Marine Network

The Garmin GCV-20 sidescan module lives on Garmin's own marine network — a
flat 172.16.0.0/16 where devices self-assign IPs (GCV-20 at 172.16.3.0;
mercat's Marine-Network NIC 172.16.55.235) — physically reachable **only from
mercat's second Ethernet port**. It is not routed onto the boat LAN, so the
/16 overlapping the WiFi-bridge subnet (172.16.20.0/24) is harmless.

`garmin_sidescan`'s `tools/garmin_marine_network_proxy.py` runs on mercat and
relays, one-way GCV→ROS except for the driver's own control frames: imagery
multicast (:50220), GCV status (:50050, filtered to the GCV's source),
chartplotter CDP config (:51000, carries the active range under auto-range),
and forwards the driver's TCP control (:50227) to the GCV. The unmodified
driver then runs on gabby pointed at the proxy. Authoritative details: the
proxy tool's docstring and `garmin_sidescan/docs/gcv_protocol.md` in
`marine_tools`.

## Physical Connections

| Device | Port | Connected To |
|--------|------|-------------|
| gabby | `enp7s0` (leftmost) | PoE switch (onboard LAN) |
| Teltonika RUTX11 | WAN | Starlink |
| Teltonika RUTX11 | LAN1 | PoE switch (onboard LAN) |
| Teltonika RUTX11 | LAN2 | OmniTIK 5 ac (WiFi bridge, VLAN 3) |
| PoE switch (TI-PG80B) | Ports 1–2 | Router (via PoE adapter) + gabby (data only) |
| PoE switch (TI-PG80B) | Ports 3–6 | OAK-1 cameras ×4 (802.3af PoE) |
| OmniTIK 5 ac | ether1 | Teltonika LAN2 (direct cable, powered by 24V adapter) |

## Router Configuration (Teltonika RUTX11)

- **LAN IP**: 192.168.20.1/24
- **DHCP pool**: 192.168.20.200–249
- **Static lease**: gabby → 192.168.20.5
- **DNS**: 1.1.1.1 (Cloudflare), 8.8.8.8, 8.8.4.4 (Google)
- **WiFi 2.4 GHz**: AP mode, SSID `BizzyBoat`
- **WiFi 5 GHz**: disabled (reserved for WiFi WAN client)
- **Timezone**: UTC

### VLAN Configuration

| Physical Label | Switch Port | VLAN | Purpose |
|---|---|---|---|
| LAN1 | 2 | 1 | Onboard LAN (br-lan, 192.168.20.0/24) |
| LAN2 | 3 | 3 | WiFi bridge (eth0.3, 172.16.20.0/24) |
| LAN3 | 4 | 1 | Onboard LAN (unused) |
| WAN | 5 | 2 | Internet (Starlink) |

## WireGuard VPN

Hub-and-spoke topology with BenCloud as hub. Migrated from OpenVPN on 2026-03-20.

| Peer | Tunnel IP | NETMAP Range |
|------|-----------|--------------|
| BenCloud (hub) | 10.132.146.1 | — |
| BizzyBoat | 10.132.146.6 | 192.168.21.0/24 |
| Operator station | 10.132.146.5 | 192.168.15.0/24, 192.168.22.0/24 |
| IzzyBoat | 10.132.146.4 | 192.168.14.0/24 |

Key material and endpoint addresses are in the private repo.

### NETMAP Rules

**BizzyBoat router** (Network → Firewall → Custom Rules):
```
iptables -t nat -I PREROUTING -i bcloud -d 192.168.21.0/24 -j NETMAP --to 192.168.20.0/24
iptables -t nat -I POSTROUTING -o bcloud -s 192.168.20.0/24 -j NETMAP --to 192.168.21.0/24
```

**Operator router** (Network → Firewall → Custom Rules):
```
# BizzyBoat
iptables -t nat -I POSTROUTING -s 192.168.13.0/24 -d 192.168.21.0/24 -j NETMAP --to 192.168.22.0/24
iptables -t nat -I PREROUTING -d 192.168.22.0/24 -j NETMAP --to 192.168.13.0/24
```

## WiFi Bridge

- **SSID**: `bizzy_bridge`
- **Security**: WPA2-PSK (password in private repo)
- **Band**: 5 GHz a/n/ac (mixed mode — SXTsq connects at a/n)
- **Protocol**: 802.11 (plain, not nv2/nstreme)

| Device | IP | Role |
|--------|----|------|
| OmniTIK 5 ac | 172.16.20.3 | AP bridge (boat side) |
| SXTsq Lite5 | 172.16.20.4 | Station bridge (shore side) |
| BizzyBoat router | 172.16.20.1 | Boat gateway |
| Operator router | 172.16.20.2 | Shore gateway |

### OmniTIK Firewall

Default RouterOS firewall rules were disabled (2026-03-25). The device is a
bridge on a private subnet behind two routers with their own firewalls; it does
not need its own firewall. See setup journal for the full troubleshooting story.

## Dual-Path Connectivity

Two independent paths between operator and boat:

1. **WiFi bridge** (172.16.20.0/24) — low latency (~1ms), direct link
2. **VPN via BenCloud** (NETMAP) — higher latency (~37ms), works when WiFi is down

Verified 2026-03-25: VPN path operates independently when WiFi bridge is down
(tested during WiFi password change).

### udp_bridge per-connection bandwidth budgets

| Connection | Budget | Notes |
|---|---|---|
| `wifi` | 1.5 MB/s | Full telemetry + cameras |
| `vpn` | 1.2 MB/s | Carries all four OAK ffmpeg streams |
| `cell` | 0.3 MB/s | Lean set, no cameras |

Measured pier calibration (2026-05-18) behind these numbers lives in the
private `ccomjhc_project11` repo. Two conclusions worth repeating here:

- The VPN/Starlink path is **structurally lossy** (~0.4% baseline) — a
  ~30% udp_bridge resend overhead on that path is expected steady-state,
  **not** a fault to chase.
- **WiFi range**: there is no "300 m hard limit" (a retired early figure).
  Degradation with distance is graceful and interference-limited; telemetry
  dropouts at range are tolerated — the boat completes lines autonomously.

### Known-cosmetic log noise

The operator router logs recurring `dnsmasq: no address range available for
DHCP request via eth0.4` — that's the boat OmniTIK left in DHCP-client mode
on the bridge VLAN. Cosmetic; not a bridge fault.

## DNS Naming

Every device has a hierarchical DNS name under **`p11.lan`**, served by
**dnsmasq on each router** (boat and operator). Use the name instead of the IP —
e.g. `ssh field@gabby.p11.lan`, `ping time.bizzy.p11.lan`.

**Authoritative source** (private `ccomjhc_project11` repo):

- Scheme spec: [`docs/dns_naming.md`](https://github.com/CCOMJHC/ccomjhc_project11/blob/jazzy/docs/dns_naming.md)
- BizzyBoat hosts file (served by the boat router): `configuration/dnsmasq/bizzyboat.hosts`

The table below is the BizzyBoat-relevant subset; the spec above is the full,
cross-vehicle source of truth. **Keep this in sync with `bizzyboat.hosts`** — if
they disagree, the hosts file wins.

### Naming convention

`<host>.<scope>.p11.lan`, **shortest unambiguous name wins**:

- **Unique hosts** get a top-level shorthand *and* a vehicle-qualified name:
  `gabby.p11.lan` = `gabby.bizzy.p11.lan`.
- **Ambiguous hosts** (`router`, `kvm`, `oak-*`) always need the vehicle scope:
  `router.bizzy.p11.lan`.
- **Path qualifiers** select how you reach a device:
  - `lan` — onboard LAN, direct (default; usually omitted)
  - `vpn` — via the WireGuard NETMAP path (use when WiFi is down): `gabby.vpn.p11.lan`
  - `wifi` — a WiFi-bridge radio / router bridge interface: `wifi.bizzy.p11.lan`
  - `wg` — a WireGuard tunnel endpoint (router-to-router): `bizzy.wg.p11.lan`

### BizzyBoat names (from `bizzyboat.hosts`)

**Onboard LAN — 192.168.20.0/24 (direct):**

| Host | Primary name | IP |
|------|--------------|----|
| Boat router | `router.bizzy.p11.lan` | 192.168.20.1 |
| gabby (Linux/ROS) | `gabby.p11.lan` | 192.168.20.5 |
| mercat (Windows/QINSy) | `mercat.p11.lan` | 192.168.20.8 |
| OAK cameras ×4 | `oak-1.bizzy.p11.lan` … `oak-4.bizzy.p11.lan` | 192.168.20.9–12 |
| KVM switch | `kvm.bizzy.p11.lan` | 192.168.20.50 |
| Time clock (TM2000B) | `time.bizzy.p11.lan` | 192.168.20.123 |

**VPN NETMAP — 192.168.21.0/24** (same hosts, `vpn` path): `router.vpn.bizzy`
(.1), `gabby.vpn` (.5), `mercat.vpn.bizzy` (.8), `time.vpn.bizzy` (.123), etc.

**WiFi-bridge radios — 172.16.20.0/24:** `wifi.bizzy.p11.lan` (boat OmniTIK, .3),
`bizzy.wifi.op.p11.lan` (shore SXTsq, .4), `router.wifi.bizzy.p11.lan` (boat
router bridge iface, .1).

**Operator hosts:** `salmon.p11.lan` (192.168.13.142), `deadpool.p11.lan`
(192.168.13.143). Reached from the boat over VPN as `salmon.vpn.bizzy.p11.lan`
(192.168.22.142).

> **Legacy note:** earlier `/etc/hosts` underscore aliases (`gabby_bb`, `gabby_v`,
> `salmon_bb`, `salmon_bv`) are **superseded** by this scheme — `gabby_bb` →
> `gabby.bizzy.p11.lan`, `gabby_v` → `gabby.vpn.bizzy.p11.lan`. Remove them where
> they still linger in station `/etc/hosts` files.
