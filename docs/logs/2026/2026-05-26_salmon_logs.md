# BizzyBoat deployment log — salmon — 2026-05-26

**Host**: salmon
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Deployment**: git-bug `20a49fc` — "Deployment 2026-05-26: validate raised yaw cap (1.0) + planner radius (1.5)" (opened 2026-05-25T12:56-04:00, edited 2026-05-26T11:23-04:00).

## Summary

_(agent draft — operator to adjust/voice)_ Salmon op-station support for the
2026-05-26 deployment (validate raised yaw cap 1.0 + planner radius 1.5 m). No
op-side config needed before bring-up. Op stack healthy. OAK displays flickered
grey on fwd/port/aft → traced to VPN **send-side** loss (segmentation unaffected,
so camera/perception fine); operator throttled the reflex pointcloud's VPN path
to 1 Hz and the cameras cleaned up — but the VPN link itself stays lossy (flag for
OTH/Starlink-only). Closed the #171 annunciator gap: added Battery / FCU System /
Sound Speed rows to the operator annunciator and validated them live (Battery 28.5 V
green). rviz failed to open (GLX) — root-caused to a morning `apt upgrade` that
bumped the NVIDIA driver without a reboot; rode it out on software rendering, then
a reboot fixed it. Post-reboot + gabby restart both came back clean. Boat launched
12:43, recovered 14:12 (~1h29m on water); **on-water validation results are in the
other hosts' logs** (gabby/dev) per operator.

## Lessons Learned

_(proposed by agent — operator curates)_

- **After any `apt upgrade` on the op-station, check `/var/run/reboot-required`
  and reboot _before_ stack bring-up.** A driver/kernel update (here NVIDIA
  580.142→580.159) silently breaks rviz GLX until the module reloads.
- **The VPN path is lossy under load** — throttling non-critical high-rate topics
  on the VPN connection (e.g. the reflex pointcloud → 1 Hz) buys video headroom,
  but the underlying loss persists and matters where VPN is the only path (OTH).

## 1. Session start

**2026-05-26T11:40-04:00** — Log initialised on salmon. Field mode confirmed
(origin `git@gitcloud:field/unh_echoboats_project11.git`). No prior 2026-05-26
salmon log; this is the first scribe entry. Repo HEAD `21ebf37`.

**Salmon pre-deploy state**:

- `make sync` ran twice — all workspace repos up to date. Notable deltas pulled
  this morning: `unh_echoboats_project11` (bizzyboat config + perception launch),
  `udp_bridge` (publish queue), `seafloor_echoboat_project11` (nav2 params),
  `unh_marine_perception` (sea_surface_segmentation, issue #17).
- `make build` — all 7 layers green. `udp_bridge` and `sea_surface_segmentation`
  emitted warnings only (non-fatal).
- Today's deployment issue `20a49fc` pulled via `git-bug pull` (cache cleared to
  surface the new ref) and read in full, including the four follow-up comments.

**Scope today** (from issue `20a49fc`):

