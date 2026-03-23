# BizzyBoat Setup Log

Setup log for BizzyBoat (EchoBoat 240). Tracks #5.

## Hardware

From #8:

| Component | Model | Notes |
|-----------|-------|-------|
| Robot computer | Neousys Nuvo 9160GC, Core i7-14700, 32 GB RAM | Hostname: `gabby` |
| GNSS | CUAV New C-RTK 2HP | Dual antenna, centimeter position, heading |
| Network switch | Trendnet TI-PG80B | Industrial PoE+ gigabit switch |
| Router | Teltonika RUTX11 (RUTX11100400) | Industrial cellular router |

## OS Installation

### Preparation

- Prepared a USB flash drive with the Ubuntu 24.04 Server ISO
- Connected laptop to gabby via ethernet; used NetworkManager "Shared to other
  computers" IPv4 method on the wired connection to provide internet during setup
- The three video ports on the motherboard did not output video; had to use a
  port on the installed discrete GPU instead
- Initial boot: expected "no boot device" error with prompt to insert recovery
  media. Inserted USB flash drive (top-left USB port) and keyboard (top-right
  USB port). Keyboard was not detected so could not acknowledge the prompt;
  power-cycled to let devices get detected at boot
- After power cycle: GRUB menu appeared but keyboard initially unresponsive.
  Without changing anything, keyboard started working. GRUB default entry
  booted into the Ubuntu Server installer (language selection screen)

### Installer Options

- **Language**: English
- **Base**: Ubuntu Server
- **Network**: 6 ethernet interfaces detected; `enp7s0` received `10.42.0.207/24`
  via DHCP from laptop's shared connection (leftmost physical port)
- **Proxy**: none
- **Partitioning**: custom layout
  - `/` on 952.8 GB drive
  - `/home` on 1.863 TB drive
- **Profile**: Full name "Field User", username `field`
- **Hostname**: `gabby`
- **Ubuntu Pro**: skipped
- **SSH**: OpenSSH server enabled
- **Snaps**: none selected

### First Boot

- Booted successfully, hostname `gabby` confirmed
- SSH verified from laptop (`ssh field@10.42.0.207`)

### Network Interfaces

6 ethernet ports detected, all with sequential MACs:

| Interface | Notes |
|-----------|-------|
| `enp0s31f6` | |
| `enp3s0` | |
| `enp4s0` | |
| `enp5s0` | |
| `enp6s0` | |
| `enp7s0` | Leftmost physical port; used for install (laptop shared connection) |

_MAC addresses and IP assignments are in the private `ccomjhc_project11` repo
(`configuration/bizzyboat_network.yaml`)._

## Physical Connections

| Device | Port | Connected To |
|--------|------|-------------|
| gabby | `enp7s0` (leftmost) | PoE switch (onboard LAN) |
| Teltonika RUTX11 | WAN | Starlink |
| Teltonika RUTX11 | LAN1 | PoE switch (onboard LAN) |
| Teltonika RUTX11 | LAN2 | OmniTIK 5 ac (WiFi bridge) |
| PoE switch (TI-PG80B) | Ports 1–2 | Router (via PoE adapter) + gabby (data only) |
| PoE switch (TI-PG80B) | Ports 3–6 | OAK-1 cameras ×4 (802.3af PoE) |
| OmniTIK 5 ac | Ethernet | Teltonika LAN2 (direct cable, powered by 24V adapter) |

## Router Configuration (Teltonika RUTX11)

### Initial Setup Wizard (Advanced Mode)

1. Connected laptop to PoE switch (same switch as router LAN1); got DHCP lease
   on default 192.168.1.0/24 subnet
2. Opened web UI at `https://192.168.1.1`, logged in with default credentials
   (printed on device label), changed password immediately
3. Wizard settings:
   - **Configuration mode**: Advanced
   - **Time**: synced with browser, timezone set to **UTC**
   - **LAN IP**: changed from 192.168.1.1 to **192.168.20.1**
   - **DHCPv4**: enabled (pool to be configured post-wizard)
   - **DHCPv6**: disabled
   - **Mobile**: SIM detected, Verizon connected, data status disconnected;
     left auto APN on (APN: `nw01.vzwstatic`)
   - **Wireless 2.4 GHz**: enabled as AP, SSID `BizzyBoat`
   - **Wireless 5 GHz**: disabled for now (reserved for future WiFi WAN client)
   - **RMS**: off
   - **Proxy**: off
4. Clicked finish; router rebooted with new LAN IP
5. Unplugged/replugged ethernet to get new DHCP lease on 192.168.20.0/24
6. Logged in at `https://192.168.20.1`

