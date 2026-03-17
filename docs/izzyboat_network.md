# IzzyBoat Network Setup

Reference documentation for IzzyBoat (EchoBoat 160) network configuration.
Intended as the basis for designing BizzyBoat (EchoBoat 240) networking.

## Device Inventory

| Device | Hostname | Role | Notes |
|--------|----------|------|-------|
| Development laptop | deadpool | Development / backup operator | Ubuntu 24.04 |
| Operator laptop | salmon | Primary operator station | |
| Robot computer | mystique | Onboard compute (IzzyBoat) | Borrowed from Ben (CWorker 4); originally `dora` |
| ArduPilot FCU | — | Autopilot | Serial `/dev/ttyUSB0:57600` |
| Norbit Winghead sonar | winghead | Multibeam sonar (loaner/eval unit, temporary) | `192.168.53.34` |
| Applanix POS MV | posmv_izzyboat | INS/GNSS for sonar nav (currently removed) | `192.168.12.4` |
| OAK-D camera | oak-camera | Depth camera | `192.168.12.9` |
| Imagenex DeltaT sonar | deltat | Multibeam sonar | `192.168.0.2` (hardcoded, not configurable) |
| IzzyBoat router | router_izzyboat | Onboard router (Teltonika RUTX11, FW `RUTX_R_00.07.15.1`) | Web UI user: `admin`, SSH user: `root` |
| AML sound speed sensor | — | Sound speed profiler (winch-deployed, WiFi AP) | SSID `AML_A30894`, connects via router 2.4 GHz radio |
| Starlink Mini | — | Boat internet (field deployments) | Connected to WAN port |
| Operator router | router_izzyboat_operator | Shore-side router (Teltonika RUTX11, FW `RUTX_R_00.07.16.1`) | Web UI user: `admin`, SSH user: `root` |
| Onboard Windows PC | blaze | Vendor software for sonars/sensors; optional flight controller monitoring | `192.168.12.8`; RDP available but unreliable (connection timeouts) |

## Network Subnets

| Subnet | Purpose | Notes |
|--------|---------|-------|
| `192.168.12.0/24` | IzzyBoat onboard network | Robot-side, WiFi-reachable from shore |
| `192.168.13.0/24` | Operator LAN | Shore-side wired network |
| `192.168.14.0/24` | NETMAP of onboard network over VPN | Not a physical subnet; maps to `192.168.12.0/24` |
| `192.168.15.0/24` | NETMAP of operator network over VPN | Not a physical subnet; maps to `192.168.13.0/24` |
| `172.16.12.0/24` | Internal WiFi link | Router-to-router backhaul |
| `192.168.53.0/??` | Norbit sonar (factory default); also used for past UDel collaboration | Coincidental overlap, not by design |
| `192.168.0.0/??` | DeltaT sonar subnet | DeltaT at `.2` |

## Host Addresses (from shared hosts file)

IP addresses are managed in `ccomjhc_project11/configuration/hosts.txt` and
distributed to machines via `update_hosts.py`.

### IzzyBoat Onboard Network (`192.168.12.0/24`)

