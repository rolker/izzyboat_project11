# 2026-08-19 — pandy log (BizzyBoat pre-deployment, Shoals survey prep)

Deployment issue: none open — this is pre-deployment (phase [0]) prep ahead of the
Isles of Shoals survey. Work stream tracked in
[`docs/roc_operator_setup_2026-08-19.md`](../../roc_operator_setup_2026-08-19.md).
Host: pandy
Side: field (origin `git@gitcloud:field/unh_echoboats_project11.git`)
Started: 2026-08-19 15:49 -04:00

Scope of this log: standing pandy up as the primary ROC operator station for
BizzyBoat, mirroring salmon (which stays untouched as warm standby).

## 2026-08-19

**2026-08-19 15:49 -04:00** — Workspace manifest bootstrapped on pandy. salmon's
`configs/project_bootstrap.url` still points at the GitHub `unh_marine_autonomy`
manifest, but salmon's actual checkout is the gitcloud site manifest — the URL
documented in `ccomjhc_project11/documentation/SettingUpOperatorStation.md`. Used
that: `BOOTSTRAP_URL=http://gitcloud/field/ccomjhc_project11/raw/branch/jazzy/config/bootstrap.yaml`,
giving manifest repo `ccomjhc_project11` (branch `jazzy`, site layer). All 7 layers
imported: 44 repos, verified by diff against salmon to be the identical repo set on
identical branches.

**2026-08-19 15:49 -04:00** — Remote-alias difference from salmon, deliberate: salmon's
project-repo remotes use `gitcloudap`, which has no DNS entry from pandy's current
network. pandy's remotes use `gitcloud` (10.242.5.191, reached over ZeroTier). Worth
revisiting if pandy is ever operated from a network where the AP alias is the
correct path.

**2026-08-19 15:55 -04:00** — System dependencies: 91 packages missing, installed by
operator via apt. One rosdep gap found — `rqt_marine_sonar` declares
`libqt5opengl5-dev`, which has **no rosdep key on noble**, so a plain
`rosdep install` over the workspace fails outright on it. The apt package itself
exists and installs fine. Workaround in use: install it directly and pass
`--skip-keys libqt5opengl5-dev`. This will block anyone bootstrapping a fresh
24.04 operator station the documented way — candidate follow-up against the
manifest or `rqt_marine_sonar`.

**2026-08-19 15:59 -04:00** — `make build` started (all layers, `--symlink-install`).

**2026-08-19 16:13 -04:00** — Build green: all 7 layers, 121 packages, 0 failures
(underlay 22, core 40, platforms 12, sensors 19, simulation 10, ui 17, site 1).
`bizzyboat_project11` installed and resolvable, with `operator_core_launch.py`,
`operator_ui_launch.py`, `bag_recorder_operator_launch.py` and
`network_monitor_operator_launch.py` all present. Matches salmon's 121-package
count from its 2026-08-05 rebuild.

**2026-08-19 16:15 -04:00** — `make sync` clean no-op — all 44 repos already at
current HEAD on their manifest branches, nothing dirty or diverged (expected;
they were cloned ~25 min earlier).

**2026-08-19 16:20 -04:00** — Shell environment mirrored from salmon into pandy's
`~/.bashrc` (backup at `~/.bashrc.bak-*`): `source ~/project11/.agent/scripts/setup.bash`,
`ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`, `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`,
`ROS_S57_ENC_ROOT=${HOME}/data/ENC_ROOT`. salmon's CUDA / nvidia-offload lines
deliberately not copied — host-specific hardware.

**2026-08-19 16:20 -04:00** — `rosdep init` + `rosdep update` run by operator, so
plain `rosdep` now works on this host. (Workspace bootstrap had been marked
skipped via `make skip-bootstrap`, since ROS 2 Jazzy, colcon, vcstool and tmux
were already installed on the machine.)

**2026-08-19 16:23 -04:00** — Name resolution: **no local `/etc/hosts` entries added,
by operator decision.** The ROC operator router serves DNS and already carries the
relevant fleet names (the pandy static lease and `pandy.op` / `pandy.vpn.bizzy` /
`pandy.cell.bizzy` / `pandy.zt` names deployed to both routers on 2026-08-19, per
`roc_operator_setup_2026-08-19.md`). Operator-reported verification from pandy:
ping and ssh to gabby over the VPN both succeed. Not independently re-checked in
this session.

