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

## Hostname Aliases

| Alias | IP | Path |
|-------|----|------|
| gabby_bb | 192.168.20.5 | WiFi bridge |
| gabby_v | 192.168.21.5 | VPN (NETMAP) |
| salmon_bb | 192.168.13.142 | WiFi bridge |
| salmon_bv | 192.168.22.142 | VPN (NETMAP, BizzyBoat path) |