| Address | Hostname | Device |
|---------|----------|--------|
| `192.168.12.1` | `router_izzyboat` | Onboard router (WiFi interface) |
| `192.168.12.4` | `posmv_izzyboat` | POS MV INS/GNSS |
| `192.168.12.5` | `dora` | Original robot computer |
| `192.168.12.8` | `blaze` | Onboard Windows PC |
| `192.168.12.9` | `oak-camera` / `stereo-camera` | OAK-D depth camera (DHCP lease name: `stereo-camera`) |
| `192.168.12.10` | `parrot` | Former experiment device (no longer on boat) |
| `192.168.12.15` | `mystique` | Mystique robot computer (DHCP static lease) |
| `192.168.12.15` | `mystique_ib` | Mystique robot computer (alias to avoid disrupting Ben's hosts entry for `mystique`) |

### Operator LAN (`192.168.13.0/24`)

| Address | Hostname | Device |
|---------|----------|--------|
| `192.168.13.1` | `router_izzyboat_operator` | Operator router |
| `192.168.13.142` | `salmon_ib` | Operator laptop (IzzyBoat alias) |
| `192.168.13.143` | `deadpool` | Development laptop |

### VPN Network (`192.168.14.0/24`)

| Address | Hostname | Device |
|---------|----------|--------|
| `192.168.14.1` | `router_izzyboat_v` | Onboard router (VPN) |
| `192.168.14.4` | `posmv_izzyboat_v` | POS MV (VPN-routed) |
| `192.168.14.5` | `dora_v` | Original robot computer (VPN) |
| `192.168.14.8` | `blaze_v` | Onboard Windows PC (VPN) |

### VPN Network — Operator (`192.168.15.0/24`)

| Address | Hostname | Device |
|---------|----------|--------|
| `192.168.15.1` | `router_izzyboat_operator` | Operator router (VPN) |
| `192.168.15.142` | `salmon_v` | Operator laptop (VPN alias) |

### Internal WiFi Link (`172.16.12.0/24`)

| Address | Hostname | Device |
|---------|----------|--------|
| `172.16.12.1` | `router_izzyboat_iw` | Onboard router (internal WiFi) |
| `172.16.12.2` | `router_izzyboat_operator_iw` | Operator router (internal WiFi) |
| `172.16.12.3` | `wifi_izzyboat_iw` | WiFi radio — boat side |
| `172.16.12.4` | `wifi_izzyboat_operator_iw` | WiFi radio — operator side |

## Host Addresses — Detail

### deadpool (development laptop)

| Interface | Address | Network |
|-----------|---------|---------|
| `enp61s0` | `192.168.13.143/24` | Operator LAN (DHCP/static lease) |

### salmon (operator laptop)

Ubuntu 24.04, user `field`, timezone UTC. NTP via chrony; syncs to
`time.unh.edu` (manually configured in `/etc/chrony/sources.d/unh.sources`)
plus Ubuntu pool servers when internet is available. Runs the operator side of the project11 framework
(`operator_core_launch.py` with operator-side UDP bridge). Also hosts a GitLab
instance for development when internet is unavailable. Has a local `~/project11`
workspace (may be outdated).

| Interface | Address | Network |
|-----------|---------|---------|
| `enp3s0` | `192.168.13.142/24` | Operator LAN (DHCP/static lease) |
| `wlp4s0` | down | WiFi (not in use) |
| `ztrfynkltp` | `10.242.32.155/16` | ZeroTier (`salmonz` in hosts) |
| `ztbpakpbd3` | `10.245.32.155/16` | ZeroTier (`salmondz` in hosts) |

### mystique (robot computer)

Ubuntu 24.04.2 LTS, kernel 6.8.0-71-generic, user `field`, timezone UTC.
Mystique is Ben's spare autonomy computer, borrowed for IzzyBoat. Its primary
hostname (`mystique`) resolves to `192.168.10.112` on Ben's network. To avoid
disrupting Ben's hosts file, `mystique_ib` was added as a separate alias
pointing to its IzzyBoat address.

NTP via chrony with default Ubuntu pool (`ntp.ubuntu.com`) — no custom sources
configured. Clock does not sync when boat lacks internet.

**Autostart** (`@reboot` crontab): `start_tmux_virtual_framebuffer.bash` sets up
Xvfb (virtual framebuffer at `:0`, 1920x1080), fluxbox, and x11vnc (no password)
for remote GUI access, then calls `start_tmux_project11.bash` to launch the
ROS 2 stack with `DISPLAY=:0 ros2 launch -g`.

**USB**: FTDI USB-to-serial bridge → `/dev/ttyUSB0` (Cube Orange flight controller).

**Workspace**: `~/project11/jazzy_ws/` with 24 packages. Legacy `~/project11/noetic_ws/`
also present.

| Interface | Address | Network |
|-----------|---------|---------|
| `enp89s0` | `192.168.12.15/24` (DHCP) | Onboard LAN (MAC `54:b2:03:fd:7a:0a`) |
| `wlp0s20f3` | — (down) | WiFi (unused) |

Default gateway: `192.168.12.1` (boat router)

## UDP Bridge Configuration

The UDP bridge handles ROS 2 topic transport between robot and operator over
WiFi and VPN links.

### Robot Side (`izzyboat.yaml`)

- **Bridge name**: `izzy`
- **Listen port**: `4200`
- **Max packet size**: 1000 bytes
- **Remote**: `operator`
  - **WiFi**: max 1.5 MB/s
  - **VPN**: max 1.0 MB/s

### Operator Side (`operator.yaml`)

- **Bridge name**: `operator`
- **Remote**: `izzy`
  - **WiFi**: host `mystique_ib`, port `4200`, return host `salmon_ib`, return port `4200`
  - **VPN**: host `mystique_v`, port `4200`, return host `salmon_v`, return port `4200`

### Hostname Aliases for UDP Bridge

| Alias | Resolves to | Subnet | Purpose |
|-------|-------------|--------|---------|
| `mystique_ib` | `192.168.12.15` | `192.168.12.0/24` | Robot — onboard WiFi network |
| `salmon_ib` | `192.168.13.142` | `192.168.13.0/24` | Operator — operator LAN |
| `mystique_v` | `192.168.14.15` | `192.168.14.0/24` | Robot — VPN (NETMAP of `.12.15`) |
| `salmon_v` | `192.168.15.142` | `192.168.15.0/24` | Operator — VPN |

## ROS 2 Networking

- **Discovery**: `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`
- **Robot namespace**: `izzy`
- **Frame prefix**: `izzy/`
- **Operator namespace**: `operator`

## NTRIP RTK Corrections

- **Host**: `macorsrtk.massdot.state.ma.us`
- **Port**: `31000`
- **Mountpoint**: `RTCM3_MASA`
- **Route**: RTCM → `mavros/gps_rtk/send_rtcm`

## Operator Router (Teltonika RUTX11) Port Assignment

| Physical Port | VLAN | Interface | Subnet | Purpose |
|---------------|------|-----------|--------|---------|
| LAN port 2 | VLAN 1 | `br-lan` (eth0) | `192.168.13.0/24` | Operator LAN |
| LAN port 3 | VLAN 3 | `br-wifi_bridge` (eth0.3) | `172.16.12.0/24` | WiFi bridge to IzzyBoat |
| LAN port 4 | VLAN 4 | `eth0.4` | `192.168.50.0/24` | Mobile lab network (johnny5 PTZ camera, AIS Pi); may be repurposed for BizzyBoat WiFi link |
| WAN port 5 | VLAN 2 | `eth1` | DHCP | Internet (often Starlink in the field) |

### Operator Router Routing Table

| Destination | Gateway | Interface | Purpose |
|-------------|---------|-----------|---------|
| `default` | `192.168.200.1` | `wlan1-2` (WiFi uplink) | Internet via CCOMGuest |
| `172.16.12.0/24` | direct | `br-wifi_bridge` | WiFi backhaul link |
| `192.168.12.0/24` | `172.16.12.1` | `br-wifi_bridge` | Boat onboard network — WiFi path |
| `192.168.13.0/24` | direct | `br-lan` | Operator LAN |
| `192.168.14.0/24` | `10.132.146.4` | `tun_c_1` (OpenVPN) | Boat onboard network — VPN path |
| `192.168.50.0/24` | direct | `eth0.4` | Mobile lab |
| `192.168.53.0/24` | `172.16.12.1` | `br-wifi_bridge` | Norbit sonar subnet — WiFi path |
| `10.132.146.0/24` | direct | `tun_c_1` | BenCloud VPN subnet |
| `10.12.2.0/24` | `10.132.146.1` | `tun_c_1` | Ben internal via VPN |
| `10.13.2.0/24` | `10.132.146.1` | `tun_c_1` | Ben internal via VPN |

### Operator Router Additional Interfaces

- **Onboard WiFi**:
  - **Radio 0 (2.4 GHz, 802.11g)**: AP mode, SSID `izzyboat_operator`, bridged
    to operator LAN — wireless devices join the operator network here
  - **Radio 1 (5 GHz, 802.11ac VHT80)**: STA (client) mode, connects to
    `CCOMGuest` (lab WiFi) for internet uplink (`ifWan1`). The 5 GHz AP
    (`izzyboat_operator`) exists but is disabled since the radio is used as a
    client
- **Internet sharing**: the router shares its internet connection (WAN or WiFi
  uplink) with all devices on the operator LAN. This avoids routing conflicts
  on client machines that would otherwise have dual default gateways (one for
  internet, one for the operator network)
- **Cellular modems** (mob1s1a1, mob1s2a1): both disabled
- **WireGuard** (test): disabled, residual from testing
- **ZeroTier** on LAN bridge: residual from VPN-between-routers testing

### Operator Router Internet Failover (mwan3)

Health checks ping `1.1.1.1` and `8.8.8.8`; 3 failures to mark down, 3 to
mark up.

| Priority | Interface | Enabled | Path |
|----------|-----------|---------|------|
| 1 | `wan` | yes | Wired WAN (Starlink, etc.) |
| 2 | `ifWan1` | yes | WiFi uplink (onboard WiFi as client) |
| 3 | `mob1s1a1` | no | Cellular SIM 1 |
| 4 | `mob1s2a1` | no | Cellular SIM 2 |
| 5 | `wifi_bridge` | no | WiFi bridge to boat |
| 6 | `mobile_lab` | no | Mobile lab port |

**Note:** mwan3 failover has not been reliable in practice; connections are
often manually enabled/disabled instead.

### Operator Router DHCP

- **Pool**: `192.168.13.100` – `192.168.13.249` (12h leases)

| MAC | Hostname | IP | Notes |
|-----|----------|----|-------|
| _salmon_ | `salmon` | `192.168.13.142` | Operator laptop |
| _deadpool_ | `deadpool` | `192.168.13.143` | Development laptop |
| _johnny5_ | `johnny5` | `192.168.13.200` | PTZ camera (mobile lab) |

### Operator Router — Items to Revisit

- **LAN zone masquerade**: `masq='1'` is set on the `lan` zone, which includes
  the WiFi bridge. This may cause traffic to the boat to appear as coming from
  the router (`192.168.13.1`) instead of the actual source. The original reason
  is unclear — may have solved a routing issue during initial setup. Should test
  whether removing it breaks anything.
- **No port forwarding**: no redirects configured.
- **DNS**: default dnsmasq, forwarding upstream. No custom entries.

## Boat Router (Teltonika RUTX11) Port Assignment

| Physical Port | VLAN | Interface | Subnet | Purpose |
|---------------|------|-----------|--------|---------|
| LAN port 2 | VLAN 1 | `br-lan` (eth0) | `192.168.12.0/24` | Onboard LAN |
| LAN port 3 | VLAN 3 | `br-wifi_bridge` (eth0.3) | `172.16.12.0/24` | WiFi bridge to operator |
| LAN port 4 | VLAN 4 | `eth0.4` | — | _unused_ |
| WAN port 5 | VLAN 2 | `eth1` | DHCP | Internet (Starlink Mini in field) |

### Boat Router Routing Table

| Destination | Gateway | Interface | Purpose |
|-------------|---------|-----------|---------|
| `default` | `192.168.200.1` | `wlan1-2` (WiFi) | Internet (lab only; Starlink/cellular in field) |
| `172.16.12.0/24` | direct | `br-wifi_bridge` | WiFi backhaul link |
| `192.168.12.0/24` | direct | `br-lan` | Onboard LAN |
| `192.168.13.0/24` | `172.16.12.2` | `br-wifi_bridge` | Operator network via WiFi bridge |

**Note:** VPN routes are not visible in the lab — the OpenVPN tunnel is down.
When active, VPN routes are pushed dynamically from BenCloud.

### Boat Router Additional Interfaces

- **Onboard WiFi**:
  - **Radio 0 (2.4 GHz, 802.11g)**: AP mode SSID `izzyboat` (disabled); STA
    (client) mode for AML sound speed sensor (SSID `AML_A30894`, disabled when
    not in use). The AML sensor acts as a WiFi AP; the router connects as a client
  - **Radio 1 (5 GHz, 802.11ac VHT80, ch 36)**: AP mode SSID `izzyboat`
    (disabled); STA (client) mode connects to `CCOMGuest` for internet (lab only,
    `ifWan1`)
- **Cellular**: SIM 1 with Verizon (`VZWINTERNET` APN, metric 3); SIM 2 disabled.
  No signal indoors in the lab
- **ZeroTier** on LAN bridge: residual from testing
- **Disabled interfaces**:
  - `ifLan1` (`lan53`): `192.168.53.1/24` — was for Norbit Winghead sonar subnet
  - `lan1` (`aml_lan`): `172.18.127.1/24` — AML sensor alternate subnet

### Boat Router Firewall

- **lan zone**: ACCEPT all, `masq='1'`, networks: `wifi_bridge lan ifLan1 lan1`
  (same masquerade concern as operator router)
- **wan zone**: REJECT in/fwd, `masq='1'`, networks: `wan wan6 mob1s2a1 mob1s1a1 ifWan1`
- **openvpn zone**: ACCEPT all, `masq='1'`, device `tun_+ tap_+`
- **zerotier zone**: ACCEPT all, `masq='1'` (residual)
- **relayd zone**: input/fwd REJECT, no masq, network `ifWan3` (AML) — relays
  between AML sensor WiFi and onboard LAN
- Forwarding: lan ↔ wan, lan ↔ zerotier, lan ↔ openvpn, lan ↔ relayd
- OpenVPN traffic (port 1194) allowed from WAN
- SSH/HTTP/HTTPS on WAN: disabled

### Boat Router NETMAP Rules (`/etc/firewall.user`)

```
# Outbound: boat LAN → operator VPN subnet, rewrite source to .14.x
iptables -t nat -I POSTROUTING -s 192.168.12.0/24 -d 192.168.15.0/24 -j NETMAP --to 192.168.14.0/24

# Inbound: traffic to .14.x → rewrite dest to boat LAN
iptables -t nat -I PREROUTING -d 192.168.14.0/24 -j NETMAP --to 192.168.12.0/24
```

### Boat Router OpenVPN

- **Instance**: `bencloud` (enabled)
- **Device**: `tun_c_1` (TUN client)
- **Server**: `18.213.242.76:1194` (BenCloud), UDP
- **Cipher**: AES-256-CBC
- **Client CN**: `izzyboat`
- **Config file**: `/etc/vuci-uploads/cbid.openvpn.inst1.configizzyboat.ovpn`

### Boat Router DHCP

- **Pool**: `192.168.12.200` – `192.168.12.249` (start 200, limit 50, 12h leases)
- **DHCP disabled on**: `wifi_bridge`, `ifLan1` (Norbit), `lan1` (AML)

| MAC | Hostname | IP | Notes |
|-----|----------|----|-------|
| `44:a9:2c:33:bf:0a` | `stereo-camera` | `192.168.12.9` | OAK-D camera |
| `00:E0:33:08:E4:89` | `dora` | `192.168.12.5` | Original robot computer |
| `20:7B:D2:A1:3F:5C` | `blaze` | `192.168.12.8` | Onboard Windows PC |
| `B0:41:6F:0A:8D:F6` | `parrot` | `192.168.12.10` | Former experiment device |
| `54:b2:03:fd:7a:0a` | `mystique` | `192.168.12.15` | Current robot computer |

### Boat Router Internet Failover (mwan3)

| Priority | Interface | Enabled | Path |
|----------|-----------|---------|------|
| 1 | `ifWan1` (wifi_internet_5g) | no | WiFi internet (lab only) |
| 2 | `wan` | yes | Wired WAN (Starlink Mini in field) |
| 3 | `mob1s1a1` | yes | Cellular SIM 1 (Verizon) |
| 4 | `mob1s2a1` | no | Cellular SIM 2 |
| 5 | `wifi_bridge` | no | WiFi bridge to operator |
| 6 | `ifWan3` (aml) | no | AML sensor WiFi |

**Note:** Starlink/cellular failover has been problematic at times; connections
are often manually enabled/disabled.

### Boat Router GPS

The RUTX11 has a built-in GNSS receiver (GPS, Galileo, GLONASS, BeiDou).

- **gpsd**: enabled
- **NMEA forwarding**: enabled, target `192.168.1.5:8500` (UDP) — stale config
  from when dora was at `192.168.1.5` on a previous subnet layout. If mystique
  keeps the dora name and moves to `.5`, this target address will need updating
  to `192.168.12.5`
- **Forwarded sentences**: GPGSV, GPGGA, GPVTG, GPRMC at 1-second intervals
- **GPS as NTP source**: tested but not reliable enough for the router to serve
  as a local NTP server

### Boat Router NTP

- NTP client: **disabled**
- NTP server: **disabled**
- Timezone: UTC

### Boat Router — Items to Revisit

- **LAN zone masquerade**: same `masq='1'` concern as operator router
- **NMEA forwarding target**: update to correct subnet/address when robot
  computer assignment is finalized
- **NTP**: router has no time sync configured; consider enabling NTP client
  at minimum
- **Starlink/cellular failover reliability**: investigate and improve

## WiFi Configuration

The boat and shore each have a WiFi radio forming a dedicated point-to-point
link on the `172.16.12.0/24` subnet. The operator router bridges this into the
operator LAN (`192.168.13.0/24`). The boat-side router bridges it into the
onboard network (`192.168.12.0/24`).

### WiFi Radios (MikroTik)

The operator-side radio is a MikroTik SXTsq Lite5 (RBSXTsq5nD) and the
boat-side radio is a MikroTik OmniTIK 5 ac (RBOmniTikG-5HacD). Both are
5 GHz, running RouterOS.

- **SSID**: `EchoBoat`
- **Frequency**: 5745 MHz (channel 149)
- **Band**: 5 GHz a/n, 20 MHz channel width
- **Security**: WPA-PSK, AES-CCM
- **Protocol**: nv2-nstreme-802.11 (operator side) / 802.11 (boat side)

**Operator side** (`wifi_izzyboat_operator_iw`, `172.16.12.4`):
- RouterOS v7.4.1, web UI user: `admin`
- Mode: station-bridge (client)
- `ether1`: `172.16.12.4/24` — connected to operator router port 3 (VLAN 3)

**Boat side** (`wifi_izzyboat_iw` / `EB160`, `172.16.12.3`):
- MikroTik OmniTIK 5 ac (RBOmniTikG-5HacD), RouterOS 6.49.10
- Mode: AP bridge
- `ether1`: connected to boat-side router (active bridge port)
- `ether2`: management IP `172.16.12.3/24` (not bridged)
- `ether3-5`: bridged but inactive
- `wlan1`: wireless AP, bridged with `ether1`
- Web UI / SSH user: `admin`

**Note:** Operator side uses `nv2-nstreme-802.11` protocol while boat side
uses plain `802.11`. The link likely falls back to standard 802.11. RouterOS
versions also differ (6.49.10 vs 7.4.1) — consider aligning for BizzyBoat.

## VPN Configuration

A VPN (BenCloud OpenVPN, see below) provides an alternate data path as fallback
when WiFi is out of range.

The `192.168.14.0/24` and `192.168.15.0/24` subnets are **not physical
networks** — they are NETMAP NAT translations that allow the same host
numbering to work over both WiFi and VPN paths:

- `192.168.14.0/24` — onboard network as seen over VPN (maps to `192.168.12.0/24`)
- `192.168.15.0/24` — operator network as seen over VPN (maps to `192.168.13.0/24`)

### Operator Router NETMAP Rules (`/etc/firewall.user`)

```
# Outbound: operator LAN → boat VPN subnet, rewrite source to .15.x
iptables -t nat -I POSTROUTING -s 192.168.13.0/24 -d 192.168.14.0/24 -j NETMAP --to 192.168.15.0/24

# Inbound: traffic to .15.x → rewrite dest to operator LAN
iptables -t nat -I PREROUTING -d 192.168.15.0/24 -j NETMAP --to 192.168.13.0/24
```

The purpose of this scheme is **path selection by destination address**: to
reach a device on the boat via WiFi, use its `192.168.12.x` address; to reach
it via VPN, use its `192.168.14.x` address. The NETMAP rules translate
addresses at each end so the actual devices don't need multiple IPs or
routing awareness. The UDP bridge uses this directly — its `wifi` and `vpn`
connection entries point to the same host via different address families.

This NETMAP approach was developed by Val Schmidt at UNH CCOM.

_TODO: find and reference Val Schmidt's documentation/writeup on the NETMAP approach_

## BenCloud OpenVPN

IzzyBoat uses BenCloud, an OpenVPN server hosted on AWS (`bencloudap` at
`18.213.242.76`), originally set up for Ben (CWorker 4). IzzyBoat was added to
the same VPN so the boats can communicate for potential multi-vehicle operations.
This is the VPN behind the `_v` hostname aliases.

**Operator router OpenVPN client config:**
- **Server**: `18.213.242.76:1194` (`bencloudap` — AWS public IP), UDP
- **Cipher**: AES-256-CBC, SHA256 auth
- **Device**: `tun_c_1` (TUN mode)
- **Client CN**: `operatorizzyboat`
- **Routes**: pushed from server (no client-side route directives)
- **Alternate access**: BenCloud is also reachable via ZeroTier

| Address | Hostname | Role |
|---------|----------|------|
| `10.132.146.1` | `bencloud_bc` | VPN server |
| `10.132.146.2` | `router_ben_bc` | Ben's router |
| `10.132.146.3` | `router_ben_operator_bc` | Ben's operator router |
| `10.132.146.4` | `router_izzyboat_bc` | IzzyBoat's router |
| `10.132.146.5` | `router_izzyboat_operator_bc` | IzzyBoat's operator router |

**Server config** (`/etc/openvpn/bencloud.conf`):
- Proto UDP, TUN mode, topology subnet
- Server IP: `10.132.146.1/24`
- DHCP pool: `10.132.146.100` – `10.132.146.200`
- `client-to-client` enabled (clients can reach each other)
- Pushed routes: `10.12.2.0/24`, `10.13.2.0/24` (Ben internal networks)
- `keepalive 10 120`, `link-mtu 1400`

**Per-client configs** (`/etc/openvpn/ccd/`):

| Client CN | Static IP | iroute (announces) | Pushed route (learns) |
|-----------|-----------|--------------------|-----------------------|
| `ben` | `10.132.146.2` | `192.168.10.0/24` | `10.11.3.0/24 via .3` |
| `operatorben` | `10.132.146.3` | `192.168.50.0/24`, `172.18.3.0/24` | `10.10.3.0/24 via .2` |
| `izzyboat` | `10.132.146.4` | `192.168.14.0/24` | `192.168.15.0/24 via .5` |
| `operatorizzyboat` | `10.132.146.5` | `192.168.15.0/24` | `192.168.14.0/24 via .4` |

**NETMAP VPN path (full loop)**:
1. Operator sends to `192.168.14.x` → operator NETMAP rewrites source to `.15.x`
   → VPN carries to boat router → boat NETMAP rewrites dest `.14.x` → `.12.x`
   → arrives at device on onboard LAN
2. Reply: device sends to `.15.x` → boat NETMAP rewrites source to `.14.x`
   → VPN carries to operator router → operator NETMAP rewrites dest `.15.x` → `.13.x`
   → arrives at device on operator LAN

## Ben (CWorker 4) Network Summary

Included for reference to avoid conflicts if Ben is deployed alongside the
EchoBoats. Ben and IzzyBoat use separate operator networks and separate physical
infrastructure.

| Subnet | Suffix | Purpose |
|--------|--------|---------|
| `192.168.10.0/24` | (base) | Ben internal/onboard network |
| `192.168.11.0/24` | (base) | Ben operator network (separate from IzzyBoat's `192.168.13.0/24`) |
| `10.10.1.0/24` | `m` | Kongsberg MBR (long-range line-of-sight radio) |
| `10.10.2.0/24` | `aw` | _TODO: confirm meaning_ |
| `10.10.3.0/24` | `v` | VPN |
| `10.10.4.0/24` | `w` | WiFi |
| `10.11.1-4.0/24` | operator variants | Ben operator-side suffixed networks |

## Considerations for BizzyBoat

When designing BizzyBoat's network, the following must not conflict with IzzyBoat:

- **Namespace**: needs a unique ROS namespace (e.g., `bizzy`)
- **UDP bridge port**: needs a different port than `4200`
- **Subnets**: needs its own onboard subnet (not `192.168.12.0/24`); avoid `192.168.0.0/24` and `192.168.1.0/24` (Starlink conflict; `192.168.0.0/24` is also DeltaT's hardcoded subnet)
- **Hostnames**: needs distinct host entries and `_ib`-style aliases
- **NTRIP**: can likely share the same NTRIP caster but needs its own credentials
- **WiFi**: separate point-to-point link; operator router port 4 (currently mobile lab) is a candidate
- **Operator station**: shared with IzzyBoat (same salmon laptop, same operator router)
- **VPN**: needs its own BenCloud client cert and CCD entry with unique NETMAP subnets
- **OpenVPN cipher**: AES-256-CBC is deprecated; consider AES-256-GCM for new configs

## Firmware Versions and Upgrade Status

_Researched 2026-03-17._

### Teltonika RUTX11

| Role | Current | Latest Available | Gap |
|------|---------|-----------------|-----|
| Operator router | `RUTX_R_00.07.16.1` | `RUTX_R_00.07.21.1` | 5 minor versions |
| Boat router | `RUTX_R_00.07.15.1` | `RUTX_R_00.07.21.1` | 6 minor versions |

No critical CVEs for versions 7.15+. Upgrade recommended for accumulated bugfixes,
WebUI improvements, and security hardening. Upgrade via WebUI (System > Firmware);
back up configuration first. Direct upgrades across multiple minor versions are
supported.

### MikroTik RouterOS

| Device | Role | Current | Latest Long-term | Latest Stable |
|--------|------|---------|-----------------|---------------|
| SXTsq Lite5 | Operator WiFi | **7.4.1** | **7.20.8** | **7.21.3** |
| OmniTIK 5 ac | Boat WiFi | **6.49.10** | **6.49.19** | N/A (v6 long-term only) |

**Release channels**: Long-term = bugfix only (recommended for production);
Stable = new features + bugfixes.

**Upgrade priorities**:

1. **SXTsq Lite5 (operator) — HIGH**: 7.4.1 is vulnerable to multiple critical
   CVEs including CVE-2024-54772 (WinBox auth enumeration) and CVE-2025-10948
   (buffer overflow). Upgrade to at least 7.20.8 (long-term).

2. **OmniTIK 5 ac (boat) — MEDIUM**: 6.49.10 is vulnerable to CVE-2024-54772.
   Upgrade to 6.49.19 (long-term, stays within v6 branch, low risk). RouterOS 7
   is supported on this hardware (MIPSBE architecture) but the wireless subsystem
   was redesigned — test on bench before migrating. If upgrading to v7.13+, must
   go through v7.12 first for wireless package conversion.

**For BizzyBoat**: start with aligned firmware versions on both WiFi radios
(both on v7 long-term) to avoid the protocol mismatch seen on IzzyBoat.
