# BizzyBoat deployment log — gabby — 2026-05-01

**Host**: gabby
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Deployment**: [#121](https://github.com/rolker/unh_echoboats_project11/issues/121)

## Scope

TBD as work proceeds.

## 1. ZDA serial bridge for M3 sonar wall-clock

**2026-05-01T10:00-04:00** — Roland flagged that the M3 sonar may need
NMEA `$ZDA` time/date sentences over a serial input for wall-clock
tagging. Asked which on-boat clock source is best for that.

Surveyed candidates:

- **`/bizzy/sensors/sbg/utc_time`** (`sbg_msgs/SbgUtcTime`) — purpose-built:
  carries explicit calendar fields (year/month/day/hour/min/sec/nano),
  already published at 1 Hz (canonical ZDA cadence), GPS-disciplined
  via the SBG, and includes a `clock_status` substruct (`clock_stable`,
  `clock_status` 0–3, `clock_utc_sync`, `clock_utc_status` 0–2) for
  gating output during cold-start. Already in the bag
  (`bizzyboat.yaml:251`).
- `/bizzy/mavros/time_reference` — also GPS-disciplined via the Cube
  Orange's GPS but a single timestamp; would need calendar arithmetic.
  Fallback only.
- System clock — ruled out per the 2026-04-09 NTP investigation; not
  reliably disciplined on the boat.

Picked the SBG topic.

**2026-05-01T10:15-04:00** — Roland: "write a quick package in
marine_tools to read the SBG time message and generate a $ZDA, default
to ttyS2 at 9600". Modeled the package shape on `sound_speed_bridge` (same
repo, similar role: ROS topic in, serial out).

