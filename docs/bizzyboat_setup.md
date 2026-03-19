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