**2026-08-19 16:23 -04:00** — ENC chart data deliberately **not** downloaded to
`~/data/ENC_ROOT`, pending the automated path. Note the two consumers are
distinct: `ROS_S57_ENC_ROOT` feeds the runtime `s57_grids/grid_publisher` reading a
raw ENC corpus, whereas `enc_updater` (new in core as of salmon's 08-05 sync) is
offline cron tooling driven by its own `region.yaml` `corpus_dir`, regenerating the
bathymetry store's `chart` layer with a nav-down interlock. If `enc_updater` is the
path adopted for the ROC, no manual ENC download is needed and the env var stays
inert. `~/data/ENC_ROOT` does not currently exist on pandy.

**2026-08-19 16:23 -04:00** — Gap found for field-side deployment mode on this host:
**`git-bug` is not installed on pandy.** `.agents/deployment.yaml` makes
`field_pull` / `field_list_open` / `field_show` hard-required on the field side
(no `gh` fallback), and all three are `git bug` invocations — so `/start-deployment`
would stop at issue lookup here. The workspace bootstrap step that installs git-bug
was skipped on this machine. Needs installing before pandy runs a live deployment
session.

## 2026-08-20

**2026-08-20 09:20 -04:00** — Operator-stack readiness review on pandy before
running anything. Build/env side is sound: every package the operator tree pulls
in resolves (`bizzyboat_project11`, `marine_autonomy`, `udp_bridge`, `camp`,
`rqt_operator_log`, `mikrotik_monitor`, `teltonika_monitor`, `starlink_stats`,
`network_tools`), and `ros2 launch bizzyboat_project11 operator_core_launch.py
--show-args` composes the whole include tree without error. Both boat paths are
up from here: `gabby.vpn.bizzy.p11.lan` 39 ms, `gabby.cell.bizzy.p11.lan` 44 ms,
0% loss. Joysticks present (`js0`, `js1`); CAMP's background chart
(`camp/workspace/13283/13283_2.KAP`) is installed. ENC absence blocks nothing —
neither operator launch starts an s57 node.

**2026-08-20 09:35 -04:00** — Blocker found and fixed: `config/operator.yaml` was
salmon's file — `return_host: salmon.*` on all three connections, plus a `wifi`
connection to `gabby.bizzy.p11.lan` (192.168.20.5), confirmed unreachable from the
ROC. `return_host` is not a local setting: udp_bridge ships it to the boat, which
then transmits there (`remote_node.cpp:79`). Launching as-is from pandy would have
sent the downlink to salmon.

Deleting `return_host` and relying on the boat learning our source address does
**not** work, and the reason matters for any future station changeover: the
learned-address fallback applies only when the boat-side connection is *created*
(`remote_node.cpp:66-80`). An existing connection is re-pointed only when
`return_host` is non-empty. A boat whose bridge has been up since the previous
station's session would keep transmitting there, with no error at either end.

Fixed station-agnostically rather than with a pandy variant (commit `eaf8976`):

- `wifi:=false` (default `true`) layers a new `config/operator_no_wifi.yaml`,
  which shortens `connections_list` to `[vpn, cell]`. udp_bridge iterates only
  the listed connections (`udp_bridge.cpp:376-383`), so the `wifi` block is never
  read and nothing is duplicated — topic lists and byte budgets stay in
  `operator.yaml` and are inherited. The boat needs no change: its own `wifi`
  connection carries no host and only learns one from an inbound packet.
  Named for the condition, not the site, per operator decision — salmon has
  operated without wifi too, and the same argument governs the ping targets,
  the mikrotik monitor and the annunciator's wifi indicators.
- `return_host` derived from the station's short hostname per `dns_naming.md`
  rule 8 (`<host>.op` / `<host>.vpn.bizzy` / `<host>.cell.bizzy`), overridable
  via `return_host_prefix`, and logged at startup — a wrong return host is
  otherwise invisible from the operator end. On salmon the derivation reproduces
  the removed literals exactly, so behaviour there is unchanged.

Four regression tests cover the derivation, the salmon-literal equivalence, the
conditional overlay ordering, and the never-empty invariant. Package tests green
(43 tests, 0 failures).

**2026-08-20 09:50 -04:00** — rqt perspectives were missing on pandy entirely
(`~/.config/ros.org/` did not exist). `operator_ui_launch.py` starts four rqt
processes by perspective *name*; an unknown name does not error — qt_gui creates
an empty perspective (`perspective_manager.py:159-161`) — so all four windows
would have come up blank with no warning.

They are not files on salmon: all 39 of salmon's perspectives live inside
`~/.config/ros.org/rqt_gui.ini` (3.4 MB of QSettings, accumulated over years).
Extracted the four that matter (`bizzyboat`, `bizzyboat-diagnostics`, `logger`,
`bizzy_sonar`) using qt_gui's own export serialisation, and imported them into
pandy under their real names — deliberately *not* via `--perspective-file`, which
recreates the perspective from disk on every launch (`main.py:625-629` +
`perspective_manager.py:350-355`) and would discard in-session layout changes.
Verified by re-exporting from pandy's settings: all four byte-identical to
salmon's. `rqt_gui --list-perspectives` shows all four; all eight referenced
plugin packages are installed here. Window geometry came across as salmon had it,
so placement across pandy's four monitors is a manual first-run adjustment.

Versioning them in the repo is deferred by operator decision until the layouts
have been tweaked here.

**2026-08-20 09:55 -04:00** — Finding that supersedes part of the ROC handoff:
**the annunciator's configuration lives inside the rqt perspective, not in
`config/bizzyboat_operator_annunciator.yaml`.** Each plugin instance carries the
full indicator list as an embedded `config_yaml` string. Salmon's
`bizzyboat-diagnostics` runs two instances, and both are **already VPN-only** —
boat-side (Bizzy Starlink, Ping Gabby VPN, Ping Boat Router VPN, Internet DNS,
UDP VPN, Battery, FCU System, Sound Speed) and op-side (Op Starlink + the four
network rows). There are no WiFi indicators to remove, so handoff item 3 is
effectively already done.

The repo's `bizzyboat_operator_annunciator.yaml` — which still carries
`Op WiFi Bridge`, `Ping Gabby (WiFi)`, `Ping Boat Router (WiFi)` and `UDP WiFi` —
is dead config. `2026-05-22_salmon_logs.md:526` already recorded the suspicion
that it is not loaded; this confirms it, and line 791 of that log has "Annunciator
YAML cleanup" sitting in a backlog. What the ROC actually needs is different from
what the handoff predicted: `Op Starlink` (`Starlink: starlink.op`) has no dish at
the ROC (192.168.100.1 unreachable) so that row goes permanently stale, and there
are no cell-path indicators at all despite cell being one of the two live paths.

**2026-08-20 10:00 -04:00** — AIS check at operator request: **live AIS is
arriving on pandy's udp/2125 and is being dropped on the floor.** 15 sentences in
15 s from `10.242.80.203` (ZeroTier, no reverse DNS); decoded over 20 s: 10
distinct MMSIs, message types 1/3 (Class A position), 18 (Class B), 21 (AtoN), 24
(static) — mostly US MIDs plus one Cayman-flagged vessel and two aids to
navigation. Real current traffic, not a replay.

Nothing is bound to 2125 (`ss -ulnp` empty before the test socket), and the
operator stack would not pick it up if it were running: CAMP subscribes to ROS
`marine_ais_msgs/AISContact` topics (`camp/ais/ais_manager.cpp:36`), not UDP. See
the new task in `roc_operator_setup_2026-08-19.md` for the gap and what closing
it needs.

Loose thread: `ccomjhc_project11/scripts/ais_sender.py:34-36` hardcodes its
ZeroTier destinations (`snowpetrelz`, `penguinz`, `pandora`) and lists neither
pandy nor salmon — yet pandy is receiving. The deployed sender has drifted from
the committed copy. Worth reconciling; the repo copy is currently misleading
about who gets the feed.

**2026-08-20 10:25 -04:00** — Network monitoring gated on station equipment
(commit `12142f3`). Three of the four operator-side monitor nodes poll hardware
the ROC does not have; a launch here produced four permanently failing
diagnostics and two dead ping targets.

`network_monitor_operator_launch.py` now takes `wifi` and `op_starlink`
(both default `true`), forwarded from `operator_core_launch.py`. `wifi:=false`
skips the mikrotik monitor — `bizzy.wifi.op.p11.lan` is absent at the ROC, not
temporarily unreachable — and selects `ping_targets_operator_no_wifi.yaml`.
`op_starlink:=false` skips the Starlink node. Kept as two arguments rather than
one: the ROC lacks both a bridge radio and a dish, but those are independent
facts about a station's equipment.

Ping targets gained the cell path (`gabby_cell`, `router_bizzy_cell`, both
verified reachable from here). The cell link had no health signal anywhere
despite being one of the two redundant paths to the boat. The no-wifi list is a
full copy minus the two direct targets, not an overlay — `ping_monitor` takes
`targets` as a flat string array, so a second file replaces the list rather than
shortening it; a test pins the two files to that relationship so they cannot
drift.

Sweep timing is why the variant matters rather than tolerating red rows: pings
are sequential and an unreachable target costs `ping_count * ping_timeout`
(~15 s) against an auto stale timeout of `3 * poll_interval` (30 s). Two
unreachable targets are enough to flip healthy ones to STALE.

**2026-08-20 10:30 -04:00** — Annunciator updated in pandy's
`bizzyboat-diagnostics` perspective (operator gave the go-ahead to edit it
directly). Added `Ping Gabby (Cell)`, `Ping Boat Router (Cell)` and `UDP Cell`
to both instances, and replaced the op-side `Op Starlink` row with `Op Router`
(`Teltonika: router.op: connection`) — with no dish at the ROC the Starlink node
does not run, so that row would have sat stale forever, while `router.op` is the
ROC's actual uplink and teltonika_monitor already polls it. Diagnostic name
formats verified against source before adding
(`udp_bridge.cpp:1954`, `ping_monitor_node.py:92-117`,
`teltonika_monitor_node.py:142-186`) so none of the new rows is a name that will
never appear. Everything outside the two `config_yaml` values is byte-unchanged.

Instance 1 (boat): Bizzy Starlink, Ping Gabby VPN/Cell, Ping Boat Router
VPN/Cell, Internet DNS, UDP VPN/Cell, Battery, FCU System, Sound Speed.
Instance 2 (station): Op Router, Ping Gabby VPN/Cell, Ping Boat Router VPN/Cell,
Internet DNS, UDP VPN/Cell.

**2026-08-20 10:24 -04:00** — Created `~/data/logs/operator` on pandy. The
operator bag recorder writes `~/data/logs/operator/<date>/bags/` and
rqt_operator_log is configured for `/home/field/data/logs/operator`; neither
existed. Plain directory on the root filesystem (410 GB free) — relocate or
symlink if operator bags should live on another disk.

**2026-08-20 11:10 -04:00** — One-command bring-up replicated from salmon
(commit `717ff4b`). Salmon symlinks `start_tmux_operator_project11.bash`,
`stop_tmux_project11.bash` and `screenshooter.bash` into `~`, pointing into the
source tree so edits take effect without a rebuild; pandy now has the same three.

The script launched `operator_core_launch.py` with no arguments, which since
`12142f3` is only correct at a station that has both a bridge radio and a dish.
Rather than forking it, it now sources `~/.config/project11/station.env` if
present and appends `$OPERATOR_LAUNCH_ARGS` / `$OPERATOR_UI_LAUNCH_ARGS`,
echoing both so the tmux log shows what was picked up. Arguments passed to the
script are appended after the file's, for one-off overrides.

The env file is deliberately outside the repo — a station's equipment is a fact
about the machine and where it sits, not about BizzyBoat, and committing one
station's would hand it to every other. Stations without the file get the
defaults, so salmon's behaviour is byte-identical. `config/station.env.example`
documents the options and ships with the package.

pandy's file sets `OPERATOR_LAUNCH_ARGS="wifi:=false op_starlink:=false"`.
Verified by dry run against a tmux shim: with the file the core launch receives
both arguments; with `STATION_ENV` pointed at a nonexistent path it falls back
to the bare command salmon runs today.

**2026-08-20 11:33 -04:00** — **First operator-stack bring-up on pandy**, via
`~/start_tmux_operator_project11.bash`. Deliberately a dry run: salmon is powered
up but not running the stack, and gabby's stack is not running either, so
nothing could perturb the boat's return path while every station-side path was
still exercised for real.

Everything under test verified:

- `[INFO] [launch.user]: operator station return hosts: pandy.vpn.bizzy.p11.lan
  (vpn), pandy.cell.bizzy.p11.lan (cell)` — the derivation resolves to this
  station.
- udp_bridge reports **only** `bizzy: vpn` and `bizzy: cell` connections. No
  wifi connection exists, so the `wifi:=false` overlay is doing what it should.
- All six ping targets OK, including the two new cell ones — `gabby_cell`
  43.3 ms, `router_bizzy_cell` 46.3 ms. `gabby_direct` and `router_bizzy_direct`
  are absent, confirming `ping_targets_operator_no_wifi.yaml` is the list in use.
- `mikrotik_monitor` and `starlink_diagnostics` are **not** in `ros2 node list` —
  the equipment gating works.
- `Teltonika: router.op: connection` = OK "reachable", `system` = RUTX11. The
  `Op Router` row that replaced `Op Starlink` works, which was the least-proven
  thing in the annunciator change.
- All four rqt perspectives loaded (`-p bizzyboat`, `-p bizzyboat-diagnostics`,
  `-p logger`, `-p bizzy_sonar`) plus CAMP. (`ros2 node list` shows only
  `rqt_diagnostics` by name — the perspectives hosting C++ plugins register as
  `rqt_gui_cpp_node_*`; all four processes are running with the right `-p`.)
- Bag recorder writing to
  `~/data/logs/operator/2026-08-20/bags/operator_2026-08-20T11.33.06/`.

Incidental: teltonika reports `interface/bizzy_wifi_bridge Up` on router.op while
the radio itself (`bizzy.wifi.op.p11.lan`, 172.16.20.4) stays unreachable — the
router-side interface is up, the far end is out of range. Consistent with the ROC
situation and a reminder that the router interface is not evidence of a link.

**Finding — the UDP connection rows are green with no peer.**
`udp_bridge operator: bizzy: vpn` and `: cell` both report **OK**, "tx 858 B/s,
rx 0 B/s", with gabby's stack down. The connection diagnostic reflects transmit
health, not whether anything is answering, so `UDP VPN` / `UDP Cell` on the
annunciator are green while no boat data exists at all. I had predicted these
would go red; they do not.

This matters for annunciator trust in the other direction from the WiFi rows: a
row that is green when the link is dead is worse than one that is red when it is
alive. An operator glancing at the panel cannot distinguish "link healthy" from
"boat stack down". Candidate fixes: WARN on sustained `rx 0 B/s` while tx is
flowing, or an annunciator row keyed on something that requires bidirectional
traffic (heartbeat age). Filed as a follow-up rather than changed mid-session —
it touches shared udp_bridge behaviour that salmon and the boat also rely on.

**2026-08-20 12:05 -04:00** — AIS wired into the operator stack (`fb90cdd`,
bizzyboat_project11) and a heading bug fixed in the parser (`9aa53be`,
marine_ais).

The feed was arriving on udp/2125 and being discarded: nothing bound the port,
and CAMP does not read UDP — it scans the graph every second for any topic of
type `marine_ais_msgs/AISContact` and subscribes to what it finds
(`camp/ais/ais_manager.cpp:18-43`). `launch/ais_launch.py` runs the three nodes
that bridge it (`nmea_relay` -> `ais_parser` -> `ais_contact_tracker`), included
from `operator_core_launch.py` under `ais:=true`. marine_ais_tools' own launch
file could not be used as-is: it omits `ais_contact_tracker`, the only node that
publishes AISContact, and its parameters default to serial `/dev/ttyACM0` so the
socket would never bind. Both failures are silent.

**Operator-reported bug, confirmed and fixed**: contacts were drawing as
pointing east. AIS encodes "true heading not available" as 511, which the
decoder correctly turns into None, but `ais_parser.py` then skipped its
orientation block — and leaving `geometry_msgs/Quaternion` untouched is not
neutral. It defaults to the *identity* (0, 0, 0, 1), a valid orientation meaning
yaw 0, which is due east in ENU. On the live feed that was 16 of 18 contacts,
including every Class B report, every static report and all three aids to
navigation.

The consumer side was already correct and merely waiting to be told: CAMP tests
`length2() > 0.1` before believing an orientation
(`camp/ais/ais_contact.cpp:45-58`), falls back to course over ground when the
contact is moving, and `ShipTrack::drawTriangle` draws an ellipse for a NaN
heading (`ship_track.cpp:13-23`). The parser now emits a null quaternion, which
matches its own convention (it already writes NaN for unknown position,
altitude, rate of turn and speed). Regression test verified to fail without the
fix. Operator confirmed the display afterwards.

**2026-08-20 12:20 -04:00** — **First ROS traffic between pandy and BizzyBoat.**
gabby's stack came up and 72 `/bizzy/...` topics appeared. Boat-side diagnostics
are reaching the operator (`mavros: Battery` Normal, `GPS` 3D fix, `Heartbeat`
Normal, `sound_speed_bridge` OK, `Starlink: starlink.bizzy` 0.0% drop / 22 ms /
0.01% obstructed), so the annunciator's boat rows populate. This closes the gap
that had stood since the station was built: everything before this was tested in
isolation.

Link rates: vpn `tx 7457 B/s, rx 420718 B/s`; cell `tx 7586 B/s, rx 122907 B/s`.

**Finding — `wifi:=false` does not stop a wifi connection from existing.** A
third connection appeared once gabby's bridge came up:

```
udp_bridge operator: bizzy: wifi    WARN  tx failures/drops
   host                 192.168.23.5      <- gabby.cell.bizzy.p11.lan
   tx_ok_bytes_per_sec  6931.15
   rx_bytes_per_sec     0
```

Dropping `wifi` from the operator's `connections_list` only stops the *operator*
configuring one. The boat's `bizzyboat.yaml` still lists `wifi` in its own
operator remote, and `RemoteNode::update` creates a connection for every
connection the remote advertises, filling the host from the learned source
address (`remote_node.cpp:66-80`). The learned source was a packet that arrived
over the cell NETMAP, so the operator now transmits ~6.9 KB/s to the cell
address under the label "wifi" — a redundant uplink stream on the more
constrained of the two links, mislabelled as the path that does not exist here.
Not fatal, but it eats cell uplink budget and makes the diagnostic lie about
which path is in use. Needs a decision: boat-side config, an operator-side way
to refuse unconfigured connection ids, or accept it.

**Observation — resend give-up rate is not trustworthy as reported.** The
give-ups task showed `give_ups_total 247006`, `give_up_rate_per_s 18555.8`,
`window_s 0.000754481`, while summarising as OK — the rate is computed over a
sub-millisecond window, so it swings between 0 and five orders of magnitude
above the 50/s error threshold depending on when it is sampled. The totals are
worth understanding on their own, but the rate as published cannot drive an
alarm.

**Observation — vpn duplicates are the redundancy, not a fault.** vpn reports
`rx 431207 B/s` with `rx_duplicate 122091 B/s`, and cell reports
`rx 122907 B/s`. The duplicate rate tracks the cell receive rate almost exactly:
the boat sends the same topics down both paths and the second copy to arrive is
counted as a duplicate. Expected behaviour for the redundant-path design, worth
recording so it is not re-diagnosed as loss.

**2026-08-20 19:31 -04:00** — **ONGOING: recurring 5-16 s stalls of all
boat-originated data.** Operator reported video delayed and the sonar displays
frozen; the freeze they saw was 13.7 s at 19:17:33. Eight such stalls between
19:02 and 19:30, durations trending upward.

Ruled out from this end: not the operator station (pandy's own udp_bridge
published 2602 statistics messages with zero gaps over 3 s in the same window),
not the Starlink link (`0.0% drop, 18-22 ms, 0.01% obstructed` throughout), and
not a boat-side restart (no `Assuming remote udp_bridge restart`, unlike the
14:09 event).

The finding that matters: ICMP loss to gabby appears on a **different path each
time** — vpn 50% loss at 19:17 with cell clean, cell 25% loss at 19:23 with vpn
clean — and **both** bridge connections stop regardless. vpn and cell are
independent bearers, so a fault in one cannot explain the other going silent.
Working hypothesis is head-of-line blocking in the boat's udp_bridge sender,
stated as a hypothesis because it cannot be confirmed from pandy.

Full evidence, method and the gabby-side checks in the deep-dive:
[`2026-08-20_pandy_link-stalls_logs.md`](2026-08-20_pandy_link-stalls_logs.md).
Needs someone on the boat.

**2026-08-20 20:19 -04:00** — **Automated chart updates working on pandy.**
This closes the item parked on 2026-08-19, when ENC data was deliberately not
downloaded by hand pending "the auto stuff". The auto stuff is
`enc_updater` in `s57_tools` — actively developed, with merges landing today
(`ff11faa`, `e9e3413`) — and it now runs here.

Ran `--dry-run` first (which is a real download, export, stage and validate; it
only skips the interlock and the swap), then a committing run. Both exit 0.

- 13 cells selected from the region bbox `[-70.85, 42.93, -70.55, 43.11]`
  (the shipped New Castle / Isles of Shoals example; covers the Shoals and the
  Piscataqua): `US4NH1BC/BD`, `US5NH1AD/AE/AF/AG/CD`, `US5PSMBC/BD/BE/CC/CD/CE`.
- Datum grids auto-provisioned: geoid `us_noaa_g2018u0` (SHA-256 pinned) and
  the `MENHMAgome23_8301` VDatum bundle — **312 MB**, the bulk of the transfer.
- Exported 12 of 13. `US4NH1BC` has no in-datum data (all pixels no-data) and
  wrote an empty tif with a warning — a band-4 approach cell that does not
  overlap the vertical-datum coverage. Benign, but it is the kind of warning
  that should not be allowed to become background noise.
- Chart layer swapped into `~/data/world/store`: **85 MB**, GGGS levels 6-8.

Config at `~/.config/enc_updater/region.yaml` (per-machine, not in the repo —
same reasoning as `station.env`).

**PRUNING — operator was not aware of this, flagging it prominently.**
`enc_updater` treats `corpus_dir` as **its own**: every run removes cells that
are not in the current region/catalog selection. That is deliberate (the D7
export runs over the whole corpus, so a stale cell would keep feeding tiles
into every future chart layer) and it is documented, but it means the tool
DELETES from that directory. Anything hand-placed there will disappear on the
next run. Pruning is skipped under `--dry-run`, is refused if a still-Active
cell has unparseable coverage, and runs only after a successful download pass —
but the ownership is the point: **do not point `corpus_dir` at a directory that
holds anything you put there yourself.**

**Corpus location — moved, `~/data/ENC_ROOT` retired.** It was first set to
`~/data/ENC_ROOT` to share one corpus with `ROS_S57_ENC_ROOT`; the operator's
plan to retire that path made the location wrong, so at 20:24 the corpus moved
to `~/data/world/charts/ENC_ROOT` (the path the shipped
`region_example.yaml` uses). Three changes, all on this machine only:
`corpus_dir` in the config, the 5.7 MB corpus itself, and
`ROS_S57_ENC_ROOT` in `~/.bashrc` (backup alongside). The sharing arrangement
is unchanged — one corpus, two consumers — only its location moved.

Verified by re-running the updater afterwards: `no upstream change — nothing to
do`, exit 0. The manifest travelled with the corpus and change detection
matched the store's edition registry, so nothing re-downloaded. `~/data/ENC_ROOT`
no longer exists.

This also lines pandy up with where gabby is going: their
`scripts/build_bathy_store.sh` moved its defaults to `~/data/world/depths` and
`~/data/world/imagery/backscatter` the same day. The layout on this machine is
now `~/data/world/{charts/ENC_ROOT, datum, store}` — 5.7 MB corpus, 312 MB
datum grids, 85 MB chart layer.

**Store-dir guard, worth knowing.** The first run failed with `cannot create
store dir ... parent must already exist (is the data volume mounted?)`. That is
the tool working correctly: it creates the store leaf but refuses to invent the
parent, so an unmounted data volume fails loudly instead of silently building a
chart layer on the root filesystem. `~/data/world` had to be created by hand.

**Interlock is NOT configured here**, and the tool says so on every run:
`nav-liveness interlock not configured (nav_liveness.nodes is empty) —
skipping probe`. Acceptable on the operator station, where the chart layer
feeds CAMP's display. An empty list means **no** interlock, not a lenient one —
any machine where the chart layer feeds a nav stack must list its nav nodes.

**Not scheduled.** `crontab -l` is still empty. Running it by hand first was
the operator's call and the right one.

**Doc bug in `enc_updater/README.md`**: both the usage block and the cron
example invoke a bare `enc_updater`, but the entry point installs to
`lib/enc_updater/` and is not on PATH. The correct form is
`ros2 run enc_updater enc_updater --config ...`. The published cron line would
fail with "command not found" — worth fixing upstream before anyone copies it.

### Outstanding for pandy before the survey

Updated 2026-08-20. Done items struck from the handoff list in
`roc_operator_setup_2026-08-19.md`; see that doc for the current task list.

- **udp_bridge config** — done (`eaf8976`), station-agnostic rather than as a
  pandy variant. Not yet exercised against the boat.
- **rqt perspectives** — imported on pandy from salmon; layout tweaks and
  version-control still to come.
- **Annunciator** — already VPN-only in the live perspective; the ROC gaps are
  the stale `Op Starlink` row and the absent cell-path indicators.
- **Network monitors** — done (`12142f3`) and verified live 2026-08-20,
  `Op Router` included.
- **Follow-up**: udp_bridge connection diagnostics report OK with `rx 0 B/s`
  (see the 11:33 entry) — the annunciator's UDP rows are green with no peer.
- **Follow-up (operator request)**: add rviz to the operator UI launch.
- **Schedule enc_updater** once the corpus move is settled. The nav-liveness
  interlock needs thought at the ROC: pandy sees `/bizzy/...` nodes whenever
  the bridge is up, so a nightly slot with nodes configured would refuse on any
  evening the boat is running (the README calls this the "Exit 2 every night"
  symptom).
- **Fix the `enc_updater` README PATH/cron bug** in `s57_tools` (see above).
- **OPEN, needs gabby**: recurring 5-16 s stalls of all boat data, escalating —
  see `2026-08-20_pandy_link-stalls_logs.md`.
- **AIS into CAMP** — live traffic on udp/2125 is currently discarded; see the
  AIS task in `roc_operator_setup_2026-08-19.md`.
- `git-bug` install (see 2026-08-19 entry) — `/start-deployment` stops at
  field-side issue lookup without it.
- `pre-commit` cannot run here: `python3.12-venv` is not installed, so `make lint`
  fails at `ensurepip`. Both commits made from pandy so far went in unhooked, with
  the markdown/YAML hooks hand-checked instead.
- ssh key auth to the boat from pandy (`ssh-copy-id`) — salmon has the alias set
  up, pandy may not. (ssh pandy→salmon with key auth is confirmed working.)
- Dockside/pre-departure rehearsal from the ROC: full bridge load from pandy plus a
  concurrent RDP session to mercat, watching udp_bridge resend rates against the
  vpn/cell budgets.

**Verified 2026-08-20**: pandy exchanges ROS traffic with BizzyBoat over both
the vpn and cell paths, with boat-side diagnostics populating the annunciator.
Still untested: sustained load under way, resend behaviour against the byte
budgets over a full survey, and a concurrent RDP session to mercat. The bridge
must not run here while salmon's is up — the boat transmits to whichever station
last advertised a return host.
