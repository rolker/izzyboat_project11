# BizzyBoat Deployment Log

Tracking the deployment of ros2_agent_workspace on gabby (BizzyBoat robot computer).

Parent issue: [unh_echoboats_project11#14](https://github.com/rolker/unh_echoboats_project11/issues/14)

## Sub-Issue Status

### Critical Path

| # | Task | Status | Notes |
|---|------|--------|-------|
| [ros2_agent_workspace#422](https://github.com/rolker/ros2_agent_workspace/issues/422) | Sync repos to secondary git server | **repos pushed** | All repos manually pushed; script plan in PR [#424](https://github.com/rolker/ros2_agent_workspace/pull/424) |
| [unh_echoboats_project11#15](https://github.com/rolker/unh_echoboats_project11/issues/15) | Boat manifest with gitcloud URLs | **done** | PR [#21](https://github.com/rolker/unh_echoboats_project11/pull/21) merged |
| [CCOMJHC/ccomjhc_project11#5](https://github.com/CCOMJHC/ccomjhc_project11/issues/5) | Connect gabby to VPN/gitcloud | **done** | PR [#8](https://github.com/CCOMJHC/ccomjhc_project11/pull/8) merged |
| [unh_echoboats_project11#16](https://github.com/rolker/unh_echoboats_project11/issues/16) | Install ROS 2 Jazzy on gabby | **done** | PR [#20](https://github.com/rolker/unh_echoboats_project11/pull/20) merged |
| [unh_echoboats_project11#17](https://github.com/rolker/unh_echoboats_project11/issues/17) | Bootstrap and build on gabby | **done** | PR [#22](https://github.com/rolker/unh_echoboats_project11/pull/22) merged |

### Parallel Work

| # | Task | Status | Notes |
|---|------|--------|-------|
| [unh_echoboats_project11#13](https://github.com/rolker/unh_echoboats_project11/issues/13) | bizzyboat_project11 package | **in progress** | Core launch tested on gabby. Sub-issues: [#25](https://github.com/rolker/unh_echoboats_project11/issues/25) (URDF, open), [CCOMJHC#9](https://github.com/CCOMJHC/ccomjhc_project11/issues/9) (camera IPs, done) |
| [CCOMJHC/ccomjhc_project11#6](https://github.com/CCOMJHC/ccomjhc_project11/issues/6) | Site-specific config | not started | |
| [unh_echoboats_project11#23](https://github.com/rolker/unh_echoboats_project11/issues/23) | Sensors layer (OAK + DeltaT) | **done** | PR [#24](https://github.com/rolker/unh_echoboats_project11/pull/24) merged |
| [CCOMJHC/ccomjhc_project11#9](https://github.com/CCOMJHC/ccomjhc_project11/issues/9) | DHCP reservations for boat devices | **done** | PR [#12](https://github.com/CCOMJHC/ccomjhc_project11/pull/12) merged. All 6 devices verified reachable after power cycle |
| [CCOMJHC/ccomjhc_project11#11](https://github.com/CCOMJHC/ccomjhc_project11/issues/11) | Operator station manifest (salmon) | **done** | PRs [#13](https://github.com/CCOMJHC/ccomjhc_project11/pull/13), [#14](https://github.com/CCOMJHC/ccomjhc_project11/pull/14) merged |
| [ros2_agent_workspace#423](https://github.com/rolker/ros2_agent_workspace/issues/423) | Git-bug/offline agent workflow | not started | |
| [unh_echoboats_project11#18](https://github.com/rolker/unh_echoboats_project11/issues/18) | Deployment guide | not started | |

### Related Work

| # | Task | Status | Notes |
|---|------|--------|-------|
| [CCOMJHC/ccomjhc_project11#3](https://github.com/CCOMJHC/ccomjhc_project11/issues/3) | Hierarchical DNS | **done** | PR [#7](https://github.com/CCOMJHC/ccomjhc_project11/pull/7) merged. Domain: `.p11.lan` (not `.local`) |

---

## Session Log

### 2026-03-26

#### Pre-work: Repository migration

Before deployment planning began, migrated `ccomjhc_project11` from personal fork to CCOMJHC org:

- Swapped remotes on local repo: `origin` now points to `CCOMJHC/ccomjhc_project11`, `upstream` to `rolker/ccomjhc_project11`
- Migrated open issues from `rolker/ccomjhc_project11` to `CCOMJHC/ccomjhc_project11`:
  - #7 (Hierarchical DNS) → [CCOMJHC#3](https://github.com/CCOMJHC/ccomjhc_project11/issues/3)
  - #9 (IzzyBoat network update) → [CCOMJHC#4](https://github.com/CCOMJHC/ccomjhc_project11/issues/4)
- Closed #1 on personal fork (ament conversion already complete)
- Recreated worktree for issue #4 (was #9), cherry-picked existing commit
- Manifest repo (`unh_marine_autonomy`) updated to point at CCOMJHC org ([#109](https://github.com/rolker/unh_marine_autonomy/issues/109), merged)

#### Deployment planning

- Created parent issue [#14](https://github.com/rolker/unh_echoboats_project11/issues/14) on `unh_echoboats_project11`
- Broke plan into sub-issues across repos (public vs private):
  - Workspace infrastructure (#422, #423) on `ros2_agent_workspace`
  - Boat-specific work (#13, #15, #16, #17, #18) on `unh_echoboats_project11`
  - Private/sensitive tasks (#5, #6) on `CCOMJHC/ccomjhc_project11`
- Key design decisions:
  - Boat manifest uses gitcloud URLs directly (no remote switching after bootstrap)
  - Repo sync to gitcloud is a workspace feature, not boat-specific
  - Git-bug for offline agent workflow on field machines
  - Agents log everything for later deployment guide generation

#### Shared tmux sessions

Set up three shared tmux sessions for collaborative agent/human work:

- **gabby** — BizzyBoat robot computer
- **router** — BizzyBoat Teltonika RUTX11
- **deadpool** — operator/dev machine
- **op_router** — operator Teltonika RUTX11

**Protocol**: Agents may observe tmux sessions freely but must ask before issuing any command. Roland acts as air traffic controller for all sessions. Passwords are entered by Roland when prompted — agents should wait ~10 seconds before asking if not entered.

#### Active agents

- **Agent on CCOMJHC/ccomjhc_project11#3**: Hierarchical DNS — **both routers deployed, two clients verified**. gabby and deadpool both resolving `.p11.lan` names. Switched from `.local` to `.lan` to avoid systemd-resolved/mDNS conflict. PR updated: [CCOMJHC/ccomjhc_project11#7](https://github.com/CCOMJHC/ccomjhc_project11/pull/7).
  - **Tip**: On NetworkManager systems (deadpool), `nmcli device reapply` does NOT trigger DHCP renewal — must use `nmcli connection down/up`. On systemd-networkd systems (gabby), `networkctl reconfigure` works fine. **Blocker discovered and resolved**: gabby couldn't reach operator network via WiFi bridge — BizzyBoat router was missing static routes for 192.168.13.0/24 and 192.168.12.0/24 via the bridge gateway (172.16.20.2). Routes added via router web UI. Verified: `ping deadpool.op.p11.lan` 1.85ms, `ping salmon.op.p11.lan` 3.05ms. Note: ZeroTier on gabby still pending — gitcloud not yet reachable.
- **Agent on ros2_agent_workspace#422**: Sync workspace repos to a secondary git server. All repos manually pushed to gitcloud — success. Plan PR open: [#424](https://github.com/rolker/ros2_agent_workspace/pull/424). Agent now free — implementation deferred for later review.
- **Agent logging CCOMJHC/ccomjhc_project11#5**: Documented gabby ZeroTier + gitcloud setup (human-driven, agent logged). PR [#8](https://github.com/CCOMJHC/ccomjhc_project11/pull/8) merged, issue closed.

#### Routing fix

gabby couldn't reach operator network (192.168.13.0/24) via WiFi bridge. Root cause: BizzyBoat router missing static routes. Added routes for 192.168.13.0/24 and 192.168.12.0/24 via WiFi bridge gateway (172.16.20.2). Verified: deadpool 1.85ms, salmon 3.05ms via direct path.

#### Current state

- **DNS**: `.p11.lan` working on both routers, verified on gabby and deadpool
- **Routing**: gabby can reach operator network via both WiFi bridge (direct, ~2ms) and VPN (~37ms)
- **gitcloud**: All workspace repos pushed; gabby on ZeroTier and can reach gitcloud
- **Next**: Bootstrap and build on gabby (#17) — all prerequisites now met
- **Deferred**: DeltaT sonar driver not yet in workspace — tracked as [unh_marine_autonomy#111](https://github.com/rolker/unh_marine_autonomy/issues/111). Will add to boat manifest once integrated.
- **Gitcloud sync**: Pushed latest `unh_echoboats_project11` and `ccomjhc_project11` to gitcloud before bootstrap. Manual push still needed until #422 automation lands.
- **Gotcha**: Default branch on gitcloud for `unh_echoboats_project11` was not set to `jazzy` — config files weren't visible. Fixing via agent.

#### Bootstrap attempt (#17)

- Workspace cloned on gabby from gitcloud, git identity configured
- **Blocked**: Bootstrap process fetches `bootstrap.yaml` via a raw file URL from gitcloud, which returns 404. Likely a Forgejo raw URL format issue or repo name mismatch. Also identified gap: no env var or CLI flag to override the manifest URL (hardcoded to `configs/project_bootstrap.url`).
- PR [#22](https://github.com/rolker/unh_echoboats_project11/pull/22) open with progress log.
- **Session paused** — will resume later.

### 2026-03-27

#### Resuming deployment

- Fresh reboot of operator machine and BizzyBoat
- Tmux session `gabby` recreated with SSH to gabby
- Bootstrap blocker from 2026-03-26 has been fixed in the workspace repo:
  - PR [#426](https://github.com/rolker/ros2_agent_workspace/pull/426) merged — `BOOTSTRAP_URL` env var / `--bootstrap-url` CLI flag for alternate manifests
  - Additional hardening: whitespace rejection, recursive make fix for layer list
- **Next**: Agent resuming #17 — pull updated workspace on gabby, retry bootstrap with `BOOTSTRAP_URL`

#### Bootstrap issues discovered (#17 agent)

1. ~~**Site layer not created**~~ — False alarm; site_ws was there, just missed initially.

2. **rosdep not run automatically**: After layers were created and repos imported, `rosdep install` was not triggered by `make build`. There is no rosdep target in the Makefile — it's entirely manual. Opened [ros2_agent_workspace#429](https://github.com/rolker/ros2_agent_workspace/issues/429) to track.

3. **Stale `project11` package references**: Running `rosdep` manually surfaced unresolvable dependency on `project11` — the old package name for `marine_autonomy`. Found in `izzyboat_project11/package.xml` and `lr30_project11/package.xml`. Being handled by #17 agent.

4. **Gazebo pulled in by rosdep on robot computer**: `rosdep install` on gabby resolved a dependency chain that pulled in Gazebo via `nav2_bringup` — completely inappropriate for a field robot. Root cause: `nav2_bringup` is a dependency in `ben_project11` and possibly another echoboat-related package. Issues opened on the affected repos. This highlights the need for a **manifest lint** tool — see [ros2_agent_workspace#430](https://github.com/rolker/ros2_agent_workspace/issues/430).

5. **Power management check on gabby** (after Gazebo install):
   - No display manager (gdm3/lightdm/sddm) installed or running ✓
   - `logind.conf` is stock defaults, no custom power settings ✓
   - Sleep/suspend/hibernate targets all `static` and `inactive` ✓
   - No `power-profiles-daemon`, no GNOME power settings, no `acpid` ✓
   - **`upower.service` is running** — pulled in by Gazebo deps. However it sees no battery, no lid, no real power supply — effectively inert on this hardware.
   - Sleep targets not masked (masking can cause log noise per past experience). Low risk given no triggers present.

#### Continuing build

- Dependencies fully installed on gabby (including unwanted Gazebo — will clean up later)
- Build proceeding with all current layers
- Roland adding sensors layer manually to test Luxonis OAK cameras — not waiting for #23 PR
- **Build successful** on gabby with all layers including sensors. First successful full build on the robot computer.
- **OAK camera test successful** — Luxonis OAK cameras verified working on gabby with `depthai_marine` from sensors layer.
- PRs [#22](https://github.com/rolker/unh_echoboats_project11/pull/22) (#17) and [#24](https://github.com/rolker/unh_echoboats_project11/pull/24) (#23) merged.
- Agent assigned to #13 (bizzyboat_project11 package) — launch files, config, URDF for BizzyBoat hardware.
- Agent on #422 (repo sync) still working — reverted unauthorized lint change, fixing code.
- Agent on #25 (URDF) opened plan PR [#27](https://github.com/rolker/unh_echoboats_project11/pull/27), then retasked to CCOMJHC#11.
- Agent on #13 (bizzyboat_project11) paused after initial package creation.
- Agent on CCOMJHC#11 (operator manifest) found missing platform repo `molab_hardware` — opened [unh_marine_autonomy#112](https://github.com/rolker/unh_marine_autonomy/issues/112).
- Created sub-issues for #13: [#25](https://github.com/rolker/unh_echoboats_project11/issues/25) (URDF), [#26](https://github.com/rolker/unh_echoboats_project11/issues/26) (udev rules), [CCOMJHC#9](https://github.com/CCOMJHC/ccomjhc_project11/issues/9) (DHCP reservations).
- Created [CCOMJHC#10](https://github.com/CCOMJHC/ccomjhc_project11/issues/10) for NTRIP credential migration to private repo.
- Created [ros2_agent_workspace#429](https://github.com/rolker/ros2_agent_workspace/issues/429) for missing rosdep step in `make build`.
- Created [ros2_agent_workspace#430](https://github.com/rolker/ros2_agent_workspace/issues/430) for manifest lint tool.

#### Hardware enumeration on gabby

Plugged in BizzyBoat hardware and monitored syslog. All devices detected:

| Device | USB Port | Serial Port | Vendor:Product | Purpose |
|--------|----------|-------------|----------------|---------|
| HD USB Camera | 1-1 | — (UVC) | `32e4:9230` | Factory-provided USB camera (in addition to 4x OAK PoE cameras installed separately) |
| CubeOrange FCU | 1-8 | `ttyACM0`, `ttyACM1` | `2dae:1016` | ArduRover autopilot (serial `43001E000A51323237373236`) |
| Arduino | 1-5 | `ttyACM2` | `2341:0043` | CTD winch controller (serial `342343139313512040B1`) |

**Notes**:
- `nouveau` driver spamming GSP errors on Nvidia GPU (`0000:01:00.0`) — needs `nvidia-driver` install or `nouveau` blacklist
- ModemManager probed the Arduino — may need udev rule to exclude serial devices from ModemManager if it interferes with comms
- 4x OAK cameras are PoE (networked, not USB) — already tested successfully. Need static IP assignments on the BizzyBoat network.

#### Electronics bay layout (from photos)

- **Portable rack** (black frame, loose, will be screwed down): contains router + 2x PoE switches
- **Finned enclosures**: gabby (Linux, Neousys Nuvo 9160GC) on right, Windows machine on left
- Reference point sticker placed on hull for URDF measurements
- Photos saved in `~/Downloads/2026-03-27_BizzyBoat*.jpg` (7 photos total)

### 2026-03-30

#### DHCP reservation verification

- Boat powered up — all computers, switches, and cameras power cycled
- Verified all DHCP reservations from [CCOMJHC#9](https://github.com/CCOMJHC/ccomjhc_project11/issues/9) are working:
  - mercat (192.168.20.8) — confirmed by Roland
  - kvm (192.168.20.50) — ping from gabby: 0.7ms
  - bizzy-oak-1 (192.168.20.9) — ping from gabby: 0.2ms
  - bizzy-oak-2 (192.168.20.10) — ping from gabby: 0.9ms
  - bizzy-oak-3 (192.168.20.11) — ping from gabby: 0.8ms
  - bizzy-oak-4 (192.168.20.12) — ping from gabby: 0.9ms
- PR [CCOMJHC#12](https://github.com/CCOMJHC/ccomjhc_project11/pull/12) merged, issue [CCOMJHC#9](https://github.com/CCOMJHC/ccomjhc_project11/issues/9) closed

#### Operator station manifest complete

- [CCOMJHC#11](https://github.com/CCOMJHC/ccomjhc_project11/issues/11) closed — PRs [#13](https://github.com/CCOMJHC/ccomjhc_project11/pull/13) (manifest) and [#14](https://github.com/CCOMJHC/ccomjhc_project11/pull/14) (docs) merged on 2026-03-27

#### OAK camera verification via UDP bridge

**Goal**: Display OAK camera images on salmon (operator station) via ROS 2 UDP bridge from gabby (BizzyBoat).

**Prerequisites**:
- [x] `feature/issue-13` branch pushed to gitcloud (as `jazzy` branch)
- [x] gabby: switched to `jazzy` branch, rebased, built `bizzyboat_project11` (commit 07354f7, 0.47s)
- [x] salmon: pull and build `bizzyboat_project11` — fast-forward to 07354f7, built in 1.29s
- [x] DNS: `gabby_bb` resolves from salmon (192.168.20.5, 1.97ms via WiFi bridge route)
- [x] gabby: core launch (UDP bridge) running
- [x] gabby: oak_cameras_launch.py running — all 4 cameras publishing
- [x] salmon: operator bridge running — rqt UDP bridge plugin confirms connection
- [x] salmon: all 4 OAK camera images verified via rqt — correct position labels confirmed

**Salmon readiness check** (via remote Claude Code agent on salmon):
- DNS `gabby_bb` → 192.168.20.5, 1.97ms — correct. Operator network routes to 192.168.20.0/24 via WiFi bridge by default.
- `udp_bridge` — built in `core_ws/install/`
- `bizzyboat_project11` — **not built** on salmon. Package lives on `feature/issue-13` (unmerged). Need to get this branch checked out and built on salmon.
- Agent flagged that `gabby_bb` resolved to the LAN IP rather than a WiFi bridge IP — worth verifying the routing path is optimal.

**UDP bridge misconception**: Both the gabby and salmon agents initially reported that `operator.yaml` needed image topic *subscriptions* for the operator to receive images. This was incorrect — the UDP bridge automatically accepts incoming data from the remote side. The operator config only needs to declare topics it wants to *send* to the robot; the receive side is implicit. Corrected by Roland after both agents agreed on the wrong answer. Lesson: agent consensus on a technical claim doesn't make it correct — domain expertise is still ground truth.

**Deployment method**: Multiple iterate-fix-deploy cycles coordinated across 3 machines (deadpool as coordinator, gabby running cameras + bridge, salmon running operator bridge + rqt). Edits committed on deadpool, pushed to gitcloud as `jazzy` branch, then pulled and rebuilt on gabby and salmon.

**Incident — push to wrong remote**: During one fix cycle, a commit was pushed to `origin` (GitHub) instead of `gitcloud`, bypassing GitHub branch protection / PR review. Followed up with the correct push to gitcloud. Lesson: in multi-remote repos, always specify the remote explicitly — `origin` is GitHub, `gitcloud` is the field deployment server.

**Near-miss — wrong-repo checkout on gabby**: The gabby agent tried a relative `cd layers/main/.../unh_echoboats_project11` which failed, then retried with bare `git checkout jazzy` which would have run in the workspace root. Coordinator spotted the risk and warned, but the warning was nearly missed. Lesson: prompts to remote agents should use absolute paths; time-sensitive warnings about rejecting commands need to be more prominent.

**Fixes applied during testing**:
- `operator.yaml`: replaced legacy hostnames (`gabby_bb`, `salmon_bb`, etc.) with hierarchical DNS names (`gabby.bizzy.p11.lan`, `salmon.op.p11.lan`, etc.)
- OAK camera IPs: updated from placeholder IPs to DHCP-assigned IPs (`.9`–`.12`)
- OAK camera position mapping: identified correct IP-to-position by viewing images via UDP bridge

| Camera | IP | MXID |
|--------|-----|------|
| oak_forward | 192.168.20.10 | 19443010D117872D00 |
| oak_starboard | 192.168.20.12 | 19443010E11A872D00 |
| oak_aft | 192.168.20.9 | 14442C10917D8DD700 |
| oak_port | 192.168.20.11 | 194430106121872D00 |

**End-to-end verified**: 4 OAK cameras on gabby → UDP bridge over WiFi bridge → rqt on salmon. All images display correctly with correct position labels.

**Remote agent coordination notes**:
- `tmux send-keys ... Enter` submits immediately in Claude Code — multiline prompts get truncated to the first line. Single-line prompts worked reliably for directing remote agents.
- Coordinator sent a duplicate `make build` to gabby without checking tmux state first — Roland had already run it. Lesson: always observe the session before sending commands.

### 2026-03-31

#### FCU tooling setup

**Goal**: Install MAVProxy for ArduPilot parameter management, set up udev rules, review FCU config.

**Coordinator error — wrong venv path**: Coordinator sent a prompt to the gabby agent telling it to install MAVProxy in `~/.venv` instead of the workspace venv at `~/project11/.venv`. Roland interrupted the agent, redirected it to first check the workspace venv state, then ran `make lint` to properly create the venv via the Makefile's standard path. MAVProxy install then directed to the correct location. Lesson: coordinator must know the target machine's workspace layout — gabby's workspace is at `~/project11`, not `~`.

- `make generate-skills` run on gabby — 21 skill files generated
- `make lint` run on gabby — created `.venv`, installed pre-commit + deps, all linters passed
- MAVProxy installed in `/home/field/project11/.venv/`:
  - `pip install MAVProxy` pulled v1.8.74 but hit missing `future` module, then `pkg_resources` not found
  - Root cause: `setuptools` v82 dropped `pkg_resources`; MAVProxy still imports it
  - Fix: `pip install 'setuptools<81'` (installed 80.10.2) — MAVProxy 1.8.74 now working
  - ModemManager warning is informational — proper fix is udev rules to exclude FCU serial ports
- Udev rules ([#26](https://github.com/rolker/unh_echoboats_project11/issues/26)) — separate agent assigned to set up stable symlinks and ModemManager exclusions
- Opened [#30](https://github.com/rolker/unh_echoboats_project11/issues/30) — configure CUAV C-RTK 2HP GPS (depends on URDF #25 for position offsets)
- Opened [#31](https://github.com/rolker/unh_echoboats_project11/issues/31) — test thruster response and operator joystick control (incremental: cmd_vel → joystick → end-to-end manual)
- Opened [#32](https://github.com/rolker/unh_echoboats_project11/issues/32) — configure ArduPilot failsafes for comms loss (no hardware kill switch; failsafe is primary safety mechanism)
- Opened [#33](https://github.com/rolker/unh_echoboats_project11/issues/33) — outdoor GPS + Starlink connectivity test (boat moving outside today)
- **Starlink note**: already mounted on boat, connected to router WAN port, automatic failover when out of WiFi range
- Noted [ros2_agent_workspace#432](https://github.com/rolker/ros2_agent_workspace/issues/432) — opened by repo sync agent after discovering gitcloud-only changes in `marine_ais` and `unh_echoboats_project11` from field testing. Proposes a workflow for merging field hotfixes from gitcloud back to GitHub without the full worktree ceremony.

**Tmux protocol violation**: Gabby agent (working on #26 after MAVProxy install) ran `make sync` and `make build` on gabby without asking for approval. These are commands on a shared tmux session — each requires per-command human approval. The agent likely lost the tmux protocol context after being retasked from MAVProxy to #26 work. This is the same class of violation as orchestration log entry #12 (2026-03-27). Recurring pattern: agents forget tmux rules when context shifts within a session.

**Launch approach**: Gabby agent (now on #31) is creating separate tmux sessions on gabby for each launch file (core, perception, nav). This differs from IzzyBoat where the startup script (`start_tmux_project11.bash`) uses one tmux session with multiple panes for a single monolithic launch. The modular tmux approach matches BizzyBoat's modular launch design (core_launch, perception_launch, nav_launch) and allows restarting individual components independently.

- Opened [#34](https://github.com/rolker/unh_echoboats_project11/issues/34) — install ENC data on gabby for S-57 chart navigation

#### Thruster test — unexpected prop spin (INCIDENT)

First arming test on #31. Agent published `false` to `piloting_mode/standby/active`,
which armed the FCU in GUIDED mode. **Props started spinning immediately without
any cmd_vel command** — thrusters ramped up with steering input as if navigating
to a waypoint.

**Root cause**: ArduPilot had 2 stale mission waypoints loaded (`MIS_TOTAL=2`).
WP1 was ~12m from current GPS position (43.1357687, -70.9392882). On entering
GUIDED mode, ArduPilot began navigating to WP1 autonomously.

**Response**: Immediately set standby (`data: true`) — echo_helm disarmed → set
MANUAL → re-armed. Props stopped. Staying armed in MANUAL is by design for RC
fallback.

**Lessons**:
- Must clear mission waypoints before entering GUIDED mode, or send zero-velocity setpoint immediately on arm
- Need timed test wrapper scripts that auto-return to standby/MANUAL
- Nav2 plugin name mismatch found: `project11_navigation::controllers::CrabbingPathFollower` not found, available as `marine_nav_crabbing_path_follower::CrabbingPathFollower` (separate issue)

- Opened [#35](https://github.com/rolker/unh_echoboats_project11/issues/35) — discuss when to clear stale mission on GUIDED mode entry
- Draft PR [#36](https://github.com/rolker/unh_echoboats_project11/pull/36) open for #31
- **Step 1 complete**: echo_helm + mavros control path verified. cmd_vel → setpoint_velocity → thrusters working. Safety test script (`test_cmd_vel.sh`) with auto-standby created.
- **Step 2 in progress**: moving to joystick control on salmon

- Errors found from old `project11` → `marine_autonomy` rename (Nav2 plugin class name mismatch was one symptom). Agent fixing.

**Also noted**: Agent violated tmux protocol again (sent `ls` without asking).

#### PRs merged

**PR [#29](https://github.com/rolker/unh_echoboats_project11/pull/29) — udev rules + FCU baseline** (closes #26):
- Udev rules at `config/udev/99-bizzyboat.rules`: stable symlinks `/dev/fcu`, `/dev/fcu_slcan`, `/dev/winch`
- Uses `ENV{}` properties to distinguish CubeOrange MAVLink vs SLCAN interfaces
- `core_launch.py` FCU default updated from `/dev/ttyACM0:57600` to `/dev/fcu:57600`
- 935-parameter FCU baseline captured at `config/fcu/bizzyboat_fcu_baseline.param`
- BizzyBoat vs IzzyBoat parameter comparison documented
- Tested on gabby: symlinks stable across unplug/replug, MAVProxy connected via `/dev/fcu`
- USB camera intentionally omitted (only V4L2 device, `/dev/videoN` sufficient)

**PR [#27](https://github.com/rolker/unh_echoboats_project11/pull/27) — URDF plan** (closes #25):
- Plan for xacro-based URDF with hull STL mesh (2.4m EchoBoat 240)
- `base_link` reference: center screw hole in hull floor, near CG
- Sensor positions estimated from photos + manual, to be refined with physical measurements
- Reference geometry documented in `docs/bizzyboat_reference_geometry.md`

**PR [#424](https://github.com/rolker/ros2_agent_workspace/pull/424) — repo sync scripts** (closes workspace #422):
- New scripts: `add_remote.py`, `push_remote.py`, `pull_remote.py`
- Automates adding/pushing/pulling a named remote across all workspace repos
- Replaces the manual per-repo gitcloud push workflow used during earlier deployment sessions

#### Active agents

| Agent | Task | Status |
|-------|------|--------|
| gabby-agent | FCU tooling (MAVProxy) | MAVProxy installed, idle |
| Agent on #26 | Udev rules for FCU/Arduino/ModemManager | **done** — PR [#29](https://github.com/rolker/unh_echoboats_project11/pull/29) merged |
| Agent on PR #424 | Repo sync script (workspace) | **done** — PR [#424](https://github.com/rolker/ros2_agent_workspace/pull/424) merged |
| Brainstorm agent | Logging and checklist ideas | in progress |
| Logger agent | Implementing logger | in progress |
| Research agent | ArduPilot/mavros research | complete |
| Gabby agent (#31) | Thruster testing | in progress |
| This session | Coordinator / deployment log | active |
