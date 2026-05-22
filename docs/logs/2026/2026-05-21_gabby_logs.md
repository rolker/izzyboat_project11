# BizzyBoat deployment log — gabby — 2026-05-21

**Host**: gabby
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Deployment**: [#149](https://github.com/rolker/unh_echoboats_project11/issues/149) — *Deployment 2026-05-21: validate small-wins PRs + udp_bridge WARN demote + FCU EK3 Z-source reconfig* (git-bug `7d5b52c`; field-host shared one-way via gitcloud at write-time; GitHub link added dev-side at wrap-up)

## Summary *(agent-drafted, Roland to revise to user voice)*

Deployment delivered both primary headline objectives:
**#138 FCU reconfig** (`EK3_SRC1_POSZ` → 3) made
`mavros/global_position/global` chart-datum-compatible
bench-side (§6) and held under load (§8 GOTOs), enabling
the long-pending `mru_transform` switch off the 2026-05-19
field revert (§10–13). `tide_estimate` is now publishing in
the plausible band with the lever-arm chain wired correctly;
forecast residual dropped from +1.61 m to +0.91 m, the
remaining gap consistent with the unresolved
base_link-to-waterline freeboard. **`udp_bridge#24`** went
end-to-end: per-event "Giving up on resend" WARNs went
27,992-in-2h (2026-05-19) → **0 across the entire 2.5 h
session today** (§7, §17, §18, §21), with per-remote
`DiagnosticStatus` surfacing comm state at the right
granularity (validated cleanly through the §18 wifi-loss
transition into Starlink-only ops at ~520 m). Side findings:
the `mru_transform → /global` switch unmasked a Nav2
lifecycle startup race (§15, mitigation: full launch-group
relaunch) and the longstanding **`unh_marine_perception#6`
SeaSurfaceLayer matchSize segfault** is **not closed** by
#11/#13 — it fires only with multi-instance layer config
(§16's 1-vs-4 contrast is the strongest diagnostic data
point we've had on this bug). Brief's RC mode-switch
mitigation didn't get applied (§19) — RC controller
fought autonomous control on the OTH trackline; candidate
annunciator for the wrap-up follow-up.

## Lessons Learned *(agent-drafted, Roland to curate)*

- **Today's `mru_transform → /global` switch unmasks
  bugs that the 2026-05-19 revert had been hiding.** The
  lever-arm sign issue (§9 hypothesis) turned out to be
  *no lever arm at all* (§10); the matchSize segfault
  (§16) had been latent because chart-datum mismatch was
  forcing `sea_surface_estimator` to suppress everything;
  the startup-TF race (§15) was harder to trip when
  `raw/fix` came up faster. Today's chain swap is the
  right durable choice, but every downstream consumer of
  `tide_estimate` / `map_tide` got tested for the first
  time at field conditions today.
- **Brief gates that aren't bench-tested before launch
  bite on the water.** The "bench smoke: launch
  controller_server with all 4 OAK layers; confirm no
  segfault" gate from Block 2 was skipped; the segfault
  showed up mid-deployment instead. Hard to retrofit
  bench-side once the boat is wet.
- **Carry-forward cautions are doc-only until someone
  enforces them.** The RC mode-switch mitigation was the
  brief's named caution; nothing prompted at the
  pre-launch → autonomous transition; the controller
  stayed on. A diagnostic that's loud enough to make the
  operator say "no, this is wrong" would have caught it.
- **The udp_bridge#24 work is a model for diagnostic
  redesign**: replace high-volume WARN spam with a
  structured per-remote `DiagnosticStatus`. Today's bag
  has the cleanest comm-state record of any deployment
  to date, and the WARN log isn't a wall of noise. Worth
  replicating in other comm/quality monitors.
- **Memory persistence gap on field hosts**: the
  SSH-agent / `git-bug pull` workaround had to be applied
  for the second deployment in a row (§1). The 2026-05-19
  follow-up to institutionalise the agent didn't land in
  time; this one's worth a follow-up issue with teeth.
- **Locate-the-buzzer before decoding-the-buzzer.** §3 burned
  ~15 min trying to decode an FCU buzzer pattern that
  turned out to come from two ESC-like sources near the
  thrusters (§22), not from the FCU at all. My
  AP_Notify-pattern search wasn't wrong; it was applied to
  the wrong device. Always confirm physical source before
  decoding a pattern.

## 1. git-bug pull — same SSH_AUTH_SOCK gap as 2026-05-19

**2026-05-21T11:25-04:00** — Roland asked to check git-bug for today's
deployment issue. `git bug bug --label deployment --by edit` returned only
the three prior deployments (closed 04-27, 04-29, and the still-open
2026-05-19 `e3c373a`); no 2026-05-21 entry. Tried `git bug pull` to fetch a
freshly-opened issue from gitcloud:

```
Error: error creating SSH agent: "SSH agent requested but SSH_AUTH_SOCK not-specified"
```

**Same failure mode as 2026-05-19 section 1.** This `claude` process was
launched from a shell without `SSH_AUTH_SOCK` exported, so the per-repo
git-bug remote (SSH-based) can't authenticate. The persistent fix
(systemd user `ssh-agent.service` / keychain / start agent before
launching `claude`) noted as follow-up after the last deployment does not
appear to have landed yet.

**2026-05-21T11:30-04:00** — Roland confirmed: apply the same inline
workaround used 2026-05-19. Ran (single Bash invocation, no
interactive passphrase needed — gitcloud key has none):

```bash
eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519_gitcloud
git -C <unh_echoboats_project11> bug pull
ssh-agent -k
```

Pull succeeded: 10 new bug events + 2 updated (`0507eda` lever-arm
contract refresh; `e3c373a` 2026-05-19 deployment issue closed).

**2026-05-21T11:31-04:00** — Today's deployment issue now visible:
`7d5b52c` — *Deployment 2026-05-21: validate small-wins PRs +
udp_bridge WARN demote + FCU EK3 Z-source reconfig*. Read in full;
header on this log file updated with the issue reference. Per the
field-host convention, deployment issue is read-only from here — all
observations land in this file.

### Carry-forward

- The 2026-05-19 follow-up — institutionalising the SSH agent so the
  workaround stops being needed — should not slip again. Candidate
  Lessons Learned entry at wrap-up if it bites a third time.
- Only pulled the `unh_echoboats_project11` bug store this time
  (single-purpose pull). Workspace bug store + other project repos
  not refreshed; can repeat the recipe if anything else needs syncing
  during the session.

## 2. FCU param reconfig (#138) — EK3 Z-source switch

**2026-05-21T11:39-04:00** — Boat powered. Roland started MAVProxy
from `bizzyboat_project11/config/fcu/`:

```
~/project11/.venv/bin/mavproxy.py --master=/dev/fcu,57600
```

Running from that directory auto-dumped the live FCU param set to
`mav.parm` (alongside `mav.tlog` / `mav.tlog.raw`). Pre-change state
verified against `mav.parm`:

| Param | Pre-change | Target |
|---|---|---|
| `EK3_SRC1_POSZ` | `1` (baro) | `3` (GPS) |
| `GPS_POS1_X / Y / Z` | `0.835 / 0.000 / -0.890` | unchanged ✓ (from #91) |

`mav.parm` had **no** `EK3_GPS_OFFS_*` entries — the only `EK3_GPS_*`
params present are `EK3_GPS_CHECK` and `EK3_GPS_VACC_MAX`.

### Brief discrepancy: `EK3_GPS_OFFS_*` doesn't exist on this FCU

**2026-05-21T11:42-04:00** — On Roland's first `param set
EK3_GPS_OFFS_X 0.835`, MAVProxy replied:

```
Unable to find parameter 'EK3_GPS_OFFS_X'
```

Cross-checked: neither curated file (`bizzyboat_fcu_custom.param`,
`bizzyboat_fcu_baseline.param`) carries `EK3_GPS_OFFS_*`. ArduPilot
Rover (this firmware) consumes GPS antenna offsets via `GPS_POS1_X/Y/Z`
directly into the EKF — there is no separate `EK3_GPS_OFFS_*` family
to set. `GPS_POS1_*` is already at the brief's "Target" values from
PR #91.

→ The deployment brief's "EK3_GPS_OFFS_*" rows are an error.
**Substantive FCU change today is only `EK3_SRC1_POSZ` → `3`.**
Flagging for dev-side reconciliation at wrap-up (the brief, and
likely #138 itself, want their param table corrected).

### Applied + verified

**2026-05-21T11:44-04:00** — Final actions in MAVProxy:

```
param set EK3_SRC1_POSZ 3
param show EK3_SRC1_POSZ     → EK3_SRC1_POSZ    3.0
param show GPS_POS1*         → GPS_POS1_X 0.8349999785423279
                                GPS_POS1_Y 0.0
                                GPS_POS1_Z -0.8899999856948853
```

Float32 round-trip on the `GPS_POS1_*` values is exactly the stored
`0.835 / 0.000 / -0.890`. `param show` in MAVProxy only takes one
pattern at a time (not a space-separated list) — first attempt with
four names returned just the first param; second attempt split out
correctly.

### Pre-change snapshot to preserve

`mav.parm` written at 11:39 EDT is the pre-change full dump.
MAVProxy will overwrite it on the next session, so a copy should be
parked aside before any subsequent `mavproxy.py` run from this
directory. Pending Roland's preference on filename / location.

### Next: reboot Cube

**2026-05-21T11:46-04:00** — Roland to issue `reboot` in MAVProxy;
wait for FCU to come back (GPS lock + EKF home set) before ROS
bring-up on gabby.

### Post-reboot MAVProxy output

**2026-05-21T11:47-04:00** — `reboot` accepted (`COMMAND_ACK:
PREFLIGHT_REBOOT_SHUTDOWN: ACCEPTED`); `/dev/fcu` dropped and
reopened cleanly. Boot sequence to ready:

- IOMCU CRC ok / startup
- Both barometers (MS5611 on buses 4 & 1) found + calibrated
- AHRS: DCM active → later AHRS: EKF3 active
- GPS 1 specified as DroneCAN1-124 (CUAV C-RTK 2HP on DroneCAN)
- EKF3 IMU0/1/2 — tilt aligned, yaw aligned, origin set
- **"EKF3 IMU0/1/2 is using GPS"** ← `EK3_SRC1_POSZ=3` now in effect
  on all three EKF3 instances (this is the visible confirmation of
  the only substantive FCU change today)
- Field Elevation Set: 3 m

No EKF lane errors, no "stopped aiding", no GPS errors in the
visible window.

## 3. FCU buzzer "short-short-long" pattern reported

**2026-05-21T11:50-04:00** — Roland: *"I hear a beep from the fcu
two short and a longer one."* Logging as operator observation,
then investigating.

### Most likely interpretation

In ArduPilot's audible-notify convention, a **short-short-long**
buzzer pattern is the standard **pre-arm check failure**
indication. Pre-arm checks run continuously (not just at arm
time), so the buzzer keeps playing as long as a check is failing —
this is consistent with hearing it now without having attempted
to arm. The buzzer carries no detail; the *reason* is announced
on the MAVLink STATUSTEXT channel as a `PreArm: <something>`
message.

### Probe (needs Roland — MAVProxy or terminal scrollback)

If MAVProxy is still open, the cause is probably already in the
scrollback as a `PreArm: ...` line — those typically scroll past
during the boot sequence. Two ways to surface it without
restarting MAVProxy:

```
arm check        # lists all currently-enabled pre-arm checks + pass/fail
arm preflight    # forces a full pre-arm cycle and prints failures
```

(If MAVProxy has been quit, the same info is reachable by
re-opening it on `/dev/fcu` for 30 seconds — the STATUSTEXT
banner is announced periodically.)

### What I am **not** claiming

The buzzer pattern is a *probable* pre-arm failure based on
ArduPilot convention; I haven't verified it against this
firmware's `AP_Notify` table, and there's a non-zero chance the
pattern means something else (e.g., a parameter-change-requires-
reboot reminder, though we just rebooted). The `PreArm:` STATUSTEXT
is the authoritative answer.

### Probe — pre-arm checks pass; recurring beep ≠ pre-arm fail

**2026-05-21T11:54-04:00** — Verified MAVProxy `arm` subcommand
syntax against the module source
(`.venv/.../MAVProxy/modules/mavproxy_arm.py`) after I'd suggested
two non-existent variants in a row (`arm check` with no arg,
`arm preflight`). Correct command: **`arm prearms`** (sends
`MAV_CMD_RUN_PREARM_CHECKS`).

Roland ran it; FCU response:

```
Got COMMAND_ACK: RUN_PREARM_CHECKS: ACCEPTED
```

**No `PreArm:` STATUSTEXT lines** followed → pre-arm checks all
passed. My initial "short-short-long = pre-arm fail" reading was
wrong. (Memory updated: verify tool syntax before suggesting REPL
commands during live ops.)

### Next candidate: safety switch — also ruled out

**2026-05-21T11:56-04:00** — Recurring beep continued; common
periodic-warning cause is safety switch engaged. Verified via
`mavproxy_arm.py:164–174` that `arm safetystatus` reads
`SYS_STATUS.onboard_control_sensors_enabled &
MAV_SYS_STATUS_SENSOR_MOTOR_OUTPUTS`. Roland ran it:

```
Safety is OFF (vehicle is dangerous)
```

So safety state isn't the cause either.

### RC failsafe hypothesis — **wrong**

**2026-05-21T11:57-04:00** — MAVProxy showed
`AP: RCInput: decoding SBUS(1)` and Roland confirmed he had just
turned on the RC controller. I hypothesised the beep was an
RC-failsafe warning that would clear once SBUS decoded. Roland
listened: **the beep did not stop.** Hypothesis rejected.

### Status dump — what it rules out

**2026-05-21T12:00-04:00** — Roland ran `status` in MAVProxy. The
dump's negative findings (i.e., what is **not** the cause):

| Subsystem | Value | Note |
|---|---|---|
| Battery (SYS_STATUS) | 27.135 V | `BATT_LOW_VOLT=23.0`, `BATT_CRT_VOLT=21.5` (from `mav.parm`) — well above both |
| EKF_STATUS_REPORT | flags=831, variances ~10⁻³ | Healthy stationary EKF3 (ATT/VEL/POS/POS_VERT all set; AGL+CONST_POS_MODE off as expected) |
| GPS_RAW_INT | fix_type=3, 28 sats, eph=0.50 m, epv=0.79 m | Solid 3D fix; alt_ellipsoid=−24.675 m consistent with MSL≈3 m + geoid≈−25 m for Portsmouth |
| RC_CHANNELS | chan1–16 ≈ 1495 neutral, chan5=1161 (MANUAL mode position) | SBUS decoding, matches `custom_mode=0` |
| SYS_STATUS sensors | `enabled & ~health` = 0 | No enabled-but-unhealthy sensor bits |
| STATUSTEXT in dump | only `RCInput: decoding SBUS(1)` (severity 7 = DEBUG) | No warnings/errors |
| `AHRS error_yaw` | 1.0 (max) | DCM yaw ≈ −9.6° vs ATTITUDE yaw ≈ −137°; expected on a stationary vehicle with COG-based EKF yaw — not a fault |

So I can confirm what the beep **isn't** (battery, RC failsafe,
safety switch, sensor health, pre-arm), but the MAVProxy
text-channel data doesn't surface the *positive* identification.
The actual `AP_Notify` event behind the buzzer pattern isn't
exposed in any of the messages above; it would require either
log replay (DataFlash `.bin` log) or a known cheat-sheet of
buzzer patterns.

### Decision: move on, log as unresolved

**2026-05-21T12:00-04:00** — Per Roland's earlier call: deploy
without further investigation. Pre-arm clean, safety off, EKF3
healthy, RC decoded, battery fine — nothing in the dump
contraindicates proceeding with ROS bring-up. The beep is
unexplained but apparently non-blocking. Revisit at wrap-up via
the DataFlash log if it didn't clear after some operational
action.

## 4. Salmon-side fix pull — `teltonika_monitor` STRING_ARRAY exception

**2026-05-21T12:11-04:00** — Roland: *"salmon agent found a bug
and fixed it, can you pull network monitors?"* Salmon-side agent
pushed a fix to `ros2_network_monitor` while bringing up the
operator stack; gabby needs it because
`bizzyboat_project11/launch/network_monitor_boat_launch.py`
launches `teltonika_monitor` with `teltonika_monitor_boat.yaml`
on the boat side.

Pull recipe (same inline ssh-agent workaround as section 1 — gitcloud
SSH still not persistent across this `claude` session):

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519_gitcloud
cd layers/main/sensors_ws/src/ros2_network_monitor
git fetch origin jazzy
git merge --ff-only origin/jazzy
ssh-agent -k
```

Fast-forward, no conflicts:

```
bdf396c..b27abab  jazzy -> origin/jazzy
b27abab teltonika_monitor: fix InvalidParameterTypeException on STRING_ARRAY override
        teltonika_monitor/teltonika_monitor/teltonika_monitor_node.py  (+5 -1)
```

**2026-05-21T12:13-04:00** — Rebuilt the affected package only:

```bash
cd /home/field/project11/layers/main/sensors_ws
colcon build --symlink-install --packages-select teltonika_monitor
# Finished <<< teltonika_monitor [1.02s]
```

The "already built in underlay" warning is the normal in-place
rebuild noise (sensors_ws's own install is currently sourced);
build completed cleanly.

Salmon-side observation (operator-side) of the original failure
mode and root cause not captured here — that's expected to be in
the salmon log file when it shows up.

## 5. unh_echoboats pull — `ignored_interfaces` for boat teltonika

**2026-05-21T12:14-04:00** — Roland: *"pull from unh echoboats"* —
the config-side companion to section 4's salmon fix. Same inline
ssh-agent recipe; fast-forward, no conflicts (untracked
`mav.parm` / `mav.tlog*` / today's gabby log file are untouched
by the incoming commit):

```
608f7f5..02afc7f  jazzy -> origin/jazzy
02afc7f bizzyboat.yaml: add ignored_interfaces for boat-side teltonika_monitor
        bizzyboat_project11/config/bizzyboat.yaml  (+1)
```

Verified change at `bizzyboat.yaml:353` under `/**/teltonika_monitor:`:

```yaml
ignored_interfaces: ['mob1s2a1', 'wan1']
```

`mob1s2a1` is the Teltonika cellular modem interface, `wan1` is
the WAN port — both excluded from monitoring on the boat side.
This is the parameter override that triggered salmon's
`InvalidParameterTypeException` until `b27abab` accepted
`STRING_ARRAY` types.

**No rebuild needed**: `install/bizzyboat_project11/share/.../config/bizzyboat.yaml`
is a symlink back to source (confirmed via `ls -l`), so the new
config propagates on the next ROS launch without any
`colcon build`.

## 6. Block 2 sanity check — FCU reconfig validated bench-side

**2026-05-21T12:16-04:00** — Roland: *"ROS up"*. Ran the
deployment-brief Block 2 sanity checks (boat still on cart,
sky-view):

```
ros2 topic echo /bizzy/mavros/global_position/global --once
ros2 topic echo /bizzy/tide_estimate --once
```

### Result — all three criteria pass

| Brief criterion | 2026-05-19 (pre-reconfig) | 2026-05-21 (today) | Result |
|---|---|---|---|
| `global_position/global.altitude` plausible vs chart datum | −12.4 m (out of band) | **−21.94 m** (in band) | ✓ +9.5 m closer to chart datum |
| `tide_estimate` inside plausibility band [−33.74, −19.42] | suppressed | **−21.06 m**, publishing | ✓ |
| `sea_surface_estimator` "outside plausible range" WARN volume | 49 KB of WARN spam over the session (PID 19190) | **0 entries**, log size 0 B (PID 18119) | ✓ |

### Sanity check on lever-arm chain

`tide_estimate (−21.06)` − `mavros_alt (−21.94)` = **0.88 m**,
matching `GPS_POS1_Z = 0.890 m` (CUAV antenna height above
`base_link`). The chain
`mavros/global → mru_transform → /bizzy/odom → sea_surface_estimator
→ map_tide TF` is wiring through the lever arm correctly.

### What this validates

This is the deployment's primary upgrade (#138 FCU reconfig)
*passing bench-side*. The earlier 2026-04-28 → 2026-05-19 episode
that drove issue #138 — where `mavros/global_position/global` was
EKF-fused Z referenced to home altitude and ~13 m off the
chart-datum-compatible frame — is fully reversed by setting
`EK3_SRC1_POSZ = 3`. The pre-`mru_transform` revert that we
applied in section 13 of [`2026-05-19_gabby_logs.md`](./2026-05-19_gabby_logs.md)
to keep the nav stack alive (pointing `mru_transform`'s position
input at `mavros/global_position/raw/fix`) is no longer the
crutch holding chart datum together — the EKF-fused topic is
now itself chart-datum-compatible.

### What's still pending (per brief Phase 1 in-water criteria)

- Body-frame SBG−MAV offset drops toward GPS-CEP, not the 0.64 m
  steady offset documented in #111. Needs simultaneous SBG +
  mavros echo on a moving boat; not verifiable on the cart.
- Nav stack stable through a short trackline at low speed. Phase 1
  in-water (~30 min near slack).

**Block 2 complete; go/no-go on the in-water phases is Roland's
call. Deployment plan from here proceeds to Block 3 — Phase 0
bring-up confirm near pier, then Phase 1 FCU-validation trackline.**

## 7. Pre-launch baseline — diagnostics + NTP

**2026-05-21T12:38-04:00** — Captured 3 s of `/diagnostics` and a
chrony snapshot as a pre-launch baseline (to compare against
in-water and post-mission state).

### `/diagnostics` snapshot — 55 unique status entries

**Headlines (OK):**

- **`GPS: RTK Fixed`** + `NTRIP receiving corrections` — RTK lock
  live; right state for the antenna-lever-arm validation in Phase 1
- **`lifecycle_manager_navigation: Nav2 Health → Managed nodes are
  active`** — nav stack fully up (no repeat of 2026-05-19's
  `map_tide` bringup failure)
- All mavros buckets `Normal`; SBG GPS 3D fix; mavros_router OK
- **All 6 ping targets green** — cloudflare 26.9 ms, google 35.9 ms,
  router_op_direct 2.7 ms, router_op_vpn 90.5 ms, salmon_direct
  22.0 ms, salmon_vpn 72.4 ms
- **Starlink**: no alerts, no thermal alerts, 0% drop / 25 ms /
  0% obstructed
- Teltonika boat router LTE −73 dBm, all interfaces up,
  mwan3 wan online
- `zda_serial_bridge OK`; mikrotik wifi.bizzy SNR **30 dB**
  (down from 2026-05-19's 43 dB — flagged for awareness)
- **No `/diagnostics_agg`** in snapshot, **no `bencloud` ping
  target** — confirms #146 and #148 are in effect on the boat side

**WARNs (5), with read:**

| Status | Message | Read |
|---|---|---|
| `mavros: Mount` | "Can not diagnose in this targeting mode" | Cosmetic — no gimbal hardware |
| `mikrotik: interface/ether{2..5}` | "Not running" | Cosmetic — unused wired ports (same as 2026-05-19) |
| `sound_speed_bridge` | "Last reading is 0.0 m/s (sensor problem?)" | Likely expected — sensor dry on cart; expect to clear in water |
| `udp_bridge: operator: resend give-ups` | **"give-up rate 27.13/s exceeds warn threshold"** | New per-remote `DiagnosticStatus` from `udp_bridge#24` is doing its job; magnitude is high (2026-05-19 ran ~3–6/s in normal ops). Both `vpn` + `wifi` show tx/rx throughput in the same status group, so a path exists — most likely the operator stack isn't fully up on salmon yet and resends are timing out unacked. Self-resolving expected. |

No `ERROR` or `STALE` anywhere. Snapshot retained ephemerally
at `/tmp/diag_snap.yaml`; not preserved beyond session.

### chrony / NTP baseline

| Metric | Value | Read |
|---|---|---|
| `System clock synchronized` | yes | ✓ |
| Active source (`^*`) | `time.lan.bizzy.p11.lan` (stratum 1) | Boat-local GPS-disciplined server |
| System time vs NTP | +11.5 µs fast | Sub-decimal-millisecond — excellent for bag/ROS correlation |
| Last offset | +19.5 µs; RMS 26.6 µs | Stable |
| Stratum | 2 | One hop from GPS-disciplined |
| Leap status | Normal | ✓ |

External pools (Canonical, vultr, netlinkify, maxhost, ntp.li) all
`Reach=377` but `^-` (not selected) — chrony correctly defers to
the local stratum-1 source.

`router.lan.bizzy.p11.lan` and `router.lan.op.p11.lan` both `^?`
Reach=0 (unreachable) — that's git-bug `81c2fac`
*Purge router-as-NTP refs from chrony hosts + op-router DHCP
option 42; verify public-pool fallback*. Cosmetic carry-forward;
chrony falls through to the next source so timekeeping is
unaffected.

### Validations against today's brief / merged PRs

- **#146 (diagnostic_aggregator removed)**: confirmed — no
  `diagnostic_aggregator` / `/diagnostics_agg` entries in the
  diagnostics snapshot from the boat side
- **#148 (bencloud removed)**: confirmed — no `bencloud` ping
  target in `ping_monitor` group
- **udp_bridge#24 per-remote DiagnosticStatus**: confirmed
  present and active (the `udp_bridge: operator: resend give-ups`
  status entry is the new mechanism in action)

## 8. In-water, first GOTOs — Phase 1 validation holding

**2026-05-21T12:45-04:00** — Roland: *"I just issued a couple of
gotos to move the boat closer to school kids that are visiting
the pier. gotos worked fine."*

Operational context: school visitors on the pier; boat
manoeuvring under autonomous GOTO commands for viewing.
Phase: launched / in-water (Block 3 of the brief is now active).

### Implicit confirmations from "gotos worked fine"

- **Nav2 lifecycle reachable + accepting goals** — directly counters
  the 2026-05-19 §13 failure (`bt_task_navigator: Action server
  is inactive. Rejecting the goal.`)
- **controller_server planning + commanding the boat** — the
  whole brief's primary upgrade chain (`EK3_SRC1_POSZ` →
  `mavros/global` → `mru_transform` → `/bizzy/odom` →
  `sea_surface_estimator` → `map_tide` TF → costmap →
  controller) is wiring through under operational load
- **udp_bridge link to operator** alive enough to deliver goals
  to gabby (or operator-side ROS bridge active)

### Confirming snapshot

| Topic / log | Value | Comparison |
|---|---|---|
| `/bizzy/tide_estimate` | **−25.39 m** | On-cart was −21.06 m; new value sits between MLLW (−28.01) and MHHW (−25.15), very close to MHHW — physically consistent with a floating boat near high tide vs. an elevated boat on the cart |
| `/bizzy/mavros/global_position/global` | publishing, status=0 (3D fix) | Position shifted ~60 m SW of the cart position (43.0720465,−70.7116835 → 43.0719869,−70.7124684) — consistent with moving toward the pier |
| `sea_surface_estimator_18119_*.log` size | **0 B** (unchanged) | No new lines since startup |
| `sea_surface_estimator` "outside plausible range" WARN count | **0** | Still zero after GOTOs and motion — estimator is not suppressing |

### Primary deployment objective: met

The brief's headline objective — `EK3_SRC1_POSZ` reconfig fixes
the chart-datum mismatch that drove 2026-05-19 §13's in-field
revert — is now **validated under operational load**. The
`mru_transform` revert-to-`raw/fix` from 2026-05-19 is no longer
needed; the EKF-fused `mavros/global` is itself chart-datum-
compatible, and the full lever-arm chain (antenna → base_link →
sea surface → map_tide) is delivering numbers that make
physical sense.

Whatever else the deployment does or doesn't accomplish from
here, this section is the win to carry into wrap-up.

## 9. Tide forecast cross-check — likely lever-arm double-count

**2026-05-21T12:50-04:00** — Roland: *"tide forecast is 1.2m,
does that jive with what we have?"* Comparison gave a real
finding worth a careful write-up.

### Sampling

Captured `/bizzy/tide_estimate` and
`/bizzy/mavros/global_position/global.altitude` in parallel
(`stdbuf -oL ros2 topic echo … --csv` × 6 s):

| Topic | mean | stdev | range |
|---|---|---|---|
| `tide_estimate` | **−25.2666 m** | 0.31 mm | 1.1 mm |
| `mavros alt` | **−26.1578 m** | 7.51 mm | 30 mm |

Both ultra-steady — this is a systematic offset, not noise.

### Key finding: identical on-cart and in-water offset

| Window | `tide_estimate − mavros_alt` |
|---|---|
| On cart (§6, dock, dry) | **+0.88 m** |
| In water (§9, this section) | **+0.8912 m** |
| `\|GPS_POS1_Z\|` (CUAV antenna above base_link, from `mav.parm`) | **0.890 m** |

The offset is identical between cart and water — meaning
`sea_surface_estimator` is **not** doing a "waterline + heave"
calculation. It's literally `tide_estimate = mavros_alt + 0.89`
in both states.

### Sign analysis: most likely a double-counted lever-arm

Physically: the antenna is *above* base_link (and above the
waterline). Sea surface should be *below* the antenna. But
`tide_estimate = mavros_alt + 0.89` puts the sea surface
*above* the antenna — sign-flipped.

Hypothesised cause: ArduPilot's EKF applies `GPS_POS1_*`
internally to project the GPS antenna position onto base_link
before publishing `mavros/global_position/global`. If
`mru_transform` (or `sea_surface_estimator` downstream) then
applies the antenna offset again with the wrong sign, you get
exactly this signature.

### Comparison against the 1.2 m NOAA forecast

Reference: MLLW = −28.01 m (ellipsoidal Z, from
`sea_surface_estimator` 2026-05-19 §13 banner).

| Computation | Ellipsoidal Z | Height above MLLW | Residual vs 1.2 m forecast |
|---|---|---|---|
| Current (as-published): `mavros_alt + 0.89` | −25.27 m | +2.74 m | **+1.54 m** |
| If sign-flipped: `mavros_alt − 0.89` | −27.05 m | +0.96 m | **−0.24 m** |
| Gap between the two | 1.78 m | 1.78 m | 1.78 m |

The 1.78 m gap is exactly **2 × \|GPS_POS1_Z\|** — the textbook
double-counted-lever-arm signature. Flipping the sign brings
the result to within 24 cm of the NOAA forecast, well inside
chart-datum / forecast-station uncertainty.

### Deploy impact

- **Not a deploy-blocker today**: plausibility band still passes
  (the −12 m → in-band shift from #138 dominates the ±1.78 m
  bias); nav stack runs; GOTOs work. The estimator is *near
  enough* to the right answer for the controller to use.
- **`tide_estimate` is misreporting tide height by ~1.78 m**,
  which matters for any consumer that treats it as a calibrated
  reference (chart-datum-tied tasks, vertical alignment of bag
  data with hydrographic products).
- The brief's Phase 1 pass criterion *"body-frame SBG−MAV
  offset drops toward GPS-CEP"* may also be affected — if the
  chain double-counts on the MAV side, the body-frame SBG−MAV
  comparison would still show a steady offset matching the
  lever-arm magnitude, even if the FCU reconfig itself is
  fine.

### What this is, what it isn't

- It is **not** a regression from today's `EK3_SRC1_POSZ` change.
  This double-count would have been present on 2026-05-19 too —
  but the much larger `−12.4 m` EKF/baro mismatch dominated,
  forcing the estimator into suppression mode and masking the
  smaller lever-arm bug. With #138 in, the magnitude problem
  goes away and the lever-arm sign issue becomes visible.
- It is **a real bug** worth a follow-up issue at wrap-up.
  Candidate locations to audit (not verified during this
  pre-launch window):
  - `sea_surface_estimator` source — where it consumes
    `/bizzy/odom` / mavros alt and emits `tide_estimate`
  - `mru_transform` — if it's applying `GPS_POS1` offsets a
    second time after EKF already did
  - URDF `base_link` to `gnss_antenna` static transform —
    consistent with `GPS_POS1` or sign-flipped?

### Position context

Last sample at 12:54 EDT: 43.0725427, −70.7114762 (boat moved
~30 m NE from the §8 post-GOTO position, consistent with
continued manoeuvring near the pier).

## 10. Chain inspection: `mru_transform` was passing antenna alt through as base_link alt

**2026-05-21T13:00-04:00** — Roland: *"check what mru_transform
is using for position, what frame id it has, and if it seems
like mru transform is doing something to it. Also, what does
odom look like?"*

### Config inspection (pre-edit)

`bizzyboat.yaml` had `mru_transform` reading `raw/fix` (the
2026-05-19 §13 revert was still in place):

```yaml
sensors:
  mru:
    topics:
      orientation: "mavros/imu/data"
      position: "mavros/global_position/raw/fix"
      velocity: "mavros/global_position/raw/gps_vel"
```

### Topic chain snapshot

| Topic | frame_id | Z value | Notes |
|---|---|---|---|
| `mavros/.../raw/fix` (mru input) | `bizzy/base_link` | **−25.189 m** | Label says base_link; value is **antenna** ellipsoidal alt (FCU passes raw GPS through) |
| `mavros/.../global` (#138 EKF-fused) | `bizzy/base_link` | **−26.079 m** | **Is** lever-arm-corrected — `raw/fix − global = +0.865 m` ≈ \|GPS_POS1_Z\|=0.890 m |
| `/bizzy/odom` (mru output) | parent `bizzy/odom`, child `bizzy/base_link`, z=**−25.219 m** | | Within 30 mm of `raw/fix.alt` — mru passes Z through unchanged |
| `/bizzy/tide_estimate` | (scalar) | **−25.203 m** | Tracks odom.z within 16 mm |

### What `mru_transform` is doing to position: nothing

The chain `raw/fix.altitude (−25.189) → odom.z (−25.219) →
tide_estimate (−25.203)` is essentially a passthrough of the
GPS antenna's ellipsoidal Z. **`mru_transform` is not applying
any lever-arm correction to the Z value.** It publishes the
antenna altitude as `odom.pose.position.z` with
`child_frame_id: bizzy/base_link` — labelling antenna altitude
as base_link altitude.

### §9 hypothesis correction

§9 had this as a "sign-flipped double-counted lever-arm". That
was **wrong in mechanism**. The reality is the opposite: **no
lever-arm is being applied at all** because `mru_transform`'s
input is `raw/fix` (antenna alt) and the downstream just
passes it through.

The brief's #138 made `mavros/global_position/global`
chart-datum-compatible by having the FCU EKF apply
`GPS_POS1_*` internally. Switching `mru_transform` to read
`/global` would deliver actual base_link altitude to
`/bizzy/odom`.

### Forecast comparison, re-done correctly

| What we'd be computing | tide_estimate | Above MLLW | vs 1.2 m forecast |
|---|---|---|---|
| **Today** (`raw/fix`-derived, ≈ antenna alt) | −25.20 m | **+2.81 m** | **+1.61 m residual** |
| If `mru_transform` switched to `/global` (base_link alt per #138) | ~−26.08 m | **+1.93 m** | **+0.73 m residual** |
| (Plus ~0.7 m URDF base_link-to-waterline freeboard) | ~−26.78 m | **+1.23 m** | **+0.03 m residual** ✓ |

The remaining 73 cm after switching to `/global` is almost
certainly **`base_link`-to-waterline freeboard** — a URDF-side
calibration, not an estimator bug.

> **Wrap-up correction (2026-05-22 bag review)** — the ~0.7 m
> freeboard guess in the table above is too high. Per the URDF
> (`bizzyboat.urdf.xacro:235-236`), the DeltaT sonar is mounted
> at `z = −0.18 m` from base_link with the housing flipped, so
> the active face is at approximately `z = −0.22 m`. Operator
> confirms the sonar face is definitely submerged in service,
> which caps freeboard at ≤ ~0.22 m. Recomputed: after switching
> to `/global` (this section's row 2) the residual is still
> ~+0.5 m vs the NOAA forecast (0.73 m raw − ≤0.22 m freeboard),
> **not** the +0.03 m claimed in row 3. The §10 mechanism (`raw/fix`
> → `/global` switch fixes the missing lever-arm) is still right;
> the closure claim is what's revised. Candidate causes for the
> remaining ~0.5 m: VDatum-grid-MLLW vs Fort-Point-gauge-MLLW
> reference mismatch (very small at the pier — both anchored to
> the same gauge), small unmodeled tilts/lever-arms, or forecast-
> vs-actual on the day (NOAA forecasts have their own ±10-20 cm
> uncertainty). Leaving the original row 3 intact as a lesson
> in unverified assumptions.

## 11. SBG vs MAV comparison — 0.64 m offset persists (brief Phase 1 criterion NOT met)

**2026-05-21T13:01-04:00** — Roland: *"compare the sbg with
/global, they should be the same"*. Sampled 4 topics in
parallel for ~8 s and computed ellipsoidal Z (SBG: MSL +
undulation).

### Vertical Z picture

| Source | Value | Physical interpretation |
|---|---|---|
| `mavros/.../raw/fix` alt | **−25.118 m** | CUAV antenna ellipsoidal (raw GPS) |
| `mavros/.../global` alt | **−25.982 m** | CUAV base_link (FCU EKF applied `GPS_POS1_Z`) |
| `sbg/gps_pos` MSL+und | **−25.692 m** | SBG GPS antenna ellipsoidal (raw) |
| `sbg/ekf_nav` MSL+und | **−26.618 m** | SBG INS fused (`frame_id: imu_link_ned` — at SBG IMU, **not** base_link) |

### Key deltas

| Comparison | Value | Interpretation |
|---|---|---|
| **`SBG_ekf_nav − mavros /global`** | **−0.636 m** | **Matches the #111 0.64 m baseline almost exactly — #138 did not move the needle** |
| `SBG_gps_pos − mavros /raw/fix` | −0.575 m | SBG GPS antenna physically ~57 cm below CUAV antenna |
| `SBG_ekf_nav − SBG_gps_pos` | −0.926 m | SBG GPS-to-IMU vertical lever-arm (SBG driver's internal projection) |
| `/raw/fix − /global` | +0.865 m | Confirms FCU EKF's lever-arm application (≈ \|GPS_POS1_Z\|) |

### Horizontal agreement

`SBG_ekf_nav` vs `mavros /global`: lat 0.19 cm, lon 6.69 cm.
Both ekf-fused sources are dialled in horizontally.

### Why #138 didn't shrink the SBG−MAV gap

The brief's #138 implementation today was only
`EK3_SRC1_POSZ = 3` (the other 3 `EK3_GPS_OFFS_*` rows in the
brief turned out to be non-existent params; see §2). That's a
CUAV-side change. The **SBG side received no corresponding
configuration**, so SBG's INS still projects to
`imu_link_ned`, not to a CUAV-consistent base_link. The 64 cm
gap is the unresolved **SBG IMU mount → base_link**
lever-arm — exactly what open issue
[`57a6134`](#) (*urdf: model SBG INS, GNSS antenna(s), and
IMU mounting alignment on bizzyboat*) was opened to address.

### Brief Phase 1 criterion → not met

> *"body-frame SBG−MAV offset drops toward GPS-CEP (sub-decimeter
> ideally), not the 0.64 m steady offset documented in #111"*

Today still at **0.636 m**, same as the #111 baseline. The
criterion was implicitly assuming the SBG lever-arm would
also get fixed; with only the CUAV side changed, no movement.

## 12. Applied: `mru_transform` switched to `/global`

**2026-05-21T13:09-04:00** — Roland: *"reconfigure mru
transform to use .../global, the boat is safe and I'll
restart the stack"*. Roland flagged boat safe; this is the
deployment's authoritative "the chart-datum chain can come off
the field-revert workaround" trigger from the brief's
carry-forward cautions.

### Edits

Both `mru_transform` config blocks in `bizzyboat.yaml`
swapped (the original 2026-04-28 pair, reverting the
2026-05-19 §13 revert):

```diff
       sources:
         mru:
           topics:
             orientation: "mavros/imu/data"
-            position: "mavros/global_position/raw/fix"
-            velocity: "mavros/global_position/raw/gps_vel"
+            position: "mavros/global_position/global"
+            velocity: "mavros/local_position/velocity_body"
```

Applied at **lines 25–26** (under `nav.sources.mru.topics`)
and **lines 43–44** (under `mru_transform.sensors.mru.topics`).

### Deliberately left untouched

| Lines | Node | Why left |
|---|---|---|
| 137-138, 205-206 | `udp_bridge` | Operator-side downlink names; changing them affects what salmon receives — separate decision |
| 220-221 | `logger` | rosbag recording of raw GPS — valuable to keep for post-hoc geodetic analysis |
| 234-237 | comment | Now stale (references the 2026-05-19 revert as still-active); flagged for wrap-up cleanup |

### Propagation: symlink-install, no rebuild needed

`install/bizzyboat_project11/share/.../config/bizzyboat.yaml`
is a symlink to source (confirmed §5). Edit propagates on
next ROS launch.

### Expected outcome on restart

1. `/bizzy/odom.z` will track `/global.altitude` (~−26 m), not
   `raw/fix.altitude` (~−25.1 m).
2. `tide_estimate` will drop by ~0.86 m → height above MLLW
   drops from +2.81 m to ~+1.93 m.
3. Forecast residual goes from +1.61 m to ~+0.73 m. The
   remaining 73 cm is the URDF base_link-to-waterline
   freeboard — a separate calibration, not an estimator bug.
4. SBG−MAV vertical gap (§11's 0.636 m) will **not** shrink —
   that's an SBG-side mount issue (`57a6134`), independent of
   the `mru_transform` switch.

Awaiting Roland's stack restart to verify (1)-(3).

## 13. Post-restart verification — chain swap landed cleanly

**2026-05-21T13:15-04:00** — Roland: *"restarted, check the
chain"*. Sampled all 5 chain topics in parallel for ~8 s.
Confirmation of restart: `sea_surface_estimator` PID is now
24693 (was 18119); new node log at 0 B / 0 suppression WARNs.

### Per-topic post-restart values

| Source | Mean | Stdev | Samples |
|---|---|---|---|
| `tide_estimate` | **−25.896 m** | 1.24 mm | 71 |
| `mavros /global altitude` | **−25.912 m** | 16.3 mm | 69 |
| `mavros /raw/fix altitude` | **−25.017 m** | 20.4 mm | 69 |
| `/bizzy/odom.z` | **−25.912 m** | 16.3 mm | 69 |
| `sbg/ekf_nav` ellipsoidal | **−26.531 m** | 15.8 mm | 173 |

### All four §12 predictions held

| Prediction | Result |
|---|---|
| `/bizzy/odom.z` tracks `/global` | ✓ **`odom.z − /global = −0.0000 m`** (identical to sub-mm) |
| `/bizzy/odom.z` decoupled from `raw/fix` | ✓ Now offset by `−0.895 m` (the antenna lever-arm); was ~0 pre-restart |
| `tide_estimate` drops by ~0.86 m | ✓ Dropped from −25.203 → −25.896, Δ = **−0.693 m**. The 17 cm of "missing" expected change is the boat drifting ~7 cm higher in `/global` between sampling windows (`/global` moved −25.982 → −25.912 in the same span). The model holds — `tide_estimate ≈ /global ≈ odom.z` is now the chain. |
| SBG−MAV vertical gap unchanged | ✓ Pre-restart −0.636 m → post-restart **−0.619 m** (17 mm noise); the SBG side hasn't changed, as expected — `57a6134` (URDF mounting) still the open follow-up |

### Forecast comparison after the switch

| | tide_estimate | Above MLLW | Residual vs 1.2 m |
|---|---|---|---|
| Pre-restart (§9) | −25.203 m | +2.81 m | +1.61 m |
| **Post-restart** | **−25.896 m** | **+2.11 m** | **+0.91 m** |
| Δ improvement | −0.693 m | −0.70 m | **−0.70 m** |

Residual against the NOAA forecast dropped from 1.61 m to
0.91 m. The remaining 0.91 m is the unresolved
`base_link`-to-waterline freeboard (URDF calibration, ~0.7 m
typical for BizzyBoat) plus chart-datum-reference and
tidal-phase imprecision.

### What this clears

- **Closes** the 2026-05-19 §13 in-field revert as a durable
  state. With #138 + this restart, the chart-datum chain runs
  off the EKF-fused topic as the brief's design intended; the
  `raw/fix` workaround is no longer load-bearing.
- **Validates** the brief's carry-forward caution *"can come
  off the field-revert workaround once a deployment confirms"*.
- **Confirms** `sea_surface_estimator` band check still passes
  under the new config — no regression on the safety side.

### What's still open

- **URDF / base_link calibration** — the residual 0.91 m
  vs forecast is consistent with base_link-to-waterline
  freeboard. Candidate work item: model BizzyBoat freeboard
  in URDF or expose as a `sea_surface_estimator` param.
- **SBG IMU mounting to base_link** — open issue `57a6134`,
  unchanged by today's work. The 0.62 m SBG−MAV vertical
  offset is downstream of this.
- **Comment cleanup at `bizzyboat.yaml:234-237`** — stale
  reference to the 2026-05-19 revert as "currently restored".
- **Velocity input audit** — we swapped `position` *and*
  `velocity`. Velocity went `raw/gps_vel` →
  `local_position/velocity_body`. Direction/sign of the body
  velocity input affects `mru_transform`'s odometry chain;
  worth a sanity check that twist signs in `/bizzy/odom`
  remain consistent during motion (not verified during this
  brief sampling window since boat was relatively still).

## 14. 1-hour camera + local costmap recording

**2026-05-21T13:25-04:00** — Roland: *"we have a script to
record video, add the local costmap to it and run it to record
an hour"*. Edited
`bizzyboat_project11/scripts/record_camera_topics.sh`:

- Added `/bizzy/local_costmap/costmap` to the `TOPICS=()` array
  (just before the closing `)`, after the segmentation
  `camera_info`s)
- Updated the header comment to mention the costmap and note
  the rationale: *"so the segmentation-vs-costmap chain can
  be verified end-to-end against what the planner actually saw"*
- Total topics: **26** (was 25)

Started recording:

```bash
./record_camera_topics.sh 3600
```

| Param | Value |
|---|---|
| Output bag | `~/data/logs/bizzy_images/bag_2026-05-21T13.25.26_ffmpeg_seg/` |
| Duration | 3600 s (clean SIGINT-flushed mcap at ~14:25 EDT) |
| Storage | mcap + zstd_fast (matches 2026-05-19 bags) |
| Wrapper PID | 27019 (`timeout`); child PID 27020 (`ros2 bag record`) |

### Choices on what to include

Added only the visualization-friendly `nav_msgs/OccupancyGrid`
(`/bizzy/local_costmap/costmap`). Available siblings left
off by default:

- `/bizzy/local_costmap/costmap_raw` — full `nav2_msgs/Costmap`
  with all cell-cost metadata (vs 0–100 occupancy mapping)
- `/bizzy/local_costmap/costmap_raw_updates` — delta updates,
  smaller per message
- `/bizzy/local_costmap/published_footprint` — robot polygon
  in costmap frame

If a future deployment wants full-fidelity costmap replay
(cell costs preserved, not just the 0–100 occupancy
projection), `costmap_raw` + `costmap_raw_updates` are the
ones to add.

### Schedule note

Brief's hard stop is 14:00 EDT; this recording runs to ~14:25,
so it'll keep capturing through recovery / power-down. Plenty
of bandwidth for that — the 2026-05-19 50-min bag was 2.0 GB
(~40 MB/min), so this should land at ~2.4 GB plus a modest
increment from the costmap topic.

## 15. Nav2 lifecycle stuck — post-restart startup race for `map_tide` TF

**2026-05-21T13:30-04:00** — Roland: *"What's up with the nav
stack?"* Investigation found a Nav2 bringup failure that's a
**direct consequence of §12's `mru_transform` config change**.

### Symptoms

- `/diagnostics` reports
  **`lifecycle_manager_navigation: Nav2 Health: Managed nodes
  are unconfigured`** (regressed from §6/§7's *"active"*)
- `ros2 node list` shows nav stack partially present:
  - **Missing**: `controller_server`,
    `/bizzy/local_costmap/local_costmap`
  - **Alive**: `behavior_server`, `bt_task_navigator`,
    `collision_monitor`, `global_costmap`,
    `lifecycle_manager_navigation`, `planner_server`,
    `smoother_server`, `velocity_smoother`, `waypoint_follower`
- `tf2_echo bizzy/base_link bizzy/map_tide` **does** return
  live data (TF works **now**, in steady state)
- `tide_estimate` is publishing in band (§13 confirmed)
- `sea_surface_estimator` log: 0 B / 0 suppression WARNs
- `controller_server` log ends at **13:11:19** with:

```
[INFO] Activating
[INFO] local_costmap: Timed out waiting for transform from
       bizzy/base_link to bizzy/map_tide to become available,
       tf error: Invalid frame ID "bizzy/map_tide" passed to
       canTransform argument target_frame - frame does not exist
```

…repeating 7 times over ~3.5 s, then silence. `controller_server`
appears to have exited after the failed activation.

### Diagnosis: startup race made worse by `/global` switch

This is a **timing race**, not a TF that doesn't exist. The TF
**does** exist at steady state — it's just not available within
`local_costmap`'s activation wait window.

Before §12: `mru_transform` read `mavros/.../raw/fix`, which
publishes as soon as GPS gets a fix (~1 s after boot). The chain
`raw/fix → mru_transform → /bizzy/odom → sea_surface_estimator →
map_tide TF` was up quickly enough that lifecycle activation
found the TF on time.

After §12: `mru_transform` reads `mavros/.../global`, which only
flows after the FCU EKF has finished initialising — several
seconds longer. The activation race is lost; `local_costmap`
gives up; `controller_server` exits; lifecycle stuck unconfigured.

The §13 forecast/chain verification all passed because by the
time we sampled (minutes later), the chain was steady-state.
The race only fails during the brief bringup window.

### Recommendation: full launch-group relaunch

Same pattern as 2026-05-19 §13's lesson learned: *"for a
launched-as-a-group node, restart everything beats per-node
restart"* (and [[feedback_dont_kill_launched_nodes]] memory).
The chain is steady-state now, so a fresh relaunch attempt
should find `map_tide` TF ready on time.

**I am not surgically killing nodes** — that's Roland's call to
re-issue the launch.

### Carry-forward (durable follow-ups for wrap-up)

- **Sequence `sea_surface_estimator` ahead of Nav2 lifecycle
  bringup** in the launch group, so `map_tide` TF is guaranteed
  available when `local_costmap` tries to activate.
- **Bump `local_costmap` activation wait / `transform_tolerance`**
  to cover the FCU-EKF init delay.
- **Or add a `wait_for_transform` guard** in the launch sequence
  before Nav2 bringup fires.
- All three of these become important now that `mru_transform`
  depends on `/global` for chart-datum correctness. The choice
  is essentially: live with the startup-race risk on every
  relaunch, or invest in proper sequencing.

### Operational impact today

- Pre-§12, GOTOs worked (§8). Post-§12 restart, nav stack is
  down and any further GOTO requests would be rejected (action
  server inactive — exact 2026-05-19 §13 symptom).
- Manual / RC control is independent of Nav2 and unaffected.
- The 14:00 EDT hard stop is in ~30 min; whether to relaunch
  the nav stack vs finish out the deployment in manual is
  Roland's call.

## 16. Nav stack relaunch hits known `SeaSurfaceLayer::matchSize` segfault (perception #6)

**2026-05-21T13:32-04:00** — Roland relaunched the nav stack
per §15's recommendation. The TF race resolved cleanly this
time (chain steady-state), but `controller_server` hit a
**SIGSEGV** during local_costmap activation:

```
[lifecycle_manager-11] Activating controller_server
[controller_server-1] Activating
[controller_server-1] local_costmap: Activating
[controller_server-1] local_costmap: Checking transform
[controller_server-1] local_costmap: start
[controller_server-1] local_costmap: Tide offset updated: 2.31988 m (water above chart datum)
[controller_server-1] local_costmap: Matching size of SeaSurfaceLayer to parent costmap    # forward
[controller_server-1] local_costmap: Matching size of SeaSurfaceLayer to parent costmap    # port
[controller_server-1] local_costmap: Matching size of SeaSurfaceLayer to parent costmap    # starboard
[controller_server-1] local_costmap: Matching size of SeaSurfaceLayer to parent costmap    # aft
[ERROR] process has died [pid 28419, exit code -11]
```

`exit code -11` = SIGSEGV. Crash signature exactly matches the
brief's stretch item `rolker/unh_marine_perception#6 —
SeaSurfaceLayer::matchSize segfault`.

### Build-state check: all brief-mentioned PRs are merged

| Repo | Latest local commit | PR |
|---|---|---|
| `unh_marine_perception` | `723c0e7 Merge PR #13` (HEAD) | #11 + #13 both merged |
| `seafloor_echoboat_project11` | `d1237fd Merge PR #19` (HEAD) | #19 merged — this is what re-enabled `sea_surface_layer ×4` |

So the brief's *prerequisite* PRs are all in the build, but
the segfault still triggers — the perception fixes #11/#13
aren't sufficient to close #6.

### Tide-offset sanity inside the crash

`Tide offset updated: 2.31988 m (water above chart datum)` is
chart_layer reading the new (post-§12) chain. Above-MLLW
height of 2.32 m vs §13's 2.11 m suggests the boat moved
~20 cm higher in `/global` between sampling windows — consistent
with the small drift we already observed in §13's pre/post
delta. **The chain is healthy through to costmap input** — the
segfault is downstream in the layer init.

### Brief gate skipped

> *"Bench smoke: launch controller_server with all 4 OAK
> sea_surface_layer_{forward,port,starboard,aft} enabled;
> confirm no segfault and that at least one OAK direction
> publishes segmentation."*

This pre-launch gate from Block 2 was not run. Doing it
on dry land would have caught this before water work.

### Why §8 worked but §16 didn't

§8 had the same 4-layer config and GOTOs ran successfully —
suggesting the segfault is **intermittent**, dependent on
runtime state (camera input, costmap origin, layer init
order). Not a deterministic config break.

### Field workaround applied

Per Roland's call ("Keep 1 layer (forward), drop 3"), edited
`seafloor_echoboat_project11/echoboat_project11/config/nav2_params.yaml`:

```diff
       plugins: ["chart_layer",
                 "sea_surface_layer_forward",
-                "sea_surface_layer_port",
-                "sea_surface_layer_starboard",
-                "sea_surface_layer_aft",
+                # 2026-05-21 field workaround: port/starboard/aft
+                # commented out to dodge SeaSurfaceLayer matchSize
+                # segfault (unh_marine_perception#6). Restore the
+                # full 4-layer list once #6 is verified fixed via
+                # bench smoke.
+                # "sea_surface_layer_port",
+                # "sea_surface_layer_starboard",
+                # "sea_surface_layer_aft",
                 "inflation_layer"]
```

- Plugin definition blocks (lines 134–151) left in place;
  harmless if not in the `plugins:` list.
- `install/.../nav2_params.yaml` is a symlink to source
  (verified) → no rebuild needed.
- Meets brief's *"at least one OAK direction"* criterion via
  the still-active forward layer.

### Diagnostic value of the planned relaunch

| Outcome | Implication for #6 |
|---|---|
| Activation succeeds, no crash | Segfault is triggered by multi-layer interaction (>1 SeaSurfaceLayer instance) |
| Crash on forward layer alone | Bug is in per-instance init |
| Activation succeeds then crashes later | Bug is in segmentation-input or update path, not init |

### Carry-forward

- **`unh_marine_perception#6` is not closed by today's PRs
  #11/#13.** Add a follow-up note on the issue with today's
  crash log + the conditions (multi-layer, on-water).
- **Brief's bench-smoke gate must be enforceable** — it's the
  only check between #6's intermittent behaviour and a
  mid-mission outage. Candidate workspace-level pre-flight
  automation.
- **Project memory** [[project_mru_global_startup_race]] saved
  for next agent re §15's startup race. Today's incident is
  not the same bug as §15 — §15 was a startup-timing TF race,
  §16 is the perception layer segfault — but both are
  symptoms of fragile bringup downstream of the `/global` chain.

### Outcome: forward-only relaunch succeeded — multi-layer interaction is the trigger

**2026-05-21T13:38-04:00** — Roland: *"relaunched, activation
succeeded — no crash this time"*. Health check confirmed:

- `lifecycle_manager_navigation: Nav2 Health: Managed nodes
  are active` ✓ (regressed → recovered from §15's
  *"unconfigured"*)
- `controller_server`, `/bizzy/local_costmap/local_costmap`,
  `/bizzy/bt_task_navigator` all in `ros2 node list` ✓
- No new ERROR / FATAL across nav node logs

**This is the 1st of 3 outcomes predicted in §16's table** —
*"activation succeeds with forward layer alone"* → **the
`SeaSurfaceLayer::matchSize` segfault is triggered by
multi-instance interaction**, not by the layer's per-instance
init. Probably shared state or per-instance init touching
common memory.

**Real diagnostic to post on `unh_marine_perception#6`** at
wrap-up: today's crash log + this 1-vs-4 contrast + the build
state confirming #11 and #13 are merged but insufficient.

### Other diagnostic shifts noted

- **New WARN: `ping_monitor: salmon_vpn: 25% packet loss`** —
  cellular VPN to salmon degrading. Could be cellular signal,
  salmon-side WiFi, or transient. Not deploy-blocking but
  worth watching through the 14:00 stop.
- **`udp_bridge: operator: resend give-ups` rate**: 21.18/s
  (was 18.13/s in §15, 27.13/s at pre-launch in §7) —
  oscillating in a similar band; consistent with the
  intermittent operator-side path conditions.

## 17. OTH trackline sent — Phase 2 (udp_bridge#24 validation) baseline

**2026-05-21T13:39-04:00** — Roland: *"just sent an OTH
trackline"*. With nav stack recovered (§16) and ~21 min to
the 14:00 EDT hard stop, this is a compressed Phase 2 run
per the brief's priority table (*"Take boat to 300-500 m
WiFi-only, then a brief Starlink-only segment"*).

### Start-of-trackline baseline

| Metric | Value | Context vs prior snapshots |
|---|---|---|
| Position | 43.0728946, −70.7096245 | ~157 m ENE of §13's pier-area position (Δlat +39 m N, Δlon +152 m E) |
| `tide_estimate` | **−25.620 m** | 28 cm higher than §13's −25.896 m |
| `mavros/global` altitude | −25.647 m | tracks tide_estimate to within 27 mm (chain healthy) |
| **`udp_bridge` cumulative per-event WARN log** | **0 entries** | Per-event WARN log (`udp_bridge_node_24704_*.log`, 81 KB) contains **zero** "Giving up on resend" lines |
| `udp_bridge` give-up DiagnosticStatus rate | 36.21/s | New #24 mechanism flagging at WARN level via per-remote status; not spamming the WARN log |
| `salmon_vpn` packet loss WARN | cleared | Was 25% in §16; transient |
| Nav stack | `Nav2 Health: Managed nodes are active` | Healthy per §16's outcome |

### Brief Phase 2 criterion → already met

> *"Per-event WARN volume orders-of-magnitude reduced from
> 27,992-in-2h baseline (2026-05-19); per-remote
> DiagnosticStatus shows give-up rate"*

**Both halves confirmed at the start of the OTH run:**

- Per-event WARN count: **27,992 (2026-05-19) → 0 (today)**.
  Not just "orders of magnitude reduced" — *zero* in the
  fresh log. The WARN-demote half of `udp_bridge#24` is doing
  exactly what it was meant to do.
- DiagnosticStatus per-remote: publishing the give-up rate
  (36.21/s) so operators / annunciators / monitoring still
  see the signal without log-spam noise. The DiagnosticStatus
  half is working.

This is the deployment's **second headline win**, separate
from the §13 FCU-reconfig chain validation:

1. §13: FCU reconfig (#138) validated — chart-datum chain
   off the field-revert workaround.
2. §17: `udp_bridge#24` WARN demote validated — log noise
   eliminated, structured signal preserved.

### What to capture at end of OTH run

When Roland reports the trackline complete, snapshot:

- Cumulative per-event "Giving up on resend" count in this
  session's `udp_bridge_node_*.log` (should remain ≈ 0)
- `udp_bridge` DiagnosticStatus give-up rate evolution
- Position at apex of the run (max distance from pier)
- Starlink alerts / `link.drop`/`link.latency` evolution
- `salmon_vpn` and `salmon_direct` ping evolution

These give the per-distance / per-condition profile of
today's link behaviour for offline analysis.

## 18. WiFi out of range — Starlink-only carrying ops

**2026-05-21T13:47-04:00** — Roland: *"we are out of wifi
range"*. Clean transition into Starlink-only operations
~520 m SSE of the pier (within / just past the brief's
300–500 m WiFi-only target band).

### Position vs §17 start

| Snapshot | Position | Δ from pier (§13) |
|---|---|---|
| §13 (pier) | 43.0725407, −70.7114819 | — |
| §17 (OTH start) | 43.0728946, −70.7096245 | +157 m ENE |
| **§18 (wifi out, now)** | **43.0699033, −70.7077253** | **~520 m SSE** |

### Comms state at transition

| Path | Level | Status |
|---|---|---|
| `udp_bridge: wifi` | **ERROR** | `no rx for 278s` |
| `mikrotik: interface/wlan1` | WARN | `Not running` — L2 down (not just no peer) |
| `ping_monitor: router_op_direct` | ERROR | 100% packet loss |
| `ping_monitor: salmon_direct` | ERROR | 100% packet loss |
| `ping_monitor: router_op_vpn` | STALE | cached sample 40 s old |
| `ping_monitor: dns_cloudflare`/`dns_google` | STALE | cached sample 35–37 s old |
| **`ping_monitor: salmon_vpn`** | **OK** | **73.1 ms** |
| **`udp_bridge: vpn`** | **OK** | **tx 390 kB/s, rx 8.2 kB/s** |
| `Starlink: link` | OK | 0% drop, 19 ms, no obstruction, no thermal alerts |

Operations are now riding entirely on **Starlink → VPN → salmon**.

### Brief Phase 2 criterion holds under wifi-loss

- Per-event WARN log **still at 0 entries** (88 KB
  `udp_bridge_node_*.log`, no "Giving up on resend" lines
  even with one full path failed) — `udp_bridge#24`'s
  WARN-demote is robust under degraded conditions, not just
  the easy case.
- DiagnosticStatus correctly surfaces three different signals
  at three different severities (OK on VPN, ERROR on WiFi,
  WARN on give-up rate) — the per-remote granularity from #24
  is doing exactly what its design intent was.

### Comparison with 2026-05-19 §9 (controlled wifi-disable rehearsal)

| Aspect | 2026-05-19 §9 | 2026-05-21 §18 |
|---|---|---|
| Method | Operator-side WiFi manually disabled at pier | Natural loss from physical distance |
| Boat position | On cart (dock) | ~520 m SSE underway |
| WiFi `connection_id` in stats | Persisting in record (transient ageing) | Path explicitly **ERROR** with last-rx age (cleaner) |
| Resend WARN log behaviour | Active spam (resend attempts 6 → 1 visible in WARNs) | **Zero WARN entries** — #24 hadn't merged yet on 2026-05-19; now in, demote is holding |
| VPN path | Already carrying ops (operator-side WiFi off, gabby tmux survived) | Same — VPN/Starlink tunnel carrying ops |

Today's case is the field-realistic test that 2026-05-19's
controlled rehearsal validated; the headline difference is
that `udp_bridge#24` eliminates the log-spam side-effect.

### Schedule context

13 min to the 14:00 EDT hard stop. If the trackline is an
out-and-back, recovery turn should begin around now. Flagged
to Roland — operator's call on geometry.

## 19. RC controller interference during OTH run

**2026-05-21T13:48-04:00** — Roland: *"rc controller didn't
turn off, was screwing with me"*.

The RC controller stayed powered on during the OTH autonomous
trackline; FCU honoured RC channel inputs in parallel with
GUIDED nav commands, fighting the autonomous control.

### This was the deployment brief's named carry-forward caution

From [git-bug `7d5b52c`](#) (today's deployment issue) under
*Carry-forward cautions*:

> **RC mode-switch at fringe range** — FCU honors RC channel
> even with `FS_THR_ENABLE=0`. Pin RC mode switch to
> AUTO/GUIDED or power off the controller before autonomous
> segments.

Mitigation didn't happen: the RC controller was turned on
at 11:57 EDT (§3, while diagnosing the FCU buzzer pre-launch)
and remained on through the in-water phases. The RC channel
position (chan5=1161 in §7's status dump, MANUAL-mode
position) was honoured by the FCU during the OTH trackline.

### What was actually happening (from earlier snapshots)

§7 / status dump captured the relevant RC state pre-launch:

```
RC_CHANNELS chan1=1495 chan2=1495 chan3=1493 chan4=1493 chan5=1161 ...
```

- chan1–4 at neutral (~1495) — sticks centred, no manual
  throttle / steering input as long as the operator hands
  off the controller
- chan5=1161 — mode switch in **MANUAL** position; FCU
  reads this as a request for MANUAL mode even when nav
  sends GUIDED commands

ArduPilot Rover priority: RC mode switch overrides MAVLink
mode requests when RC is decoded and `FS_THR_ENABLE=0`.
With the controller on and chan5 in MANUAL, the boat would
have been alternating between (or fighting) autonomous
GUIDED control and operator-initiated MANUAL — exactly the
"screwing with me" behavior Roland reported.

### Why the brief's mitigation didn't get applied

A plausible chain (not verified, candidate explanation for
wrap-up review):

- The RC controller was turned on in the buzzer-mystery
  investigation context (§3), where verifying RC input was
  the immediate task. That was effectively the
  "power-up-RC-to-debug" step.
- The brief's mitigation was *"power off the controller
  before autonomous segments"*, but there was no operator
  reminder or annunciator at the transition from
  pre-launch → autonomous; the controller stayed on by
  default.
- §16's pre-OTH validation didn't include an RC-channel /
  mode-switch check.

### Candidate follow-ups (wrap-up)

- **Annunciator: RC controller detected with chan5 in
  non-GUIDED position during autonomous mode active**.
  Would have flashed an explicit pre-flight warning. ROS
  has all the data (mavros/rc/in + current mode).
- **Pre-launch checklist enforcement**: the brief's "RC
  mode switch to AUTO/GUIDED before autonomous segments"
  item is currently a doc line, not a verified checklist
  step. Bench-side `/diagnostics` entry showing
  "RC mode switch: MANUAL — manual override active"
  would force the conversation.
- **Look at `mavros/rc/in` + `mavros/state` from this
  deployment's bag** (the camera bag from §14 may have
  captured these via `/tf` + diagnostics; alternatively
  `~/data/logs/bizzy_images/...` mcap + a dataflash log
  pull from the FCU). Quantifying how much the RC
  inputs disrupted the GOTOs would close out this
  incident properly.

### Operator phase note

After this incident the practical move is to either
power off the RC controller, set chan5 to AUTO/GUIDED, or
finish in manual.

## 20. 1-hour bag closed cleanly

**2026-05-21T14:39-04:00** — `record_camera_topics.sh 3600`
from §14 finished at **14:25:26 EDT** via SIGINT, mcap
flushed cleanly.

### Bag stats

| Field | Value |
|---|---|
| Path | `~/data/logs/bizzy_images/bag_2026-05-21T13.25.26_ffmpeg_seg/` |
| Storage | mcap + zstd_fast |
| Size | **3.4 GiB** (~56 MB/min; 2026-05-19's rate was ~40 MB/min — higher today, likely from more dynamic camera content) |
| Duration | 3599.6 s (exact 1-hour run, SIGINT-flushed) |
| Total messages | 453,224 |
| Window | 13:25:26 → 14:25:26 EDT (covers §14 start through ~25 min post-14:00 hard stop) |

### Per-topic counts (the interesting ones)

| Topic | Count | Notes |
|---|---|---|
| `/bizzy/local_costmap/costmap` | **3,238** | Topic only joined the bag at `13:32:13` (the §16 forward-only relaunch) — pre-13:32 the publisher didn't exist (§15 failed bringup). ~1 Hz over the ~53 min it was up. |
| `/bizzy/sensors/cameras/oak_{forward,port,starboard,aft}/image_raw/ffmpeg` | 18,000–18,001 each | ~5 Hz × 3600 s, as designed |
| `…/segmentation` (raw + compressed + camera_info) × 4 cameras | 18,000–18,001 each | All four OAK directions producing segmentation continuously — the brief's "at least one OAK direction publishes segmentation" criterion is clearly exceeded |
| `/diagnostics` | 46,782 | ~13 Hz, matches §7 cadence |
| `/tf` | 115,186 | ~32 Hz (active boat) |
| `/tf_static` | 5 | One per latched frame, as expected |

### What this bag captures end-to-end

A complete record of the deployment's experimental window
from §14 start through recovery:

- **13:25–13:32** — pre-§15-restart state (chart_layer working,
  nav stack lifecycle stuck unconfigured, no local_costmap publisher)
- **13:32–13:38** — §16 forward-only relaunch; activation
  succeeds; tide offset chart_layer announcement; local_costmap
  starts publishing
- **13:39–13:47** — §17 OTH trackline outbound; udp_bridge#24
  per-event WARN log holding at 0
- **13:47–~14:00** — §18 wifi-out, Starlink-only ops at ~520 m
- **~14:00–14:25** — recovery + post-deployment quiescence
  (cameras still streaming on the cart)

This is the primary perception-replay artifact for offline
analysis of: the `SeaSurfaceLayer` segfault triggering
conditions (4-layer vs 1-layer comparison), the
`udp_bridge#24` per-event WARN demote validation, the
`mavros/.../global` chain behaviour over a full hour, and
the wifi-loss → Starlink-only transition geometry.

## 21. Recovery + final snapshot

**2026-05-21T14:42-04:00** — Roland: *"boat recovered"*.
Boat on the cart; ROS stack coming down. `mavros/...`,
`tide_estimate`, `/diagnostics` no longer publishing.
Power-down in progress.

### Final tally

| Metric | Value |
|---|---|
| `udp_bridge` per-event "Giving up on resend" total for the session | **0 / 162 KB log** |
| Brief Phase 2 criterion | **Met end-to-end** (2026-05-19 baseline was 27,992/2h) |
| Bag closed | §20 — 3.4 GiB, 453,224 messages, intact |
| Nav stack final state before tear-down | Active (forward-only sea_surface_layer per §16) |
| Boat recovery | Reported clean by Roland |

### Carry-forward for wrap-up (consolidated)

From sections 2, 9–11, 15–16, 18–19:

- **`unh_marine_perception#6`** — `SeaSurfaceLayer::matchSize`
  segfault, **not closed** by #11/#13. Post on #6 with §16
  crash log + 1-vs-4 layer contrast.
- **`#138` Z-source reconfig** — only the `EK3_SRC1_POSZ`
  half landed; `EK3_GPS_OFFS_*` rows in the brief turned out
  to be non-existent params (ArduPilot uses `GPS_POS1_*`,
  already correct). Brief #138 description needs correcting.
- **SBG–MAV vertical offset (`57a6134`)** — unchanged at
  ~0.62 m after today's CUAV-side reconfig. SBG IMU → base_link
  lever-arm needs URDF/TF work.
- **Nav lifecycle startup race** with `/global` chain
  (§15) — durable fix candidates: sequence
  `sea_surface_estimator` before Nav2 bringup, bump
  `local_costmap` activation wait, or `wait_for_transform`
  guard.
- **Brief carry-forward "RC mode-switch at fringe range"**
  bit hard (§19) — needs annunciator or enforced
  pre-flight check rather than doc-only mention.
- **URDF base_link-to-waterline freeboard** — residual
  73 cm of `tide_estimate` vs NOAA forecast (§13) consistent
  with unmodeled freeboard; candidate URDF / estimator
  param work.
- **Stale comment at `bizzyboat.yaml:234-237`** —
  references the 2026-05-19 revert as still active; needs
  rewrite as part of the §12 commit's PR review.
- **SSH-agent persistence on gabby** — workaround applied
  for 2nd deployment in a row; needs an actually-landed fix.

### Uncommitted state (Roland handling wrap-up)

| File | Repo | Status |
|---|---|---|
| `bizzyboat_project11/config/bizzyboat.yaml` | unh_echoboats | M — mru_transform → /global (§12) |
| `bizzyboat_project11/scripts/record_camera_topics.sh` | unh_echoboats | M — local_costmap added (§14) |
| `docs/logs/2026/2026-05-21_gabby_logs.md` | unh_echoboats | ?? — this file |
| `echoboat_project11/config/nav2_params.yaml` | seafloor_echoboat | M — sea_surface_layer forward-only (§16) |
| `bizzyboat_project11/config/fcu/mav.{parm,tlog,tlog.raw}` | unh_echoboats | ?? — MAVProxy artifacts; transient |

## 22. Buzzer source correction — not the FCU, looks like motor controllers

**2026-05-21T14:45-04:00** — Roland, after recovery:
*"beeps are still there, it's actually two things beeping
the same short-short-long signal at the same time. Around
the thrusters so I suspect motor controllers maybe?"*

This **invalidates §3's premise**. My entire FCU-buzzer
investigation (pre-arm checks, safety status, `status`
dump SYS_STATUS sensor health, RC failsafe hypothesis) was
looking at the wrong device. §3's *negative findings*
about the FCU remain valid — pre-arm clean, safety off,
sensor health OK, all of that's true — but the **buzzer
itself was never an FCU notification**.

### Revised hypothesis: thruster ESCs

Two sources beeping the same `short-short-long` pattern
*in sync*, physically located near the thrusters,
suggests both thruster ESCs (Electronic Speed Controllers)
in the same fault state. Common ESC behaviours that
generate audible patterns:

- Boot-time signal-detect / throttle calibration confirmation
- No-signal / signal-loss warning
- Low-battery warning (some marine ESCs)
- Locked-rotor / over-current / over-temp condition
- Programming-mode entry (some ESCs)

`servo_output_raw` from §7's status dump was at ~1500 µs
(neutral) for the thruster-relevant channels — that
*should* be a quiet/idle state for most ESCs. So either:

- The ESC interprets exactly-1500 µs as a fault rather
  than neutral (some models require a precise calibration
  window),
- The PWM signal is intermittent / has gaps that look like
  signal-loss to the ESC,
- Or these are a low-battery / over-temp signal that's been
  active since the start of the deployment.

### Wrap-up follow-ups (added to §21 list)

- **Identify BizzyBoat thruster ESC model + decode pattern**
  — short-short-long against the ESC's documented codes
  will give a positive ID of the condition.
- **Sanity-check `servo_output_raw` cadence vs ESC
  signal-loss timeout** — could be a publish-rate issue if
  the FCU isn't keeping the PWM up at the expected rate.
- **Operationally**: if these ESCs have been beeping since
  pre-launch and we still made GOTOs work (§8) and the OTH
  trackline (§17–18), the audible warning is presumably not
  blocking actuation — but it's a real condition the ESCs
  are flagging continuously.

### What this means for §3 in the log

Leaving §3 in place (it has diagnostic value — shows how
FCU buzzer investigations should be ruled out before
accepting an ESC-side hypothesis). Adding this section as
the correction; §3's "buzzer pattern unidentified" stays
correct because it never claimed FCU as the source, only
ruled out specific FCU mechanisms.

### Carry-forward

- **Audible notification provenance**. Twice now (different
  signatures, both deployments) we've spent minutes parsing FCU
  buzzer patterns by guesswork. A short cheat-sheet in
  `bizzyboat_project11/docs/` mapping common Rover patterns to
  their STATUSTEXT counterparts would pay for itself fast. Candidate
  follow-up issue at wrap-up.
- **MAVProxy `arm` subcommand syntax confusion**. Today's missteps
  on `arm check` / `arm preflight` are not a one-off — the
  ArduPilot/MAVProxy `arm` family has overloaded subcommands (some
  manipulate `ARMING_CHECK` bitmask, only `prearms` triggers a
  check cycle). Roland's correction stands as guidance going
  forward; saved to agent memory.