### Post-Wizard: Internet via WiFi WAN

- The new LAN IP caused the router to become the default gateway, breaking
  internet access on the laptop (lab network unreachable)
- Used the 5 GHz radio to scan and connect to the lab WiFi network as a WAN client
- Enabled failover so the router uses WiFi WAN for internet when Starlink is
  unavailable (indoor setup, no Starlink signal)
- Internet restored through router's WiFi WAN uplink

### Firmware Update

- Factory firmware: `RUTX_R_00.07.11.3` (2024-12-13), kernel 5.10.226
- Modem firmware: `EG06ALAR04A01M4G_01.004.01.004` (already newest)
- Updated to: `RUTX_R_00.07.20.3` (via OTA from router's firmware page)
- Settings survived update; verified LAN IP, WiFi AP, timezone all intact
- Updated again to: `RUTX_R_00.07.21.2` (2026-03-05), kernel 6.6.119
- Includes fix for edge-case network hang after reboot

### DHCP Configuration

- DHCP pool: 192.168.20.200–249 (150 addresses reserved for static below .200)
- Static lease: `gabby` → 192.168.20.5 (enp7s0 via PoE switch)
- Verified: gabby boots and receives 192.168.20.5, SSH works from laptop on
  BizzyBoat WiFi

### DNS Configuration

- Router inherited DNS from multiple WAN sources; Starlink (down) was providing
  stale `192.168.1.1` which caused DNS failures for LAN clients
- Added static DNS servers: `1.1.1.1` (Cloudflare), `8.8.8.8` and `8.8.4.4` (Google)
- Verified: LAN clients can now resolve hostnames via the router

## WireGuard VPN

Migrated from OpenVPN to WireGuard on 2026-03-20. BenCloud serves as the hub;
each boat and operator station connects as a spoke.

### BenCloud Setup

1. Installed `wireguard-tools` on BenCloud (Ubuntu, via apt)
2. Generated key pairs for BenCloud, BizzyBoat, and operator station
3. Stopped and disabled OpenVPN (`systemctl stop/disable openvpn@bencloud`);
   config preserved in `/etc/openvpn/` for rollback
4. Created `/etc/wireguard/wg0.conf`:
   - Interface: `10.132.146.1/24`, listen UDP 51820
   - Peer: BizzyBoat (`10.132.146.6/32`, `192.168.21.0/24`)
   - Peer: Operator (`10.132.146.5/32`, `192.168.15.0/24`, `192.168.22.0/24`)
5. Brought up with `wg-quick up wg0`, enabled on boot via systemd
6. IP forwarding was already enabled (`net.ipv4.ip_forward=1`)
7. AWS security group already had UDP 51820 inbound (added 2026-03-19)

### Tunnel Addressing

Uses the same IPs as the previous OpenVPN setup to minimize disruption:

| Peer | Tunnel IP | NETMAP Range |
|------|-----------|--------------|
| BenCloud (hub) | 10.132.146.1 | — |
| BizzyBoat | 10.132.146.6 | 192.168.21.0/24 |
| Operator station | 10.132.146.5 | 192.168.15.0/24, 192.168.22.0/24 |
| IzzyBoat | 10.132.146.4 | 192.168.14.0/24 |

_Key material is in the private `ccomjhc_project11` repo
(`configuration/bencloud/wireguard/`)._

### Operator Router (Teltonika RUTX11)

#### Firmware Update

- Factory firmware: `RUTX_R_00.07.16.1` (2025-07-16), kernel 6.6.92
- Modem firmware: `EG06ALAR04A01M4G` (already newest)
- Updated to: `RUTX_R_00.07.20.3` (2026-01-21), kernel 6.6.115
  - After this update, the machine connected to the router lost internet
    connectivity. DNS resolved but pings were silent. A router reboot
    restored connectivity. (This edge case is fixed in 00.07.21.2.)
- Updated to: `RUTX_R_00.07.21.2` (2026-03-05), kernel 6.6.119
- Modem firmware: update was offered (unlike BizzyBoat which reported "already newest");
  applied update, version string unchanged at `EG06ALAR04A01M4G`, now reports current

- Removed stale WireGuard test config; disabled OpenVPN client

#### WireGuard Configuration

Configured via Teltonika web UI at 192.168.13.1 under Services → VPN → WireGuard.

**Interface** (instance name: `bcloud`):
- Enable: on
- Private key: _(in private repo)_
- IP address: `10.132.146.5/24`
- Listen port: 51820 (default)
- Advanced: all defaults (metric, MTU, DNS, watchdog all empty/auto)

**Peer** (name: `bencloud`):
- Public key: `7z8/BYsq/MVKo6VlVktRpqzhle3JMYFiPTFfqHrtz3Q=`
- Endpoint host: `18.213.242.76`
- Endpoint port: `51820`
- AllowedIPs: `10.132.146.0/24`, `192.168.14.0/24`, `192.168.21.0/24`
- Route Allowed IPs: on
- Persistent keepalive: 25
- Tunnel source: Any (failover across WAN interfaces)
- Tunnel source mode: Prefer (default)
- Pre-shared key: none

### IzzyBoat Router (Teltonika RUTX11)

#### Firmware Update

- Factory firmware: `RUTX_R_00.07.15.1` (2025-06-16), kernel 6.6.87
- Modem firmware: `EG06ALAR04A01M4G` — update was offered but failed within
  seconds, then reported "newest version installed". Unlike the operator router
  which completed a multi-minute upgrade successfully. BizzyBoat's router
  reported "already newest" without offering an update at all. Inconsistent
  behavior across the three routers with the same modem firmware version.
- Updated to: `RUTX_R_00.07.20.3` (2026-01-21), kernel 6.6.115
  - After this update, modem firmware update was offered again
- Updated to: `RUTX_R_00.07.21.2` _(pending — router temporarily shut down)_

### BizzyBoat Router (Teltonika RUTX11)

- WireGuard interface: `10.132.146.6/24`
- Peer: BenCloud at `18.213.242.76:51820`
- AllowedIPs: `10.132.146.0/24`, `192.168.14.0/24`, `192.168.15.0/24`, `192.168.22.0/24`
- Persistent keepalive: 25s

_(Not yet configured — boat powered off)_

## WiFi Bridge (MikroTik Radios)

### Discovery

Both MikroTik radios were connected to the operator router LAN3 port (previously
the mobile_lab interface on VLAN 4, 192.168.50.0/24). Temporarily changed mobile_lab
IP to 192.168.1.25/24 to reach the devices on their Seafloor-configured subnet.

Devices found via operator router network scan:

| IP | MAC | Manufacturer | Likely Device |
|----|-----|-------------|---------------|
| 192.168.1.20 | C4:AD:34:90:72:47 | MikroTik | TBD |
| 192.168.1.21 | 08:55:31:E0:74:D3 | MikroTik | TBD |

Note: BizzyBoat is powered on, so one device may be on the boat side (OmniTIK)
communicating wirelessly with the shore-side device (SXTsq) on LAN3.

### As-Shipped Configuration (Seafloor Systems)

Per the EchoBoat 240 manual (Section 3.8), Seafloor ships everything on a flat
192.168.1.0/24 network: the onboard Windows PC at .8, shoreside laptop at .4,
MikroTik radios bridging all ports + wireless. No routing, no VLANs, no gateway.
Remote Desktop from shoreside laptop to 192.168.1.8, user `EchoBoat`.

The OmniTIK acts as the bridge AP on the boat (SSID `Boatside`), and the SXTsq
connects as a station-bridge client on shore. WiFi: 5 GHz a/n/ac, WPA-PSK,
password `[redacted]`.

#### OmniTIK 5 ac (boat side) — 192.168.1.20

- **Model**: RBOmniTikG-5HacD
- **RouterOS**: 6.45.9
- **Serial**: C7020B21270E
- **MAC**: C4:AD:34:90:72:47

```routeros
# jan/02/1970 02:13:35 by RouterOS 6.45.9
# software id = W00D-83IZ
# model = RBOmniTikG-5HacD
# serial number = C7020B21270E
/interface bridge
add name=bridge1
/interface wireless
set [ find default-name=wlan1 ] band=5ghz-a/n/ac disabled=no mode=bridge ssid=Boatside \
    wireless-protocol=802.11
/interface list
add name=WAN
add name=LAN
/interface wireless security-profiles
set [ find default=yes ] authentication-types=wpa-psk mode=dynamic-keys \
    supplicant-identity=MikroTik wpa-pre-shared-key=[redacted] wpa2-pre-shared-key=\
    [redacted]
/interface bridge port
add bridge=bridge1 interface=ether1
add bridge=bridge1 interface=ether2
add bridge=bridge1 interface=ether3
add bridge=bridge1 interface=ether4
add bridge=bridge1 interface=ether5
add bridge=bridge1 interface=wlan1
/interface list member
add interface=ether1 list=WAN
add interface=ether2 list=LAN
add interface=ether3 list=LAN
add interface=ether4 list=LAN
add interface=ether5 list=LAN
add interface=wlan1 list=LAN
/ip address
add address=192.168.1.20/24 interface=ether2 network=192.168.1.0
```

#### SXTsq Lite5 (shore side) — 192.168.1.21

- **Model**: RBSXTsq5nD
- **RouterOS**: 7.4.1
- **Serial**: E6FA0D952975
- **MAC**: 08:55:31:E0:74:D3

```routeros
# jan/05/1970 00:27:47 by RouterOS 7.4.1
# software id = NREB-SDHP
# model = RBSXTsq5nD
# serial number = E6FA0D952975
/interface bridge
add name=bridge1
/interface wireless
set [ find default-name=wlan1 ] band=5ghz-a/n channel-width=20/40mhz-XX disabled=no \
    frequency=auto mode=station-bridge ssid=Boatside
/interface list
add name=WAN
add name=LAN
/interface wireless security-profiles
set [ find default=yes ] authentication-types=wpa-psk,wpa2-psk group-ciphers=\
    tkip,aes-ccm mode=dynamic-keys supplicant-identity=MikroTik unicast-ciphers=\
    tkip,aes-ccm
/ip hotspot profile
set [ find default=yes ] html-directory=hotspot
/interface bridge port
add bridge=bridge1 interface=wlan1
add bridge=bridge1 interface=ether1
/ip neighbor discovery-settings
set discover-interface-list=!dynamic
/interface list member
add interface=wlan1 list=WAN
add interface=ether1 list=LAN
/ip address
add address=192.168.1.21/24 interface=ether1 network=192.168.1.0
```

### MikroTik Firmware Updates

#### SXTsq Lite5 (shore side)

- Could not use built-in update check (DNS not resolving; device has no
  default gateway or DNS configured on its flat bridge network)
- Downloaded `routeros-7.22-mipsbe.npk` (stable, 2026-03-09) on laptop
- Uploaded via web UI (Files → drag and drop), then System → Reboot
- Updated from 7.4.1 → **7.22 (stable)**
- Set password on first login (RouterOS 7 requires it)
- Wireless was lost after upgrade: `wireless` package not included in base
  RouterOS 7.13+ (separated into its own package). Skipping the 7.12
  conversion step meant the wireless config was dropped.
- Downloaded `wireless-7.22-mipsbe.npk`, uploaded via Files, rebooted
- Wireless restored, reconnected to OmniTIK automatically
- Note: `wireless` (legacy) is the only wifi package for MIPSBE architecture;
  the newer `wifi-qcom` packages are ARM-only

#### OmniTIK 5 ac (boat side)

- Accessed via WiFi link through SXTsq at 192.168.1.20
- Step 1: uploaded `routeros-6.49.19-mipsbe.npk`, rebooted (set password)
- Step 2: uploaded `routeros-7.22-mipsbe.npk` + `wireless-7.22-mipsbe.npk`
  together, rebooted. Skipped 7.12 intermediate step — uploading the
  wireless package alongside the firmware avoided the conversion issue.
- Updated from 6.45.9 → 6.49.19 → **7.22 (stable)**
- Wireless config survived: AP bridge mode, SSID Boatside, 5745 MHz (ch149)
- Both devices now on matching RouterOS 7.22 with wireless package

### WiFi Bridge Reconfiguration

#### OmniTIK 5 ac (boat side) — partial, lost access

- Removed ether2-5 from bridge (kept ether1 + wlan1) via web UI
- **Lost access**: the device's IP (192.168.1.20) was on ether2, which was
  just removed from the bridge. With ether2 no longer bridged, the IP is
  unreachable via the WiFi path (wlan1 → bridge → ether2). Need to access
  from boat side (BizzyBoat router LAN2 → OmniTIK ether1) to finish config.
- Still needed: add management IP 172.16.20.3/24 on ether2, remove old
  192.168.1.20 IP, change SSID to `bizzy_bridge`, set WiFi security,
  set frequency

#### SXTsq Lite5 (shore side) — configured

- Changed SSID from `Boatside` to `bizzy_bridge`
- Security profile (`default`): mode `dynamic-keys`, authentication
  `wpa2-psk`, password set (WPA1 removed)
- Mode: `station-bridge` (unchanged, correct for shore/client side)
- Band: 5GHz a/n, channel width 20/40MHz Ce, frequency auto
- Wireless protocol: 802.11 (plain, not nv2/nstreme — avoids protocol
  mismatch issue seen on IzzyBoat)
- Added IP `172.16.20.4/24` on ether1 (kept old `192.168.1.21/24`
  temporarily for access during operator router reconfiguration)
- WiFi link to OmniTIK currently down (SSID mismatch — OmniTIK still
  on old `Boatside` SSID, will be fixed from boat side later)

#### Operator Router

- Renamed `mobile_lab` interface to `wifi_bridge_bizzyboat`
- Changed IP from `192.168.1.25/24` to `172.16.20.2/24` on `eth0.4` (VLAN 4, LAN3)
- Disabled DHCP on the interface
- Firewall zone: `lan` (matches IzzyBoat WiFi bridge)
- mwan3: disabled for this interface
- Added static route: `192.168.20.0/24 via 172.16.20.1` metric 5
  (won't function until BizzyBoat router LAN2 is configured at 172.16.20.1)
- Verified SXTsq reachable at `172.16.20.4` from deadpool
- Removed old `192.168.1.21/24` address from SXTsq (kept `172.16.20.4/24`)

##### NETMAP rules — blocked by firmware

- Firmware 00.07.21.2 dropped the `xt_NETMAP` kernel module. The old iptables
  NETMAP rules in `/etc/firewall.user` fail with `unknown option "--to"`.
  This means IzzyBoat's existing NETMAP rules were also silently failing
  since the operator router was upgraded to this firmware.
- Despite `nft` being available (v1.0.7) and kernel 6.6.119, the firmware
  does not ship `nft_nat.ko` — only filter/reject/redirect nft modules are
  included. Creating nftables NAT chains fails with "No such file or directory".
- The firewall is actually **fw3** (iptables-based), not fw4. Confirmed by
  `/* !fw3 */` comments in `iptables -L` output. `nft` is installed but
  not used by the system firewall.
- **Investigation summary**:
  - `xt_NETMAP`: not in `/lib/modules/`, not available via `opkg`
  - `nft_nat.ko`: not in `/lib/modules/`, not available via `opkg list`
  - `kmod-nf-nat` (iptables NAT): loaded and working (standard SNAT/DNAT/MASQUERADE)
  - Only NETMAP (subnet-to-subnet translation) is missing
- **Potential fix**: install `kmod-nft-nat` via opkg (if available) to enable
  nftables NAT chains, then use nft `prefix` syntax for NETMAP. Or find
  a firmware version / opkg package that includes `xt_NETMAP`.
- `/etc/firewall.user` currently contains the nft commands (non-functional);
  needs to be updated once a working approach is found.
- **Impact**: NETMAP is needed for dual-path (WiFi + VPN) addressing. Without
  it, the operator station can reach boat networks via WiFi or VPN but not
  with translated source addresses. This affects IzzyBoat too (same router).

## MultiWAN / Cellular Connectivity (2026-03-23)

On first connecting deadpool to the BizzyBoat router this morning, internet
worked briefly then stopped after a few minutes. The Teltonika web UI status
overview showed the MultiWAN priorities in this order:

1. **wan** — offline
2. **mob1a1a1** — offline
3. **wifi1** — standby

Moved **wifi1** to the top of the priority list in the MultiWAN configuration
page, which restored internet. After the change, the status overview showed:

1. **wifi1** — online
2. **wan** — offline
3. **mob121a1** — standby

The cellular connection (Verizon) has not been working reliably — last week it
was connecting to the network but not obtaining an IP address or internet access.
Not investigating further today; noting for future troubleshooting.

## NETMAP Restore (2026-03-23)

The `xt_NETMAP` kernel module was removed from base firmware starting with
RutOS 7.13 and must be installed as an optional package. See
[unh_echoboats_project11#10](https://github.com/rolker/unh_echoboats_project11/issues/10)
for background and the boot-order race condition fix.

1. Navigated to **System → Package Manager** in the BizzyBoat router web UI
2. Found **"IPtables NAT extra"** (status: Available), clicked **Install**
3. Status changed to **Installed**
4. Verified via SSH: `lsmod | grep xt_NETMAP` — module loaded (12288 bytes)
5. Confirmed **Package Restore** is already enabled (ensures the package is
   reinstalled automatically after firmware upgrades with "keep settings")

### Remaining BizzyBoat Router Configuration

- [ ] LAN2 as separate interface for WiFi bridge (172.16.20.1/24)
- [ ] Firewall / routing between LAN1 and LAN2
- [ ] NETMAP rules (192.168.20.0/24 ↔ 192.168.21.0/24 on wg0)
- [ ] WireGuard configuration
- [ ] Disable IPv6 globally
- [ ] Operator router NETMAP — resolve missing xt_NETMAP / nft_nat on FW 00.07.21.2
