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

### Remaining Router Configuration

- [ ] LAN2 as separate interface for WiFi bridge (172.16.20.1/24)
- [ ] Firewall / routing between LAN1 and LAN2
- [ ] NETMAP rules (when VPN is configured)
- [ ] Disable IPv6 globally
