# BizzyBoat NTP Investigation — RUTX11 as GPS-Synced NTP Server

**Issue**: [rolker/unh_echoboats_project11#45](https://github.com/rolker/unh_echoboats_project11/issues/45)
**Date**: 2026-04-09

## Goal

Investigate using the Teltonika RUTX11 router as an NTP server for
BizzyBoat's onboard network. The router has a built-in GPS receiver
that can provide time. Internet NTP sources should provide immediate
sync at boot, with GPS time preferred once a fix is acquired.

## Problem Statement

Initial testing showed the RUTX11 serves incorrect time after a power
cycle because it has no battery-backed RTC. The clock starts stale and
GPS takes 30–60s to acquire a fix. Clients picking up this bad time
causes problems for ROS 2 operations.

## Approach

Use internet NTP pools (pool.ntp.org, etc.) as immediate time sources
at boot, then prefer GPS time once available. This avoids serving wrong
time during the GPS cold-start window.

## Investigation Log

### Session 1 — 2026-04-09

#### NTP Components on the RUTX11

The router has three NTP-related components — two clients and one server:

| Component | Config | Process | Role | Status |
|-----------|--------|---------|------|--------|
| `sysntpd` (busybox) | `system.ntp` | not checked | NTP client (standard OpenWrt) | **Disabled** (`enabled='0'`) |
| `ntpclient` (Teltonika) | `ntpclient.ntpclient` | `/usr/sbin/ntpclient -s -l` (running) | NTP client with GPS integration | Process running, but **sync disabled** (`sync_enabled='0'`, `gps_sync='0'`) |
| `untpd` (Teltonika) | `ntpserver.general` | `/usr/sbin/untpd` (running) | NTP server (serves LAN clients) | **Enabled** (`enabled='1'`) |

**Key finding**: The NTP server (`untpd`) is running and serving time to LAN
clients, but *neither* NTP client is syncing the clock from any source. The
system clock happens to be correct right now, but would be wrong after a
power cycle.

#### Installed Packages

```
ntpclient - 2026-02-11-1     # Teltonika NTP client
untpd - 1.34.1-111.18        # Teltonika NTP server
ntp_gps - 2025-11-27-1       # GPS-to-NTP integration
gpsd - 2025-11-27-1           # GPS daemon
gpsctl - 2025-11-27-1         # GPS control CLI
```

No `chrony` or standard `ntpd` installed.

#### NTP Client Config (`uci show ntpclient`)

```
ntpclient.ntpclient.enabled='1'        # process runs
ntpclient.ntpclient.sync_enabled='0'   # but sync is OFF
ntpclient.ntpclient.gps_sync='0'       # GPS sync is OFF
ntpclient.ntpclient.interval='60'
ntpclient.ntpclient.zoneName='UTC'
```

Configured upstream servers (not currently used since sync is off):
- `0–3.openwrt.pool.ntp.org`
- `pool.ntp.org`
- `time.google.com`
- `192.168.100.1`

#### System NTP Config (`uci show system.ntp`)

```
system.ntp.enabled='0'
system.ntp.enable_server='0'
system.ntp.server='0.pool.ntp.org' '1.pool.ntp.org' '2.pool.ntp.org' '3.pool.ntp.org'
```

Fully disabled — this is the standard OpenWrt busybox ntpd, not used.

#### GPS Status

`gpsd` is running with multi-constellation support (GPS, Galileo, GLONASS, BeiDou).

```
gpsctl -s  →  1              # fix status: has fix (weak)
gpsctl -e  →  2026-04-08 18:35:48   # stale — ~18.5h behind system clock
gpsctl -p  →  2              # only 2 satellites (need 4+ for good fix)
gpsctl -u  →  500.000000     # 500m accuracy — very poor (indoors)
```

GPS time is stale because the antenna has poor sky view indoors. System clock
(`2026-04-09 13:08:20 UTC`) is correct from some other source.

#### Configuration Changes Applied

```bash
uci set ntpclient.ntpclient.sync_enabled='1'   # enable NTP sync
uci set ntpclient.ntpclient.gps_sync='1'       # enable GPS time sync
uci commit ntpclient
/etc/init.d/ntpclient restart
/etc/init.d/ntp_gps restart
```

#### Corrected Understanding of NTP Architecture

Initial assumption was that `ntpclient` and `sysntpd` were two independent NTP
clients. Research and debug output revealed a different picture:

**There is no `sysntpd`** on this router. Teltonika stripped the busybox ntpd.
The only init scripts are `ntpclient`, `ntpserver`, and `ntp_gps`. The
`system.ntp` UCI section exists but has no corresponding service.

**`ntpclient` handles both modem time AND NTP pool servers.** Debug output
(`/usr/sbin/ntpclient -d -s`) revealed the actual sync cycle:

```
Configuration:
    failover_count          5
    time_sync_enabled       1
    Hosts:
      1. 0.openwrt.pool.ntp.org
      2. 1.openwrt.pool.ntp.org
      3. 2.openwrt.pool.ntp.org
      4. 3.openwrt.pool.ntp.org
    Compiled with NTP_MAX_SERVERS = 4
```

Each 60-second cycle:
1. Try modem/cellular time via AT commands → fails (no SIM) → logs error
2. Try NTP pool server → succeeds silently (no log on success)

The modem error log ("Failed to get proper datetime from operator station")
is noisy but harmless — NTP pool sync works fine after it.

**`ntp_gps` is a separate service** that bridges GPS time to the system clock.
Its init script (`/etc/init.d/ntp_gps`) reads `gps_sync` from the `ntpclient`
UCI config. When `gps_sync='1'`, it launches `/usr/sbin/ntp_gps` which reads
from gpsd and sets the system clock periodically.

#### UCI Option Mapping (from Teltonika wiki + debug output)

| UCI Option | Web UI Label | Function |
|------------|-------------|----------|
| `ntpclient.ntpclient.enabled` | — | Master on/off for ntpclient process |
| `ntpclient.ntpclient.sync_enabled` | Enable NTP Client | Enables NTP pool + modem time sync |
| `ntpclient.ntpclient.gps_sync` | GPS Synchronization | Enables `ntp_gps` service (GPS → system clock) |
| `ntpclient.ntpclient.interval` | Update interval | Sync cycle in seconds (default 60) |
| `ntpclient.ntpclient.save` | Save time to flash | Persist time across reboots |
| `ntpclient.ntpclient.force` | Force Servers | Use unreliable NTP servers |
| `ntpclient.ntpclient.tmz_sync_enabled` | Operator Station Sync (timezone) | Sync timezone from cellular network |
| (not set, default 5) | Count of failed NTP requests | Failures before modem fallback |

#### Compiled Limit: Max 4 NTP Servers

The binary is compiled with `NTP_MAX_SERVERS = 4`. The first 4 entries
(`0-3.openwrt.pool.ntp.org`) are used; entries 5+ (`pool.ntp.org`,
`time.google.com`, `192.168.100.1`) are silently ignored. This is fine —
the openwrt pool servers provide adequate coverage.

#### Current State After Changes

| Component | Status |
|-----------|--------|
| `ntpclient` (PID 22321) | Running, syncing from NTP pools every 60s |
| `ntp_gps` (PID 24723) | Running, will set clock from GPS when fix is good |
| `untpd` | Running, serving system clock to LAN clients on port 123 |
| `gpsd` | Running, weak fix (2 sats, indoors) |

#### `ntp_gps` Debug

Ran `/usr/sbin/ntp_gps -d` (after stopping the service to avoid ubus conflict).
Output was only "Starting gps time sync" followed by silence — the process
sits in a loop waiting for GPS data from gpsd. With only 2 satellites and a
stale fix (indoors), it has nothing to act on. Expected to work properly
outdoors with a good sky view.

#### Salmon NTP Query Test

Tested from salmon using `sudo chronyd -Q "server 192.168.13.1 iburst"`:

```
2026-04-09T16:47:17Z chronyd version 4.5 starting
2026-04-09T16:47:17Z Disabled control of system clock
2026-04-09T16:47:21Z System clock wrong by -0.038793 seconds (ignored)
2026-04-09T16:47:21Z chronyd exiting
```

**Result**: Router is serving accurate NTP to LAN clients. Salmon's clock
differs by only ~39ms from the router — well within acceptable range for
ROS 2 operations.

#### Working Chain

1. `ntpclient` syncs router clock from internet NTP pools (every 60s) ✓
2. `untpd` serves that time to LAN clients on port 123 ✓
3. Salmon can query the router (192.168.13.1) and gets accurate time ✓
4. `ntp_gps` is running but idle (poor GPS fix indoors) — will activate
   with good sky view outdoors

#### `untpd` Stratum Problem

Raw NTP packet query from salmon (python3 script) revealed that `untpd`
reports dishonest NTP metadata:

```
Stratum: 1          # claims primary reference clock
LI: 0               # claims fully synchronized
Root delay: 0.0 s   # claims zero delay
Root dispersion: 0.0 s  # claims perfect precision
```

This is a problem: `untpd` always claims stratum 1 with zero dispersion
regardless of whether the router's clock is actually synchronized. After a
power cycle, it would serve confidently wrong time and chrony clients would
have no way to detect it's unreliable.

A community report ([Teltonika forum](https://community.teltonika.lt/t/ntp-server-synch/17415))
shows the opposite problem on a RUT956: `untpd` reports stratum 16 even when
GPS time is correct, causing PLCs to reject it. Either way, `untpd` does not
report honest stratum based on actual sync status.

This means we **cannot safely add the router as a chrony source** on salmon
or other LAN clients while using `untpd` — chrony's cross-checking relies on
honest stratum and dispersion values.

#### Decision: Replace Teltonika NTP Stack with ISC `ntpd`

ISC `ntpd` (4.2.8p15) is available via `opkg` and is referenced in Teltonika's
own wiki as installable via System → Package Manager. It provides:

- Honest stratum reporting (stratum 16 when unsynchronized, correct value once synced)
- Real root delay and dispersion values
- Combined client + server in one daemon (replaces both `ntpclient` and `untpd`)
- GPS refclock support via gpsd shared memory (SHM)
- Standard, well-documented configuration

#### ISC `ntpd` Installation

Disabled Teltonika services first, then installed:

```bash
# Disable Teltonika NTP stack
/etc/init.d/ntpserver stop; /etc/init.d/ntpserver disable
/etc/init.d/ntpclient stop; /etc/init.d/ntpclient disable
/etc/init.d/ntp_gps stop; /etc/init.d/ntp_gps disable

# Install ISC ntpd
opkg install ntpd    # installs ntpd 4.2.8p15-3
# Binary: /usr/local/sbin/ntp (not /sbin/ntpd)
# UCI config: /etc/config/ntpd
# Generated config: /var/run/ntpd.conf

# Enable and configure
uci set ntpd.ntp.enabled='1'
uci set ntpd.ntp.enable_server='1'
uci commit ntpd
/etc/init.d/ntpd enable
/etc/init.d/ntpd start
```

Generated config (`/var/run/ntpd.conf`):

```
driftfile /var/lib/ntp/ntp.drift

restrict default limited kod nomodify notrap nopeer
restrict -6 default limited kod nomodify notrap nopeer
restrict source noquery
restrict 127.0.0.1
restrict -6 ::1

server 0.openwrt.pool.ntp.org iburst
server 1.openwrt.pool.ntp.org iburst
server 2.openwrt.pool.ntp.org iburst
server 3.openwrt.pool.ntp.org iburst
```

Port 123 bound on all interfaces including 192.168.13.1 (LAN). No conflict
with Teltonika services (all disabled).

#### Stratum Verification — ISC `ntpd` vs `untpd`

Raw NTP packet query from salmon after switching to ISC ntpd:

```
# untpd (before)          # ISC ntpd (after)
Stratum: 1                Stratum: 3
LI: 0                     LI: 0
Root delay: 0.0 s          Root delay: 0.080 s
Root dispersion: 0.0 s     Root dispersion: 0.075 s
```

ISC ntpd reports honest values: stratum 3 (one below the stratum 2 pool
servers), real root delay and dispersion. Chrony clients can now make
informed trust decisions.

#### Current Running State

```
16719 ntp  /usr/local/sbin/ntp -g -u ntp:ntp -p /var/run/ntpd.pid -n -c /var/run/ntpd.conf
```

Teltonika `ntpclient`, `untpd`, `ntp_gps` — all stopped and disabled.
`gpsd` still running (needed for future GPS refclock).

#### GPS Refclock Investigation

NMEA data confirmed on `/dev/ttyUSB1` (GPRMC, GPGSV, GLGSV sentences).
Currently showing void fix (`$GPRMC,,V,,,,,,,,,,N`) due to poor sky view
indoors.

Teltonika's `gpsd` is a custom stripped-down build that does **not** create
NTP shared memory (SHM) segments — the standard gpsd SHM refclock approach
(driver 28) won't work. The standard gpsd package is not available in the
Teltonika opkg repo.

Options investigated for GPS refclock:
- **NMEA serial refclock (driver 20)**: ntpd reads `/dev/ttyUSB1` directly,
  but conflicts with Teltonika's gpsd on the same port
- **Re-enable `ntp_gps`**: Sets system clock from GPS, but ntpd wouldn't
  know it's GPS-disciplined (stratum wouldn't reflect GPS)
- **Defer**: Internet NTP is already working well; GPS refclock can be
  tackled as a follow-up when testing outdoors

**Decision**: Defer GPS refclock integration. The current ISC ntpd + internet
NTP pool setup is a significant improvement. GPS can be added later,
potentially by replacing Teltonika's gpsd with a standard build or using
the NMEA driver after stopping gpsd.

#### Salmon Chrony Configuration

Added operator router as an NTP source and BizzyBoat router + gabby as
monitor-only sources on salmon.

Created `/etc/chrony/sources.d/project11.sources`:

```
server router.op.p11.lan iburst
server router.bizzy.p11.lan iburst noselect
server gabby.bizzy.p11.lan iburst noselect
```

- `iburst` — fast initial sync
- `noselect` — monitor only, never use for synchronization

After `sudo chronyc reload sources`, all three sources appeared:

```
^- router_izzyboat_operator      3   6    17     6  +6452us[+6452us] +/-   53ms
^? router_bizzyboat              0   7     0     -     +0ns[   +0ns] +/-    0ns
^? gabby                         0   7     0     -     +0ns[   +0ns] +/-    0ns
```

- **Operator router**: Working, stratum 3, ~6.4ms offset, accepted as valid
  source (`^-`) but not selected (pool stratum 1 server preferred — correct)
- **BizzyBoat router**: Not responding (`^?`) — likely not running NTP server
- **gabby**: Not responding (`^?`) — likely not running NTP server

Chrony correctly cross-checks the operator router against pool servers and
would reject it if it served bad time (falseticker detection).

#### Reboot Test

Rebooted router at 18:12 UTC. Results:

- **ntpd started at 18:15:08** (~2 min after reboot, after network init)
- **"Clock Unsynchronized"** reported at 18:15:08 and 18:20:51 — ntpd
  correctly reports stratum 16 while unsynchronized, so clients won't
  accept bad time during this window
- **Synced by ~18:24** — salmon shows router at stratum 2, offset -12ms,
  reach 377 (fully reachable), status `^-` (valid but not selected)
- **Clock was correct at boot** — only ~2 min power-off, so clock didn't
  drift significantly. A longer outage would produce a larger error, but
  ntpd would not serve until synced

**Issue found**: Teltonika's `ntpclient` restarted despite being "disabled"
via `/etc/init.d/ntpclient disable`. The init script checks the UCI flag
`ntpclient.ntpclient.enabled` (not the init.d symlinks). Similarly,
`ntpserver.general.enabled` was still `'1'`.

**Fix applied**:

```bash
uci set ntpclient.ntpclient.enabled='0'
uci commit ntpclient
uci set ntpserver.general.enabled='0'
uci commit ntpserver
```

Teltonika services use UCI `enabled` flags to control startup, not the
standard OpenWrt `/etc/init.d/<service> enable/disable` mechanism. Both
must be set to fully disable.

Post-reboot salmon view:

```
^- router_izzyboat_operator      2   6   377    28    -12ms[  -12ms] +/-   56ms
```

Stratum 2 with honest dispersion. Chrony correctly accepted it once synced
and would have rejected it during the unsynchronized window.

#### Summary of Changes Made

**Operator router (RUTX11):**
1. Installed ISC `ntpd` 4.2.8p15 via `opkg install ntpd`
2. Enabled NTP client + server via UCI (`ntpd.ntp.enabled='1'`,
   `ntpd.ntp.enable_server='1'`)
3. Disabled Teltonika `ntpclient` via UCI (`ntpclient.ntpclient.enabled='0'`)
4. Disabled Teltonika `untpd` via UCI (`ntpserver.general.enabled='0'`)
5. Disabled Teltonika `ntp_gps` via init.d (no separate UCI enabled flag)
6. Verified honest stratum reporting and ~12ms accuracy from salmon
7. Verified correct behavior after reboot (stratum 16 while unsynchronized)

**Salmon:**
8. Added `/etc/chrony/sources.d/project11.sources` with operator router
   as source and BizzyBoat router + gabby as monitor-only sources
9. Verified operator router appears as valid chrony source after reboot

#### Remaining Work

- [x] Reboot test — ISC ntpd starts on boot, reports honest stratum ✓
- [ ] Second reboot test — verify UCI disable of ntpclient/ntpserver persists
- [ ] Apply same ntpd setup to BizzyBoat's RUTX11
- [ ] GPS refclock integration (future task, needs outdoor testing)
- [ ] Monitor firmware update impact on configuration
- [ ] Consider enabling `save` (persist time to flash) as additional safeguard