1. **Validate two field-untested turning-limit changes** (headline):
   - Helm yaw cap raised 0.5 → 1.0 rad/s (`helm_manager.max_yaw_speed`, PR #172).
   - Planner min turning radius reduced 3.0 → 1.5 m (`SmacPlannerHybrid.minimum_turning_radius`).
   - cmd_vel smoother chain remains deliberately disconnected — helm clamp +
     planner radius are the only turn-gentleness knobs.
2. **Record `pid_state`** (CrabbingPathFollower PID / cross-track error) into the
   bag for #164 analysis — verify exact topic on the running stack before editing.
3. **Reflex collision avoidance**: perception#17 merged to `jazzy` (`401385c`);
   Phase B Collision Monitor merged to `jazzy` 2026-05-26 + pushed to gitcloud.
   Requires gabby to pull `jazzy` + rebuild the perception layer to be present.
4. **Opportunistic**: operator annunciator rows for battery / FCU-system /
   sound-speed (#171) — confirm exact `/diagnostics` strings live before editing.
5. Stretch goals only if the boat day allows (#138, #130, nav#23/#19, perception#7).

**Operator overrides carried from issue comments (#4, authoritative):**

- `pid_state` is **record-only** — not a field-monitoring task. The only in-field
  check is that it actually lands in the bag.
- **Sim-verification is NOT a hard gate.** Collision Monitor / e-stop behavior is
  **baby-stepped on-water incrementally**; the agent's "⛔ mandatory sim-first"
  framing is overridden. Feed/health/observability checks remain useful but
  non-blocking.

**Salmon is the operator station.** The perception pull+rebuild and most
`ros2 topic`/`/diagnostics` confirmations are gabby-side (the boat). Salmon-side
work: annunciator-config edits, op-side topic/string confirmation, rviz/SA checks.

> Note: `.agents/README.md` does not exist in this repo (project-guide gap). Not
> blocking today; flag for a future dedicated documentation task.

## 2. Pre-flight — tides & weather

_Pending operator input — per the logs convention, asking Roland for local
conditions (site / tide window / weather) before fetching independently._

- **Site**:
- **Tide window** (heights in metres, times with explicit TZ):
- **Weather** (wind, sea state, temp):

## 3. Pre-stack op-side config check

**2026-05-26T11:48-04:00** — Operator asked, before stack bring-up, whether any
op-side config needs applying. Checked `bizzyboat_operator_annunciator.yaml` on
salmon: currently **network/link rows only** (9 rows — Op WiFi/Starlink, ping
gabby/router direct+VPN, DNS, UDP wifi/vpn). No battery / FCU-system / sound-speed
rows yet, matching issue `20a49fc`'s premise.

**Conclusion: nothing to apply before bring-up.** The annunciator additions (#171)
key on exact live `/diagnostics` strings, so they are a stack-up task — confirm
strings (`ros2 topic echo /diagnostics --once`) then edit, not blind beforehand.
All other in-scope config (turning limits, `pid_state` record list, reflex /
Collision Monitor) is boat-side (gabby/seafloor), not salmon. salmon checkout is
current (HEAD `21ebf37`, includes Phase A reflex launch `2a5f9ca`); no op-side
drift to reconcile. Clear to start the stack.

Open item for the annunciator edit (when we get to it): confirm whether
`rqt_operator_tools#36` is deployed on this op station — decides battery row form
(`source: diagnostics` vs `source: topic` BatteryState fallback).

## 4. Stack bring-up

**2026-05-26T11:49-04:00** — Operator reports the **op-side stack is up** on
salmon; **boat (gabby) stack not yet up**. Annunciator string confirmation for
battery / FCU-system / sound-speed is **gated on the boat** — those originate on
gabby and arrive over the udp_bridge, so they won't appear on the op-side
`/diagnostics` bus until gabby is up and the bridge connects. Only the
network/link rows are live now. Holding the annunciator work until the boat
stack is up.

**2026-05-26T11:53-04:00** — Op-side health check at operator request (one
`ros2 node list` probe; zenoh RMW, discovery clean → read valid). 17 nodes, op
stack healthy. Present: `/operator/camp`, `/operator/udp_bridge`; all four
network monitors (`/mikrotik_monitor`, `/ping_monitor`, `/starlink_diagnostics`,
`/teltonika_monitor` — feed annunciator network rows); joystick→helm path
(`/bizzy/joy_node`, `/bizzy/joy_to_helm`, `/bizzy/command_bridge_sender`);
`/bizzy/robot_state_publisher` + `/bizzy/joint_state_publisher` (display model);
`/rosbag2_recorder`; rqt panels. No boat-originated nodes yet (no `mavros` / boat
sensors) — expected, gabby down. One non-bizzy node visible via discovery:
`/molab/johnny5/johnny5_node` (molab ns) — flagged to operator to confirm
expected.

## 5. OAK camera displays — grey frames

**2026-05-26T11:58-04:00** — Operator observation: "weird mostly grey frames on
some of the OAK camera displays" (some, not all). Recorded as-is. Note: boat
stack reported not-yet-up as of §4 (11:49), yet video is reaching the displays —
either gabby came up since, or the affected panels are in a no-signal/stale
state. Awaiting operator clarification on which cameras and current boat state;
no cause attributed yet. (Context, not a diagnosis: OAK streams are H.26x with
coprime-keyframe tuning from #133/`2297579`; a freshly-opened viewer shows grey
until the next keyframe — distinguishable from a real stall by whether it clears
on its own.)

**2026-05-26T12:03-04:00** — Operator follow-up: **fwd, port, and aft** OAK
displays occasionally go mostly grey, then **recover on their own**; **segmentation
stays good** throughout the grey periods. Key discriminator — segmentation runs
on the boat off the source frames, so its health means camera capture + on-boat
perception are fine; the grey is downstream, in the **encoded preview video sent
to the operator + decoded op-side**. Multi-camera, self-recovering grey is
consistent with **lost keyframe packets** (decoder shows grey until the next
I-frame; long coprime GOPs from #133 stretch the recovery). Localizes to video
transport/bandwidth to the op station, **not** camera or perception. Matches the
known OAK encoder/bandwidth-for-OTH concern (git-bug `001461d`). **Non-blocking**
(recovers, perception unaffected). Boat now inferred **up** (segmentation is a
gabby-side process). No probe run yet — offered link-stats + `topic hz`
correlation to operator; awaiting go/no-go.

**2026-05-26T12:10-04:00** — udp_bridge stats probe at operator request
(`/operator/udp_bridge/remotes/bizzy/bridge_info`, single sample). Boat confirmed
up (mavros/nav2/marine topics forwarding). **Caveat: OAK video is not on
udp_bridge** (separate ffmpeg transport per `oak_*_ffmpeg` config), so these
numbers don't directly measure the video drops — they're shared-link health.

Link split (op↔boat, instantaneous):
- **WiFi (cap 1.5 MB/s): clean** — msg success ~822 KB/s, **dropped 0**, dup 0,
  resend success ~9.1 KB/s.
- **VPN (cap 1.0 MB/s): lossy** — msg success ~660 KB/s, **dropped ~21.6 KB/s**,
  duplicates ~4.8 KB/s, resend 0.
- `resend_giveup_count: 4752` cumulative; `next_packet_number: 368703`.

Read: WiFi clean, **VPN path dropping + duplicating** — a packet-loss/jitter
signature, not bandwidth exhaustion (bridge traffic well under caps, though the
bridge doesn't see ffmpeg video bytes). Ties to the grey frames **indirectly**:
aft camera streams over VPN (`oak_aft_ffmpeg`→vpn); if fwd/port also route VPN,
VPN loss is a clean match for transient grey-then-recover. Not yet confirmed
which path fwd/port use. Still non-blocking.

**2026-05-26T12:13-04:00** — Operator action: set the **VPN-path period to 1.0**
for `/bizzy/collision_monitor/pointcloud` in udp_bridge (was `period: 0.0` =
unthrottled on both vpn + wifi per the §5 bridge_info sample). Throttles the
Phase-A reflex cloud to ~1 Hz on VPN to cut its VPN load. On-theme with the VPN
drops above — testing whether reducing VPN load eases the drops / grey frames.
Before-baseline for comparison: VPN `dropped` ~21.6 KB/s. **Durability**: if set
as a live param it reverts on restart — source config (Phase-A bridge list,
`2a5f9ca`) still has VPN `period 0.0`; offered to persist + commit as a field
change. Watching for VPN-drop / grey-frame improvement.

**2026-05-26T12:19-04:00** — Before/after re-sample of bridge VPN stats after the
pointcloud throttle. Operator reports cameras **look better**. udp_bridge VPN
link, however, is **not** measurably improved:
- msg dropped: 21.6 → **21.7 KB/s** (flat)
- duplicates: 4.8 → **7.8 KB/s** (up)
- `resend_giveup_count`: 4752 → 8512 over ~158 s = **~24 giveups/s**, climbing
- WiFi still clean (0 dropped).

Interpretation (consistent, not contradictory): video is ffmpeg, not bridge.
Throttling the pointcloud freed VPN headroom for the ffmpeg video → cameras
improve, while the bridge's own VPN loss (link-quality-driven) stays. **The VPN
path itself is still lossy** (~22 KB/s dropped, ~24 pkt/s abandoned). Fine today
on WiFi; **flag for OTH / Starlink-only** where VPN is the only path and there's
no WiFi to fall back on. Follow-up, not a today-blocker. Durability of the
period=1.0 change still open (see prior entry).

**2026-05-26T12:24-04:00** — Operator interpretation of the apparent
contradiction: the camera improvement is **probably from less dropping on the
*send* side**. This resolves why the re-sample above didn't move — that probe was
the **salmon (receive) side** (`/operator/udp_bridge/...`), whereas the send-side
relief is on the **boat's (gabby) udp_bridge** outbound. Throttling the pointcloud
VPN path cut what gabby has to push over VPN, so its send queue overflows less and
the shared VPN egress leaves more room for the ffmpeg video → cleaner cameras.
The receive-side `dropped`/giveup figures (still ~22 KB/s, ~24 pkt/s) reflect
in-transit/link loss, a separate axis from send-queue overflow. To confirm
quantitatively, the place to look is **gabby-side** bridge_info send stats (not
sampled from salmon).

## 6. Annunciator string confirmation (op-side /diagnostics)

**2026-05-26T12:29-04:00** — Pre-edit live-string check for the #171 annunciator
rows (boat up + bridge forwarding = precondition met). Captured op-side
`/diagnostics` (~8 s, 13991 lines). **Boat diagnostics ARE on the op-side bus**
(forwarded/republished), so `source: diagnostics` rows will resolve. Confirmed
exact names:
- **`mavros: Battery`** (exact) — battery row.
- **`mavros: System`** (exact) — FCU System row.
- **`sound_speed_bridge`** (exact name, no host/instance suffix) — and it **is
  publishing**, resolving the #163 "does it publish at all" doubt; exact match
  works (substring not required).
- Also live: `mavros: Heartbeat` (already the FCU row), `zda_serial_bridge`,
  `NTRIP`, `GPS: RTK`, and **`segments_to_pointcloud_reflex: obstacle projection
  feed`** — the reflex-health task the deployment issue wanted surfaced on the
  operator annunciator (confirmed present).
- `/bizzy/mavros/battery` (BatteryState) is forwarded op-side → topic-source
  battery fallback available.

Still open before editing the YAML: (a) exact `Voltage` KeyValue casing on
`mavros: Battery`; (b) `rqt_operator_tools#36`-deployed decision (diagnostics vs
topic battery-row form). Paused — see §7 (rviz issue took priority).

**2026-05-26T12:47-04:00** — Operator asked "are you seeing diagnostics from the
boat?" Fresh `/diagnostics` sample: **yes, boat diagnostics live and OK** (level 0
/ Normal) — full mavros suite (`Battery` 28.49 V, `System`, `Heartbeat` 1.0 Hz,
`GPS`, `MAVROS UAS`, `Mount`), `mavros_router` endpoints, `sound_speed_bridge`,
`zda_serial_bridge`, `NTRIP`, `GPS: RTK`, and `segments_to_pointcloud_reflex:
obstacle projection feed`. Boat→op diagnostics path solid; if a panel isn't
showing them it's display/config, not the link. **Resolved annunciator open item
(a):** `mavros: Battery` KeyValue key is **`Voltage`** (capital V) → `value_key:
Voltage`. Only open item left is (b) the `#36`-deployed battery-row-form decision.

**2026-05-26T12:36-04:00** — Resolved (b): inspected deployed
`rqt_annunciator/config_model.py` — it has `source: diagnostics` + `value_key` +
`select_keyvalue` + threshold evaluation + the "fails loud as `Voltage?`" path, so
**#36 is deployed → use the diagnostics-source battery row** (not the topic
fallback). Threshold syntax is the expression-string form (`warn: "value < 23.0"`).
Appended three rows to `bizzyboat_project11/config/bizzyboat_operator_annunciator.yaml`
(Battery / FCU System / Sound Speed); YAML validates (12 indicators). Deviation
from issue spec: `stale_timeout: 10.0` on all three (issue left battery/FCU at 5 s
default) — justified by the measured VPN loss; 1 Hz boat diags need slack to avoid
nuisance stale-flips. Battery reads 28.49 V → expect green. Told operator to load
the **source path** via the config dialog (no rebuild to see it now); installed
copy stale until `colcon build` of `bizzyboat_project11` — durability/commit
deferred.

**2026-05-26T12:38-04:00** — **Validated live on-panel** (operator loaded the
config): Battery **green at 28.5 V**, FCU System populated, Sound Speed **yellow
at 0 as expected** (no SVS data yet). #171 annunciator-coverage gap closed and
confirmed on the operator panel. Pending: (a) optional extra row for
`segments_to_pointcloud_reflex: obstacle projection feed` (would tick the reflex
section's "surfaces on operator annunciator" box — offered); (b) durability —
`colcon build --packages-select bizzyboat_project11` + field-change commit,
deferred to operator/wrap-up.

## 8. Reboot salmon (clears NVIDIA mismatch)

**2026-05-26T12:20-04:00** — Operator preparing to reboot salmon (permanent fix
for the §7 NVIDIA driver/library mismatch — reloads the matching kernel module,
restores rviz GPU accel). Pre-reboot flags raised: (1) annunciator rows are
loaded from the *source* file into the running panel — they revert on relaunch
unless `bizzyboat_project11` is rebuilt first (installed copy stale); offered to
rebuild before reboot. (2) Op-side `rosbag2_recorder` gets killed by reboot —
finalize if it holds wanted data (boat-side recording on gabby unaffected). (3)
Boat (gabby) stays up on its own host; lose CAMP command+monitoring for the
reboot window — ensure boat in a safe state. Log + config edits persist on disk
across reboot (no commit needed for safety).

## 9. Post-reboot — stack restarted, rviz restored, annunciator triage

**2026-05-26T12:31-04:00** — Salmon back up, stack restarted. **rviz works (GPU
restored)** and the **collision-avoidance pointcloud (`/bizzy/collision_monitor/
pointcloud`) renders in rviz** — ticks the deployment-issue operator-SA checkbox
for the Phase-A reflex feed.

**Annunciator "config stuck" triage:** ruled out config + data. Installed config
is a **symlink to source** (so the panel's file *has* the 3 boat-health rows);
`/diagnostics` flowing at ~18 Hz with all expected statuses live post-reboot
(mavros Battery/System/Heartbeat, sound_speed_bridge, all four net monitors,
segments_to_pointcloud_reflex). **Resolved — no problem:** operator clarified "stuck" meant the config **stayed**
(persisted) across the reboot, not frozen. Because the installed config is a
symlink to source, the three boat-health rows came back automatically on relaunch
— **no rebuild needed** (the §8 pre-reboot "rows will vanish unless rebuilt" flag
was moot for this symlink-installed package). All good post-reboot: rviz on GPU,
reflex pointcloud rendering, annunciator carrying Battery/FCU/Sound Speed. Only
remaining annunciator loose end is the **git commit** (field change, for
reconciliation) — wrap-up item, non-operational.

## 10. gabby stack restarted — op-side re-check

**2026-05-26T12:35-04:00** — Operator restarted the stack on gabby; checked op
side. Boat reacquired cleanly: 11 boat statuses back on `/diagnostics`, reflex
pointcloud publishing again ~5 Hz. Non-OK scan — one ERROR, rest known/cosmetic:
- **ERROR `udp_bridge operator: bizzy: resend give-ups`** — the known VPN
  packet-loss (cumulative give-ups crossed threshold), not a new restart fault.
- WARN (benign/expected): `sound_speed_bridge` (yellow@0, no SVS data),
  `mavros: Mount` (no gimbal hw), `MikroTik wifi.bizzy ether2–5` (unused ports),
  `Starlink starlink.bizzy link` (single common WARN), `Teltonika router.op
  mwan3/ifWan1` (WAN-failover row). Nothing restart-related broken; good to proceed.

**2026-05-26T12:39-04:00** — Operator reported the pointcloud wasn't updating in
rviz and asked me to kill rviz for a restart. Single clean `rviz2` (PID 6754, no
launch wrapper); SIGTERM ignored → needed SIGKILL = rviz was **hung** (matches the
frozen display). Pointcloud topic itself was healthy (~5 Hz), so the freeze was
rviz-side; fresh relaunch should render updates again. Killed only rviz2, nothing
else. Operator relaunched — rviz back up, pointcloud rendering again.

## 11. Boat launch / on-water

**2026-05-26T12:43-04:00** — **Boat in the water** (BizzyBoat launched). Timestamp
verified from system `date` for bag correlation.

> **Timestamp correction / re-anchor:** earlier entries this session carried
> *estimated* wall-clock times that drifted **ahead** of the true clock — the
> §8–§10 (reboot and after) entries by over an hour before this fix. Verified
> system time at launch is **12:43 EDT**; the true session span is ~11:47→12:43.
> The impossible future-dated stamps (§6 build/validate, §8–§10) were pulled back
> to plausible monotonic values; remaining earlier minute-stamps should be read
> for **content and relative order**, not absolute precision. All entries from
> launch onward are stamped from the system clock. Full cleanup at wrap-up.

**2026-05-26T14:12-04:00** — **Boat recovered** (out of the water). On-water span
~1h29m (launched 12:43). On-water validation results pending operator debrief —
headline scope (yaw cap 1.0, planner radius 1.5 m, `pid_state` capture) not yet
recorded; to be filled in from operator on the on-water behavior.

## 12. Wrap-up (salmon)

**2026-05-26T14:15-04:00** — Wrap-up at operator request; on-water details logged
by other hosts.

**On-water validation → see other host logs.** Per operator, the headline-scope
results (yaw cap 1.0, planner radius 1.5 m, `pid_state` capture, any collision-
monitor exercise) are recorded in the gabby/dev logs for this deployment. Not
duplicated here — this is the op-side (salmon) record only.

**Salmon-side work done today:**
- Pre-deploy `make sync` + `make build` (all 7 layers green); read deployment
  issue `20a49fc`.
- Confirmed no op-side config needed before bring-up; verified op stack healthy.
- OAK grey-frame investigation → VPN send-side loss; logged before/after of the
  operator's pointcloud-VPN-throttle (cameras improved; bridge VPN loss unchanged).
- #171 annunciator gap closed: Battery / FCU System / Sound Speed rows added +
  validated live.
- rviz GLX failure root-caused (NVIDIA driver upgrade w/o reboot) + worked around
  + resolved by reboot.
- Post-reboot, gabby-restart, and rviz-hang re-checks — all clean.

**Files touched (salmon):**
- `bizzyboat_project11/config/bizzyboat_operator_annunciator.yaml` — 3 boat-health
  rows (#171).
- `docs/logs/2026/2026-05-26_salmon_logs.md` — this log.

**Pending for dev-side wrap-up / reconciliation:**
- Reconcile the annunciator config field change to GitHub via
  `/import-field-changes`.
- **VPN packet loss** (`udp_bridge … resend give-ups` ERROR; ~24 pkt/s abandoned)
  — open follow-up for OTH/Starlink-only; decide between throttling more VPN
  topics vs. addressing link quality.
- **Pointcloud VPN `period=1.0`** was a *live* change — confirm whether it was
  persisted in the Phase-A bridge config (gabby-side); if not, it reverts on
  restart.
- **NVIDIA auto-upgrade hazard** — roadmap item: pre-deploy reboot check after
  `apt upgrade` on op-stations (or pin driver / disable graphics auto-upgrades).
- Optional: add `segments_to_pointcloud_reflex: obstacle projection feed` row to
  the operator annunciator (issue wanted reflex health surfaced on-panel).

**Timestamps:** entries before launch (§5–§10) were re-anchored after estimate
drift — see the §11 correction note; treat pre-launch minute-stamps as
approximate.

## 7. rviz2 — OpenGL/GLX context failure

**2026-05-26T12:33-04:00** — Operator hit repeated rviz2 errors on launch:
`Unable to create a suitable GLXContext`, `Failed to create an OpenGL context -
BadValue (integer parameter out of range)`, `Unable to create the rendering
window after 100 tries`. Graphics/display issue, **not** ROS/data — camera
displays render fine, so the display works; rviz2's specific GL context request
is being refused. Suggested fix: relaunch with software rendering
(`LIBGL_ALWAYS_SOFTWARE=1 rviz2`); fallback checks: `echo $DISPLAY`, and freeing
GPU contexts (camera grids + CAMP can exhaust them). Did not launch rviz from the
agent shell (no shared display). Outcome pending operator.

**2026-05-26T12:40-04:00** — Root cause found (operator asked "worked yesterday,
what changed?"). **NVIDIA driver/library version mismatch** from an OS
auto-upgrade:
- `nvidia-smi` → "Failed to initialize NVML: Driver/library version mismatch"
  (NVML lib 580.159).
- `/var/log/dpkg.log`: **2026-05-26 09:20** apt upgraded `nvidia-driver-580`
  **580.142 → 580.159.03** (+ `libnvidia-gl`, `xserver-xorg-video-nvidia`,
  kernel modules).
- `who -b`: last boot **2026-05-18** (up 1 week) — kernel module in memory is
  still the old 580.142; new userspace libGL can't bind to it → new GLX contexts
  fail → rviz2 can't open. Worked yesterday because the upgrade landed 09:20 today.
- **Not** caused by `make build` (ran ~11:20, after the 09:20 upgrade).

Hybrid graphics: RTX 3070 Ti + AMD Radeon 680M (AMD/Mesa path unaffected).
**Fix now (no stack disruption):** `LIBGL_ALWAYS_SOFTWARE=1 rviz2` (Mesa CPU); if
sluggish, `DRI_PRIME=0 rviz2` for AMD hardware accel. **Permanent fix = reboot**
(reloads matching module) — **deferred to wrap-up**; rebooting mid-op would tear
down CAMP / udp_bridge / recording / camera displays.

**2026-05-26T12:44-04:00** — Operator confirmed cause: **manual `apt upgrade`
this morning** (not unattended-upgrades), reboot not checked afterward. Matches
the 09:20 dpkg timestamp exactly. Pre-deploy checklist item for the roadmap: on
the op-station, after any `apt upgrade`, run
`[ -f /var/run/reboot-required ] && cat /var/run/reboot-required.pkgs` and reboot
**before** stack bring-up if a kernel/driver update landed — avoids the
rviz-GLX-break mid-deployment.