New package:
[`marine_tools/zda_serial_bridge`](https://github.com/rolker/marine_tools)
(`71a5dec` on jazzy, gitcloud).

- `format_zda(year, month, day, hour, minute, second, nanosec, talker_id)`
  — pure-string formatter. Returns `$xxZDA,hhmmss.ss,dd,mm,yyyy,,*HH\r\n`
  with NMEA XOR checksum, CRLF terminator, empty local-zone fields
  (UTC). Centisecond fractional precision via `%05.2f`; leap-second
  case (`sec=60`) keeps two integer digits cleanly.
- Output gating on `SbgUtcTimeStatus.clock_utc_status >= min_utc_status`
  (default 1: "valid UTC, no leap-seconds info"). Bumpable to 2 if a
  consumer cares about leap-second correctness. Optional
  `require_utc_sync` adds a PPS-sync requirement.
- Serial reconnect loop with throttled retry on write errors
  (`reconnect_delay_sec`, default 2 s).
- `/diagnostics`: serial state, write/suppressed/error counts, last-emit
  age, last `clock_utc_status` / `clock_utc_sync`, last status text.
- 6 unit tests on `format_zda` (basic, checksum-matches-body,
  zero-padding, leap second, talker-id override, fractional rollover)
  plus the standard flake8 / pep257 lint tests. 8/8 pass under
  `colcon test --packages-select zda_serial_bridge`.

**2026-05-01T10:24-04:00** — Verified the SBG was fully synced before
launching the bridge: `ros2 topic echo --once /bizzy/sensors/sbg/utc_time`
showed `clock_status=3` (PPS-converged within 500 ns), `clock_utc_sync=true`,
`clock_utc_status=2` (valid UTC with leap seconds). Reporting
`2026-05-01 14:24:23 UTC`.

Started the standalone launch:

```
ros2 launch zda_serial_bridge zda_serial.launch.py
```

(Defaults: `/dev/ttyS2 @ 9600`, talker `GP`, remap `utc_time` →
`/bizzy/sensors/sbg/utc_time`.) Diagnostic at +20 s showed `OK`,
`write_count=16`, `suppressed_count=0`, `serial_error_count=0`,
`last_emit_age_s=0.76`. Exactly one ZDA per `SbgUtcTime` message, no
backlog, no errors.

**2026-05-01T10:35-04:00** — Roland confirmed `$GPZDA` reaching the M3's
debug window cleanly. Sample bytes-on-the-wire (from the live
formatter, captured before launch):

    $GPZDA,165612.50,01,05,2026,,*66\r\n

**2026-05-01T10:50-04:00** — Wired the bridge into the boat's core launch
in `unh_echoboats_project11` (`7d7ce0e` on jazzy, gitcloud):

- `bizzyboat_project11/launch/zda_launch.py` — new file, mirrors
  `sound_speed_launch.py`'s shape. `Node(zda_serial_bridge)` with
  `respawn=True`, remap `utc_time → /<ns>/sensors/sbg/utc_time`,
  defaults `/dev/ttyS2 / 9600 / GP` overridable via launch args.
  No namespace push or frame_prefix — no topics published, no sensor
  frame.
- `bizzyboat_project11/launch/core_launch.py` — include `zda_launch.py`
  inside the existing `PushRosNamespace` group, immediately after the
  `sound_speed_launch.py` include. `launch_arguments={'namespace': namespace}`.
- `bizzyboat_project11/package.xml` —
  `<exec_depend>zda_serial_bridge</exec_depend>`. `marine_tools` is
  already in `config/repos/core.repos` from yesterday's hotfix
  (`4ae7fee`), so a `make sync` + `colcon build` is enough to pick up
  the new package without a manifest change.

Verified by build + a Python launch-description load through the
installed share/ paths: both `zda_launch.py` (5 entities) and
`core_launch.py` (8 entities) parse without error.

**2026-05-01T10:58-04:00** — Killed the standalone test node so the next
`start_tmux_project11.bash` doesn't have two consumers fighting for
`/dev/ttyS2`. On exit the node printed an `RCLError: failed to
shutdown: rcl_shutdown already called` traceback — the standard rclpy
double-shutdown footgun where the SIGINT signal handler calls
shutdown internally and then `main()`'s `finally:` calls it again.
Cosmetic; the process exited correctly. `sound_speed_bridge` has the
exact same pattern, so leaving the fix to a future bundled cleanup
across both packages rather than churning a one-line commit now.

### Follow-up

- Future: `clock_utc_status=2` is achievable on this SBG; consider
  bumping `min_utc_status` default from 1 to 2 once we're sure all
  downstream M3 / sounder consumers care about leap-second-correct
  time. Conservative default for now.
- Future: harmonize the rclpy shutdown pattern in `zda_serial_bridge`
  and `sound_speed_bridge` to avoid the cosmetic shutdown traceback
  (e.g. `if rclpy.ok(): rclpy.shutdown()` in `main()`'s finally).

## 2. SBG-vs-FCU nav comparison readiness

Pre-relaunch audit driven by Roland's question: are we logging the
right topics, with the right frame_ids, to do a meaningful
SBG-vs-FCU comparison at base_link from the bag?

### 2.1 Logger gap — `mavros/local_position/*` was missing

**2026-05-01T11:05-04:00** — Audited `bizzyboat.yaml` topics list. SBG
side complete (all 9 topics). FCU side covered `imu/data`,
`global_position/{global,raw/fix,raw/gps_vel}`, `gpsstatus/gps1/raw`,
`state`, `rc/out`, `nav_controller_output`, plus `/bizzy/odom`. But
**no `mavros/local_position/*` topic** — those are the FCU EKF3-fused
outputs from the recently-landed `#91` switch and the most direct
counterparts to SBG `ekf_nav` / `ekf_quat`. Notably,
`local_position/velocity_body` is consumed by `mru_transform` but was
never bagged.

Added five topics to the `logger.topics` list in
`bizzyboat_project11/config/bizzyboat.yaml`:

- `/bizzy/mavros/local_position/odom`
- `/bizzy/mavros/local_position/pose`
- `/bizzy/mavros/local_position/velocity_local`
- `/bizzy/mavros/local_position/velocity_body`
- `/bizzy/mavros/local_position/accel`

YAML parses cleanly (62 logger topics now). `colcon build
--packages-select bizzyboat_project11` to ship the updated yaml to
`install/`. Not committed yet — batched with later config tweaks.

### 2.2 ZDA launch-arg collision regression

**2026-05-01T11:15-04:00** — Roland relaunched core to test the PPS
cable. Reported "I'm not seeing zda on the other end". Pulled the
running node's params:

```
ros2 param get /bizzy/zda_serial_bridge device   →   /dev/ttyS0
```

Wrong port — should have been `/dev/ttyS2`. Root cause:
**`LaunchConfiguration` namespace is global within a launch tree.**
`zda_launch.py` declared `device` with default `/dev/ttyS2`, but
`sound_speed_launch.py` had already declared the same arg name with
default `/dev/ttyS0` earlier in the same `core_launch` invocation.
First-declared default wins for any `LaunchConfiguration('device')`
read, so the ZDA node inherited sound_speed's value. Same hidden
collision on `baud` (both default 9600 — silently fine) and
`talker_id` (only ours uses it — also silently fine).

Compounding effect: gabby's ttyS0 has the TX-side fault from
2026-04-29 §6.4, so the ZDA bytes the bridge thought it was emitting
were going into the void.

Fixed by renaming all three args in `zda_launch.py` to be `zda_`-prefixed:

- `device` → `zda_device`
- `baud` → `zda_baud`
- `talker_id` → `zda_talker_id`

Added an explanatory comment so the next agent doesn't undo it.
`grep -h DeclareLaunchArgument launch/*.py | uniq -d` returned
empty after the fix — no remaining duplicates across all boat-side
launch files.

`marine_tools/zda_serial_bridge/launch/zda_serial.launch.py` (the
standalone) was left as-is — that one is invoked alone and has no
collision risk.

`colcon build --packages-select bizzyboat_project11`. Roland
relaunched core; verified the diagnostic now shows
`device=/dev/ttyS2`, `write_count` climbing, `serial_error_count=0`.
M3 receiving ZDA again.

### 2.3 Frame-ID survey (live, post-relaunch)

**2026-05-01T11:35-04:00** — One-shot `ros2 topic echo --once` on
every relevant nav topic. Snapshot:

| Topic | frame_id | Notes |
|---|---|---|
| `mavros/imu/data` | `bizzy/base_link` | clean |
| `mavros/global_position/global` | `bizzy/base_link` | clean |
| `mavros/global_position/raw/fix` | `bizzy/base_link` | clean |
| `mavros/local_position/odom` | `bizzy/map` (child `base_link` bare) | yesterday's plugin no-op |
| `mavros/local_position/pose` | `bizzy/map` | clean |
| `mavros/local_position/velocity_local` | `base_link` (bare) | yesterday's plugin no-op |
| `mavros/local_position/velocity_body` | `base_link` (bare) | yesterday's plugin no-op |
| `mavros/local_position/accel` | — | publisher exists, no msg yet |
| `/bizzy/odom` (mru_transform) | `bizzy/odom` | clean |
| All 9 SBG topics | `imu_link_ned` | URDF gap (no `imu_link_ned` link) |

The bare-`base_link` cases on three of the new local_position topics
confirm the [2026-04-29 §5](2026-04-29_gabby_logs.md) mavros plugin
no-op is still live. The static-TF identity bridges in
`core_launch.py` keep TF lookups resolvable; `tf` and `tf_static` are
in the bag, so post-flight TF-to-base_link will work for FCU.

SBG side is uniformly `imu_link_ned`. That URDF gap from
`sbg_ellipse_d.yaml:58-59` (`# TODO: align with URDF frame once an
SBG link is added`) is unchanged. Per pre-relaunch discussion: data
captured consistently, post-flight transform applicable once the
SBG's lever arm to base_link is measured. Not blocking today.

### 2.4 Logger subscription verification

Verified all 5 new local_position topics show the boat logger as a
live subscriber:

```
ros2 topic info <topic> --verbose | grep logger
```

returns 1 match for each. Subscription counts: odom=1, pose=2,
velocity_local=1, velocity_body=3, accel=1.

### 2.5 SBG cable repair window

**2026-05-01T11:50-04:00** — Roland disconnected the SBG cable to
finish a repair (presumably the PPS line he'd flagged earlier). All
SBG topics went silent for the duration. The ZDA bridge's
diagnostic correctly reported `No SbgUtcTime for 204.8s` while the
cable was off, and the M3 saw zero ZDA in that window — confirming
the gating logic does the right thing on a real-world stale-input
event, not just at cold-start.

**2026-05-01T12:00-04:00** — Cable reconnected. Re-verified all SBG
topics flowing at expected rates: imu_data / ekf_nav / ekf_quat /
mag at 25 Hz, gps_pos / gps_vel / gps_hdt at 5 Hz, utc_time / status
at 1 Hz. Clock back to `clock_status=3` (PPS-converged <500 ns),
`clock_utc_sync=true`, `clock_utc_status=2`. ZDA bridge resumed
emission once status >= 1. `suppressed_count=223` in the diagnostic
captured the early-bringup window where utc_time was arriving but
clock had not yet locked UTC — visible proof the gate was doing its
job, and a useful diagnostic to keep an eye on.

### 2.6 Position sample at the dock

**2026-05-01T12:10-04:00** — Sampled positions from all four
candidate sources to see how they relate:

```
FCU EKF3 (global)      43.0720430, -70.7116608   alt=-23.739 m
SBG EKF (ekf_nav)      43.0720431, -70.7116608   alt=  9.978 m
FCU raw GPS (fix)      43.0720417, -70.7116506   alt=-21.069 m
SBG raw GPS (gps_pos)  43.0720451, -70.7116735   alt= 10.902 m
```

Horizontal Δ (haversine):

| Pair | Δhoriz | Δalt |
|---|---|---|
| FCU EKF vs SBG EKF | **0.013 m** | -33.72 m |
| FCU EKF vs FCU raw | 0.84 m | -2.67 m |
| SBG EKF vs SBG raw | 1.06 m | -0.92 m |
| FCU raw vs SBG raw | 1.90 m | -31.97 m |

Horizontal: **the two EKF outputs agree to 1.3 cm at the dock**.
Both projecting to each unit's configured logical reference. The
**raw GPS antennas are physically ~1.9 m apart** — sane for the
boat's GNSS layout. Each EKF moves its raw value by ~1 m to land at
its configured CG/base_link, and the two CGs converge.

FCU RTK status verified separately via
`/bizzy/mavros/gpsstatus/gps1/raw` (NavSatFix doesn't carry RTK
state; mavros's `GPSRAW` does):

```
fix_type: 6                ← RTK_FIXED
satellites_visible: 35
h_acc: 23 mm   v_acc: 33 mm
yaw: 10192     ← 101.92° dual-antenna heading
alt:           +6.020 m   (MSL — see §2.7)
alt_ellipsoid: -21.695 m  (WGS84)
```

So **both nav sources are RTK-locked and tight**: FCU 2.3 cm
h_acc, SBG `status.type=7` RTK_INT with `position_accuracy.x/y =
1.41 cm`.

### 2.7 Altitude convention — different geoid models

The 33 m vertical gap between FCU and SBG looked alarming but
unwound cleanly into a vertical-datum convention difference, not a
sensor disagreement.

**SBG altitude convention** — `gps_pos` carries both `altitude` and
`undulation`:

```
altitude:    10.912797 m
undulation: -32.491897 m
```

`altitude` here is **orthometric/MSL** (already geoid-corrected, not
ellipsoidal as initially assumed). To recover ellipsoidal:

```
ellipsoidal = altitude + undulation = 10.913 + (-32.492) = -21.579 m
FCU alt_ellipsoid                                       = -21.695 m
```

**FCU and SBG agree on WGS84 ellipsoidal height to within 11 cm.**
The 33 m apparent gap was entirely a vertical-datum convention
difference between MSL (SBG default) and ellipsoidal (FCU NavSatFix
default).

The remaining 4.9 m MSL-vs-MSL gap (FCU `alt`=+6.02 vs SBG
`altitude`=+10.91) is **two different geoid models**:

```
FCU geoid offset (alt_ellipsoid → alt):  6.020 - (-21.695) =  27.715 m
SBG geoid offset (undulation):                                32.492 m
Δ                                                              4.777 m
```

Portsmouth NH EGM2008 undulation is approximately 28 m, so the FCU's
27.7 m matches modern EGM2008. The SBG's 32.5 m is closer to older
EGM84/EGM96 territory or a vendor-specific adjustment. Both units
are internally self-consistent — they just disagree on which geoid
to subtract.

**Practical implication for downstream consumers** (chart-datum,
tide-corrected pipelines, etc.):

- For SBG-vs-FCU comparison in post: use **WGS84 ellipsoidal as the
  common reference** (FCU `alt_ellipsoid`; SBG `altitude + undulation`).
- For any user-facing MSL display: pick **one** geoid model and apply
  it to both sources. Don't mix the two units' MSL values.

Worth noting on the bag side: `mavros/global_position/raw/fix`
publishes ellipsoidal altitude in `NavSatFix.altitude` (the
`alt_ellipsoid` value, not `alt`). So FCU's bagged altitude is
already ellipsoidal — comparison-friendly with `SBG altitude +
undulation`. No bag-config change needed for this; just a post-
processing convention to document.

### 2.8 Attitude sample at the dock

**2026-05-01T13:00-04:00** — Sampled orientation from each EKF plus
the FCU's dual-antenna GPS heading. FCU `mavros/imu/data` lives in
ENU body (REP-103: X=forward, Y=left, Z=up). SBG `ekf_quat` lives in
NED body (X=forward, Y=right, Z=down) per `sbg_ellipse_d.yaml`'s
`use_enu: false`.

Quaternions converted to Tait-Bryan ZYX (roll-X, pitch-Y, yaw-Z) in
each source's native frame, then yaw rebased to compass heading
(0=N, 90=E, CW from above) for an apples-to-apples comparison:

| Source | Roll (native) | Pitch (native) | Yaw (native) | Compass heading |
|---|---|---|---|---|
| FCU `imu/data` (ENU) | -1.208° | +0.922° | -11.984° | **101.984°** |
| SBG `ekf_quat` (NED) | +0.181° | -0.660° | +102.138° | **102.138°** |
| FCU dual-antenna GPS (`gpsstatus/gps1/raw.yaw`) | — | — | — | **102.020°** |

**Heading agreement** (compass-common reference):

| Pair | Δ |
|---|---|
| FCU IMU vs SBG IMU | -0.154° |
| FCU IMU vs FCU dual-antenna | -0.036° |
| SBG IMU vs FCU dual-antenna | +0.118° |

All three within 0.15° at the dock — excellent.

**Roll / pitch — frame-convention notes before reading the numbers**:

- **Roll** (about X=forward) has the **same sign** in both ENU and
  NED: positive = right-wing-down.
- **Pitch** (about Y) **flips sign** between ENU (Y=left) and NED
  (Y=right). FCU ENU pitch +0.92° ↔ SBG NED pitch -0.66° both
  describe **nose-down** (FCU 0.92°, SBG 0.66°). Magnitude Δ ~0.26°
  — within sensor noise at the dock.
- **Roll**: FCU -1.21° (left-wing-down 1.21°) vs SBG +0.18°
  (right-wing-down 0.18°). **|Δroll| ≈ 1.39°.** That is well beyond
  either unit's 1-sigma — it looks like a real **static mounting
  misalignment** between the SBG enclosure and the FCU IMU's body
  axis. The kind of constant offset that an SBG URDF link with the
  measured mounting rotation would absorb. Currently uncalibrated;
  carry forward.

**SBG `ekf_quat.accuracy`** (1σ, body axes; field is in radians):

| Axis | accuracy |
|---|---|
| x (roll) | 0.130° |
| y (pitch) | 0.130° |
| z (yaw) | 0.233° |

Both units self-report tightly; the cross-source disagreements are
~1× SBG-yaw-1σ on heading and ~10× on roll, which is consistent
with "tight angular discipline + a real roll mounting offset", not
with an EKF problem on either side.

### Follow-up

- Commit `bizzyboat.yaml` and `zda_launch.py` changes (§2.1 + §2.2).
  Batched for now.
- Roadmap-track: SBG URDF link with **measured rotation as well as
  translation** — the §2.8 ~1.4° static roll offset between the two
  IMUs is exactly the residual that the URDF mounting transform
  needs to absorb. Not blocking today; flag for a bench session.
- Roadmap-track: capture the geoid-convention difference in a doc
  note alongside chart-datum / tide-correction pipeline docs so
  future agents don't rediscover it.

## 3. Camera bandwidth audit + tweaks

**2026-05-01T13:30-04:00** — Sampled per-stream bandwidth on the four
OAK cameras + the USB cam to size up the VPN/WiFi load against
yesterday's ~4.1 Mbps udp_bridge / ~5 Mbps Starlink ceiling finding.
Methodology: parallel `ros2 topic bw` on each topic for ~10 s
(~5 Hz × 50 messages each).

Per-stream measured rates (boat at the dock, no scene motion):

| Stream | KB/s | ~Mbps |
|---|---|---|
| `oak_forward/image_raw/ffmpeg` | 113.5 | 0.91 |
| `oak_starboard/image_raw/ffmpeg` | 102.4 | 0.82 |
| `oak_aft/image_raw/ffmpeg` | 95.9 | 0.77 |
| `oak_port/image_raw/ffmpeg` | 97.9 | 0.78 |
| `oak_forward/segmentation/compressed` | 34.1 | 0.27 |
| `oak_starboard/segmentation/compressed` | 30.6 | 0.24 |
| `oak_aft/segmentation/compressed` | 26.1 | 0.21 |
| `oak_port/segmentation/compressed` | 26.2 | 0.21 |
| `usb/image_raw/compressed` | 22.2 | 0.18 |
| `usb/image_raw/ffmpeg` | (no subscriber, dormant) | — |

Per-camera totals (FFMPEG + segmentation/compressed):
forward 1.18 Mbps, starboard 1.06 Mbps, aft 0.97 Mbps, port 0.99 Mbps.
USB 0.18 Mbps. **All cameras combined: ~4.4 Mbps on the bus.** Most
of that traverses one or both of WiFi / VPN per the udp_bridge
config. USB ffmpeg is dormant — no subscriber driving the
image_transport encoder. Not a problem.

### 3.1 Forward camera encoder bitrate: 1000 → 800 kbps

`oak_forward` was configured at `h265_bitrate_kbps: 1000` while the
other three OAKs were at 800 kbps. The measured 113.5 KB/s ≈ 910 kbps
matches that config. Equalised at 800 kbps in
`bizzyboat_project11/launch/oak_cameras_launch.py` to cut the asymmetry
and recover ~200 kbps everywhere the forward stream is forwarded.
Takes effect on the next core relaunch.

### 3.2 oak_aft FFMPEG dropped from VPN topics_list

VPN uplink is the bandwidth-constrained path. Dropped
`oak_aft_ffmpeg` from
`/**/udp_bridge.../connections.vpn.topics_list` in `bizzyboat.yaml`,
along with its dict entry. **Kept `oak_segmentation_aft`** on VPN
(1 Hz / ~42 kbps over VPN) so the operator still gets the rear
classification overlay for situational awareness; just not the live
~770 kbps video feed.

The WiFi-bridge entry for `oak_aft_*` is **unchanged** — operator
still has the full rear stream when on WiFi, drops only when traffic
is forced onto Starlink/VPN.

Net VPN savings expected: ~770 kbps from aft ffmpeg + ~200 kbps from
the forward bitrate cut on whatever streams traverse VPN, total
roughly **1 Mbps off the VPN path**. Yesterday VPN sat at ~4.1 Mbps
against a ~5 Mbps Starlink ceiling, so this should restore real
headroom.

## 4. FCU `FS_THR_ENABLE` set to 0 (RC throttle failsafe disabled)

**2026-05-01T14:00-04:00** — Roland asked for the current
`FS_THR_ENABLE` value, then to set it to 0.

```
before: Integer value is: 2  (Hold on RC throttle loss)
set:    Set parameter successful
after:  Integer value is: 0  (Disabled — no failsafe action)
```

ArduRover semantics for `FS_THR_ENABLE`:
0 = Disabled, 1 = Enabled, 2 = Hold, 3 = Hold + Disarm. Setting 0
removes any automatic action when the RC throttle PWM goes invalid;
the FCU will simply continue executing whatever was most recently
commanded (autonomous setpoints in our case). Sensible for a boat
operating fully autonomously where there's no live RC controller to
fall back to.

Path used:

```
ros2 service call /bizzy/mavros/param/pull mavros_msgs/srv/ParamPull \
    "{force_pull: false}"
ros2 param get /bizzy/mavros/param FS_THR_ENABLE
ros2 param set /bizzy/mavros/param FS_THR_ENABLE 0
```

The mavros `mavros_msgs/srv/ParamGet` service consistently hung for
me even after a successful `ParamPull`. The working pattern is the
**standard ROS 2 param interface against the `/bizzy/mavros/param`
node** (the mavros parameter sub-node), once the param cache has been
populated by a `ParamPull`. Mavros pushes the value through MAVLink
to the FCU under the hood; flash persistence is handled by the FCU
itself.

## 5. Network egress check + Starlink diag stall

**2026-05-01T14:30-04:00** — Roland asked which path the boat router
is using for internet, then which Starlink diagnostics look like.

### 5.1 Active internet path: Starlink (`wan` / eth1)

Pulled the Teltonika diagnostic from `/diagnostics` (filter on
`hardware_id == 'router.bizzy'`). mwan3 multi-WAN snapshot:

| mwan3 entry | status | enabled | l3_device | proto |
|---|---|---|---|---|
| **wan** | **Online** | True | eth1 | dhcp |
| mob1s1a1 | Standby | True | wwan0 | wwan (cell SIM 1) |
| mob1s2a1 | notracking | False | (Down) | wwan (cell SIM 2) |
| wan1 | notracking | False | wlan1-4 | dhcp (WiFi bridge) |

So internet egress is going out **`wan` / eth1 = Starlink**. **Cell
SIM 1** sits on warm Standby (LTE -72 dBm RSRP, healthy) ready to
take over on Starlink failure. The **WiFi bridge** to operator
(`wan1` / wlan1-4) is up at the interface level but disabled in
mwan3 — it carries LAN-to-operator traffic only, not internet
egress. Consistent with yesterday's bandwidth attribution
([2026-04-29 dev §"udp_bridge saturating Starlink uplink"](2026-04-29_dev_logs.md))
showing the WiFi bridge as the high-throughput LAN path while
Starlink is the constrained internet path.

`bcloud` WireGuard tunnel is up, riding on top of the active `wan`.

### 5.2 Starlink diagnostics: stale node, healthy dish

First check showed all six `starlink.bizzy` diagnostic statuses as
**STALE — no dish response for 247.9 s**. Cached values from before
the stall looked good (0% drop, 17.9 ms pop latency, 5.6 Mbps up,
0.02% obstruction, no thermal/SNR alerts), but the ROS reporting was
clearly broken.

Disambiguated dish-vs-node:

```
ping 192.168.100.1            → 0% loss, 1.07 ms RTT
TCP 192.168.100.1:9200        → OPEN
ros2 node list | grep starlink → /bizzy/starlink_diagnostics  (alive)
```

Dish itself fine, gRPC port open. The **`starlink_diagnostics` ROS
node was alive but its poller was stuck** — most likely a stalled
gRPC connection. The dish was in fact actively routing internet at
the time per §5.1 (`wan` mwan3 status Online).

### 5.3 Kicked the node — no respawn supervision (carry-forward)

Tried to `kill -INT $PID` expecting launch's `respawn=True` to
resurrect it. **It didn't come back.** Looking at
`bizzyboat_project11/launch/network_monitor_boat_launch.py:29-35`:

```python
Node(
    package='starlink_stats',
    executable='starlink_diagnostics_node',
    name='starlink_diagnostics',
    parameters=[bizzyboat_config],
    output='screen',
),
```

No `respawn=True` — unlike the other long-running drivers (sbg,
zda, sound_speed) which all have it. Restarted manually with the
exact argv that launch was using (recovered from the `[ERROR]
process has died` line in `~/.ros/log/latest/launch.log`):

```
/home/field/project11/layers/main/sensors_ws/install/starlink_stats/lib/starlink_stats/starlink_diagnostics_node \
    --ros-args -r __node:=starlink_diagnostics -r __ns:=/bizzy \
    --params-file <bizzyboat.yaml> ...
```

Diagnostic recovered immediately:

| Sub-status | Level | Message |
|---|---|---|
| comms | OK | dish reachable (1.0 s ago) |
| state | OK | state not reported by dish |
| link | OK | 0.0% drop, 21 ms |
| obstruction | OK | 0.02% obstructed |
| thermal | OK | no thermal alerts |
| alerts | OK | no alerts |

**Carry-forward (real)**: add `respawn=True, respawn_delay=2.0` to
the `starlink_diagnostics` Node in `network_monitor_boat_launch.py`
so this self-heals on the next stuck-gRPC event. The same probably
applies to `mikrotik_monitor`, `teltonika_monitor`, and
`ping_monitor` in that file — should audit and add respawn to the
ones that lack it. Not blocking; the dish was healthy throughout.

**Carry-forward (also)**: investigate why the gRPC connection
stalls in the `starlink_diagnostics_node`. A stuck connection that
the running process can't recover from is a node-level robustness
bug — `starlink-grpc-tools`-style libraries usually rebuild the
channel on a per-poll basis or honor a deadline. Worth a real fix
upstream in the `starlink_stats` package.

## 6. FCU failsafe audit (snapshot)

**2026-05-01T15:30-04:00** — After the §4 `FS_THR_ENABLE=0` change,
Roland asked for the broader failsafe picture. Pulled every
`FS_*`, `BATT_FS_*`, `BATT_LOW_*`, `BATT_CRT_*`, and `FENCE_*` param
from the FCU via `ros2 param list /bizzy/mavros/param` then a
batched `ros2 param get` over the relevant subset. ArduRover 4.5
semantics.

**Headline: nearly every FCU-level failsafe is disabled**, with
thresholds left configured but actions zeroed. The boat relies on
the autonomy stack (mission_manager + BT + CAMP) for safety, not the
autopilot.

| Category | Status | Notes |
|---|---|---|
| General `FS_ACTION` | Disabled | No FCU-side response to any failsafe trigger |
| RC throttle (`FS_THR_ENABLE`) | Disabled (was 2 / Hold) | Changed today — see §4 |
| GCS link (`FS_GCS_ENABLE`) | Disabled | No reaction to lost GCS — normal at sea |
| EKF health (`FS_EKF_ACTION`) | Disabled | Threshold stored, action zero |
| Crash check (`FS_CRASH_CHECK`) | Disabled | |
| Battery low (`BATT_FS_LOW_ACT`) | None | 23.0 V / 10 s threshold fires MAVLink statustext only |
| Battery critical (`BATT_FS_CRT_ACT`) | None | 21.5 V threshold, statustext only |
| Geofence (`FENCE_ENABLE`) | Disabled | 0 polygon pts, 300 m circle configured but inert |

### Full snapshot (2026-05-01T15:30 EDT)

```
FS_TIMEOUT          1.0 s
FS_ACTION           0           (Nothing | 1=RTL 2=Hold 3=SmartRTL/RTL 4=SmartRTL/Hold 5=Terminate)
FS_OPTIONS          0           (bitmask)
FS_THR_ENABLE       0           Disabled (was 2=Hold; changed today)
FS_THR_VALUE        910 PWM
FS_GCS_ENABLE       0
FS_GCS_TIMEOUT      5.0 s
FS_EKF_ACTION       0
FS_EKF_THRESH       0.80
FS_CRASH_CHECK      0
BATT_FS_LOW_ACT     0           None
BATT_FS_CRT_ACT     0           None
BATT_FS_VOLTSRC     0           Raw voltage (no sag compensation)
BATT_LOW_VOLT       23.0 V      (per 2026-04-29 dev commit a72125b)
BATT_LOW_TIMER      10 s
BATT_CRT_VOLT       21.5 V
BATT_LOW_MAH        0           disabled
BATT_CRT_MAH        0           disabled
FENCE_ENABLE        0           Disabled
FENCE_TYPE          7           altitude_max | circle | polygon (bitmask)
FENCE_ACTION        1           RTL (inert)
FENCE_RADIUS        300 m
FENCE_MARGIN        3 m
FENCE_TOTAL         0           polygon point count
```

### Implications

- **No automatic safety net at the autopilot layer.** When the
  autonomy stack stops commanding — exactly the
  cmd_vel-silent / BT-stuck event that surfaced earlier this
  session ([§7 below], if/when it gets logged) — the FCU just
  holds last-commanded velocity. There's no FCU-level "stop and
  hold" intervention.
- Battery thresholds produce MAVLink `STATUSTEXT` warnings (which
  reach the operator annunciator) but the FCU will not slow, stop,
  or RTL on its own at low/critical voltage.
- Coherent design choice for an autonomous boat — RC failsafes,
  GCS-link failsafes, and FCU-level RTL all have plausible
  off-by-design reasons in this environment — but it does mean the
  **operator-side annunciator + mission_manager are the only
  watchdogs**. Anyone reviewing operator-side health-monitoring
  configuration should know this baseline: the FCU is **not** doing
  belt-and-suspenders for them.

### Carry-forward

- Confirm operator-side annunciator alarms exist for: battery
  STATUSTEXT (low + critical), EKF health degradation, lost-link
  conditions (boat→operator and op→shore). These are what's left as
  watchdogs given the FCU is hands-off.

## 7. RC mode switch latching FCU into Loiter

**2026-05-01T15:38-04:00** — Roland: "Something is triggering the
state to go to Loiter, what is it?"

Live state was `mode: GUIDED, armed: true, guided: true`. Set up a
22 s state+statustext watcher — no transitions caught in the
window. So mode flipping is intermittent, not always-on.

Failsafes ruled out as triggers (per [§6](#6-fcu-failsafe-audit-snapshot)
all FCU-level failsafes are disabled, and we just ran the audit).
`MIS_DONE_BEHAVE=1` (Loiter on mission complete) was suspicious but
only fires from AUTO mode, and the boat operates in GUIDED.

### 7.1 Root cause: RC channel 5 mode switch parked in a Loiter slot

```
MODE_CH       = 5         RC channel 5 controls FCU mode
MODE1         = 0         Manual    (≤ ~1230 PWM)
MODE2         = 0         Manual    (~1230-1360)
MODE3         = 5         Loiter    (~1360-1490)  ← <- here
MODE4         = 5         Loiter    (~1490-1620)
MODE5         = 10        Auto      (~1620-1750)
MODE6         = 10        Auto      (≥ ~1750)
INITIAL_MODE  = 0         Manual at boot
```

Earlier RC sample (from §"is RC still in range" check at ~14:21) had
**ch5 at PWM 1402** — which sits in the **MODE3 = Loiter** band.
The transmitter was parked in a slot that maps to Loiter.

Why Roland was seeing intermittent transitions despite `set_mode
GUIDED` from autonomy: ArduRover re-evaluates the RC mode channel on
events like an RC packet drop+reacquire, an internal state-machine
tick, or a band-boundary crossing. Each re-evaluation latches mode
to the channel's mapping. The autonomy stack
(`seafloor_echoboat_project11/echo_helm/src/echo_helm_node.cpp:218,
:227` — `set_mode_request->custom_mode = "GUIDED"|"MANUAL"`)
then races back to GUIDED. The cycle repeats whenever the FCU
re-evaluates RC.

### 7.2 Fix applied — RC switch moved to Manual band

**2026-05-01T15:43-04:00** — Roland physically moved the ch5 switch
to a Manual slot. Verified: **ch5 PWM = 1161** (MODE1 = Manual).
Live `/bizzy/mavros/state` still `mode: GUIDED, guided: true,
armed: true` — autonomy in control as expected.

**Net effect**: any future RC-driven mode re-evaluation now lands on
**Manual** instead of Loiter. On a boat, Manual = direct RC stick
control — with no operator hand on the sticks the boat just stops /
idles. Much safer fallback than Loiter (which actively commands
thrust to hold position, fighting whatever the autonomy is
trying to do).

### 7.3 Future hardening options (none applied today)

In increasing intrusiveness:

1. **Re-map `MODE3` / `MODE4`** away from Loiter — e.g. `4` (Hold)
   so any switch position becomes a stop-and-disarm rather than an
   active position-keep that fights the autonomy.
2. **Set `MODE_CH = 0`** to disable RC mode switching entirely. FCU
   then only mode-changes via MAVLink (the autonomy stack). Cleanest
   for fully-autonomous ops, but loses the manual-override-via-RC
   option.

Today's "park the switch in Manual" fix is enough for the current
deployment; the above are documented here as roadmap items.

### Carry-forward

- Update the boat's hardware / RC docs (likely
  `bizzyboat_project11/docs/bizzyboat_hardware.md` or similar) to
  note: **the RC mode switch should be parked in a Manual slot any
  time the boat is operating autonomously**, with the rationale
  above. Avoids future surprise re-discoveries of the same
  Loiter-latching behavior.
- Consider option 1 above (`MODE3 = MODE4 = 4` for Hold) as a
  belt-and-suspenders against an inadvertent switch nudge during
  ops.

## 8. Network resilience — out-of-sight ops + WiFi-drop test

Over the afternoon the boat went out of visual line-of-sight, then
Roland intentionally dropped the WiFi bridge to characterise comms
failover behaviour.

### 8.1 Out-of-sight baseline (boat past WiFi range)

**2026-05-01T15:50-04:00** — Boat went past WiFi-bridge LOS. Pulled
a comprehensive health snapshot. State was clean: FCU GUIDED/armed,
`setpoint_velocity` 10 Hz, RTK locked on both nav sources (FCU
fix_type=6, SBG status.type=7), battery 26.39 V (well above the
23.0 V LOW threshold from §6), Starlink Online, cell on warm
Standby.

What's already-broken-by-design when out of WiFi range, surfacing as
WARN/ERROR in `/diagnostics`:

```
[ERROR] ping.bizzy: salmon_direct      100% packet loss
[ERROR] ping.bizzy: router_op_direct   100% packet loss
[WARN]  wifi.bizzy: interface/wlan1    Not running
[WARN]  wifi.bizzy: interface/ether{2,3,4,5}  Not running
```

The four `etherN` warns are the unused MikroTik dish ports — already
in [2026-04-29 dev §"Annunciator config noise"](2026-04-29_dev_logs.md)'s
"100% WARN over the survey" list — they're noise, not new. The
`ping_monitor` salmon_direct / router_op_direct ERRs are the real
WiFi-bridge-loss signal.

The other WARN we always carry — `mavros: Mount: Can not diagnose in
this targeting mode` — is cosmetic.

### 8.2 Intentional WiFi-bridge drop test

**2026-05-01T16:25-04:00** — Roland deliberately dropped the WiFi
bridge to validate failover behaviour. Boat was mid-mission at the
time. Observations after the drop:

| | Before drop | After drop |
|---|---|---|
| FCU mode + arm | GUIDED, armed | unchanged |
| `setpoint_velocity/cmd_vel` to FCU | 10 Hz | **10.007 Hz** (no glitch) |
| `mwan3 wan` (Starlink) | Online | unchanged Online |
| `mob1s1a1` (cell SIM 1) | Standby | unchanged Standby |
| `ping bencloud` (WG) | OK ~48 ms | OK 48 ms |
| `ping salmon_vpn` | OK | OK 58 ms |
| `ping router_op_vpn` | OK | OK 82 ms |
| `ping salmon_direct` | OK (WiFi) | **STALE 31 s** |
| `ping router_op_direct` | OK (WiFi) | **ERR 100% loss** |
| `udp_bridge` connection_id `vpn` | active | **still active** |
| `udp_bridge` connection_id `wifi` | active | silent |

Net: **clean failover, no operator intervention required**. Mission
control + telemetry continued uninterrupted via VPN/Starlink. What
was lost: the high-bandwidth `wifi` connection of `udp_bridge` (live
camera streams), and any direct LAN paths between boat and operator.

The `mwan3 wan1` (WiFi-bridge-as-internet) entry was already
`notracking` in mwan3 from §5.1, so the drop had **zero effect on
internet egress** — it was always Starlink-only. Cell SIM 1 stayed
warm but never had to take over. Mission-resilient design under
this comms model is doing what it should.

### Carry-forward

- The 4× `etherN` "Not running" WARNs and the `mavros: Mount` WARN
  on the boat-side annunciator are persistent noise and have been
  flagged on the dev side since 2026-04-29
  ([`#114`](https://github.com/rolker/unh_echoboats_project11/issues/114)).
  Not field-actionable, just noise to triage past.

## 9. Kernel UDP receive-buffer drops — 17k since boot

**2026-05-01T16:00-04:00** — While auditing TCP congestion settings
(BBR + fq + 16 MiB tcp buffers, all clean — see persisted
`/etc/sysctl.d/30-starlink-tcp.conf`), looked at UDP next. The
counters showed a real receive-side drop pattern:

```
UdpInDatagrams      2,462,334
UdpInErrors            17,023   (almost all RcvbufErrors)
UdpRcvbufErrors        17,018   ≈ 0.69% of UDP receives dropped
UdpSndbufErrors             0
```

NIC-level `rx_dropped/tx_dropped` are zero on both `enp7s0` and the
ZeroTier interface — the loss is at the kernel→app socket-buffer
handoff, not the NIC. Send side is clean.

Current defaults are conservative for our traffic profile:

```
net.core.rmem_default        =     212,992  (208 KiB)
net.core.rmem_max            =  16,777,216  (16 MiB — already big)
net.ipv4.udp_rmem_min        =       4,096  (4 KiB)
net.core.netdev_max_backlog  =       5,000
```

`rmem_max` is already 16 MiB so apps that explicitly
`setsockopt(SO_RCVBUF, big)` can claim large buffers — but the
**default any UDP socket gets is only 208 KiB**. Apps that don't
ask for more are exposed to bursts.

### Recommended sysctl tuning (NOT YET APPLIED)

```
net.core.rmem_default       4194304   # 4 MiB default (up from 208 KiB)
net.ipv4.udp_rmem_min        131072   # 128 KiB pressure floor (up from 4 KiB)
net.core.netdev_max_backlog  100000   # RX backlog before NAPI processes
net.core.netdev_budget          600   # only if softnet_stat shows budget exhaustion
```

Best landing spot: a new `/etc/sysctl.d/31-udp-buffers.conf`
(lexically separate from the Starlink-TCP file). Takes effect for
new sockets after `sysctl -p`; existing sockets keep their already-
allocated buffer until the app reopens.

**App-level fix** is also worth flagging upstream: `udp_bridge`
(and any other UDP receiver in the stack) should call
`setsockopt(SO_RCVBUF, ...)` to a large value explicitly rather
than rely on system default. That's a code change, not sysctl.

### Verification protocol after tuning

```
nstat -rsz UdpRcvbufErrors UdpInDatagrams
sleep 60
nstat -rsz UdpRcvbufErrors UdpInDatagrams       # delta — should be 0
```

If drops stay at 0 over ~5 min of traffic, the tuning landed. If
they don't, the bottleneck is downstream (app draining too slowly).

## 10. `udp_bridge` is a `LifecycleNode` — restart procedure

While answering "if we get an updated udp_bridge, how do we best
restart it?", confirmed the supervision shape and the right
sequence.

`udp_bridge_launch.py` (in `core_ws/src/udp_bridge/udp_bridge/launch/`)
declares it as a **`LifecycleNode`** with `respawn=True,
respawn_delay=2`. Then a separate `LifecycleTransition` action
fires once at launch start to drive it inactive → active.

The catch: **`LifecycleTransition` only runs at the original launch
start** — it does NOT re-fire on respawn. So `kill -INT` brings the
process back via respawn, but the new instance sits in the
`unconfigured`/`inactive` state until manually transitioned.

### The right sequence (documented for next time)

```bash
# 1. Build the new binary (C++, no symlink-install shortcut)
cd /home/field/project11/layers/main/core_ws
colcon build --packages-select udp_bridge

# 2. SIGINT the running process; respawn=True forks the new install/
PID=$(pgrep -f "/lib/udp_bridge/udp_bridge_node$")
kill -INT "$PID"

# 3. Wait for respawn (zenoh shutdown can take ~13 s before the new
#    process starts) and check lifecycle state
sleep 20
ros2 lifecycle get /bizzy/udp_bridge

# 4. If "unconfigured" or "inactive" — drive it up by hand
ros2 lifecycle set /bizzy/udp_bridge configure
ros2 lifecycle set /bizzy/udp_bridge activate

# 5. Verify
ros2 topic hz /bizzy/udp_bridge/topic_statistics    # should hit ~1 Hz
```

**Don't `pkill -f /lib/udp_bridge/udp_bridge_node` from inside a
bash subshell** — the surrounding bash command line will contain
that exact path string (because of the shell snapshot pattern), and
pkill will self-match and kill the bash before reaching the actual
target. Use the explicit-PID `kill -INT $PID` form instead, with a
`pgrep` pattern anchored by `$` so it doesn't catch the wrapper.

The 13-second window before respawn is **zenoh's `close operation
timed out`** during shutdown — the prior process logs an `ERROR
... close.rs:122` line just before exiting. Cosmetic but slow;
budget for it. Verified live during today's restart: PID 30322 →
55597, total handoff ~15 s, lifecycle came back `unconfigured`,
manual `configure → activate` worked first try, topic_statistics
publishing at 1 Hz immediately after.

### What NOT to do

- **Don't restart the whole `core_launch`** — takes SBG, mavros,
  nav2, mission down with it for tens of seconds. Only do this if
  you're also refreshing those.
- **Don't rely on `--symlink-install`** — `udp_bridge_node` is
  C++, the install path is a real binary. Symlink-install only
  short-circuits Python and shared data files.

### Side-effect to expect

The operator-side `/operator/udp_bridge` will see boat side
disconnect for ~5–10 s during the restart. It reconnects on its own
once the boat side hits active. Salmon doesn't need touching unless
its binary is also being updated.

### Real-world correction — both sides DO need restarting

Field-tested today the §10 procedure with a fresh udp_bridge build.
Boat-side handoff went exactly as documented (PID 30322 → 55597,
~13 s zenoh-close window, manual configure → activate, 1 Hz
topic_statistics resumed). But Roland reported **forward camera
data wasn't reaching him** afterwards.

Investigation showed `udp_bridge/topic_statistics` was reporting
**100% drop** on the VPN connection for forward ffmpeg
(success=0/s, dropped=310 KB/s) while the boat was publishing
healthy. Root cause: **the boat-side and operator-side bridges
maintain per-peer packet sequence/session state** — visible in the
prior launch log as `Discarded N incomplete packets from operator`
and `Received next packet number that is less than previous one`
INFO/WARN lines. After the boat-side restart, boat had fresh
session state; salmon-side still tracking the old. New packets
arriving with mismatched sequence got dropped at the operator
bridge.

**Fix**: Roland restarted `/operator/udp_bridge` on salmon (same
LifecycleNode + lifecycle-transition pattern, just symmetric on
that host). Symptoms cleared immediately:

- VPN forward-ffmpeg drops: **310 KB/s → 0 KB/s**
- Aggregate VPN throughput: 156.6 KB/s success / 7.2 KB/s
  dropped — a normal residual under rate limiting
- One "Discarded 50 incomplete packets" cleanup burst on the boat
  side at the moment of salmon's restart, then back to trickle-level
  (1-2 per minute) discards

**Updated guidance**: when restarting `udp_bridge` on either side
to pick up a new build, **restart both sides** in close succession.
The §10 sequence applies symmetrically:

```bash
# Boat side (gabby)
PID=$(pgrep -f "/lib/udp_bridge/udp_bridge_node$")
kill -INT "$PID"; sleep 20
ros2 lifecycle set /bizzy/udp_bridge configure
ros2 lifecycle set /bizzy/udp_bridge activate

# Operator side (salmon) — same shape with /operator/ namespace:
# pgrep -f "/lib/udp_bridge/udp_bridge_node$" → kill -INT
# ros2 lifecycle set /operator/udp_bridge configure
# ros2 lifecycle set /operator/udp_bridge activate
```

Either side first is fine; the second-restarted side just clears
its now-stale peer state on the way up.

### Residual finding — bridge subscriber is dropping ~85% of frames

Even with both sides resync'd, **forward ffmpeg appears in
`topic_statistics` at only ~0.79 msg/s while the topic is
publishing at 5 Hz** on the boat. Bridge `bytes/s` (the count of
data the bridge receives from its subscription) is ~14.4 KB/s vs
the ~102 KB/s the topic actually emits. So **the bridge is dropping
~85% of frames at the ROS subscription stage — before its rate
limiter, before the VPN hop, before any operator-side
processing**.

The bridge's send-side counters are healthy (success ≫ dropped on
both connections), confirming the loss is upstream of fragmentation.
Likely subscription QoS / queue-depth mismatch in the new build.
Today's symptom is a low effective frame rate at the operator end,
not "no frames at all" — Roland was unblocked by the resync.

**Carry-forward**: file with the `udp_bridge` package upstream.
Useful diagnostics to attach to a bug report:

- `ros2 topic info <topic> --verbose` showing the bridge's
  subscription QoS profile + reliability + history depth
- `ros2 topic hz <topic>` on the publisher side
- The per-topic `bytes/s` and `messages_per_second` from
  `udp_bridge/topic_statistics` showing the upstream rate
- Whether other camera-rate / image-rate topics show the same
  ~14% throughput ratio — earlier sample today suggested the
  pattern is consistent across cameras, not unique to forward

(See [§12](#12-udp_bridge-throughput-regression-root-caused--fixed-with-reentrant-republish_group_) for the actual root-cause + fix.)

## 12. `udp_bridge` throughput regression — root-caused & fixed with Reentrant `republish_group_`

The §10–11 udp_bridge restart episode left a residual finding (§10's
"Residual finding"): bridge was only forwarding ~14% of camera
frames at the subscription stage. Tracked it down today.

### 12.1 What we ruled out before reading source

Sequentially ruled out hypotheses by direct measurement:

1. **QoS mismatch?** No — both publisher and bridge subscriber use
   `BEST_EFFORT, VOLATILE`. Compatible.
2. **Subscriber queue too small?** No — bumped `queue_size` from the
   default 10 → 100 in `bizzyboat.yaml` for the four oak ffmpeg + four
   `oak_segmentation_*_raw` topics on both wifi and vpn (§"set those
   queues to 100"). Live `topic info` confirmed `KEEP_LAST(100)` took
   effect. Forward ffmpeg subscription rate stayed at ~0.19 msg/s
   vs the topic's 5 Hz publish rate — **no improvement**.
3. **WiFi-down doubling work?** No — once WiFi was restored
   (§"reenabled the wifi") and all `ping_monitor` paths returned to
   OK, subscription rate was unchanged.

### 12.2 Root cause from the source

In `udp_bridge.cpp:181-184` (post-PR-#12, today's build):

```cpp
socket_drain_group_ = create_callback_group(rclcpp::CallbackGroupType::MutuallyExclusive);
republish_group_    = create_callback_group(rclcpp::CallbackGroupType::MutuallyExclusive);
periodic_group_     = create_callback_group(rclcpp::CallbackGroupType::MutuallyExclusive);
```

And in `udp_bridge_node.cpp:45` (post-PR-#12 commit `605d5c1`,
"udp_bridge_node.cpp: pin executor threads"):

```cpp
rclcpp::executors::MultiThreadedExecutor executor(rclcpp::ExecutorOptions(), 3);
```

**All forwarding subscriptions** — every `oak_*_ffmpeg`, every
`oak_segmentation_*`, plus tf, mavros, odom, ~20 topics in total —
share `republish_group_`. Because that group is `MutuallyExclusive`,
**only one of those subscription callbacks executes at a time**, on a
single dedicated executor thread. With ~20 forwarding subscriptions
all racing for that one thread, plus the per-frame work each does
in `UDPBridge::callback` →  `send()` (acquire `subscribers_mutex_`,
serialize/compress/fragment, acquire `remote_nodes_mutex_` +
`pending_connections_mutex_`, sendto across all configured connections,
update stats), the throughput ceiling lands somewhere around what
we measured.

Earlier today's commit chain landed via PR #12:

```
3d34a50 Switch to MultiThreadedExecutor + add callback groups (3a)
b1e4736 Mutex audit + lock guards for shared state under MultiThreadedExecutor (3b)
... (intervening review-fix commits 4-13) ...
605d5c1 udp_bridge_node.cpp: pin executor threads + correct invariants comment (14)
8494890 Merge pull request #12 from rolker/feature/issue-11
```

This is a **regression introduced by today's merge**. The pre-merge
(single-threaded executor) version handled forwarding-subscription
throughput differently — although also serialized, without the
overhead of the new locks under multi-thread design.

### 12.3 Field fix applied — `Reentrant` + 8 threads

Two-line edit in `core_ws/src/udp_bridge/udp_bridge`:

```cpp
// udp_bridge/src/udp_bridge.cpp:185
republish_group_    = create_callback_group(rclcpp::CallbackGroupType::Reentrant);
```

```cpp
// udp_bridge/src/udp_bridge_node.cpp:45
rclcpp::executors::MultiThreadedExecutor executor(rclcpp::ExecutorOptions(), 8);
```

Reentrant on `republish_group_` lets multiple forwarding-subscription
callbacks run concurrently. Threads 3 → 8 gives the executor enough
worker threads to actually exploit that concurrency (the PR #12
"pin to 3" commit was correct given MutuallyExclusive groups, but is
exactly the wrong number once we move one group to Reentrant).

The PR #12 mutex audit (`b1e4736`) is what makes Reentrant safe —
shared state (`subscribers_`, `remote_nodes_`, `pending_connections_`)
is already lock-protected, so concurrent callbacks contend on those
locks but don't corrupt state.

`colcon build --packages-select udp_bridge` clean (only pedantic
warnings about flexible array members, unrelated). Roland restarted
on both gabby and salmon per [§10](#10-udp_bridge-is-a-lifecyclenode--restart-procedure)'s symmetric procedure.

### 12.4 Verified results

Before fix (peak of investigation, with WiFi up + queue_size=100 already applied):

```
forward ffmpeg subscriber:        0.19 msg/s  (vs 5 Hz published — 4% throughput)
forward ffmpeg VPN drops:          310 KB/s   (100% of forward incoming dropped)
aggregate VPN: success=127 KB/s, dropped=107 KB/s   (54% throughput)
aggregate WiFi: success=247 KB/s, dropped=30 KB/s
```

After fix:

```
forward ffmpeg subscriber:        5.00 msg/s  (full publisher rate, 100% throughput)
forward ffmpeg VPN drops:           0 KB/s
all 3 oak ffmpeg on VPN:          5.00 msg/s each, ~106 KB/s success, 0 dropped
aggregate VPN: success=365 KB/s, dropped=  0 KB/s   (100% throughput, zero loss)
aggregate WiFi: success=551 KB/s, dropped=  0 KB/s
```

**Restored ~26× the camera subscription throughput.** Roland's
operator-side observation: cameras visibly recovered to live frame
rate after both bridges restarted.

### 12.5 Upstream report content (high priority)

This needs to land on the `udp_bridge` package as a real fix. Ticket
content for the dev side to file properly:

**Title**: PR #12 multi-threaded refactor introduces severe forwarding-subscription throughput regression on high-rate topics

**Repro**: Bridge configured to forward ~20 topics across two
connections (wifi + vpn), some at 5 Hz × ~100 KB/s (camera ffmpeg
streams). Compare `topic_statistics.messages_per_second` on the
forwarded topics against `ros2 topic hz <source>` on the publisher.
With `MutuallyExclusive republish_group_` (PR #12 default), bridge
forwards at ~0.19 msg/s vs 5 Hz published — 4% throughput.

**Root cause**: `udp_bridge.cpp:181-184` puts all forwarding
subscriptions in a `MutuallyExclusive` callback group, serializing
all per-frame work onto a single executor thread. Combined with
`udp_bridge_node.cpp:45`'s 3-thread pin (one per group), the
forwarding throughput ceiling is the per-thread cost of
serialize+compress+fragment+sendto across all subscribed topics.

**Fix tested in field**:

1. `udp_bridge.cpp:185` — change `republish_group_` to `Reentrant`.
2. `udp_bridge_node.cpp:45` — bump executor threads from 3 to 8 (or
   `std::thread::hardware_concurrency()`).

The PR #12 mutex audit already protects the relevant shared state,
so Reentrant is safe.

**Verified result**: subscription throughput rises from 0.19 msg/s
to 5 msg/s (full publisher rate) on the same hardware, same
network, same workload. ~26× improvement, no errors, no
correctness issues observed across a multi-hour deployment session.

**Optional follow-on improvements** documented in §10:

- Avoid per-destination work duplication in `callback()` — serialize
  + compress + fragment once, reuse across destinations.
- Move per-frame work off the subscription callback entirely (move
  to internal queue + worker thread — already noted as "option (b)"
  in `udp_bridge_node.cpp`'s invariants comment as a future change).

### 12.6 Carry-forward

- File the upstream issue on the `udp_bridge` repo with the §12.5
  content as soon as the dev side has GitHub access. Likely #16 or
  similar. Tag for backport.
- Field hosts (gabby + salmon) are now running with the local
  Reentrant + 8-thread patch. The `/import-field-changes` skill on
  next dev pull should catch and route this; if it lands as a
  field-mode patch on the udp_bridge package, that's a clean way to
  PR the fix back through the dev workflow.

## 11. BT design issue — `SkipUnknownTaskType` masks execution failures

**2026-05-01T16:20-04:00** — Tracing why the boat hovered
mid-mission during the [§"out of sight" cmd_vel-stuck event](#52-starlink-diagnostics-stale-node-healthy-dish)
(when `mission_manager` reported `Current Nav Task: done_hover`
alongside `trackline0000 (done)` while the line wasn't actually
finished). Found a real BT design issue.

### The mechanism

The top-level task dispatch in
`run_tasks.xml:127-160` is a `ReactiveFallback`:

```
ReactiveFallback "SelectTaskReactiveFallback":
    HoverTask
    GotoTask
    SurveyLineTask
    SurveyLineSetTask
    SurveyAreaTask
    SetTaskDone name="SkipUnknownTaskType"   ← catchall
```

`ReactiveFallback` returns the first non-FAILURE child. Each task
subtree's first node is a `ScriptCondition` checking
`current_task_type == 'X'` — if the type doesn't match, the subtree
returns FAILURE immediately and the fallback tries the next.

**The problem**: when a matching subtree (e.g.
`SurveyLineTask` for type `survey_line`) **passes its script
condition but its execution sequence later fails** — e.g.
`FollowPath` action returns ABORTED, transit nav fails, etc. — the
ReactiveFallback treats that the same as "type didn't match" and
moves on to the next sibling. SurveyLineSetTask + SurveyAreaTask
fail their script conditions (wrong type), then the catchall
**`SetTaskDone "SkipUnknownTaskType"` fires unconditionally and
marks the trackline done** — even though it just aborted, not
completed.

### Forensic match to today's event

The trace lined up exactly:

- `follow_path/_action/status` showed multiple `status: 6 ABORTED`
  in its history before the EXECUTING (status 2) at the end
- BT log was looping at `HoverTask FAILURE` (HoverTask script-cond
  was failing because by then current_task_type had become `'hover'`
  via `done_hover` after the trackline got marked done)
- mission_manager status showed `trackline0000 (done)` with
  `Current Nav Task: done_hover`
- That's the chain: **FollowPath aborted → SurveyLineTask sequence
  failed → ReactiveFallback fell through → SkipUnknownTaskType
  catchall fired → trackline marked done → only remaining task is
  `done_hover` (priority 100, always present per §"why did it
  hover" / `mission_manager.py:73-78`) → boat falls into hover.**

The `done_hover` task itself isn't a bug — it's the intentional
"never-empty fallback" behaviour added by mission_manager. The bug
is upstream: the BT shouldn't be marking known-type tasks done just
because their subtree failed mid-execution.

### Carry-forward (real)

The catchall conflates "no script condition matched" (genuine
unknown type) with "a matching subtree's execution failed"
(transient controller / planner / action issue). Suggested fixes,
in increasing intrusiveness:

1. **Replace `SkipUnknownTaskType`** with a `ScriptCondition` that
   explicitly checks `current_task_type` against the list of known
   types — if it IS known, return SUCCESS without calling
   SetTaskDone (let retry / supervision handle the failure
   upstream). If it's NOT in the list, then SetTaskDone.
2. **Wrap each task's execution sequence in a retry node** so a
   transient `FollowPath` ABORTED triggers a retry, not a
   FAILURE-bubble that the catchall sees.
3. **Demote the SetTaskDone catchall to a logging-only fallback**
   in the production tree, with task-done lifecycle handled
   exclusively inside each known-type subtree.

This is a real bug worth filing on the
`marine_nav_bt_task_navigator` package upstream.
