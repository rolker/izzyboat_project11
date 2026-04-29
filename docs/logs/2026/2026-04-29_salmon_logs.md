# BizzyBoat deployment log — salmon — 2026-04-29

**Host**: salmon
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Deployment**: TBD (pre-deployment bench session)

## Summary

Bench prep session: workspace sync + build, operator-stack bring-up
verification, an annunciator UI fix made and pushed in field mode,
and a draft of an operator-side annunciator design with a working
preliminary config that landed live during the same session.

## 1. Workspace sync + build

2026-04-29T11:30-04:00 — `make sync`, then `make build`.

Sync pulled six repos.  Operator-relevant headlines:

- `rqt_operator_tools` (`d936384..3b9df5b`) — PR #30 / issue-27:
  `rqt_camera_grid` `TransportHints` fix in `subscribe()` try block
  + `resolve_base_from_combo` helper extraction + tests.
- `unh_echoboats_project11` (`a1cf758..85befd0`) — PR #109 / issue-97:
  new operator-side `bag_recorder_operator_launch.py`; PR #98 /
  issue-91: BizzyBoat nav source switched to FCU EKF3-fused topics;
  mavros local_position velocity_body frame_id namespace fix;
  SBG Ellipse-D bring-up on gabby + RTCM relay (PRs #102, #106, #108).
- `unh_marine_perception` (`97b270f..377f008`): per-camera `frame_id`
  on `depthai_marine` + `sea_surface_segmentation` aligned to URDF.
- `marine_tools` (`61885f3..311523f`): repo restructured —
  `marine_tools` package moved into a subdirectory; new
  `sound_speed_bridge` package added.
- `unh_marine_autonomy` (`80e012e..d7d11f5`): new `SoundSpeed.msg`.
- `seafloor_echoboat_project11` (`37b5d84..0d2b7fd`): nav2
  `FollowPath` default speed bump — different boat, not relevant
  to bizzyboat.

### `make build` gotcha — marine_tools stale CMake cache

First `make build` failed at the `sensors` layer.  Root cause:
`marine_tools` was restructured to live in a subdirectory of its
repo; the prior build's `CMakeCache.txt` had the old absolute path
baked in, so `cmake --build` aborted with:

```
CMake Error: The source directory ".../sensors_ws/src/marine_tools" does
not appear to contain CMakeLists.txt.
```

Fix: remove the stale `build/marine_tools` and `install/marine_tools`
directories under `layers/main/sensors_ws/`, then `make build` again.
Both came back clean.

**Heads-up for gabby**: the same failure will hit the first
`make build` after `make sync` on gabby today.  Same fix.

Final build: all 7 layers, 91/91 packages, only stderr noise being
the upstream PCL/FLANN `CMP0144` policy warning (harmless) and the
pre-existing CAMP unused-parameter warnings.

## 2. Operator stack — startup script verification

2026-04-29T11:57-04:00 — Roland ran `start_tmux_operator_project11.bash`.
Verified everything came up clean from logs and live ROS state:

- Zenoh router up, advertising on `192.168.13.142:7447` (op LAN),
  ZeroTier; router id `1fcab3f871c2d7a105059a3acfb62937`.
- `operator_core_launch.py` clean: `joy_to_helm` reading the right
  axes/buttons, `starlink_diagnostics` connected to dish (hw
  `rev4_prod3`, sw `2026.04.10.mr77882.1`).
- `rosbag2_recorder` (PR #109): `All requested topics are subscribed.
  Stopping discovery...` — got all 10 expected topics on first pass:
  `/diagnostics`, `/bizzy/marine/command`,
  `/bizzy/piloting_mode/manual/helm`, the four
  `/operator/udp_bridge/{,remotes/bizzy/}{topic_statistics,bridge_info}`
  topics, `/rosout`, `/tf`, `/tf_static`.
- Bag growing on disk:
  `~/data/logs/operator/2026-04-29/diagnostics_11.57.56/`,
  ~57 KB → ~286 KB over ~7 min.
- CAMP up on the right projection (Global Mercator, central_meridian
  −70 → NH coast).

Note: `ros2 topic hz` returns "Terminated" with no output under
`rmw_zenoh_cpp` for many topics — known Zenoh quirk.  Use `ros2 topic
echo --once` or watch the bag size to verify flow; don't chase hz
noise.

PR #109 / issue-97 (operator-side bag recorder) — **verified live**.

## 3. Annunciator UI fix — field-mode commit

Roland flagged a long-standing bug: when an indicator has a short
label and a long value (or vice versa), the longer side gets
clipped even though the rendered font already fit-to-cell.

Root cause in `rqt_annunciator/indicator_widget.py`: the per-cell
`QHBoxLayout` had no stretch factors set, and both `QLabel`s use
`QSizePolicy.Ignored` horizontally — so the layout fell back to
splitting the cell evenly.  `_fit_font()` was correctly shrinking
the combined font to fit, but each side only ever got half the
cell, and the wider side clipped.

Fix: set per-cell HBox stretch from the cached reference text widths
(already maintained for the EMA-driven grid stretch), with a floor
of 1 so neither side collapses when its text is empty.  Reuses the
existing reference metrics; no new allocations on the hot path.
Three regression tests added to
`rqt_annunciator/test/test_resize_invariants.py`.

Pushed in field mode to `gitcloud:field/rqt_operator_tools.git`
on `jazzy`, commit `2811fb0`.  All 54 package tests pass.
**Confirmed live by Roland**: clipping resolved.

## 4. Operator-side annunciator — design + preliminary config

Discussion item: the existing annunciator config is 100 %
boat-prefixed.  When the boat is off (or the link drops) every
indicator goes red and the operator can't tell whether the link,
the boat, or salmon broke.

Sampled live `/diagnostics` to ground the design — discovered the
`diagnostic_aggregator` config already declares an `operator:`
analyzer group, and salmon is publishing the matching keys:
`MikroTik: bizzy.wifi.op:*`, full `Starlink: starlink.op:*`,
`Ping: ping.op:{gabby_direct,gabby_vpn,router_bizzy_*,bencloud,dns_*}`,
plus the `udp_bridge operator: bizzy: {wifi,vpn}` link state.
Aggregator-side everything is wired; only the display side was
missing.

Wrote a preliminary Tier 1 config and a design doc:

- `bizzyboat_project11/config/bizzyboat_operator_annunciator.yaml` —
  10 indicators, all backed by already-published keys.
- `bizzyboat_project11/docs/operator_annunciator_design.md` —
  rationale, deferred Tier 2 monitors (joystick liveness, recorder
  health, disk free, chrony, zenohd), open questions.

Pushed in field mode to `gitcloud:field/unh_echoboats_project11.git`
on `jazzy`, commit `fe48d69`.  Roland added the panel as a second
annunciator widget in the existing `bizzyboat-diagnostics`
perspective.  **Looks good live.**

Notes for follow-up:

- `Teltonika: router.op` is configured in
  `network_monitor_operator_launch.py` but isn't on the wire today.
  Either the op router doesn't have a Teltonika to query or the
  monitor isn't actually starting.  Add to the panel only after we
  see it publish.
- The `udp_bridge` indicators currently exist on **both** the boat
  panel and the new op panel.  They conceptually belong on the op
  panel (it's our bridge state, not the boat's).  Move them off the
  boat panel in a follow-up commit once the new panel has soaked.
- Some boat-side ping keys (`ping.bizzy:*`) showed up while gabby's
  ROS was still down — initially confusing, but explained when
  Roland brought gabby up: those are gabby's `ping_monitor`
  publishing under hardware_id `ping.bizzy`, which arrives via the
  UDP bridge once the link is alive.

## 5. Boat ROS up — link verification

Roland brought up gabby's ROS stack.  Sampled bridge state:

- `failed_bytes_per_second: 0.0` and `dropped: 0.0` on every topic on
  both `wifi` and `vpn` connections.
- `/diagnostics` publisher count: 4 → 5 (boat-side aggregator now
  forwarding).
- EKF3-fused topics from PR #98 / issue-91 present:
  `/bizzy/mavros/global_position/global`,
  `/bizzy/mavros/local_position/velocity_body` (the namespace from
  the d40845e mavros frame_id fix), `/bizzy/odom`.
- All four OAK cameras + segmentation flowing via H.265
  (ffmpeg) — camera grid has data to subscribe to.

Pending verifications (not done this session):

- **rqt_camera_grid `TransportHints` fix** (PR #30) — needs
  interactive exercise of pane add/remove + transport switches in
  the rqt UI.
- **Nav-source switch sanity** — beyond topic existence, confirm
  the values are sane (lat/lon match dock; velocity_body frame_id is
  the post-fix namespace) and that CAMP actually consumes them.

## 6. Bandwidth observation — global costmap eating wifi

Live `topic_statistics` showed `/bizzy/global_costmap/costmap`
crossing the bridge at ~150 KB/s on `wifi` (0.4 Hz × 6.4 MB/s
aggregate from boat side, heavily fragmented at 549 frags/msg).
Local costmap was ~20 KB/s at 0.3 Hz over wifi.

Currently zero failures, but on a thin link this is the first thing
to drop when conditions worsen.

### Field change — disabled global costmap on the bridge

Roland disabled `/bizzy/global_costmap/costmap` from being forwarded
by the boat-side udp_bridge at runtime.  This **does not persist**
across a relaunch — the persistent fix lives in the boat-side
config:

- `bizzyboat_project11/config/bizzyboat.yaml` — line 74 lists
  `global_costmap` in the per-remote topic set, and line 108 carries
  the per-topic config (`{source: global_costmap/costmap, period: 3.0}`).

Removing both entries (or the matching block elsewhere) is the way
to make the disable survive a launch.  Deferred — not done this
session because it deserves its own commit and a quick check that
nothing on the operator side actually wants the global costmap (CAMP
or otherwise).  Until that lands, the disable has to be re-applied
each time the boat-side bridge restarts.

## 7. Nav-source switch verification — gabby is stale

Sampled the EKF3-fused topics + `velocity_body` frame_id + `/bizzy/odom`
to verify PR #98 / issue-91 plus d40845e.

What's working:

- `/bizzy/mavros/global_position/global` — clean RTK fix.
  43.0720 °N, −70.7117 °W (Portsmouth/coast), σ ≈ 2 cm horizontal,
  `header.frame_id: bizzy/base_link`.  The EKF3-fused position is
  landing as PR #98 intended.
- `/bizzy/odom.pose` is publishing real values with
  `frame_id: bizzy/odom`, `child_frame_id: bizzy/base_link` — both
  namespaces correct.

What's broken (or rather, not yet deployed):

- `/bizzy/mavros/local_position/velocity_body.header.frame_id` is
  bare `base_link`, not `bizzy/base_link`.  The d40845e fix
  (`child_frame_id: "bizzy/base_link"` added to `mavros.yaml`'s
  `local_position:` block) is not in effect on gabby.
- No `/bizzy/.*sbg` topics on the wire — the SBG Ellipse-D bring-up
  from PR #106 / issue-103 is also absent.

Two independent signals → **gabby is on `jazzy`, but pre-2026-04-28
`jazzy`**.  It was launched from a build that pre-dates today's
sync.  The d40845e fix and the SBG bring-up are both present in the
salmon-side checkout we synced this morning, just not on gabby.

Symptom this leaves us with: per the d40845e commit message,
mru_transform's `lookupTransform("bizzy/base_link", "base_link", …)`
fails for every velocity sample → `/bizzy/odom.twist` is silently
degraded (throttled WARN, no twist updates).  Pose is fine, twist
isn't.  Worth re-sampling `/bizzy/odom.twist` post-gabby-resync to
confirm it un-zeros.

**Action item for gabby (not done from salmon)**:

```
make sync
# Will hit the same marine_tools stale-cache failure salmon hit
# this morning (CMake error: source dir does not contain
# CMakeLists.txt).  Fix:
rm -rf layers/main/sensors_ws/build/marine_tools \
       layers/main/sensors_ws/install/marine_tools
make build
# Restart boat-side core launch
```

After that: the velocity_body frame_id should flip to
`bizzy/base_link`, SBG topics should appear, and `/bizzy/odom.twist`
should populate.

Net of this check: PR #98 is verified at the EKF3-data level (clean
RTK), but the namespace-fix half (d40845e) + SBG bring-up (#106)
remain pending until gabby resyncs.  Camera-grid `TransportHints`
verification (PR #30) is also still pending — needs interactive rqt
exercise.

## 8. WG/VPN diagnostic + annunciator change

Roland flagged that `Internet (bencloud)` on the new op annunciator
panel was always showing red.  Walked the path:

- Salmon ↔ op router (`192.168.13.1`) — 0.3 ms, fine.
- Salmon → `bencloud.wg.p11.lan` (`10.132.146.1`) — 100 % loss; TTL=1
  produced no ICMP-Time-Exceeded; mtr returned no hops.
- Salmon → `bizzy.wg.p11.lan` (`10.132.146.6`) — same: 100 % loss.
  Every WG-mesh address from salmon fails identically.
- Salmon → `router.vpn.bizzy.p11.lan` (`192.168.21.1`, NETMAP'd
  through WG) — 57–66 ms, **fine**.

Initial diagnosis was "op router's WG tunnel is down."  Roland
corrected: the VPN path **is** WG.  So the tunnel is up (the
NETMAP'd 192.168.21.x address proves it carries traffic); what
salmon can't address is the raw mesh `10.132.146.0/24`.

Topology insight: salmon has no WG client of its own (no `wg*`
interface — only ZeroTier).  Its WG-bound traffic is mediated by
the op router, which only NETMAPs salmon-LAN traffic onto specific
WG-tunneled subnets.  The mesh endpoints themselves (10.132.146.x)
aren't exposed to salmon-side hosts by design.  So the
`bencloud.wg.p11.lan` ping was always destined to fail from
salmon — a property of the network architecture, not of any
outage.

### Annunciator change

Removed `Internet (bencloud)` from
`bizzyboat_project11/config/bizzyboat_operator_annunciator.yaml`
(panel down to 9 indicators).  Added a "What we deliberately don't
include" subsection to the design doc capturing the topology insight
so it doesn't get re-discovered next deployment.  `Ping Boat Router
(VPN)` is the right proxy for "is WG transport carrying traffic"
since it goes through the NETMAP path.

The underlying `bencloud:bencloud.wg.p11.lan` target in
`ping_targets_operator.yaml` is left alone — it still serves as a
data-collection record, just not as an annunciator indicator.

## Commits

- `rqt_operator_tools` `2811fb0` — `fix(rqt_annunciator):
  proportional HBox stretch so long values stop clipping`
- `unh_echoboats_project11` `fe48d69` — `feat(bizzyboat_project11):
  preliminary operator-side annunciator`
- `unh_echoboats_project11` `02b4c80` — `docs(logs): start
  2026-04-29 salmon bench-prep log`
- `unh_echoboats_project11` `aac2c09` — `fix(bizzyboat_project11):
  drop bencloud-WG ping from op annunciator`
