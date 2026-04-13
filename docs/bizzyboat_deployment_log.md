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
| [unh_echoboats_project11#13](https://github.com/rolker/unh_echoboats_project11/issues/13) | bizzyboat_project11 package | **in progress** | Core launch tested on gabby. Jazzy merged into feature/issue-13 (15 commits). Sub-issues: [#25](https://github.com/rolker/unh_echoboats_project11/issues/25) (URDF, done — PR #27 merged), [CCOMJHC#9](https://github.com/CCOMJHC/ccomjhc_project11/issues/9) (camera IPs, done) |
| [unh_echoboats_project11#37](https://github.com/rolker/unh_echoboats_project11/issues/37) | GPS antenna offsets | **GPS working** | Moving baseline RTK heading verified. PR [#38](https://github.com/rolker/unh_echoboats_project11/pull/38) open. NTRIP deferred |
| [CCOMJHC/ccomjhc_project11#6](https://github.com/CCOMJHC/ccomjhc_project11/issues/6) | Site-specific config | not started | |
| [CCOMJHC/ccomjhc_project11#16](https://github.com/CCOMJHC/ccomjhc_project11/issues/16) | Operator dnsmasq hosts | **PR open** | PR [CCOMJHC#17](https://github.com/CCOMJHC/ccomjhc_project11/pull/17) deployed, needs gabby verification |
| [mobile_lab#1](https://github.com/rolker/mobile_lab/issues/1) | johnny5 camera integration | **in progress** | Repo consolidated from molab_description + molab_hardware |
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

#### Joystick control progress (#31 continued)

Operator launch on salmon with joystick connected at `/dev/input/js0`. Helm messages confirmed reaching gabby via UDP bridge. Several issues found and fixed during testing:

- **Topic name mismatches**: stale `project11/` prefixes in UDP bridge configs (`bizzyboat.yaml`, `operator.yaml`) → updated to `marine/` prefix. Fixed.
- **echo_helm topic prefix**: `marine_autonomy/` vs `marine/` mismatch between echo_helm and helm_manager. Fixed in `seafloor_echoboat_project11` (PR [#7](https://github.com/rolker/seafloor_echoboat_project11/pull/7), merged as [#6](https://github.com/rolker/seafloor_echoboat_project11/issues/6)).
- **helm_manager output_type**: default `helm` only publishes Helm msg, not TwistStamped that echo_helm expects. Fix: set `output_type: twist` in `bizzyboat.yaml` — **config added but not yet deployed or tested**.

**Blocked on**: pushing `output_type: twist` change to gitcloud, rebuilding on gabby + salmon, restarting launches. This is the last known gap before end-to-end joystick → thruster control.

Detailed session log: `docs/bizzyboat_thruster_test_2026-03-31.md` in issue-31 worktree.

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

### 2026-04-02

#### GPS antenna offsets (#37)

Separate agent on [#37](https://github.com/rolker/unh_echoboats_project11/issues/37) configured CUAV C-RTK 2HP dual-antenna moving baseline RTK. Key results:

- GPS1 (CAN 124) is the **forward** antenna — opposite from IzzyBoat
- Moving baseline heading confirmed ~74° ENE, matching pier orientation
- 28 sats, 3D fix at 43.072°N, 70.712°W
- Key ArduPilot params: `GPS_POS1_X=0.835`, `GPS_POS2_X=-0.835`, `GPS_MB1_TYPE=1`, `GPS_MB1_OFS_X=1.67`
- NTRIP deferred — needs credential migration ([CCOMJHC#10](https://github.com/CCOMJHC/ccomjhc_project11/issues/10))
- Docs committed to `feature/issue-37` branch; PR [#38](https://github.com/rolker/unh_echoboats_project11/pull/38) open

#### Operator network — mobile lab interface

Added `192.168.50.1` interface on operator router for mobile lab network. This provides access to johnny5 (Axis PTZ camera, 192.168.50.55) on the mobile lab roof.

#### Operator dnsmasq (CCOMJHC#16)

- [CCOMJHC#16](https://github.com/CCOMJHC/ccomjhc_project11/issues/16) opened — add dnsmasq hosts file for operator router with fleet-wide hierarchical names
- PR [CCOMJHC#17](https://github.com/CCOMJHC/ccomjhc_project11/pull/17) created by another agent:
  - `operator.hosts` covering operator LAN, mobile lab (192.168.50.x), BizzyBoat (WiFi + VPN), IzzyBoat, ZeroTier, and WireGuard hosts
  - Updated `bizzyboat.hosts` with new entries and bare convenience aliases
  - Renamed operator router UCI interfaces (`mobile_lab`→`bizzy_wifi_bridge`, `wifi_bridge`→`izzy_wifi_bridge`, `lan1`→`mobile_lab`)
  - Deployed to both routers, DNS verified from deadpool
  - Still needs verification from gabby

#### Mobile lab repos consolidated

`molab_description` + `molab_hardware` merged into new `rolker/mobile_lab` repo. Manifest updated (PR [unh_marine_autonomy#119](https://github.com/rolker/unh_marine_autonomy/pull/119) merged, [unh_marine_autonomy#112](https://github.com/rolker/unh_marine_autonomy/issues/112) closed).

#### johnny5 camera investigation (mobile_lab#1)

Agent started on [mobile_lab#1](https://github.com/rolker/mobile_lab/issues/1) — worktree created, consolidation commits done (molab_description + molab_hardware into subdirs). No johnny5-specific commits yet.

#### Merged jazzy into feature/issue-13

15 commits pulled in: URDF xacro, hull mesh, udev rules, FCU baseline params, reference geometry docs.

### 2026-04-03

#### WiFi bridge unreachable

Cannot reach BizzyBoat via WiFi bridge from operator side. Suspected cause: UCI interface renaming in CCOMJHC#17 (dnsmasq PR from April 2) may have broken firewall zones or routing rules that reference old interface names. Opened [CCOMJHC#19](https://github.com/CCOMJHC/ccomjhc_project11/issues/19) — agent investigating.

Boat is inside the mobile lab today — no GPS or Starlink.

**Fixed**: PR [CCOMJHC#22](https://github.com/CCOMJHC/ccomjhc_project11/pull/22) (closes [CCOMJHC#19](https://github.com/CCOMJHC/ccomjhc_project11/issues/19)). Root cause: PR #17 renamed operator router UCI network interfaces but didn't update the firewall zone — `bizzy_wifi_bridge` and `izzy_wifi_bridge` were outside any zone, so all forwarded traffic was rejected. Also renamed BizzyBoat router's `lan1` → `wifi_bridge` across all UCI subsystems for consistency. Verified: deadpool → WiFi bridge → gabby ping working.

#### DNS forwarding broken on boat router — fixed

External DNS resolution failing on gabby (`ping google.com: Name or service not known`)
despite internet working via cell modem failover. Investigated:

- `ping 8.8.8.8` works — internet via cell (mwan3 failover from dead Starlink)
- `nslookup google.com 8.8.8.8` works — external DNS reachable directly
- `nslookup google.com 192.168.20.1` fails — boat router's dnsmasq returning NXDOMAIN
- Same NXDOMAIN from `127.0.0.1` on the router itself

**Root cause**: dnsmasq had hardcoded `server=8.8.8.8/8.8.4.4/1.1.1.1` entries. These
queries originate from the router itself, bypass mwan3 firewall marks, and follow the
main routing table's default route via WAN (Starlink, `eth1`). With Starlink down (no
DHCP lease indoors), these queries fail. Meanwhile, the auto-generated resolv file
(`/tmp/resolv.conf.d/resolv.conf.auto`) has working Verizon DNS servers from the cell
modem interface.

**Fix**: Removed hardcoded `server=` entries from dnsmasq UCI config, relying solely on
the resolv file populated by active interfaces:
```
uci delete dhcp.cfg01411c.server
uci commit dhcp
/etc/init.d/dnsmasq restart
```

Verified: `ping google.com` and `nslookup gabby.bizzy.p11.lan` both work from gabby.
Fix is provider-agnostic — dnsmasq uses whichever upstream DNS servers are available.

#### DNS naming scheme revision

Reviewed the hierarchical DNS naming structure and identified several improvements:

- **WiFi bridge radios**: Replace model-specific names (omnitik, sxtsq) with generic `wifi.<vehicle>` pattern. Operator-side radios: `<vehicle>.wifi.op`
- **WireGuard endpoints**: New `wg` segment to distinguish tunnel endpoints from VPN NETMAP addresses (`bizzy.wg` vs `gabby.vpn.bizzy`)
- **VPN NETMAP**: Canonical form `<host>.vpn.<vehicle>` with shorthands for unique hosts (`gabby.vpn`)
- **Documentation**: Tree diagrams (operational vs infrastructure) and addressing quick guide

Opened [CCOMJHC#20](https://github.com/CCOMJHC/ccomjhc_project11/issues/20) with full naming spec. Agent completed the work — PR [CCOMJHC#21](https://github.com/CCOMJHC/ccomjhc_project11/pull/21) open.

#### Resuming joystick work (#31)

- Both agents synced and built (`make sync`, `make build`) — gabby: 40 packages, salmon: all layers clean
- Symlink added on gabby: `~/start_tmux_project11.bash` → installed script in `platforms_ws/install/bizzyboat_project11/lib/bizzyboat_project11/`
- Ran `./start_tmux_project11.bash` on gabby — `project11` tmux session created with 3 windows (core, perception, nav)
- Cron not yet configured — manual launch only during setup phase
- Added `source ~/project11/layers/main/site_ws/install/setup.bash` (or similar) to gabby's `.bashrc` so ROS 2 commands work without manual sourcing
- **Perception launch failed**: `cube_bathymetry` package not found — not in sensors layer on gabby
- **Nav launch partial failure**: Nav2 `controller_server` crashed (stale plugin class `project11_navigation::controllers::CrabbingPathFollower`), but `echo_helm` and `helm_manager` started successfully
- **Heartbeat not seen** on `/bizzy/marine/heartbeat` — helm_manager is running and publishing, but mavros not connected to FCU
- **Root cause**: `core_launch.py` still defaulted to `/dev/ttyACM0:57600` but udev rules (PR #29) created `/dev/fcu` symlink pointing to `ttyACM1`. PR #29 added the udev rules but didn't update the launch file default. March 31 thruster test worked because agent used explicit parameter override.
- **Fix**: Updated `core_launch.py` default to `/dev/fcu:57600` (edit on gabby, not yet committed)
- After fix, core relaunched — mavros connected, heartbeat flowing: `connected: true`, `armed: false`, `mode: MANUAL`, `marine_autonomy_standby: true`
- S57 ENC data: downloaded latest NOAA dataset, rsync'd from deadpool `~/data/ENC_ROOT/` to gabby `/home/field/data/ENC_ROOT/` (referenced by `ROS_S57_ENC_ROOT` in launch script). Note: next time, copy the zip and unpack on target — faster than rsync of many small files over WiFi bridge.
- Operator launch running on salmon in tmux session `core` — UDP bridge, foxglove bridge, joy_to_helm all up
- **Heartbeat confirmed on salmon** — flowing from gabby via UDP bridge over WiFi bridge
- **First joystick test failed** — props spun in GUIDED mode but not responding to joystick. No stale waypoints (`wp_received=0`), but `helm_manager output_type` was still `helm` — config not loaded because helm_manager was in `nav_launch.py` which didn't load `bizzyboat.yaml`.

#### Launch file restructure

Reorganized launch files to put everything needed for joystick driving in core:

**core_launch.py (new)**: mavros, UDP bridge, mru_transform, sea_surface_estimator, robot state publisher, marine_autonomy robot_core (helm_manager, command_bridge), echo_helm, S57 charts. Loads `bizzyboat.yaml` via `SetParametersFromFile`.

**nav_launch.py (new)**: Nav2 only. Can be restarted independently without affecting joystick control or chart loading.

After rebuild and relaunch, `helm_manager output_type` confirmed as `twist`.

- **Joystick → thruster END-TO-END VERIFIED** — full chain working: joystick (salmon) → joy_to_helm → helm_manager (twist) → UDP bridge → echo_helm (gabby) → mavros → FCU → props responding to joystick input.

#### Steering direction issues

Throttle responds correctly but steering direction is intermittently reversed:
- Sometimes correct, sometimes wrong, sometimes oscillates between the two before settling
- Heading is stable (~244.6° from dual-antenna GPS), GPS has fix — not a heading drift issue
- `setpoint_velocity/cmd_vel` values look correct (angular.z ~-0.5 to -0.8 rad/s)
- Reduced `max_yaw_speed` from 1.5 to 0.5 — improved range/resolution but direction still inconsistent
- No stale waypoints (`wp_received=0`)

**Suspected root cause**: ArduRover's handling of `BODY_NED` velocity commands with `PILOT_STEER_TYPE=0` (throttle + steering servo). IzzyBoat uses `PILOT_STEER_TYPE=3` (skid-steer/differential throttle) where ArduPilot directly mixes velocity into left/right throttle. BizzyBoat's type 0 goes through a steering PID controller (`ATC_STR_*` params), which may not handle body-frame velocity commands well when stationary on a trailer (no actual yaw rate feedback → PID integral windup → oscillation/reversal).

**Next session TODO**:
- Test on water where actual yaw feedback exists — the PID may behave correctly when the boat can rotate
- Research ArduRover GUIDED velocity control for `PILOT_STEER_TYPE=0` — does it properly support `BODY_NED`?
- Consider testing `PILOT_STEER_TYPE=1` (direction+throttle steering) or other modes
- If body-frame velocity remains problematic, consider `rc_mode=true` as fallback (direct PWM, no PID)
- Check ArduPilot `GUID_OPTIONS` parameter for velocity control behavior flags

#### Uncommitted changes on gabby (jazzy branch)

- `bizzyboat.yaml`: `max_yaw_speed` 1.5 → 0.5

#### Committed and pushed to gitcloud

- `core_launch.py`: fcu_url `/dev/ttyACM0` → `/dev/fcu`, moved marine_autonomy/echo_helm/S57 from nav_launch
- `nav_launch.py`: Nav2 only
- `start_tmux_project11.bash`: tmux window names (core, perception, nav)

#### Other notes

- Moved boat outside for Starlink connectivity — cell was dropping API connections
- gabby `.bashrc` now sources workspace setup
- Legacy `~/dora_as_core.bash` symlink on salmon points to old ROS 1 catkin workspace

#### Sub-issue status update

| # | Task | Status | Notes |
|---|------|--------|-------|
| [#37](https://github.com/rolker/unh_echoboats_project11/issues/37) | GPS antenna offsets | **GPS working** | Moving baseline heading verified; PR [#38](https://github.com/rolker/unh_echoboats_project11/pull/38) open. NTRIP deferred |
| [CCOMJHC#16](https://github.com/CCOMJHC/ccomjhc_project11/issues/16) | Operator dnsmasq hosts | **PR open** | PR [CCOMJHC#17](https://github.com/CCOMJHC/ccomjhc_project11/pull/17) — deployed, needs gabby verification |
| [mobile_lab#1](https://github.com/rolker/mobile_lab/issues/1) | johnny5 camera integration | **in progress** | Repo consolidated, camera work not started |
| [unh_marine_autonomy#112](https://github.com/rolker/unh_marine_autonomy/issues/112) | mobile_lab manifest entry | **done** | PR [#119](https://github.com/rolker/unh_marine_autonomy/pull/119) merged |

### 2026-04-06

Boat on pier, powered up, sky view. Strong winds — not going in the water today.

#### Operator station RDP (mercat) — fixed

RDP from deadpool (Remmina) to mercat was failing:

1. **Kerberos auth failure**: FreeRDP tried NLA/Kerberos against `CCOM.NH` domain, couldn't reach KDC. Fix: changed Remmina security setting from default to TLS.
2. **Login rejected**: Password accepted locally but rejected over RDP. Root cause: someone had changed the Windows **display name** but not the actual **username** (via Control Panel "Change your account name", which only changes the display name). The Remmina connection was using the displayed name, which didn't match the real account. Fixed by using the actual username (confirmed via `net user`).

#### NTRIP / MACORS setup

MACORS registration process for RTK corrections:
1. Go to https://macors.massdot.state.ma.us/
2. Create an account (one per device — convention: use boat name as username)
3. From the account, subscribe to the **real-time GPS corrections service** (free)
4. Wait for service activation (not instant — status shows "awaiting activation")
5. Once active, credentials go in `ntrip_launch.py` (host: `macorsrtk.massdot.state.ma.us`, port: 31000, mountpoint: `RTCM3_MASA`)

BizzyBoat account created, subscription submitted — activated same day.
NTRIP uncommented in core_launch.py, relaunched on gabby. RTK fix confirmed —
position visibly tighter in CAMP.

#### Operator UI on salmon — working

Created `operator_ui_launch.py` for bizzyboat (thin wrapper around
`marine_autonomy/operator_ui_launch.py` with `bizzy` namespace, CAMP + rqt).
Committed in issue-13 worktree, pushed to gitcloud as jazzy, pulled and built
on salmon. Boat position visible in CAMP.

#### RTK confirmed working

MACORS account activated. Uncommented NTRIP in `core_launch.py`, relaunched on
gabby. RTK fix confirmed — position visibly tighter and more stable in CAMP.
Also adjusted steering rate in `bizzyboat.yaml`. Both changes committed and
pushed from gabby to gitcloud.

#### Mavros FCU — confirmed working

Previously listed as TODO (had timed out). Now working end-to-end via
core_launch — joystick driving, GPS position, and RTK corrections all
functional.

#### OAK cameras — switched to sea_surface_segmentation

Updated `oak_cameras_launch.py` to use `sea_surface_segmentation` instead of
raw `depthai_ros_driver`, matching the IzzyBoat pattern. One node per camera
with respawn. Committed and pushed to gitcloud.

Perception launch was failing due to missing `cube_bathymetry` in gabby's
sensors layer — added it, perception now launches.

#### DeltaT sonar — partial connectivity

DeltaT verified communicating with mercat (Windows operator machine). Still need
to configure it to send data to gabby and verify gabby's deltat ROS node receives
the data stream.

#### Starlink Mini — ethernet not working, WiFi fallback

Starlink Mini connected to RUTX11 via ethernet (eth1). Link up at 100Mbps,
DHCP lease received (192.168.1.212), but zero ARP responses from gateway
(192.168.1.1). Rebooted Starlink via web dashboard — same result. Dish MAC
(74:24:9f:10:10:c2) visible in ARP table but never completes resolution.

Suspect the Mini needs bypass mode enabled (via Starlink app or Mini's WiFi
management page) to work properly with a third-party router. Could not reach
Mini's management interface at 192.168.100.1 from gabby (same L2 issue).

**Workaround**: Connected RUTX11 to Starlink Mini via WiFi instead of ethernet
(ifWan1 interface). Status TBD — session ended before verifying.

mwan3 failover config:
- ifWan1 (WiFi to Starlink): metric 1 (highest priority)
- wan (ethernet to Starlink): metric 2 — currently broken
- mob1s1a1 (Verizon cell): metric 3 — flapping
- mob1s2a1 (SIM 2): disabled

**TODO**:
- Verify WiFi-to-Starlink path works for internet + ZeroTier
- Investigate Starlink Mini bypass mode for ethernet
- Consider disabling `wan` in mwan3 until ethernet issue resolved
- Stabilize cellular fallback

### 2026-04-07

#### Conditions

At the pier. Boat inside mobile lab being charged. No sky view — Starlink and GPS
unlikely to work. Access to gabby via WiFi bridge from deadpool/salmon.

#### Network troubleshooting

`make sync` on gabby partially succeeded — some repos fetched, others failed,
suggesting intermittent internet connectivity. Without Starlink (no sky view inside
the lab), gabby's only internet path is cellular (Verizon via RUTX11 mwan3).

**Symptom**: `make sync` on gabby partially succeeded — some repos fetched, others
timed out. Intermittent internet via cellular (only viable path with no sky view).

**Root cause**: mwan3 tracking thresholds too aggressive for cellular. Default config
marked mob1s1a1 offline after just ~9 seconds of dropped pings (interval=3, count=1,
down=3), causing rapid flapping between online/offline.

**Fix applied** (RUTX11 router, `uci commit mwan3 && mwan3 restart`):

| Setting | Before | After |
|---------|--------|-------|
| `mwan3.mob1s1a1.interval` | 3 | 5 |
| `mwan3.cfg0afbac.count` | 1 | 3 |
| `mwan3.cfg0afbac.down` | 3 | 5 |

Now requires ~25 seconds of total blackout before marking offline (vs ~9s before).
After restart, mob1s1a1 stayed online 5+ minutes continuously. `make sync` on gabby
succeeded on retry.

#### WireGuard tunnel (bcloud) investigation

**Symptom**: `wg show` on RUTX11 showed `0 B received, 1.01 KiB sent` — tunnel sending
keepalives but getting no response from BenCloud (18.213.242.76:51820).

**Findings**:

- BenCloud WireGuard is running (confirmed via SSH). Public key matches RUTX11 config.
- BenCloud last saw BizzyBoat handshake ~23 min ago (endpoint 174.196.200.125:4818).
- RUTX11 can ping BenCloud public IP (18.213.242.76) over cellular — 0% loss, 40-87ms.
- BenCloud reachable from gabby via ZeroTier (10.242.7.97) — confirmed working.
- gitcloud also reachable from gabby via ZeroTier — `make sync` succeeded through it.
- NETMAP NAT confirmed correct: 192.168.20.0/24 ↔ 192.168.21.0/24 for WG traffic.
- BenCloud allowed IPs for BizzyBoat peer: `10.132.146.6/32, 192.168.21.0/24` — correct.

**Log analysis**: mwan3 hotplug triggers WireGuard restarts on every WAN interface
state change (Teltonika firmware behavior, source not found in shell scripts — likely
proprietary). wan1 (WiFi to Starlink) flapping inside lab triggered 6+ restarts in
~2 minutes before our mwan3 threshold fix.

**Conclusion**: Verizon cellular is blocking outbound UDP to port 51820. Evidence:
- ICMP ping from RUTX11 to BenCloud (18.213.242.76) works — 0% loss, ~50ms.
- RUTX11 sends WG keepalives (7.66 KiB sent, 0 B received).
- BenCloud (rebooted, fresh state) sees no packets from BizzyBoat peer — no endpoint,
  no handshake, no transfer.
- First peer (153.66.163.21, non-cellular) re-established immediately after reboot.

**Fix needed**: Change BenCloud WG listen port to a carrier-friendly port (443, 53,
or 500) and update RUTX11 endpoint to match. Both sides need to change.

**Update**: After DNS fix changed the default route to Starlink (wan1), bcloud tunnel
came up immediately — handshake established, bidirectional traffic confirmed. The UDP
51820 block is **Verizon cellular specific**. Tunnel works fine over Starlink. For
offshore use: if Starlink drops and only cellular remains, the VPN will go down.
Port change still needed for full cellular resilience.

#### DNS resolution broken on gabby — fixed

**Symptom**: `nslookup google.com` and other external hostnames failing on gabby.
`make sync` worked earlier (via gitcloud/ZeroTier, which doesn't need DNS).

**Root cause**: Multiple interacting issues with dnsmasq upstream DNS on RUTX11:

1. wan1 (WiFi to mobile lab Starlink) provided 192.168.1.1 as DNS via DHCP — the
   Starlink router's built-in DNS proxy is unreliable (intermittent NXDOMAIN).
2. Verizon IPv4 DNS (198.224.186.x) unreachable when default route goes through
   Starlink (carrier-specific servers only work from Verizon's network).
3. wan6 IPv6 DNS (`fd2c:81e:f07e:10::1`) from Starlink ethernet (broken L2 interface)
   was returning fast NXDOMAIN responses that won the race against working servers.
4. With `all-servers` enabled, dnsmasq uses the first response — a fast wrong NXDOMAIN
   beats a slow correct answer.

**Fix applied** (RUTX11 router):
```
# Add reliable public DNS servers
uci add_list dhcp.cfg01411c.server='8.8.8.8'
uci add_list dhcp.cfg01411c.server='1.1.1.1'
uci set dhcp.cfg01411c.allservers='1'
uci set dhcp.cfg01411c.nonegcache='1'
uci commit dhcp

# Stop interfaces from advertising broken DNS servers
uci set network.wan1.peerdns='0'
uci set network.wan6.peerdns='0'
uci set network.mob1s1a1.peerdns='0'
uci commit network

/etc/init.d/network reload
/etc/init.d/dnsmasq restart
```

**Design rationale**: Public DNS (8.8.8.8, 1.1.1.1) works over any ISP path — Starlink
or cellular. `peerdns='0'` on all WAN interfaces removes unreliable per-carrier DNS.
`allservers` and `nonegcache` provide resilience. Prior approach (April 3) of removing
hardcoded servers failed because dnsmasq's locally-originated queries bypass mwan3 marks
and follow the main routing table — hardcoded servers only work if the default route is
alive. Public DNS + `peerdns='0'` avoids this because the servers are ISP-agnostic.

**Verified**: `nslookup google.com` and `nslookup macorsrtk.massdot.state.ma.us` both
resolve correctly on gabby.

#### OAK cameras — working, compressed image workaround needed

4x OAK cameras launch and produce images via `sea_surface_segmentation`. However,
compressed images (via `image_transport`) are not published unless the raw topic also
has a subscriber.

**Root cause**: Bug in `depthai_bridge::BridgePublisher` (upstream `depthai-ros`).
In `BridgePublisher.hpp:239`, `publish()` is gated on
`_node->count_subscribers(_rosTopic)` which only counts raw topic subscribers.
`image_transport::Publisher::publish()` would produce compressed output, but it never
gets called because `count_subscribers` doesn't see compressed-only subscribers
(they subscribe to `<topic>/compressed`, a different topic name). The correct fix
would be to use `image_transport`'s own `getNumSubscribers()` which includes all
transport plugin subscribers.

**Workaround**: Configure `udp_bridge` to subscribe to raw image topics with
`period: -1` (never actually send), which creates a raw subscriber that satisfies
the `count_subscribers` check, enabling compressed publishing for the real
compressed subscriptions.

#### Nav stack — launched, GPS-dependent errors expected

Nav2 controller server was failing due to old `project11_navigation` plugin names —
fixed in [seafloor_echoboat_project11#9](https://github.com/rolker/seafloor_echoboat_project11/pull/9).
After fix, full nav stack launches successfully. GPS and tide errors are expected
indoors (no fix → sea_surface_estimator can't look up tide data). Confirmed
sea_surface_estimator is included in core_launch.py.

Also reconciled gitcloud/GitHub divergence for unh_echoboats_project11 —
field fixes from Apr 2-6 merged via [#42](https://github.com/rolker/unh_echoboats_project11/pull/42).

#### ROS discovery fix

`ros2 node list` returned empty from SSH shells due to
`ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` only set in the project11 tmux windows,
not globally. Fixed by adding `export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` to
`~/.bashrc` on gabby. Also required `ros2 daemon stop && ros2 daemon start` to
clear stale daemon state.

#### IMU position offsets — applied to FCU

Refined AutoNav box dimensions and Cube Orange IMU position from IzzyBoat
measurement photos (2024-06-14, same Seafloor Systems AutoNav model):

- Box: 0.23 × 0.28 × 0.14 m (was 0.20 × 0.15 × 0.15 estimated)
- IMU at (-0.99, 0.0, 0.05) in ROS frame from base_link
- ArduPilot INS_POS: X=-0.99, Y=0.0, Z=-0.05 (all 3 IMUs)

Applied via mavproxy on gabby. Updated URDF, reference geometry doc, and created
`bizzyboat_fcu_custom.param` overlay file. Merged as part of PR #38 (issue #37).

#### Outstanding issues at end of session

- **NTRIP not running**: PR #38 merged the NTRIP credential launch change (loads
  from `ccomjhc_project11` private config). But `ros2 pkg prefix ccomjhc_project11`
  returns "Package not found" on gabby despite it building in the site layer. Needs
  investigation — may be a sourcing order issue or the package install wasn't picked
  up after sync/rebuild. Core launch fails because it can't find the NTRIP config.

- **`molab_description` stale build**: On deadpool, `make build` failed due to stale
  build artifacts for `molab_description` (consolidated into `mobile_lab` repo).
  Fixed by removing stale build/install dirs. Gabby may have the same issue.

- **WireGuard port**: ~~bcloud tunnel works over Starlink but not Verizon cellular
  (UDP 51820 blocked). Port change still needed for cellular resilience.~~
  Re-tested 2026-04-08 — tunnel works over Verizon cellular (see session below).
  Original block was likely transient. Monitor; add iptables port redirect if recurs.

- **Startup script**: `start_tmux_project11.bash` still has redundant
  `ROS_AUTOMATIC_DISCOVERY_RANGE` exports (now in `.bashrc`). Should be cleaned up.

- **`nav_launch.py` removed**: The gitcloud merge (PR #42) deleted nav_launch.py
  but the startup script still references it (line 45). Needs updating.

### 2026-04-08

#### WireGuard over Verizon cellular — working (was transient issue)

Re-investigated the April 7 finding that UDP 51820 was blocked by Verizon cellular.

**Test conditions**: BizzyBoat router on cellular only (mob1s1a1). WAN (Starlink
ethernet) and wan1 (WiFi bridge) both offline, confirmed via `mwan3 interfaces`.

**Result**: WireGuard tunnel to bcloud is working over Verizon cellular on port 51820.

- Router side: `wg show` on RUTX11 shows active handshake (8s ago), bidirectional
  transfer (565 KiB rx, 432 KiB tx), persistent keepalive every 25s.
- bcloud side: `wg show` on wg0 shows BizzyBoat peer (174.242.69.124:4130) with
  active handshake (9s ago), 166 MiB rx / 10 MiB tx.
- Both operator and BizzyBoat peers connected simultaneously.

**Conclusion**: The April 7 block was transient — possibly Verizon CGNAT port
mapping issue or mwan3 flapping disrupting the tunnel before our threshold fix
stabilized cellular tracking. No port change needed at this time.

**Additional test**: Re-enabled WAN interface (Starlink ethernet) — WireGuard tunnel
remained up through the mwan3 failover. No disruption to the bcloud tunnel when
switching from cellular-only back to multi-WAN.

**Starlink WAN**: Re-enabled WAN (Starlink ethernet) interface — confirmed online
via `mwan3 interfaces` (3m uptime alongside cellular). Starlink connectivity working
today (boat presumably has sky view).

**Contingency**: If UDP 51820 gets blocked again, plan is to add an iptables
PREROUTING REDIRECT on bcloud (e.g., UDP 4500 → 51820) so only the BizzyBoat
router endpoint needs updating — other clients stay on 51820.

#### ccomjhc_project11 package not found — fixed

**Symptom**: `ros2 pkg prefix ccomjhc_project11` returned "Package not found" on
gabby even after `make clean && make build`. Core launch failed because NTRIP
launch couldn't resolve `FindPackageShare('ccomjhc_project11')`.

**Root cause**: `package.xml` was missing the `<export><build_type>ament_cmake</build_type></export>`
tag. Without it, colcon didn't generate the `local_setup` entries in `package.dsv`,
so the package was never added to `AMENT_PREFIX_PATH` when sourcing the workspace.
Symptom was catkin-related CMake warnings during build (`CATKIN_INSTALL_INTO_PREFIX_ROOT`,
`CATKIN_SYMLINK_INSTALL` not used).

**Fix**: Added `<export><build_type>ament_cmake</build_type></export>` to
`ccomjhc_project11/package.xml`, rebuilt. Package now found, NTRIP launches
successfully as part of core_launch.

**Also noted**: Layer sourcing order mismatch — `setup.bash` sources sensors before
site, but `layers.txt` has site before sensors. Not blocking but should be
investigated.

#### Operator station working

Operator station (salmon) confirmed working:
- OAK camera views in rqt
- Foxglove with battery gauge
- johnny5 PTZ camera (192.168.50.55)

#### Agent incident — unauthorized tmux keystrokes

Claude Code agent sent `ros2 node list` into the gabby tmux session while the
user was actively typing, garbling both commands. Violation of the established
rule: always ask before sending ANY command to a tmux session. Logged in agent
feedback memory to prevent recurrence.

#### mru_transform missing sensor config — fixed

`mru_transform` had empty sensor topics (orientation, position, velocity) because
`bizzyboat.yaml` had no `mru_transform` section. Added sensor config pointing to
mavros topics (`mavros/imu/data`, `mavros/global_position/raw/fix`,
`mavros/global_position/raw/gps_vel`). Odom now publishing, tide frame working.

#### NTRIP/RTK lost on WAN failover

WAN (Starlink ethernet) connection dropped. Fallback to cellular did not restore
NTRIP — RTK fix lost. Workaround: re-enabled WiFi connection to Starlink (wan1),
disabled WAN (ethernet), RTK came back. Suggests mwan3 failover to cellular doesn't
properly re-route the NTRIP connection, or MACORS drops the session and ntrip_client
doesn't reconnect. Needs investigation — this is a reliability concern for offshore
operation where connectivity paths change.

#### Nav stack — manda_coverage added, hover not working

Added `manda_coverage` (ComputeSonarCoveragePath action server) to echoboat
`navigation_launch.py` — was missing from the lifecycle nodes list and launch
entries. Soundings remapped to `sensors/deltat/soundings` for BizzyBoat.

`behavior_server` appears to hang or silently crash when loading the
`marine_nav_behaviors::Hover` plugin. The `hover` action server never appears
in `ros2 action list`. bt_task_navigator fails activation because it can't find
the hover action server (1s timeout). Needs investigation — possible segfault
on plugin load or TF frame issue.

#### Water test

Boat in the water. Results:
- **RC manual control**: working
- **RC loiter mode**: working
- **Project11 manual control (joystick via operator)**: working
- **Hover (station keeping via nav stack)**: launches and engages, but drifts
  away rather than holding station. Had to take over with RC and return to
  ArduPilot loiter mode. Nav launch was initially not running (missed in startup),
  started it manually. Hover behavior needs tuning or investigation — may be
  PID params, odom quality, or cmd_vel mapping issue.
- **Trackline mission**: Planner failed — "start is occupied". Costmap S57 chart
  layer not adjusting for tides, marking boat basin as too shallow. Charted depths
  plus `minimum_depth: 0.1` makes the entire basin an obstacle. Need to verify
  sea_surface_estimator tide correction and/or adjust minimum_depth for testing.

Boat recovered and back inside mobile lab. Successful initial water test —
RC control, loiter, and project11 manual joystick all working end-to-end.

#### Forward USB camera — black image

Added `field` user to `video` group on gabby for USB camera access. Forward USB
camera (non-OAK) now opens but produces a black image. Low priority — secondary
camera, not blocking water test. Needs investigation later.

---

### 2026-04-10 — Field operations continued

**Location**: Pier / mobile lab area
**People**: Roland

Rolled boat out of mobile lab, powered up, connected charger.

#### Starlink Mini bypass mode — verified

Enabled bypass mode on the Starlink Mini while offline (in mobile lab, no sky view).
After rolling outside and powering up, verified via the RUTX11 router web UI that the
WAN interface received an address from the Starlink and is working. This resolves the
Starlink Mini ethernet issue from 2026-04-06 — bypass mode was the fix as suspected.

Re-enabled the WAN interface on the RUTX11 so Starlink ethernet is now an active WAN
path alongside cellular. Working for now — long-term stability TBD.

#### WireGuard VPN confirmed

Pinged gabby from deadpool via WireGuard (bcloud) — VPN is up.

#### NTP — Time Machines TM2000B setup

A colleague installed a Time Machines TM2000B GPS NTP appliance on the boat
network. Device not visible in the router's DHCP scan or ARP table — had a
static IP from a previous setup on a different subnet.

**Finding the device**: `arp-scan -l` from gabby (installed for this purpose)
found only known devices on 192.168.20.0/24. Factory default IP is 192.168.1.20.
Factory reset via front-panel pinhole button, then added temp IP
(`192.168.1.100/24`) on gabby to reach it. SSH tunnel from deadpool to access
web UI via gabby.

**Configuration**:
- Default login: `admin` / `tmachine` (lowercase)
- Changed password, enabled DHCP
- Device picked up 192.168.20.211 via DHCP

**Network integration** ([CCOMJHC/ccomjhc_project11#30](https://github.com/CCOMJHC/ccomjhc_project11/issues/30)):
- DHCP reservation on boat router: MAC `d4:e9:5e:06:15:63` → `192.168.20.123`
- DNS names added to both routers:
  - `time.lan.bizzy.p11.lan` / `time.bizzy.p11.lan` (192.168.20.123)
  - `time.vpn.bizzy.p11.lan` (192.168.21.123)
- Version-controlled hosts files updated in worktree (feature/issue-30)
- DHCP reservations for both routers backed up to `configuration/dnsmasq/`
- Rebooted TM2000B, confirmed it picked up .123 — `ping time.bizzy` works
  from deadpool via VPN
- Removed temp IP from gabby
- Version-controlled files committed, PR [CCOMJHC#31](https://github.com/CCOMJHC/ccomjhc_project11/pull/31)
  merged, closes [CCOMJHC#30](https://github.com/CCOMJHC/ccomjhc_project11/issues/30)

**NTP verification**: After reboot, TM2000B initially had only 2D fix (12 sats
tracked but not converged). NTP query returned "no eligible servers" — device
won't serve time without 3D fix (configurable). After a few minutes, 3D fix
acquired and NTP confirmed working:

```
ntpdate -q 192.168.20.123
2026-04-10 14:19:36 -0.017872 +/- 0.001383 192.168.20.123 s1 no-leap
```

Stratum 1, ~18ms offset, healthy. TM2000B is now the primary NTP source for the
boat network.

#### ISC ntpd on boat router

Replaced Teltonika NTP stack with ISC ntpd 4.2.8p15, same as operator router
(see `bizzyboat_ntp_investigation_2026-04-09.md` for background).

**Steps**:
1. Stopped/disabled Teltonika `ntpclient` (UCI `enabled='0'` + init.d disable),
   disabled `ntp_gps`. `untpd` was already disabled on this router.
2. Installed ISC ntpd: `opkg install ntpd`
3. UCI `file_flag='1'` + `config_file='/etc/ntp.conf'` — the UCI server list
   doesn't support per-server options like `prefer`, so using a static config.
4. Custom `/etc/ntp.conf`:
   - TM2000B (192.168.20.123) as preferred server
   - 0–3.openwrt.pool.ntp.org as backup
   - Server enabled for LAN clients

**Verification from gabby**:
```
ntpdate -q 192.168.20.123  →  s1, -17.9ms offset (TM2000B, GPS direct)
ntpdate -q 192.168.20.1    →  s2, -17.7ms offset (router, via TM2000B)
```

NTP chain: GPS → TM2000B (stratum 1) → router (stratum 2) → LAN clients.

#### Operator router NTP updated

Updated op router ISC ntpd config to include boat sources (also switched to
`file_flag='1'` + `/etc/ntp.conf` for consistency with boat router):
- TM2000B (192.168.20.123) via WiFi bridge
- Boat router (192.168.20.1) via WiFi bridge
- Internet pools as fallback

These sources are only reachable when the boat is nearby on the WiFi bridge.
ISC ntpd handles unreachable servers gracefully.

Also added DHCP option 42 (NTP server) on the op router LAN:
`uci add_list dhcp.lan.dhcp_option='42,192.168.13.1'`
This pushes the op router as NTP server to all DHCP clients, though Ubuntu
clients need a dispatcher script to act on it (not yet configured).

#### NTP client configuration — all machines

| Machine | Client | Sources | Notes |
|---------|--------|---------|-------|
| **gabby** | chrony (new, replaced timesyncd) | TM2000B (prefer), boat router, op router | Most critical — ROS 2 compute |
| **salmon** | chrony | op router, boat router (WiFi+VPN), TM2000B (WiFi+VPN), gabby (noselect) | Operator station |
| **deadpool** | chrony | op router, boat router (WiFi+VPN), TM2000B (WiFi+VPN) | Dev station |
| **boat router** | ISC ntpd | TM2000B (prefer), internet pools | Serves stratum 2 to LAN |
| **op router** | ISC ntpd | TM2000B (WiFi bridge), boat router (WiFi bridge), internet pools | Serves stratum 2-3 to LAN |

All chrony configs use `/etc/chrony/sources.d/project11.sources`.
Deadpool and salmon include both WiFi bridge and VPN paths for redundancy.

**Verified**: deadpool selected TM2000B via WiFi bridge as primary (`^*`),
stratum 2, -216μs offset, sub-millisecond accuracy from GPS.

#### PRs merged for water test

- [rolker/mru_transform#9](https://github.com/rolker/mru_transform/pull/9) —
  chart_datum_node for ellipsoid-to-MLLW vertical datum transform. Reviewed
  Copilot comments, fixed curl `--fail` flag and libproj runtime dependency.
- [rolker/unh_echoboats_project11#44](https://github.com/rolker/unh_echoboats_project11/pull/44) —
  mru_transform config and segmentation streams for bizzyboat.
- Both repos synced to gitcloud.

#### chart_datum_node added to BizzyBoat launch

Added `chart_datum_launch.py` include to `core_launch.py` (directly on gabby,
between sea_surface_estimator and MAVRos sections). This provides the
`map → chart_datum` MLLW vertical datum transform needed for correct
depth-aware planning against S57 charts.

VDatum grids (~1.7GB) copied from deadpool via rsync to `~/.cache/mru_transform/`
on gabby — CMake build-time download was too slow. Opened
[rolker/mru_transform#10](https://github.com/rolker/mru_transform/issues/10) to
make the build check-and-warn instead of downloading.

Full rebuild on gabby completed successfully. Gabby rebooted (pending kernel
upgrade). Setting up for second water test.

#### Starlink ethernet down after launch

Starlink was working all morning on the pier. After launching the boat,
the WAN interface (eth1) shows physical link UP but DHCP fails — no IP
assigned. `ifup wan` doesn't help. Starlink web GUI (via app) shows
satellite connection is fine. Cellular fallback is marginal (SINR 0 dB,
33% packet loss). Attempting remote Starlink reboot.

Bypass mode may have reverted, or the ethernet adapter needs a power cycle.
This is the same symptom as the April 6 ethernet issue.

#### WiFi bridge bandwidth saturation

Camera streams via UDP bridge saturated the WiFi bridge link to the operator
station, making it unusable. Had to manually reduce stream rates in UDP bridge
to recover. Need to reduce default bandwidth usage — lower resolution/FPS,
compress more aggressively, or send on demand only.

#### Water test #2 — partial, connectivity issues

Boat launched. Starlink ethernet stopped working (same bypass mode symptom as
April 6 — eth1 link UP but no DHCP). Remote reboot of Starlink via app didn't
help. Cellular fallback was marginal (SINR 0 dB, 33% packet loss, connection
bouncing). Connected boat router to mobile lab Starlink WiFi as workaround —
NTRIP/RTK recovered.

**WiFi bridge bandwidth saturation**: Camera streams via UDP bridge saturated
the WiFi bridge to the operator station, making it unusable. Had to manually
reduce stream rates to recover. Need to address default bandwidth usage.

**TF tree issue — `bizzy/map` frame missing**: mru_transform node is running,
publishing `/bizzy/odom` at 10Hz with valid position data, and registered as
a `/tf` publisher — but the `earth → bizzy/map → bizzy/odom` TF chain is not
appearing. Only `bizzy/base_link_north_up → bizzy/base_link` is on `/tf`.
Sea surface estimator IS publishing `bizzy/odom → bizzy/map_tide`. The missing
map frame means chart_datum_node can't look up position and doesn't publish
`bizzy/map → bizzy/chart_datum`. This needs investigation — may be a sensor
config issue preventing mru_transform from establishing the map frame origin.

**chart_datum_node configuration issues found**:
- Frame params (`map_frame`, `chart_datum_frame`, `base_frame`) default to
  unprefixed names (`map`, `chart_datum`, `base_link`) — need `bizzy/` prefix
- `SetParametersFromFile` from `bizzyboat.yaml` doesn't apply node-specific
  params by name — need to pass frame params inline in the launch file instead
- Added params to `bizzyboat.yaml` but they weren't picked up; set via
  `ros2 param set` as workaround but underlying TF issue blocked testing

**Changes made on gabby (not yet committed)**:
- `core_launch.py`: added chart_datum_launch.py include
- `bizzyboat.yaml`: added chart_datum params section (may need different approach)

Boat recovered.

#### TODO from water test #2
- [ ] Investigate why mru_transform isn't publishing `earth → bizzy/map → bizzy/odom` TF
- [ ] Fix chart_datum frame params — pass inline in launch file with frame_prefix
- [ ] Starlink bypass mode — why did it stop working? Physical inspection needed
- [ ] Reduce UDP bridge camera bandwidth defaults
- [ ] Test chart_datum + tide frames once map frame issue resolved

### Session 7 — 2026-04-13

#### Starlink API reachable in bypass mode

Confirmed from gabby that the Starlink dish management interface at
`192.168.100.1` is reachable even with the dish in bypass mode. `curl
http://192.168.100.1` returns the Starlink diagnostics web UI. The gRPC API at
`192.168.100.1:9200` should also be available, enabling monitoring of dish stats
(signal quality, obstruction, throughput, latency).

Original ROS 1 package by munzz11: [munzz11/starlink_stats_ros](https://github.com/munzz11/starlink_stats_ros).
Fork at [rolker/starlink_stats_ros](https://github.com/rolker/starlink_stats_ros).
Plan: port to ROS 2 and add to the workspace for network health monitoring.

#### Network status at end of April 10

Starlink ethernet stopped responding to the router (bypass mode issue recurred).
Cellular fallback was marginal — SINR ~0 dB, 33% packet loss. Both WAN links
need better monitoring to detect degradation before it becomes a problem.

#### Network monitoring plan

Comprehensive network health monitoring via ROS 2 diagnostics, covering all
communication links. Packages split by device vendor, assembled per-platform
via launch files. All publish `diagnostic_msgs/DiagnosticArray`.

**New repo**: [rolker/ros2_network_monitor](https://github.com/rolker/ros2_network_monitor)
- `teltonika_monitor` — cellular signal, mwan3 routing, VPN, interface stats via ubus JSON-RPC ([#1](https://github.com/rolker/ros2_network_monitor/issues/1))
- `mikrotik_monitor` — WiFi bridge signal, traffic, association via RouterOS API ([#2](https://github.com/rolker/ros2_network_monitor/issues/2))
- `network_tools` — generic ping latency, packet loss, link up/down ([#3](https://github.com/rolker/ros2_network_monitor/issues/3))

**Existing repo**: [rolker/starlink_stats_ros](https://github.com/rolker/starlink_stats_ros)
- `starlink_stats` — Starlink gRPC polling, port from ROS 1 ([munzz11/starlink_stats_ros#1](https://github.com/munzz11/starlink_stats_ros/issues/1))

**Integration**:
- BizzyBoat launch file + manifest update ([#47](https://github.com/rolker/unh_echoboats_project11/issues/47))
- Sensors layer manifest ([rolker/unh_marine_autonomy#120](https://github.com/rolker/unh_marine_autonomy/issues/120))

Runs on both gabby (boat-side: Starlink, cellular, boat WiFi bridge) and
salmon (operator-side: operator WiFi bridge, VPN).

#### Infrastructure completed

- Created [rolker/ros2_network_monitor](https://github.com/rolker/ros2_network_monitor) repo with `jazzy` branch
- Created `jazzy` branch on [rolker/starlink_stats_ros](https://github.com/rolker/starlink_stats_ros) fork
- Added both repos to sensors layer manifests:
  - [unh_marine_autonomy PR #121](https://github.com/rolker/unh_marine_autonomy/pull/121) — merged
  - [unh_echoboats_project11 PR #48](https://github.com/rolker/unh_echoboats_project11/pull/48) — merged
- Both repos cloned into sensors layer and pushed to gitcloud
- Added gitcloud remotes to `rqt_operator_tools` and `mobile_lab` (previously missing)
- Workspace validation passing (40/40 repos, all on correct branches)
- Merged field fix PRs: [CCOMJHC/ccomjhc_project11#29](https://github.com/CCOMJHC/ccomjhc_project11/pull/29), [seafloor_echoboat_project11#10](https://github.com/rolker/seafloor_echoboat_project11/pull/10)

#### Active development

- Starlink ROS 2 port ([munzz11/starlink_stats_ros#1](https://github.com/munzz11/starlink_stats_ros/issues/1)) — agent working, worktree active
- MikroTik monitor ([ros2_network_monitor#2](https://github.com/rolker/ros2_network_monitor/issues/2)) — agent working

## Status

Network monitoring infrastructure in place (2026-04-13). Repos created, manifests
updated, gitcloud synced. Starlink port and MikroTik monitor under active
development by parallel agents. Chart datum and TF issues from water test #2
still need investigation.
Remaining work tracked in [#43](https://github.com/rolker/unh_echoboats_project11/issues/43).
