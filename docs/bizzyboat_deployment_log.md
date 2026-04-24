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

## Next pier session — verify recent workspace / operator-station changes

Planned for the next day at the pier. Focus: `make sync` on gabby and
salmon to pull everything pushed to gitcloud the night before, then
walk through each recent change area and confirm no regressions
before any on-water work.

Hydro-payload / M3 / SBG / SVS activities have their own detailed
checklist in [`bizzyboat_project11/docs/hydro_payload_install_log.md`](../bizzyboat_project11/docs/hydro_payload_install_log.md).
This list stays boat-wide.

Strike items and add session notes inline under "### Session: YYYY-MM-DD"
below once done (follow the pattern from earlier sessions).

**Pre-deployment (bench, salmon + gabby available)**:

- [ ] On salmon: `make sync`. Expect fast-forward on every repo —
      conflicts would mean gitcloud and GitHub diverged overnight,
      which we don't expect if the push-to-gitcloud at end of the
      previous session was clean.
- [ ] On gabby (via VPN or at the boat): `make sync`. Same
      expectation. Reference: [`reference_gitcloud.md`](... memory) —
      gabby pulls from gitcloud, not GitHub.
- [ ] On salmon: `make build`. Confirm the workspace still builds
      end-to-end. `rqt_camera_grid` should be present in the build
      regardless of whether [rqt_operator_tools PR #22](https://github.com/rolker/rqt_operator_tools/pull/22)
      has merged — it's on `feature/issue-20` which salmon is tracking
      while the review cycle continues.
- [ ] On gabby: `make build`. Confirm the boat-side stack still
      builds with the post-2026-04-23 H.265 / udp_bridge changes from
      [PR #79](https://github.com/rolker/unh_echoboats_project11/pull/79).
      If cyclonedds profile drift is suspected, re-check per
      memory/`project_cyclonedds_gabby.md`.

**On-boat verification — operator station camera pipeline**:

- [ ] Start the normal boat-side core stack on gabby.
- [ ] On salmon: launch rqt, add the `Camera Grid` plugin (from
      [rqt_operator_tools PR #22](https://github.com/rolker/rqt_operator_tools/pull/22)),
      configure it with the four OAKs' base topics and `ffmpeg`
      transport. Confirm:
      - frames render in all four panes
      - per-pane rate label shows a steady value near 5 fps
      - staleness border stays Neutral while publishers are up
- [ ] Kill one OAK publisher on gabby; confirm the corresponding pane's
      border transitions to Warn at ~2 s, Error at ~5 s (the
      operator-station-consistent defaults). Restart the publisher;
      confirm the border returns to Neutral immediately (the R5 fix —
      recovery tracks frame arrival, not the 1 Hz tick).
- [ ] Replaces the `image_transport republish` workaround documented
      in the 2026-04-23 session — if rqt_camera_grid works, that
      manual bridge is no longer needed on salmon.

**On-boat verification — time sync**:

- [ ] On mercat: `ntpq.exe -pn` against `time.bizzy.p11.lan`.
      Expect the TM2000B reference as the selected peer, offset
      < 10 ms. Recovery playbook in memory/`reference_mercat_time_sync.md`.
- [ ] On gabby: `chronyc tracking` converged against the intended
      source.
- [ ] Confirm TM2000B has not locked up again since the 2026-04-23
      power-cycle (ping, ARP). Second lockup would be a real pattern,
      not a one-off — worth capturing.

**On-boat verification — network / device reach**:

- [ ] From gabby: ping all DHCP-reserved boat devices (camera IPs,
      TM2000B, mercat, RUTX11, KVM). Same list as
      [CCOMJHC/ccomjhc_project11#9](https://github.com/CCOMJHC/ccomjhc_project11/issues/9);
      all were green at the 2026-04-20 session.
- [ ] DNS via `.p11.lan` from gabby and salmon: resolve
      `time.bizzy.p11.lan`, `mercat.bizzy.p11.lan`,
      `kvm.bizzy.p11.lan`.
- [ ] Confirm the orphaned `oak_<name>` / `_info` / `_raw` udp_bridge
      entries from 2026-04-23 are still harmless (no log noise, no
      CPU cost on gabby).

**Stretch — only if above is solid**:

- [ ] Short on-water run, if conditions allow. Record a small bag
      (cameras + IMU + GPS). Usable for validating rqt_camera_grid
      under longer durations and wifi churn, and as baseline data for
      future comparisons.
- [ ] Evaluate PTP convergence on gabby (`linuxptp`) against TM2000B.
      memory/`project_time_sync_ptp.md` claims ~10–100 μs achievable
      — worth a spot check, not a blocker.

**End of session**:

- [ ] Add a "### Session: YYYY-MM-DD" entry below with what was
      accomplished, observations, and any new open items.
- [ ] Hydro-payload / M3 / SBG / SVS items: detail goes in the
      hydro install log; a short summary entry mirrored here.

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

#### Annunciator panel merged

[rqt_operator_tools PR #4](https://github.com/rolker/rqt_operator_tools/pull/4) —
dark-until-problem status indicators for operator station. Reads from
`/diagnostics` topics (what the network monitor nodes will publish to).
Three rounds of Copilot review, all findings addressed. Builds and passes
33 tests. Not yet tested with live data.

#### Rosdep fixes

- [mru_transform PR #12](https://github.com/rolker/mru_transform/pull/12) — rosdep
  key `libproj-dev` → `proj` (merged)
- [mru_transform PR #14](https://github.com/rolker/mru_transform/pull/14) — removed
  redundant `proj-data` dep (merged)
- [mobile_lab PR #3](https://github.com/rolker/mobile_lab/pull/3) — stale
  `project11` dependency → `marine_autonomy` (merged)
- [rqt_operator_tools PR #6](https://github.com/rolker/rqt_operator_tools/pull/6) —
  removed redundant `ament_python` buildtool_depend (merged)

#### Network monitoring packages — all merged

- **`starlink_stats`** ([rolker/starlink_stats_ros PR #1](https://github.com/rolker/starlink_stats_ros/pull/1)) —
  ROS 2 port complete. Moved to `starlink_stats/` subdir, uses `MessageToDict`
  instead of regex parsing, parameterized dish address and poll rate. Builds, tests pass.
- **`teltonika_monitor`** ([ros2_network_monitor PR #5](https://github.com/rolker/ros2_network_monitor/pull/5)) —
  polls RUTX11 via ubus JSON-RPC for cellular signal, mwan3 routing, WireGuard
  status, interface stats. Builds, tests pass.
- **`mikrotik_monitor`** ([ros2_network_monitor PR #4](https://github.com/rolker/ros2_network_monitor/pull/4)) —
  polls MikroTik via RouterOS API for WiFi signal, traffic, association.
  Builds, tests pass.

#### BizzyBoat launch files

[unh_echoboats_project11 PR #49](https://github.com/rolker/unh_echoboats_project11/pull/49) —
boat-side and operator-side launch files for MikroTik, Starlink, and Teltonika
monitoring with device-specific config. Pushed to gitcloud as `jazzy` for
field testing.

#### Operator station manifest fixes

- [CCOMJHC/ccomjhc_project11 PR #33](https://github.com/CCOMJHC/ccomjhc_project11/pull/33) —
  added `rqt_operator_tools` to operator UI manifest (merged)
- [CCOMJHC/ccomjhc_project11 PR #35](https://github.com/CCOMJHC/ccomjhc_project11/pull/35) —
  added `starlink_stats_ros` and `ros2_network_monitor` to operator sensors
  manifest (merged)
- Fixed `gh` repo resolution on `ccomjhc_project11` — was targeting
  `rolker/` fork instead of `CCOMJHC/` origin. Set `gh repo set-default`.

#### First test on salmon — success

All four network monitoring nodes launched on salmon and confirmed publishing
diagnostics data:
- `starlink_stats` — Starlink dish telemetry
- `teltonika_monitor` — RUTX11 cellular/mwan3/VPN stats
- `mikrotik_monitor` — WiFi bridge signal/traffic
- `network_tools` — generic network health

#### Remaining

- [ros2_network_monitor#3](https://github.com/rolker/ros2_network_monitor/issues/3) —
  `network_tools` (generic ping/latency) — in progress
- Test annunciator panel with live diagnostics data
- Deploy and test on gabby (boat-side)
- All repos pushed to gitcloud

### 2026-04-14 — Water test #3, DDS fix, tide-aware costmap

**Location**: Pier / harbor
**People**: Roland

#### Network debugging (done earlier today by other agent)

Network monitor nodes deployed to gabby. Debugging session documented in
`ccomjhc_project11/documentation/bizzyboat_network_debug_2026-04-14.md`
(private repo, on gabby only — not yet synced to origin). Field fixes
pushed to gitcloud:
- `32cc023` — chart datum node added to core launch, camera bridge rates reduced (2s→1s)
- `ed7301b` — network monitor included in core launch
- `1de8751` — fixed network monitor params (namespace issue, `chart_datum:` → `/**/chart_datum:`)

#### chart_datum_node — fixed and verified

`chart_datum_node` was running but not publishing transforms. Root cause:
params in `bizzyboat.yaml` were keyed as `chart_datum:` instead of
`/**/chart_datum:`. Without the wildcard prefix, `SetParametersFromFile`
doesn't match the namespaced node `/bizzy/chart_datum`. Frame params
defaulted to unprefixed names (`map`, `chart_datum`, `base_link`) which
don't exist in BizzyBoat's TF tree.

**Fix**: Changed `chart_datum:` to `/**/chart_datum:` in `bizzyboat.yaml`
(done live on gabby). After restart:
- `bizzy/map → bizzy/chart_datum`: Z = -28.014m (matches validated Portsmouth value)
- `bizzy/chart_datum → bizzy/map_tide`: Z = +3.1m (tide above MLLW)

#### DDS participant exhaustion — switched to Cyclone DDS

Many nodes (NTRIP, network monitors) were running as processes but invisible
to `ros2 node list`. Root cause: **DDS participant limit exhaustion**. With
~100 visible nodes (mavros alone registers 50+), FastDDS's shared memory
segments in `/dev/shm/` were exhausted (336 segments).

Switched to Cyclone DDS (`rmw_cyclonedds_cpp`). Hit the same issue —
Cyclone DDS default `MaxAutoParticipantIndex` is 99.

**Fix**: Created `/home/field/cyclonedds.xml`:
```xml
<CycloneDDS>
  <Domain>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <MaxAutoParticipantIndex>256</MaxAutoParticipantIndex>
    </Discovery>
  </Domain>
</CycloneDDS>
```

Added to `~/.bashrc`:
```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/field/cyclonedds.xml
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
```

After reboot and restart, all nodes visible including NTRIP, mikrotik_monitor,
teltonika_monitor, starlink_diagnostics, and ping_monitor.

#### NTRIP/RTK — confirmed working

With NTRIP node now properly discovered, RTCM corrections flowing at ~2.5 Hz.
GPS fix type 6 (RTK Fixed), 33 satellites, 2cm horizontal / 2.8cm vertical
accuracy. GPS `alt_ellipsoid` = -26.1m.

#### GPS altitude discrepancy

NOAA tide prediction for Portsmouth (station 8423745): low tide at 15:45,
~0.12m above MLLW. Expected ellipsoid height ≈ -28.014 + 0.12 = -27.89m.
GPS reports -26.1m (alt_ellipsoid) / -25.5m (mavros raw/fix) — ~1.8-2.4m
too high.

Contributing factors identified:
- **mavros `raw/fix` altitude** doesn't match `alt_ellipsoid` from GPS raw
  (0.6m difference, unknown mavros processing)
- **GPS antenna height**: CUAV C-RTK 2HP is 0.89m above base_link (waterline).
  mavros `raw/fix` has `frame_id: base_link` so mru_transform applies zero
  sensor offset. The URDF has `bizzy/gnss_forward` frame but mavros doesn't
  use it.
- Remaining error likely EKF altitude processing in ArduPilot

**Outstanding**: Need to either set mavros frame_id to `bizzy/gnss_forward`
or find another way to get correct ellipsoid height for the waterline.

#### S57 layer tide offset — implemented

[rolker/s57_tools#11](https://github.com/rolker/s57_tools/issues/11) /
[PR #12](https://github.com/rolker/s57_tools/pull/12)

Added `chart_datum_frame` parameter to S57 costmap layer. When set, the
layer looks up `chart_datum → global_frame` (map_tide) to get the tide
offset, then adjusts: `actual_depth = chart_depth + tide_offset`. Tiles
are regenerated when tide changes by >1cm. Backwards compatible — empty
parameter preserves existing behavior.

Pushed to gitcloud `jazzy` for field testing. Config needed in nav2_params.yaml:
```yaml
chart_layer:
  chart_datum_frame: bizzy/chart_datum
```

#### Water test #3 — first successful mission planning

After applying S57 tide offset and fixing DDS discovery:
- **Costmap shows navigable water** where the boat is located (previously
  "start occupied" due to MLLW depths without tide correction)
- **Trackline planning succeeded** — first time planner produced a valid path
- **Trackline execution partially worked** — controller_server crashed a few
  times (respawned), hover behavior applies rotation but no throttle

#### controller_server crash

`controller_server` segfaults (exit code -11) during `SeaSurfaceLayer::matchSize()`.
Crashes after getting `bizzy/map_tide` transform. Not related to S57 changes —
happens in the sea surface perception layer. Removing `sea_surface_layer` from
the local costmap plugins resolved the crash. Pre-existing issue or Cyclone DDS
related.

#### Hover behavior — no throttle

Hover (station keeping) applies yaw commands but zero throttle on `cmd_vel`.
Boat rotates in place but doesn't hold position. Same symptom as water test #1.
Needs investigation — may be PID tuning, `cmd_vel` mapping, or a missing
velocity source.

#### Bag log analysis — water test #3 (2026-04-14)

Post-hoc analysis of rosbag data from gabby (`~/data/logs`) covering the
April 14 session. Bags span 08:43–14:28 UTC across 8 recording sessions
(10 total autostart events, including rapid restarts during troubleshooting
around 16:43–16:52 UTC).

**Timeline reconstructed from GPS altitude and position:**

| Time (UTC) | Phase | Alt (m) | Notes |
|------------|-------|---------|-------|
| 08:43–11:28 | Stationary on land | -21.0 | At storage location (43.07204, -70.71165), speed 0 |
| ~11:30 | Rolled to crane | -21.1 | Speed jumps to ~0.9 m/s, position shifts toward crane |
| ~11:34 | Crane lowers to water | -21 → -23.6 | ~2.5 m altitude drop as boat enters water |
| 11:36–14:07 | On water — operations | -24.6 → -26.1 | Gradual altitude decrease tracks rising tide |
| 13:51 | GUIDED mode engaged | -25.7 | First autonomous mode of session |
| 13:54:22 | controller_server crash | -25.9 | `SeaSurfaceLayer::matchSize()` — nav lifecycle shutdown |
| 13:59, 14:07, 14:11 | MANUAL mode switches | — | Operator takes manual control |
| 14:07:44–14:09 | Fast transit | -26.1 | ~1.9 m/s to farthest point from dock |
| 14:21:45–14:22:45 | Crane lifts from water | -26.2 → -20.8 | ~5 m altitude rise |
| 14:24:45 | Moved back to storage | -21.1 | Speed ~1.25 m/s, returns to original position |
| 14:25:45+ | Stationary on land | -21.1 | Back at storage, speed 0 |

**Key findings from diagnostics:**

1. **GPS health flicker (13:48)** — ArduPilot reported GPS sensor health
   as "Fail" intermittently while the boat was stationary on the water near
   the dock. NavSatFix still had STATUS_FIX with valid coordinates
   throughout. Likely multipath or partial sky obstruction near dock
   structures. The GPS flicker at 13:48 preceded the controller_server
   crash at 13:54 — unclear if related.

2. **Direct WiFi loss (14:09–14:24)** — `router_op_direct` and
   `salmon_direct` pings showed 100% packet loss (40 error events). This
   correlates exactly with the boat being at its farthest point from the
   dock (~43.07200, -70.71052). VPN links over cellular stayed up. WiFi
   link recovered when the boat returned closer to the dock.

3. **controller_server crash (13:54:22)** — Lifecycle manager reported
   heartbeat loss after 4 seconds. Failed to cancel `follow_path` action
   and couldn't restart `controller_server` via `change_state` service.
   Consistent with the `SeaSurfaceLayer::matchSize()` segfault noted above.

4. **Sensor bitmask changes correlate with flight mode** — When the FCU
   switched to MANUAL mode, 4 control-loop sensors (angular rate control,
   attitude stabilization, yaw position, xy position control) correctly
   dropped from the enabled set. This is normal ArduPilot behavior, not a
   hardware fault.

5. **Odom rate ~9% below nominal** — 25,340 messages vs ~27,850 expected
   at 10 Hz in the last bag. No single large gap — steady small drops
   throughout. Worth monitoring.

6. **Teltonika WAN interface intermittent** — `router.bizzy` interface
   `wan1` showed WARN 105 times (out of 556 reports), and `mwan3/wan1`
   had 5 ERROR and 550 WARN. MikroTik ethernet ports 2–5 all reported
   "Not running" consistently.

7. **Arming checks disabled** — FCU logged "Warning: Arming Checks
   Disabled". Presumably intentional for testing.

**Altitude vs. tide:**

GPS ellipsoid altitude dropped from -24.6 m (11:36) to -26.1 m (14:07)
over ~2.5 hours on the water — a ~1.5 m decrease. This is consistent with
a rising tide lifting the boat's waterline higher relative to the geoid
while the ellipsoid height decreases (the boat's physical altitude above
ellipsoid goes down as the water rises). Combined with the earlier note
that GPS altitude was already ~1.8–2.4 m too high vs NOAA predictions,
the altitude trend is plausible but the absolute offset remains an open
issue (see GPS altitude discrepancy above).

#### Outstanding issues

- [ ] Merge gitcloud field fixes to origin (3 commits: chart datum, network monitor, params fix)
- [ ] Fix mavros GPS frame_id or antenna offset for correct sea surface height
- [ ] Investigate `SeaSurfaceLayer::matchSize()` segfault in controller_server
- [ ] Investigate hover behavior — no throttle, only yaw
- [ ] Sync `bizzyboat_network_debug_2026-04-14.md` from gabby to origin
- [ ] Reduce UDP bridge camera bandwidth defaults (repeat from water test #2)
- [ ] Starlink bypass mode reliability
- [ ] Monitor odom rate — 9% message loss in water test #3 bags
- [ ] Investigate WiFi range limitations — direct link lost at ~300 m from dock

### Session: 2026-04-15 — DNS failover fix

#### Symptom

`sudo apt update` on gabby failed — all repos returning "Could not resolve"
errors. Raw IP connectivity fine (`ping 8.8.8.8` works, 21ms), router
reachable (0.5ms). Problem is purely DNS. Boat is in mobile lab, router
using WiFi to mobile lab Starlink for internet (wan1).

#### Diagnosis

This is the **third recurrence** of DNS failure on the boat router (RUTX11),
each with a slightly different trigger but the same structural cause:

| Date | Trigger | Quick fix applied |
|------|---------|-------------------|
| Apr 3 | Starlink ethernet down indoors | Removed hardcoded DNS servers, rely on auto resolv |
| Apr 7 | Starlink DNS proxy returning NXDOMAIN, carrier DNS unreachable cross-WAN | Re-added hardcoded 8.8.8.8/1.1.1.1, `peerdns='0'` on wan1/wan6/mob1s1a1, `allservers=1`, `nonegcache=1` |
| **Apr 15** | Starlink ethernet down indoors (same as Apr 3) | — see proper fix below |

**Root cause analysis:**

The April 7 fix set `peerdns='0'` on wan1, wan6, and mob1s1a1 — but
**missed `wan`** (Starlink ethernet). With `wan` still injecting its DNS
server (206.214.239.195) into `/tmp/resolv.conf.d/resolv.conf.auto`,
dnsmasq was querying it alongside 8.8.8.8 and 1.1.1.1.

With `allservers=1`, dnsmasq races queries to ALL configured servers in
parallel and uses the **first response**. The dead Starlink router at
206.214.239.195 is still reachable on L2 (same subnet) but has no
internet, so it returns **NXDOMAIN fast**. The working queries to
8.8.8.8/1.1.1.1 via wan1 are slower. The fast wrong answer wins.

Additionally, 206.214.239.0/24 is in mwan3's `mwan3_connected` ipset,
so traffic to that server bypasses mwan3 policy routing entirely —
it follows the main routing table straight to the dead eth1 interface.

This is a **well-known OpenWrt/mwan3 limitation**
([openwrt/packages#5760](https://github.com/openwrt/packages/issues/5760),
[openwrt/packages#5055](https://github.com/openwrt/packages/issues/5055)):
locally-originated traffic (including dnsmasq queries) does not fully
participate in mwan3 policy routing, and dnsmasq has no awareness of
interface health.

#### Fix applied (proper)

```bash
# 1. Disable peerdns on wan (the one that was missed)
uci set network.wan.peerdns='0'
uci commit network

# 2. Remove allservers — use sequential queries, not racing
uci delete dhcp.cfg01411c.allservers
uci commit dhcp

# 3. Reload
/etc/init.d/network reload
/etc/init.d/dnsmasq restart
```

**Why this is durable (not another quick fix):**

- All four WAN interfaces now have `peerdns='0'` — no interface can
  inject its DNS servers into dnsmasq, regardless of state
- Only hardcoded 8.8.8.8 and 1.1.1.1 are used — anycast addresses
  reachable via any working WAN path
- Without `allservers`, dnsmasq tries servers **sequentially** — a dead
  path times out and falls through to the next server, rather than a
  fast NXDOMAIN winning a race
- `nonegcache='1'` (already set from Apr 7) prevents caching of negative
  responses as a safety net
- 8.8.8.8/1.1.1.1 are NOT in `mwan3_connected` ipset, so they go through
  mwan3 policy routing → wan1 (active path)

**Verified**: `nslookup google.com` on router, `sudo apt update` on gabby —
both working. All repos fetched successfully.

#### Current dnsmasq/DNS config state

```
dhcp.@dnsmasq[0].server='8.8.8.8' '1.1.1.1'
dhcp.@dnsmasq[0].nonegcache='1'
network.wan.peerdns='0'
network.wan1.peerdns='0'
network.wan6.peerdns='0'
network.mob1s1a1.peerdns='0'
```

#### Future improvements to consider

- **DNS-over-HTTPS (`https-dns-proxy`)** — RUTX11 supports this; turns DNS
  into regular HTTPS that mwan3 policy-routes properly. Most elegant fix.
- **DNS-based mwan3 health checks** — use domain resolution as
  `track_method` instead of ICMP ping, so an interface with IP connectivity
  but broken DNS is marked down.
- **`/etc/mwan3.user` hotplug script** — dynamically update dnsmasq servers
  on interface state changes. Overkill with hardcoded public DNS but useful
  if interface-specific servers are ever needed.

#### WiFi bridge routing — review of masquerade decision

The April 14 debug session (see `ccomjhc_project11` repo,
`documentation/bizzyboat_network_debug_2026-04-14.md`) disabled masquerade
on the operator router's LAN zone and added static return routes on the
OmniTIK and SXTsq bridge devices. Post-hoc review of the tradeoffs:

| Approach | Bridge device config | Real source IPs | Survives factory reset |
|----------|---------------------|-----------------|----------------------|
| Masquerade on both routers | None | No | Yes |
| Static routes per subnet (current) | 2 routes × 2 devices | Yes | No |
| Default gateway only | 1 gateway × 2 devices | Yes | No |
| DHCP on bridge subnet | Initial DHCP client setup | Yes | Mostly |

**Decision**: keep current state (masquerade off, static routes). Plan to
simplify to **default gateway** approach when next hands-on with bridge
devices — set OmniTIK default gw to 172.16.20.1 (boat router), SXTsq
default gw to 172.16.20.2 (operator router), and remove the per-subnet
static routes. This reduces config to one item per device and handles
future new subnets automatically.

Masquerade was not re-enabled because removing it had no known unintended
side effects, and preserving real source IPs aids diagnostics. If bridge
device replacement or factory reset becomes frequent, reconsider masquerade
as the zero-config option.

#### Network diagnostics improvements (2026-04-15)

Reviewed the full diagnostic collection pipeline and implemented
improvements across multiple repos. Tracked in
[ros2_network_monitor#7](https://github.com/rolker/ros2_network_monitor/issues/7).

**Signal quality thresholds** (ros2_network_monitor
[PR #8](https://github.com/rolker/ros2_network_monitor/pull/8), merged):
- teltonika_monitor: cellular diagnostic level based on RSRP (OK > -90,
  WARN -90 to -110, ERROR < -110 dBm), SINR downgrades by one bar if < 0.
  Message shows `LTE -85dBm ▁▂▃▅·`.
- mikrotik_monitor: wireless diagnostic level based on SNR (OK > 20,
  WARN 10-20, ERROR < 10 dB). Message shows `Associated SNR 22dB ▁▂▃▅·`.

**Hardware ID for instance disambiguation** (merged):
- starlink_diagnostics: added `hardware_id` parameter
  ([starlink_stats_ros PR #3](https://github.com/rolker/starlink_stats_ros/pull/3)).
  Boat: `starlink.bizzy`, operator: `starlink.op`.
- ping_monitor: added `hardware_id` parameter
  ([ros2_network_monitor PR #10](https://github.com/rolker/ros2_network_monitor/pull/10)).
  Boat: `ping.bizzy`, operator: `ping.op`.
- All four monitor node types (teltonika, mikrotik, starlink, ping) now have
  `hardware_id` for distinguishing boat vs operator instances.

**DNS ping targets** ([unh_echoboats_project11
PR #53](https://github.com/rolker/unh_echoboats_project11/pull/53), merged):
- Added 8.8.8.8 and 1.1.1.1 to boat, operator, and merged ping configs.
  Would have caught the recurring mwan3/dnsmasq DNS routing failure.

**Annunciator config** (PR #53):
- Created `bizzyboat_annunciator.yaml` with 9 indicators:
  - Link quality: WiFi Bridge, Cell Signal, Starlink
  - Critical systems: Battery, GPS, FCU, Comms, Nav Stack, Mission Manager
- Loaded by the rqt annunciator panel at runtime.

**Diagnostic aggregator config** (PR #53):
- Added boat-side network device groups (MikroTik, Teltonika, Starlink, Ping)
  using hardware_id prefixes to separate from operator-side devices.
- Added operator Ping group.
- rqt_robot_monitor and rqt_runtime_monitor can now show the full grouped
  tree for drill-down.

**Gitcloud field changes PR'd and merged**:
- [rqt_operator_tools PR #7](https://github.com/rolker/rqt_operator_tools/pull/7) —
  gitignore + rqt deps
- [ccomjhc_project11 PR #36](https://github.com/CCOMJHC/ccomjhc_project11/pull/36) —
  network debug log from April 14
- [unh_echoboats_project11 PR #51](https://github.com/rolker/unh_echoboats_project11/pull/51) —
  field fixes (network monitor YAML merge, diagnostic aggregator, chart datum)

**Other agent work merged same day**:
- [s57_tools PR #12](https://github.com/rolker/s57_tools/pull/12) — S57
  costmap layer tide offset correction via chart datum transform. Adds
  `chart_datum_frame` parameter; when set, layer looks up tide offset and
  adjusts chart depths so costmap reflects actual depth below current water
  surface. Tiles regenerated when tide changes >1cm. Field-tested April 14.
- [mru_transform PR #16](https://github.com/rolker/mru_transform/pull/16) —
  MHHW datum frame + out-of-range tide rejection. chart_datum_node now
  publishes `map → chart_datum_mhhw` TF alongside existing MLLW frame.
  sea_surface_estimator suppresses `map_tide` when estimated water level
  exceeds MHHW + margin, preventing bogus tide values from propagating.
- [unh_marine_navigation PR #13](https://github.com/rolker/unh_marine_navigation/pull/13) —
  fix BehaviorTree Script nodes to use single quotes for string literals.
  Was causing BT evaluation failures during mission execution.

#### Annunciator panel testing (2026-04-15)

First live test of annunciator panel on salmon with boat (gabby) running
updated nodes.

**Standalone entry point segfaults** — `ros2 run rqt_operator_tools annunciator`
crashes immediately. Qt initialization issue. Workaround:
`rqt --standalone rqt_operator_tools`, then load config via File dialog.
Needs investigation — likely a QApplication initialization order problem
in `annunciator_standalone.py`.

**Data partially showing** — indicators mostly grey (STALE) but some data
flickers in briefly. Likely causes:
- Stale timeouts may be too short for 10-second ping poll interval
- Diagnostic name matching may not be hitting all expected statuses
- The boat-side nodes were just started and may still be initializing
- The new `hardware_id` params need to be in the deployed configs on gabby

**Resize is very flaky** — the adaptive layout (horizontal/vertical/grid
based on aspect ratio) doesn't work well. The `_rebuild_layout()` method
deletes and recreates the layout on every resize event, which causes visual
glitches and possibly crashes. Needs rework — either debounce the resize,
or use a fixed layout that doesn't change on resize.

#### Outstanding issues (updated)

- [ ] Merge gitcloud field fixes to origin (3 commits: chart datum, network monitor, params fix)
- [ ] Fix mavros GPS frame_id or antenna offset for correct sea surface height
- [ ] Investigate `SeaSurfaceLayer::matchSize()` segfault in controller_server
- [ ] Investigate hover behavior — no throttle, only yaw
- [ ] Reduce UDP bridge camera bandwidth defaults (repeat from water test #2)
- [ ] Monitor odom rate — 9% message loss in water test #3 bags
- [ ] Investigate WiFi range limitations — direct link lost at ~300 m from dock
- [ ] Fix annunciator standalone segfault (Qt init issue)
- [ ] Fix annunciator resize flakiness
- [ ] Tune annunciator stale timeouts and diagnostic name matching
- [ ] Deploy updated configs (hardware_id, DNS ping targets) to gabby
- [ ] Consider DNS-over-HTTPS on RUTX11 for long-term DNS resilience
- [ ] WiFi bridge: switch from static routes to default gateway approach

### Session: 2026-04-16 — Annunciator deep dive

Pre-launch debugging of annunciator panel on salmon. Annunciator was
running but many indicators showed as STALE. Followed the symptom into
the monitor nodes and corrected several hypotheses from yesterday.

#### Bus is healthy — corrects yesterday's notes

Probed `/diagnostics` directly from salmon (Python subscriber, not
`ros2 topic echo` which gives lossy snapshots):

| Indicator | Age | Level | Message |
|---|---|---|---|
| `MikroTik: wifi.bizzy: wireless/wlan1/...` | 1.9s | OK | Associated SNR 41dB ▁▂▃▅█ |
| `Teltonika: router.bizzy: cellular` | 0.0s | OK | LTE -83dBm ▁▂▃▅· |
| `Starlink: starlink.bizzy: dish_get_status` | 0.9s | OK | (empty) |
| `mavros: Battery` | 0.5s | OK | Normal |
| `mavros: GPS` | 0.5s | OK | 3D fix |
| `mavros: Heartbeat` | 0.5s | OK | Normal |
| `mavros: System` | 0.5s | OK | Normal |
| `mavros: MAVROS UAS` | 0.5s | OK | connected |

Topic publishing at ~6 Hz overall. **Yesterday's hypothesis that mavros
plugins (Battery/GPS/Heartbeat) weren't loaded on gabby was wrong** —
they're all publishing fine. The earlier `topic echo` capture window
just missed them.

#### DDS discovery is partial on salmon

`ros2 node list` (cached daemon) shows `/ping_monitor`, `/mikrotik_monitor`,
`/teltonika_monitor`. But `ros2 node list --no-daemon` (fresh discovery)
shows only `/rqt_gui_cpp_node_NNNNN` — the local rqt instance.

Means: **no operator-side monitor nodes are actually running on salmon**.
The `Teltonika: router.op:`, `MikroTik: bizzy.wifi.op:`, and
`Starlink: starlink.op:` diagnostics we see are all being published by
gabby, which is configured to monitor both boat- and operator-side
equipment over the WiFi bridge link. Daemon-cached node list entries are
stale references to gabby's nodes.

Net effect: data IS reaching salmon, just discovery is unreliable. Topic
data passes through fine.

#### Why annunciator items still go STALE — three real root causes

1. **`rqt_runtime_monitor` has a hardcoded 5-second stale window**
   (`runtime_monitor_widget.py:329`). Items not republished within 5s
   flicker to STALE. `ping_monitor` polls every 10s by default —
   guaranteed to flicker.

2. **`diagnostic_aggregator/GenericAnalyzer` default timeout is ~5s**
   too. Same root cause shows up in `rqt_robot_monitor`: ping group
   shows `?` icon and ERROR badge between polls. Confirmed: ping items
   are flagged STALE in robot_monitor aggregator view.

3. **The boat-side `mikrotik_monitor` and `teltonika_monitor` poll every
   5s** — sit right on the boundary; any slow poll pushes items past the
   threshold momentarily.

The annunciator's own `match_mode` defaults to `substring`
(`config_model.py:168, 184`) — confirmed not the cause of stale-looking
indicators. Substring matching against config strings like
`MikroTik: wifi.bizzy: wireless/` correctly hits the actual published
name `MikroTik: wifi.bizzy: wireless/wlan1/<MAC>`.

#### Annunciator bug: Starlink indicator shows dish serial

Starlink indicator on the panel displayed something looking like a
serial number rather than a useful summary. Traced to
`annunciator_widget.py:229-235`:

```python
if status.values:
    try:
        val = float(status.values[0].value)
        value_text = config.format.format(val)
    except (ValueError, IndexError, KeyError):
        value_text = status.message or status.values[0].value  # <-- bug
```

`starlink_diagnostics_node.py:135-156` publishes with
`status.message = ''` (empty) and a `status.values[]` list of flattened
dish stats. Starting with `device_info.id` (the dish UT serial). The
annunciator's fallback then displays that serial.

Fix options (deferred to a separate PR on `rqt_operator_tools`):
- (a) Reverse fallback priority — use `level.name` when message is empty
  rather than `values[0].value`
- (b) Add a `value_key` config field so indicators can pick a specific
  KeyValue
- (c) Have `starlink_diagnostics_node` populate `status.message` with a
  human-readable summary

#### Decision: republish cached diagnostics at fixed rate

Rather than tweaking timeouts in three places (annunciator config,
aggregator config, runtime_monitor — last is uneditable), the cleanest
fix is in the monitor nodes themselves:

```
poll_timer    (every poll_interval): query device → update self._cached_msg
publish_timer (every publish_interval=1.0s): refresh header.stamp → publish cache
```

Each `DiagnosticStatus` will also carry a new `KeyValue`:

```
key:   last_query_time
value: 2026-04-16T13:45:23.456   (ISO 8601, set ONLY on actual poll)
```

The `last_query_time` value survives republishes unchanged so observers
can compute true data age (vs. the header timestamp which gets refreshed
each republish). Diagnostic-honest: header reflects "this message
sent now", `last_query_time` reflects "this is when the device was
actually queried".

Repos to touch:
- `rolker/ros2_network_monitor` — `ping_monitor`, `mikrotik_monitor`,
  `teltonika_monitor` (one issue + PR)
- `rolker/starlink_stats_ros` — `starlink_diagnostics_node` (separate
  smaller issue + PR)

Side benefits: also fixes the aggregator `?` icons (no need to bump
analyzer timeouts) and removes the need for any annunciator
`stale_timeout` tuning.

#### CrabbingPathFollower PID — YAML key names never took effect

Live param check on `/bizzy/controller_server` revealed the PID
parameters declared by the running node are:

```
FollowPath.pid.p
FollowPath.pid.i
FollowPath.pid.d
FollowPath.pid.i_clamp_max / i_clamp_min
FollowPath.pid.u_clamp_max / u_clamp_min
FollowPath.pid.activate_state_publisher
```

But the YAML in
`seafloor_echoboat_project11/echoboat_project11/config/nav2_params.yaml:62-73`
uses the OLD `control_toolbox::Pid` API names: `kp`, `ki`, `kd`,
`upper_limit`, `lower_limit`, `windup_limit`, `publish_debug`. These are
silently ignored by `control_toolbox::PidROS`.

**Implication**: the YAML's tuning values (`kp=20.0`, `ki=0.5`, `kd=0.6`,
`windup_limit=30.0`) have **never been in effect**. The controller has
been running with the C++ defaults from `crabbing_path_follower.cpp:29`:
`p=1.0, i=0.0, d=0.0, u_clamp=±90, i_clamp=±75`. Effectively a P-only
controller with kp=1 — explains the historical "controller feels sluggish,
must be wind/current" character of trackline runs.

**Field test of corrected gains** — set live via correct names:

```bash
ros2 param set /bizzy/controller_server FollowPath.pid.p 20.0
ros2 param set /bizzy/controller_server FollowPath.pid.i 0.5
ros2 param set /bizzy/controller_server FollowPath.pid.d 0.6
```

Tried following a line. **Boat took off in completely wrong direction.**
The "tuning values" in the YAML were never validated because they were
never applied — they're not actually correct gains for the platform.
Real tuning needs to be redone from scratch with correct param names.

**Recovery suggestion (untested)**: back off to something much lower
(e.g. `p=2.0, i=0.0, d=0.0`) and increment from there. Going 1 → 20 in
one step was a 20× jump.

**Update — actual validated values found in ben simulation config**
(`ben_project11/config/nav2_params.yaml:64-75`):

```yaml
FollowPath:
  pid:
    p: -6.0          # NEGATIVE — sign convention!
    i: -0.5          # NEGATIVE
    d: -0.6          # NEGATIVE
    i_clamp_max: 50.0
    i_clamp_min: -50.0
    u_clamp_max: 90.0
    u_clamp_min: -90.0
```

The ben config uses the correct new PidROS names AND negative signs.
Echoboat's YAML was simply left behind when the controller's underlying
API changed — and someone tried to translate the old gains to the new
keys without realizing the sign convention. The "boat ran in completely
wrong direction" symptom = positive gain driving cross-track-error in
the wrong direction.

**Sign-flip mystery resolved via git history**:

| Date | Repo | Commit | What changed |
|---|---|---|---|
| 2025-05-15 | echoboat | `10fcf8c` | switched FollowPath to old `project11_navigation::CrabbingPathFollower`, kp=6 (positive) |
| 2025-06-18 → 2025-06-20 | echoboat | `148359a`/`f3aef48` | tuned to kp=20, ki=0.5, kd=0.6, windup=30 (positive, validated on IzzyBoat) |
| 2025-10-31 | unh_marine_navigation | `c501dd2` | created new `marine_nav_crabbing_path_follower` using `control_toolbox::PidROS` (new API names: `p`/`i`/`d` instead of `kp`/`ki`/`kd`) |
| 2025-11-04 | unh_marine_navigation | `1c5db5a` | removed legacy `project11_navigation` code |
| 2025-11-04 → 2026-04-16 | echoboat | (none) | YAML plugin name updated to `marine_nav_*` but PID keys never updated |

So:

- **June 2025 → October 2025** (4 months): IzzyBoat ran with `kp=20.0`
  POSITIVE on the OLD `project11_navigation` controller. Validated.
- **November 2025 → now** (~5 months): both IzzyBoat and BizzyBoat have
  been running with PidROS *defaults* (`p=1.0, i=0, d=0`) because the
  YAML keys were silently ignored. Explains the "controller feels
  sluggish, blame wind/current" character of trackline runs in this
  period.

**The new `marine_nav_*` controller has flipped the cross-track-error
sign convention** vs the old `project11_navigation` one — confirmed by
the BizzyBoat field test where `p=20.0` (positive, what worked on the
old code) drove the boat off in the wrong direction. The ben/vrx sim
configs use negative signs and are the only places that match the new
API.

**Recommended values for echoboat YAML** (IzzyBoat-validated magnitude,
sign flipped to match new controller):

```yaml
pid:
  p: -20.0
  i: -0.5
  d: -0.6
  i_clamp_max: 30.0
  i_clamp_min: -30.0
  u_clamp_max: 90.0
  u_clamp_min: -90.0
  activate_state_publisher: true
```

Ben sim alternative (gentler, sim-only validation):
`p: -6.0, i: -0.5, d: -0.6, i_clamp: ±50`.

**Field result with `p=-20, i=-0.5, d=-0.6, i_clamp=±30`**: boat
**solidly following survey lines**. PID values confirmed working. After
~5 months of sluggish-controller behavior caused by the silently-ignored
YAML, real tracking is restored.

#### Plan-time TF extrapolation when starting next survey line

After completing a survey line, `compute_path_through_poses` repeatedly
fails with:

```
Extrapolation Error looking up target frame:
Lookup would require extrapolation into the past.
Requested time 1776355217.065278 but the earliest data is at time
1776355270.367 ... 271.268 ... 273.267 (advancing each retry)
when looking up transform from frame [bizzy/map] to frame [bizzy/map_tide]
```

Symptom: requested timestamp stays *fixed* across retries while the
earliest-available time keeps advancing. The fixed timestamp is from
~70 s before the planner is invoked — i.e., when the original survey
plan was issued, not when the next-line goal is being processed.

User hypothesis (confirmed by behavior): the survey-pattern executor
holds the original mission timestamps on the per-line goals, then when
the next line is started, the planner gets a goal with a stale
header.stamp. The `bizzy/map → bizzy/map_tide` TF buffer doesn't reach
back that far.

Behavior tree falls back to `hover` after the planner aborts —
`[behavior_server] Running hover` appears in the log. So failure mode
is non-catastrophic but blocks autonomous progress.

**Fix candidates** (to investigate):
- Refresh `header.stamp = now()` on per-line goals at the moment the
  task is dispatched (in survey-pattern executor or BT task navigator)
- Use `tf2::TimePointZero` in whatever code path resolves the goal
  transform (use latest available rather than exact-time lookup)
- Increase `sea_surface_estimator` TF publish rate / buffer length so
  older requests can still resolve

Investigating the survey-pattern executor / BT task navigator code path
next.

**Outstanding follow-ups**:
- Rewrite YAML to use correct PidROS names everywhere CrabbingPathFollower
  is loaded (echoboat, ben_project11, others)
- Re-tune gains from a known-low baseline
- Consider adding a comment in `crabbing_path_follower.cpp` near
  `initialize_from_args(...)` that the API uses different param names
  than older Pid

#### Hover deadlock — controller assumes skid-steer, BizzyBoat has vectored thrusters

In-water hover test: boat commands sustained `angular.z = -0.5`,
`linear.x = -0.0` (negative zero) and sits there. Outstanding issue
"Hover engages but drifts" / "Hover behavior — no throttle, only yaw"
finally diagnosed.

Root cause is in `marine_nav_behaviors/src/hover.cpp:130-135`:

```cpp
if (steering_proportion > 0.25)            // > 45° heading error
  current_target_speed = 0.0;              // KILL THROTTLE
current_target_speed *= (1.0 - steering_proportion*4.0);
```

For the observed `angular.z = -0.5` at `maximum_rotation_speed = 0.75`,
working backwards: `steering_angle ≈ -120°`, `steering_proportion ≈ 0.667`.
Above 0.25 the throttle is forced to zero, then multiplied by `-1.667`
giving the negative-zero in the cmd_vel output.

The "rotate-first, translate-second" logic was tuned on **IzzyBoat
(skid-steer)** which can pivot in place from differential thrust alone.
**BizzyBoat has vectored thrusters** — it needs forward velocity for
the thrust vector to develop turning authority. So:

1. Heading error > 45° → throttle killed by L132
2. No throttle → vectored thrust has no forward component to redirect
   → no turning authority
3. Boat sits → heading error stays large → goto 1 (deadlock)

Wind/current makes this worse — they keep nudging the heading while the
controller has zero authority to correct.

**Fix path**: patch `hover.cpp` to maintain minimum forward speed during
heading correction so vectored thrust has authority to redirect. User
will patch directly in the field; backport to the repo after.

**Field-applied patch v1 (2026-04-16, initial — "seems to be working OK")**:

```cpp
if (steering_proportion > 0.25)
{
    current_target_speed = 0.2;   // was 0.0
}
```

Single-character intent change — give the boat 0.2 m/s forward thrust
during large heading corrections instead of zero. Worked initially.

**Drift-away regression observed shortly after** — boat drifted beyond
`maximum_radius` (10 m) and didn't return. Diagnosed as:

1. Range > max_radius → original L107 sets `current_target_speed = 1.0`
2. v1 patch L132 *clobbers* this to 0.2
3. L135 `*= (1 - 4*0.667) = -1.667` → result is `0.2 * -1.667 = -0.333`
   (reverse thrust)
4. L139 clamps with `minimum_speed_ = 0` → effectively 0 thrust
5. Boat can't return to station; drifts further

**Field-applied patch v2** — two changes:

```cpp
if (steering_proportion > 0.25)
{
    current_target_speed = std::max(current_target_speed, 0.2);  // FLOOR, not clobber
}
current_target_speed *= std::max(0.0, 1.0 - steering_proportion*4.0);  // clamp L135 ≥ 0
```

Preserves the original "drive home at 1.0 m/s" behavior when far from
station, while still ensuring 0.2 m/s minimum thrust at station for
rudder/vectored-thrust authority during heading correction. L135 no
longer goes negative.

**Patch v2 still deadlocks** — order-of-operations bug. For
`steering_proportion >= 0.25`:

```
floor: current_target_speed = max(x, 0.2)         → 0.2 (or higher)
taper: current_target_speed *= max(0, 1 - 4*0.25) → 0.2 * 0 = 0
final clamp: max(0, minimum_speed_)               → max(0, 0) = 0  DEADLOCK
```

The 0.2 floor is applied BEFORE the multiplier, and the multiplier is
exactly zero at the 0.25 threshold and beyond. Floor gets wiped.

**Field-applied patch v3** — flip the order, floor AFTER the taper:

```cpp
current_target_speed *= std::max(0.0, 1.0 - steering_proportion*4.0);
if (steering_proportion > 0.1)   // ↓ threshold from 0.25 — vectored
{                                 //   thrust needs flow at smaller errors too
  current_target_speed = std::max(current_target_speed, 0.2);
}
```

Floor now wins because it runs after the multiplier. Threshold lowered
to 0.1 (~18°) since vectored thrust needs forward flow even for moderate
heading corrections.

Sanity check — covers all input regions:

| Region | steering | Original | After taper | After floor |
|---|---|---|---|---|
| Far (>10m), aligned | 0.05 | 1.0 | 0.8 | 0.8 (no floor at 0.05) |
| Far, 60° off | 0.333 | 1.0 | 0 | **0.2** ✓ |
| Mid (5m), 120° off | 0.667 | 0.333 | 0 | **0.2** ✓ |
| At target, aligned | 0.05 | 0 | 0 | 0 (calm) |
| At target, 30° off | 0.167 | 0 | 0 | **0.2** ✓ |
| Inside min/2, aligned | 0 | -0.05 | -0.05 | -0.05 (small reverse OK) |
| Inside min/2, 60° off | 0.333 | -0.05 | 0 | **0.2** (overrides reverse for rudder) |

**Field result with v3 (commit `ca0dc6f` on `unh_marine_navigation#14`,
pushed to `gitcloud/jazzy`)**: hover working — boat slowly spirals
toward the center. Acceptable behavior for vectored thrust: 0.2 m/s
minimum forward thrust during heading correction means the boat can't
sit perfectly still while turning, so it traces a tightening loop as
range decreases. No deadlock.

**Bag analysis (last 10 min of session, `2026-04-16T12.52.58.143303849`)**
shows the "spiral" is actually a **stable orbital limit cycle**, not
convergence:

| Metric | Value |
|---|---|
| Ground speed | mean 0.20 m/s (range 0.13–0.28) — locked at v3 floor |
| Range from centroid | mean 3.23 m, settled at 2.5–3 m for last 5 min |
| Yaw rate | mean 3.8°/s, max 9°/s |
| Orbit period | ~60–80 s |

Kinematic explanation: at v_min = 0.2 m/s and sustained yaw rate
~6°/s (0.105 rad/s), turning radius = v/ω ≈ 1.9 m — matches observed
orbit radius. The 0.2 m/s floor (necessary for rudder authority far
from station) becomes a trap when close: boat can't stop, endlessly
orbits at the kinematic radius.

**Applied v4** (commit `cfd8560` on `unh_marine_navigation#14`, pushed
to `gitcloud/jazzy`) — range-aware floor that ramps with the existing
target_speed gradient:

```cpp
if (steering_proportion > 0.1 && current_range >= minimum_radius_)
{
  double range_factor = std::clamp(
      (current_range - minimum_radius_) /
      (maximum_radius_ - minimum_radius_),
      0.0, 1.0);
  double turn_min_speed = (0.2 + 0.3 * range_factor) * maximum_speed_;
  current_target_speed = std::max(current_target_speed, turn_min_speed);
}
```

| range | turn_min (max_speed=1.0) |
|---|---|
| ≥ max_radius (10 m) | 0.5 m/s (more authority for return) |
| 6 m (mid) | 0.34 m/s |
| 3 m (just outside ring) | 0.22 m/s |
| 2.5 m (at ring) | 0.2 m/s (matches v3 at boundary) |
| < 2.5 m (inside ring) | **0** (cliff — boat can settle) |

Behavior just outside the ring is identical to v3 (continuity at the
cliff). Far away, more aggressive return (0.5 vs 0.2). Inside the
ring, original L116-128 logic takes over so the boat stops orbiting.

Bag analysis script saved at `/tmp/hover_analyze.py` for re-running
on the next session.

**Bag analysis #2 — wind perturbation events (last 25 min before v4
deploy, still on v3)**:

Phases observed in `2026-04-16T12.52.58.143303849` chunks _45–_51:

| Phase | Range | Spd max | Notes |
|---|---|---|---|
| 0–6 min | 1.7–4.9 m | 0.28 | Stable orbital limit cycle |
| 6–9 min | 1.7–6.0 m | 0.39 | First wind nudges |
| 9–13 min | up to 7.2 m | 0.30 | Larger excursions |
| **15–17 min** | **6 → 12 → 18 → 20.4 m** | 0.66 | **Big wind event, blown 20 m off** |
| 17–18 min | 20 → 5 m | 0.66 | Slow return |
| 19–22 min | 7 → 13 → 7 m | 0.54 | Second perturbation |
| 22–25 min | 3–6 m | 0.34 | Settling back to orbit |

**Why recovery was slow** — at the 20 m peak, trajectory shows ground
speed only 0.12–0.23 m/s while still ~100° off heading. v3 hover code:

- `range > max_radius` → original `target_speed = 1.0` (max)
- L131 taper `* max(0, 1 - 4 * steering_proportion)` = 0 with proportion ≈ 0.7
- → `1.0 * 0 = 0`, then v3 floor `max(0, 0.2) = 0.2`

So **v3's flat floor was actually holding the boat back from a 1.0 m/s
return** — it could only do 0.2 m/s while heading was off. After
turning around (~+10s into the recovery) it briefly hit 0.66 m/s but
spent most of the excursion at the floor.

**v4 prediction**: at range = 20 m, `range_factor = 1.0`,
`turn_min = 0.5 * max_speed = 0.5 m/s`. Recovery should be ~2.5× faster
than v3, but still won't restore full 1.0 m/s because L131 taper still
zeros the original max_speed when heading is off. v4 deployed; awaiting
field test.

**Possible v5 (deferred until v4 is validated)** — make the L131 taper
range-aware so far-away cases don't get throttled by heading error:

```cpp
double taper_slope = 4.0 * (1.0 - range_factor);  // 4.0 near, 0 far
current_target_speed *= std::max(0.0, 1.0 - steering_proportion * taper_slope);
```

At max_radius: no taper → full max_speed even with heading off (drive
home, correct yaw underway). At min_radius: original behavior (don't
overshoot). Holds for v4 floor to layer on top.

Bag script with perturbation timeline saved at `/tmp/hover_analyze2.py`.

**v4 field result**: "Hover is looking good." Range-aware floor with
the cliff at minimum_radius broke the orbital limit cycle. Boat now
settles inside the ring instead of orbiting at the kinematic radius.
v5 (range-aware taper for faster excursion recovery) still deferred —
not needed unless wind perturbations become a recurring problem.

**Bag analysis #3 — v4 quantitative validation** (new bag
`2026-04-16T17.20.52.010254426`, ~30 min post-v4 deploy):

Range from target (last 25 min):

| %ile | range |
|---|---|
| p25 | 1.67 m |
| p50 | 2.42 m (inside minimum_radius!) |
| p75 | 2.97 m |
| p90 | 4.20 m |
| p95 | 7.36 m |
| max | 16.82 m |

Killer stat:

- `cmd_lin == 0`: **8731 / 16858 (52%)** of commanded throttle is
  exactly zero. With v3 the floor of 0.2 was always on — this was
  effectively 0%. The cliff at `minimum_radius` is letting the boat
  actually settle.
- `cmd_lin > 0.45`: 405 / 7271 (5.6%) — the active "drive home"
  events when range exceeds the band.

Observed phases (post-v4):

- t = 300–360s: big thrust burst cmd_lin = 0.72–0.79 m/s — active
  recovery from a perturbation, range-aware floor doing its job
- t = 420s onwards (~22 min): stable hover, range mean 1–3 m,
  cmd_vel oscillating 0 ↔ 0.2 m/s as boat enters/exits the ring
- Recovery from largest excursion (16.8 m) worked cleanly vs v3's
  20 m crawl-home at 0.2 m/s

Actual speed ≈ commanded speed throughout — control loop healthy.
No orbital limit cycle, no drift-to-infinity, no v5 needed.

Bag script saved at `/tmp/hover_analyze3.py`.

#### Logger config: cmd_vel and udp_bridge per-remote stats

Topics added for post-mortem analysis (commit `8f2bb99` on PR #54):

- `/bizzy/piloting_mode/autonomous/cmd_vel` ✓ (TwistStamped, captured)
- `/bizzy/mavros/setpoint_velocity/cmd_vel` ✓ (captured)
- `/bizzy/cmd_vel_nav` and `/bizzy/cmd_vel_smoothed` — ABSENT in
  recorded topics. Implies `velocity_smoother` is not in the active
  launch's pipeline; nav2 publishes directly to
  `piloting_mode/autonomous/cmd_vel`. Not a problem for analysis;
  `piloting_mode/autonomous/cmd_vel` is the raw hover output.
- `/bizzy/udp_bridge/remotes/operator/{bridge_info,topic_statistics}` ✓
  (per-remote bandwidth stats now captured for WiFi/VPN attribution)

For future reference: the hover behavior parameters
(`minimum_radius=2.5`, `maximum_radius=10`, `maximum_speed=1.0`,
`maximum_rotation_speed=0.75`) and the "kill throttle above 45° error"
heuristic are platform-dependent — they assumed skid-steer kinematics.
A second hover variant or a `vectored_thrust: true` parameter may be
the right long-term shape.

#### Outstanding issues (updated)

Replaced "Tune annunciator stale timeouts and diagnostic name matching"
since the root cause is now understood and being fixed properly.

- [ ] Implement republish-cached pattern in `ros2_network_monitor` (3 nodes)
- [ ] Implement republish-cached pattern in `starlink_stats_ros`
- [ ] Fix annunciator `_handle_diagnostics` value-extraction fallback
      (Starlink-shows-serial bug)
- [ ] Have `starlink_diagnostics_node` populate `status.message` with a
      readable summary
- [ ] Backport hover.cpp patch (minimum-speed-during-turn) to
      `unh_marine_navigation` after field validation
- [ ] Consider hover behavior variants for skid-steer vs vectored-thrust
      platforms (or a `vectored_thrust` parameter)

### 2026-04-16 — Starlink ethernet root cause update

The recurring Starlink Mini ethernet drops (2026-04-06, 2026-04-07,
2026-04-10 water test #2) were likely **not** caused by bypass mode
reversion. On inspection, the ethernet connector to the dish was not
clipping securely — an intermittent physical connection. A colleague
glued the connector in place (~2026-04-13). Starlink ethernet has been
stable since. Bypass mode was also enabled and doesn't hurt, but the
loose connector was probably the real issue.

#### Bag debrief (2026-04-16, post-session analysis on salmon)

Post-deployment bag analysis of four sessions recorded today
(`~/data/logs/logs/bizzyboat/2026-04-16T*`):

| # | Start (UTC) | Duration | Activity |
|---|---|---|---|
| 1 | 12:52:58 | 4h 27m | Idle → hover debugging (v1–v4), PID tuning |
| 2 | 17:20:52 | 30m 30s | Hover v4 validation, active autonomous ops |
| 3 | 17:51:37 | 5m 04s | Restart after code fix |
| 4 | 17:56:58 | ~17 min | Active ops, ended by crane recovery |

Session 4 bag incomplete (no `metadata.yaml`, `_3.mcap` corrupted) —
expected, rsync caught mid-write; will complete on next sync.

**Findings:**

1. **`mikrotik_monitor` and `teltonika_monitor` silently crash on
   startup in sessions 3 & 4.** Diagnostic source count dropped from
   45 to 18 — all Teltonika and MikroTik diagnostics lost. Root cause:
   `ParameterUninitializedException` on `ignored_interfaces` (commit
   `d7c096a` declared it with type-only, no default). Crashes in
   `__init__` before any rosout output. Fix confirmed on salmon:
   `self.declare_parameter('ignored_interfaces', [])`.
   Tracked in [ros2_network_monitor#16](https://github.com/rolker/ros2_network_monitor/issues/16).

2. **Battery percentage stuck at 0.99 all day** (160k samples, current
   always ≈0 A). No current sensor wired on BizzyBoat; factory baseline
   `BATT_MONITOR=4` is wrong. Corrected in
   [PR #56](https://github.com/rolker/unh_echoboats_project11/pull/56)
   (draft — merge after field apply to Cube).

3. **BT/Nav2 action-status topics not logged** — rosout shows 20×
   planner aborts and 9× BT task aborts but bags can't reconstruct
   goals, decisions, or planned paths. Issue opened:
   [unh_echoboats_project11#58](https://github.com/rolker/unh_echoboats_project11/issues/58).

4. **Tide offset jumped ~4 m during session 4** — confirmed as crane
   recovery (boat lifted out of water), not a software bug.

5. **`ping_monitor` republish-cached pattern working** — sessions 3 & 4
   show the new "poll every 10.0s, publish every 1.0s" format.

**Hardware inventory doc created** as part of the battery investigation:
`bizzyboat_project11/docs/bizzyboat_hardware.md` in
[PR #56](https://github.com/rolker/unh_echoboats_project11/pull/56).
Catalogs all factory and add-on equipment with Torqeedo Power 24-3500
battery spec and voltage reference card. Replaces the seed list from
[#8](https://github.com/rolker/unh_echoboats_project11/issues/8).

**Debrief skill proposed** to automate this analysis workflow:
[ros2_agent_workspace#435](https://github.com/rolker/ros2_agent_workspace/issues/435).

### 2026-04-17 — Operator station maintenance

Discovered operator router (RUTX11) WireGuard tunnel to bencloud has been
down — salmon cannot ping `bencloud.wg.p11.lan`. Updated both routers
from RUTX_R_00.07.21.2 to RUTX_R_00.07.21.3 (2026-03-24 stable). Key
fix: "occasional client disconnections in busy environment." Also fixes
edge-case network hang after reboot (.21.2). Required re-creating ubus
ACL file (wiped by firmware upgrade) and power cycling the operator-side
SXTsq WiFi bridge.

**WiFi bridge fix**: After reboot, operator-side SXTsq (`172.16.20.4`) was
unreachable. VLAN config on the switch was correct (VLAN 4 → port 4), but
the SXTsq needed a power cycle after the VLAN swap investigation. WiFi
bridge fully restored — all three endpoints reachable (boat router, boat
OmniTIK, operator SXTsq).

**WireGuard port change**: Tunnel handshakes were completing but ICMP
failed. Investigation revealed BizzyBoat router's WG tunnel over Verizon
cellular had 0 B received — UDP 51820 confirmed blocked by Verizon (packets
never reached bencloud). Tested UDP 1194 (OpenVPN port) — packets arrive
fine. Changed bencloud WireGuard from port 51820 to 1194:
- bencloud: `/etc/wireguard/wg0.conf` ListenPort → 1194, OpenVPN stopped
  and disabled
- Operator router: `uci set network.bencloud.endpoint_port='1194'`
- BizzyBoat router: `uci set network.bencloud.endpoint_port='1194'`

All three WG peers initially connected on port 1194. Op-router → bencloud
~30ms, boat → bencloud via Verizon cellular working. Shortly after, port
1194 also stopped working from cellular (0 B received again). Switched to
UDP 443 (QUIC/HTTP3 port) — added to AWS security group, all three devices
updated. Port 443 working. Verizon may be doing DPI on WireGuard handshake
patterns rather than simple port blocking — 443 is likely more resilient
since carriers expect encrypted UDP traffic on it. VPN over Verizon cellular
remains intermittent — tunnel connects briefly then drops (handshake goes
stale after a few minutes). Indoor SINR of 9 is marginal. Boat moved
outdoors for deployment; Starlink should provide a more stable WAN path.

**Teltonika ubus ACL**: Both routers missing `/usr/share/rpcd/acl.d/ros_monitor.json`
after firmware updates — recreated and added to `/etc/sysupgrade.conf` for
persistence across future upgrades.

**Switched to Zenoh RMW** (`rmw_zenoh_cpp`): Local DDS subscribers on salmon
were intermittently losing diagnostics from the UDP bridge. Switched both
boat and operator to Zenoh: boat tmux script runs `rmw_zenohd` daemon,
exports `RMW_IMPLEMENTATION=rmw_zenoh_cpp`. New operator tmux startup script
(`start_tmux_operator_project11.bash`) with Zenoh/core/foxglove/ui/rqt-diag
windows. Foxglove bridge moved from operator_core_launch to its own tmux
pane. Commit `88dc6c6` on gitcloud.

**Annunciator/aggregator findings**: Starlink diagnostics land in `/Other`
instead of `/Boat/Starlink` because the node publishes with a
`starlink_diagnostics:` prefix the aggregator `startswith` filter doesn't
expect. Mission indicator configured as diagnostics source but
`mission_manager` is a topic, not a diagnostic. Fixes pending.

**Annunciator working**: All indicators populated when running
runtime_monitor + annunciator without robot_monitor. The rqt_robot_monitor
plugin hogs the Qt GUI thread, causing runtime_monitor timers to miss
ticks and all diagnostics to go stale. Root cause: `resizeColumnToContents(0)`
called on three QTreeWidgets for every incoming `/diagnostics_agg` message
(101 entries) — expensive Qt layout operation blocks the event loop.
Workaround: don't load robot_monitor in the operational perspective.

**Operator tmux startup**: Added foxglove-studio desktop pane to operator
tmux script (`ecaac25` on gitcloud). Investigating filtering benign
warnings from diagnostics (unused MikroTik ports, disabled SIM slots,
Starlink `lower_signal_than_predicted`). Config changes pushed to gitcloud:
`ignored_interfaces` added to MikroTik and Teltonika monitor YAMLs.

**Operator tmux startup script** (`start_tmux_operator_project11.bash`):
New single-command startup for the entire operator station — zenoh router,
core launch, foxglove bridge, foxglove studio, rqt diagnostics perspective,
and johnny5 PTZ camera, each in its own tmux window with correct env setup.
Greatly reduces the effort to bring up the operator station (previously
required manually launching each component). Commits `88dc6c6`, `ecaac25`,
`a2b64e4` on gitcloud.

**UDP bridge diagnostics**: Added `diagnostic_updater` to `udp_bridge` —
per-remote/per-connection health with tx/rx rates, resend/drop stats, and
staleness detection. 134 lines across 6 files. Committed `f563c73` on
gitcloud (udp_bridge repo). Bridge runs but diagnostics emission not yet
verified — check `ros2 lifecycle get /bizzy/udp_bridge` next session.

**Warning reduction**: Added `ignored_interfaces` to MikroTik configs
(ether2-5 on boat OmniTIK) and Teltonika configs (mob1s2a1/wan1 on boat,
mob1s1a1/mob1s2a1/wifi_bridge/mobile_lab on operator). Added
`publish_cellular` parameter to teltonika_monitor (disabled for operator
router which has no SIM). Commits `e111fae`, `75bd0df` on gitcloud
(unh_echoboats_project11), `d3e05f9` on gitcloud (ros2_network_monitor).

### 2026-04-20 — Deployment prep

**Starlink annunciator**: Boat's Starlink showing `install_pending` in
the annunciator panel — diagnostics pipeline is working end-to-end.
Want to change `install_pending` to WARN level instead of current level.
Agent on gabby implemented the fix; after core restart, annunciator now
correctly shows WARN for `install_pending`.

**Operator WiFi device (MikroTik)**: Not responding to monitor node or
web GUI, but data still flowing through it. Suspect the monitor node
may be overloading the device's management interface. Investigating.

**Intermittent internet on operator machines** — possibly related to the
unresponsive MikroTik if it's in the network path. Operator router web
interface also intermittent — can't stay connected long enough to
diagnose the internet issue. Killed core launch on salmon to stop
monitor nodes — this also brought down the udp_bridge, losing boat
data on the operator side. Note: boat-side data was flowing fine
throughout the network issues (problem is operator-side only). After
killing monitor nodes, routers have not recovered — monitor node
likely not the cause. Ping to operator router by IP works — L2/L3
connectivity is fine, web GUI/management interface is the issue.
SSH session to operator router (192.168.13.1) connected but `mwan3
status` command hung and won't respond to Ctrl-C. Router up 3 days,
load 0.39 — normal. Something is locking up the management/shell
layer on the RUTX11. New SSH connection attempt also slow to respond.
Power cycled operator network equipment (router + WiFi devices).
Router came back up and is responsive. Logs only show post-boot
entries — pre-reboot logs lost (RUTX11 stores logs in RAM). LAN3
port flapped during boot but everything settled. No root cause
determined.

**UDP bridge**: After reboot, only showing traffic over VPN — nothing
on WiFi path. Power cycling operator-side MikroTik again. MikroTik
web UI now accessible after power cycle. MikroTik logs only show
entries from last boot (Apr 4) — no logs from today's lockup session,
confirming device was completely locked up (not even logging). WiFi
bridge reconnected: -48dBm signal, 150Mbps link to boat-side MikroTik.
SSH to gabby via WiFi confirmed working. Device is an SXTsq Lite5 —
only 64MB RAM (25.3MB free after fresh boot), single-core 600MHz MIPS.
Very resource-constrained; monitor node API polling was a plausible
cause of the lockup. Monitored `/system resource print` every 2s while
restarting core launch with monitor nodes — memory stayed rock solid
at 25MB free, CPU spiked briefly to 16-18% on poll cycles but recovered
immediately. Monitor node does not appear to be the cause of the
earlier lockup. Root cause remains unknown.

**Annunciator**: All clear after core restart — only warning is the
Starlink `install_pending` (expected). Attempting remote reboot of
Starlink Mini via starlink.com account portal to clear `install_pending`.
During reboot, annunciator shows "Starlink ---" in grey (stale) — but
should be showing WARN or ERROR for a stopped data source, not just
going grey/stale silently. Need to fix stale-detection behavior in
annunciator. VPN traffic dropped to 0 — expected, Starlink was the
WAN carrying the VPN and Verizon cellular blocks the WireGuard port.
Starlink back up after reboot — annunciator shows no alerts.
`install_pending` cleared by the reboot. VPN not recovering for
udp_bridge traffic despite SSH to gabby via VPN working — suspected
udp_bridge bug where data stops flowing in one direction after a
network interruption. Seen before. Agents on salmon and gabby
investigating root cause before restarting.

**Root cause analysis (gabby agent)**: Ping/ICMP works both ways over
VPN (~60ms RTT). BizzyBoat's udp_bridge shows 222K B/s tx over VPN
with 0 failures, but operator sees 0 B/s rx. Suspected cause:
operator's udp_bridge is bound to the WiFi IP (192.168.13.142) not
`0.0.0.0`, so UDP packets arriving at the VPN address
(192.168.22.142:4200) are never delivered to the process. WiFi path
worked because packets arrived on the bound address. To verify:
`ss -uln | grep 4200` on operator — if it shows `192.168.13.142:4200`
instead of `0.0.0.0:4200`, that's the bug. **Update**: source code
shows udp_bridge binds `INADDR_ANY` (line 68) — bind address is NOT
the issue. Actual likely cause: udp_bridge records the source IP of
incoming connection packets (`source_info.host`) and sends replies
back to that address. If operator initially connected via WiFi, it
recorded bizzy's WiFi IP as the reply address. When WiFi dropped and
VPN took over, bizzy sends from a different source IP but operator
still sends to the stale WiFi address. The host/port only updates on
a new `OPERATION_CONNECT` message — no automatic re-resolution on
network path change. **Further update (gabby agent)**: connection
matching uses `connection_id` from the payload, not source IP — so
receiving is interface-agnostic. Operator's vpn connection shows
`received_bytes/s = 0`, meaning no wrapped UDP 4200 packets from
bizzy are reaching operator's socket at all, despite bizzy's kernel
accepting them for tx (222 KB/s, 0 failed). Drop is in the network
between bizzy and operator on the VPN path. Suspects: (1) firewall
on operator host or router blocking inbound UDP 4200 on VPN interface,
(2) MTU black-hole — WireGuard adds ~60B overhead, large UDP packets
silently dropped while small ICMP gets through.

**tcpdump on salmon** (`sudo tcpdump -ni any 'udp port 4200 and host
192.168.21.5'`): All traffic is outbound only — salmon sending to
192.168.21.5:4200 via `enp3s0`, zero inbound packets from bizzy.
Bizzy's packets never reach salmon's network stack. ICMP works but
UDP 4200 doesn't — points to firewall blocking inbound UDP from the
VPN subnet on either the boat or operator router.

**Root cause confirmed**: mwan3 connmark on boat router is steering
VPN-destined traffic out raw WAN (eth1) instead of WireGuard tunnel
(bcloud). tcpdump on boat router shows gabby's packets to
192.168.22.142 arriving on eth0 but exiting via eth1 (Starlink WAN).
`mwan3_hook` in mangle PREROUTING restores connmarks — the UDP 4200
flow was originally marked for `wan` when VPN was working over
Starlink. After Starlink reboot, stale connmark still routes via eth1
instead of bcloud. `ip route show` has correct route
(`192.168.22.0/24 dev bcloud`) but mwan3 fwmark rules (priority 2001)
override main table (priority 32766). Both routers' NETMAP rules and
firewall zones are correct. Fix: flush stale conntrack entries; longer
term, add mwan3 exception for bcloud-routed subnets.

**Fix applied**: `echo f > /proc/net/nf_conntrack` on boat router
flushed the stale hardware-offloaded conntrack entry. VPN udp_bridge
traffic immediately resumed. `mwan3 restart` and `/etc/init.d/firewall
reload` were insufficient — the `[OFFLOAD]` flag kept the entry in
the hardware flow table. Only the proc flush cleared it. `conntrack`
CLI tool is not installed on the RUTX11.

**Prevention**: Two-layer fix applied on boat router:
1. Added `192.168.21.0/24` to `mwan3_custom_v4` and
   `mwan3_connected_v4` ipsets — prevents mwan3 from marking new VPN
   flows with a WAN fwmark. (Other VPN subnets were already present;
   192.168.21.0/24 was the only one missing.)
2. Added `echo f > /proc/net/nf_conntrack` to `/etc/firewall.user` —
   flushes all conntrack (including hardware-offloaded entries) on
   every firewall reload, which is triggered by interface up/down
   events. Belt-and-suspenders: even if a stale connmark gets saved,
   the next WAN failover event clears it.
Note: mangle PREROUTING rules in firewall.user don't survive mwan3
restart (mwan3 flushes and rebuilds the mangle table), so that
approach was abandoned.

**Testing fix**: Rebooted Starlink again — VPN traffic dropped as
expected, then recovered automatically after Starlink came back.
Fix confirmed working.

**Final fix applied**: Disabled hardware flow offloading on boat
router via `uci set firewall.@defaults[0].flow_offloading_hw='0'`.
Software flow offloading remains active. HW offload was baking stale
routing decisions into the hardware PPE table — a known incompatibility
between mwan3, FLOWOFFLOAD hw, and WireGuard (OpenWrt issues #17915,
packages#5943). Selective FORWARD RETURN rules didn't work because
FORWARD policy is DROP. Performance impact negligible for this
throughput level.

**Second test**: Rebooted Starlink again. This time lost all connection
to boat — both WiFi and VPN udp_bridge traffic at zero. Can ping boat
router and reconnect SSH, but no udp_bridge data flowing on either
link. Conntrack flush in firewall.user was killing all flows (WiFi
and VPN) on every firewall reload. Removed the auto-flush.
Software FLOWOFFLOAD also had the same stale-mark problem as hardware
offloading — disabled all flow offloading:
`uci set firewall.@defaults[0].flow_offloading='0'`. After disabling
offloading and flushing conntrack, udp_bridge connections were fully
broken — required restarting core launch on both salmon and gabby to
re-establish. Data flow restored after both sides restarted.

**Third test**: Rebooted Starlink. VPN traffic dropped to zero as
expected. After Starlink came back, **VPN recovered automatically** —
no manual intervention needed. Fix confirmed: disabling all flow
offloading on the boat router resolves the mwan3/connmark/VPN
incompatibility.

**Starlink annunciator not recovering**: Node is healthy but dish at
192.168.100.1 is unreachable from gabby — ping 100% loss, gRPC
DEADLINE_EXCEEDED. Starlink Mini is in bypass mode (no Starlink
router), plugged directly into boat router. Boat router needs a route
or interface on 192.168.100.0/24 — the dish expects its .1 peer on
that subnet. Router has no address on 192.168.100.0/24 and no route to it. Router
itself can't ping 192.168.100.1 either — 100% loss. WAN is up
(internet working via CGNAT 100.64.0.1 on eth1) but dish management
API not responding. Worked earlier today after first reboot, stopped
responding after repeated reboots for VPN testing. Not a firewall
change side-effect — router has never had the address/route and it
worked before. Possibly a Starlink bypass mode quirk after multiple
rapid reboots. Another reboot fixed it — dish management API came back and starlink
monitor recovered automatically. Annunciator showing Starlink OK.

**Annunciator improvements needed**:
- NTRIP client errors visible in gabby tmux but no annunciator entry
  for NTRIP status — should add one.
- GPS showing satellite count (34.0) which is somewhat useful, but
  RTK fix type (float/fixed/none) would be much more valuable for
  operations.

**TODO**: Disable flow offloading on operator router too — same
mwan3/connmark issue applies.

**rmw_zenoh_cpp SubscriberCallback errors**: `mru_transform_node`
logging repeated errors about subscriber callbacks triggered on
`/bizzy/mavros/imu/data`. Possibly Zenoh RMW message queue overflow
or subscription handling issue. CAMP on salmon is frozen — may be
related if position updates from mru_transform are not making it
through udp_bridge.

**NTRIP recovery**: NTRIP client lost connection during Starlink
reboot (DNS failure), but auto-reconnected to MACORS RTCM3_MASA.
NTRIP resilience appears to be working for DNS-recoverable outages.

**Testing fix**: Rebooting Starlink to verify VPN recovery. VPN
traffic dropped to 0 as expected.

**tcpdump on gabby** (`sudo tcpdump -ni any 'udp port 4200 and host
192.168.22.142'`): Same result — all outbound, zero inbound. Gabby
sends to 192.168.22.142:4200 via `enp7s0` (LAN at 192.168.20.5),
relying on boat router to forward into WireGuard tunnel. Both sides
sending, neither receiving. Packets leave hosts fine but are dropped
by the routers — not forwarding UDP between LAN and WireGuard
interfaces. Checking router firewall/routing next.

**Root cause found (salmon agent)**: Operator router's VPN NETMAP rules
are missing — didn't survive the power cycle. These rules translate
between the operator LAN (192.168.13.0/24) and VPN subnet
(192.168.22.0/24):
```
iptables -t nat -I POSTROUTING -s 192.168.13.0/24 -d 192.168.21.0/24 -j NETMAP --to 192.168.22.0/24
iptables -t nat -I PREROUTING -d 192.168.22.0/24 -j NETMAP --to 192.168.13.0/24
```
Evidence: operator→boat traffic arrives at gabby with source
192.168.13.142 (not 192.168.22.142) — POSTROUTING NETMAP missing.
Boat→operator to 192.168.22.142 has nowhere to land — PREROUTING
NETMAP missing. WiFi path unaffected (650 kB/s flowing). Fix: add
rules to `/etc/firewall.user` on operator router and reload firewall.
Initially suspected NETMAP rules were flushed by firewall reload during
Starlink reboot, but rules are in `/etc/firewall.user` AND active:
PREROUTING matched 562 pkts, POSTROUTING matched 468 pkts. Operator
router NAT is working. Drop is elsewhere — likely boat-side routing
or firewall.

### 2026-04-20 (cont.) — Software session (boat unavailable)

Followed up on annunciator improvement needs noted during deployment above.

**UDP bridge per-connection diagnostics**: Added `/diagnostics` publishing
to `udp_bridge` with per-connection tx/rx rates and silence detection.
Lifecycle state guard, `on_cleanup()` reset. Merged
[rolker/udp_bridge#8](https://github.com/rolker/udp_bridge/pull/8).

**New annunciator indicators**: Created diagnostic wrapper nodes:
- `gps_rtk_diagnostics_node.py` — mavros GPSRAW → fix type diagnostic at
  1 Hz (RTK Fixed/Float/3D/etc.), configurable thresholds.
- `ntrip_diagnostics_node.py` — monitors RTCM flow on
  `mavros/gps_rtk/send_rtcm`, WARN→ERROR on configurable timeouts.
- UDP WiFi / UDP VPN config entries from operator-side udp_bridge diagnostics.
- RTCM added to bag recording (~1.5-3 MB/hr).

Fixed RTCM topic reference (ntrip_client remaps `rtcm` →
`mavros/gps_rtk/send_rtcm`). Merged
[#63](https://github.com/rolker/unh_echoboats_project11/pull/63),
[#64](https://github.com/rolker/unh_echoboats_project11/pull/64).

**Annunciator stale escalation**: Stale indicators now escalate WARN → ERROR
instead of grey "---". Fixed startup flash and stale-text bug. Merged
[rolker/rqt_operator_tools#16](https://github.com/rolker/rqt_operator_tools/pull/16).

**Gitcloud field-fix imports** (from earlier deployment session):
- `starlink_stats_ros` — `install_pending` → WARN + test
  ([#14](https://github.com/rolker/starlink_stats_ros/pull/14))
- `ros2_network_monitor` — `publish_cellular` param
  ([#18](https://github.com/rolker/ros2_network_monitor/pull/18))
- `unh_echoboats_project11` — operator tmux startup, Zenoh RMW, interface
  suppression, idempotent session guard, graceful shutdown script
  ([#65](https://github.com/rolker/unh_echoboats_project11/pull/65))

**Operator logbook** (parallel agent):
[rolker/rqt_operator_tools#2](https://github.com/rolker/rqt_operator_tools/pull/2) —
Phase 1 operator logbook with multi-package restructure (`rqt_operator_log`).
Text logging, rosbag2 recording, daily rotation, recovery. Under review.

**Quality standard**: Added to AGENTS.md
([PR #438](https://github.com/rolker/ros2_agent_workspace/pull/438)) —
robustness non-negotiable, fix completely, don't dismiss review catches.

## Status

Continuing under [#57](https://github.com/rolker/unh_echoboats_project11/issues/57)
(BizzyBoat field ops — survey readiness and class prep).

Water test #3 partially successful (2026-04-14). DDS discovery fixed via
Cyclone DDS with raised participant limit. Chart datum transform working.
S57 tide offset correction implemented and deployed. First successful
trackline plan and partial execution. Hover and controller_server issues
remain. DNS failover fix applied (2026-04-15) — structural fix for
recurring dnsmasq/mwan3 interaction. Network diagnostics enhanced with
signal quality thresholds, hardware_id disambiguation, DNS ping targets,
annunciator config, and aggregator improvements. Annunciator panel first
tested — functional via rqt but standalone segfaults and resize needs
work. Tide awareness pipeline advanced: S57 tide offset merged, MHHW
datum frame added, BT string literal fix merged.

2026-04-16: CrabbingPathFollower PID fix field-validated (correct PidROS
key names with negative signs). Hover v4 validated — range-aware floor
with cliff at minimum_radius broke orbital limit cycle. TF extrapolation
fix for multi-line surveys applied. Multi-line survey execution working.
Starlink ethernet root cause identified (loose connector, not bypass mode).

### 2026-04-21 — Deployment session

**Pre-launch**: `make sync` and `make build` on salmon and gabby to deploy
recent merges (annunciator improvements, UDP bridge diagnostics, gitcloud
field-fix imports, deployment log).

**Tides** (Portsmouth Harbor, MLLW): Low 8:48 AM (-1.1 ft), High 3:00 PM
(8.9 ft), Low 9:00 PM (0.3 ft). Rising tide through the afternoon.

**core_launch failure**: `gps_rtk_diagnostics_node.py` and
`ntrip_diagnostics_node.py` not found at launch. Scripts exist in repo and
are installed via `install(PROGRAMS ...)` in CMakeLists, but were committed
without the execute bit (mode 0644). With `--symlink-install`, the install
symlinks inherit the source file's 0644 permissions, so ROS rejects them as
non-executable. Fix: `chmod +x` both scripts and commit. Applied locally on
gabby to unblock testing; will push to gitcloud.

**Annunciator on salmon**: Required `rqt --force-discover` to find the
annunciator plugin in its new package location (rqt_operator_tools
restructure). Once discovered, annunciator showing almost all red — expected
with gabby nodes not yet running. Confirms the stale-escalation fix
(rqt_operator_tools PR #16) is working correctly: missing data sources
show red/ERROR instead of grey "---".

**Gabby launch successful** after chmod fix. Annunciator showing all clear
except one red entry — label clipped, likely mission manager. Need to
investigate: could be expected (no mission loaded) or a real issue.
Annunciator label clipping is a UI issue worth noting for class-ready
polish.

**Systems check**: GPS position good and stable in CAMP. All cameras
showing in Foxglove. Controller manual mode verified — thrusters
actuate, returned to standby. Hover command issued — thrusters
responded, nav stack launched successfully, returned to standby.
Mission annunciator still red after hover — not resolved by having
the nav stack running. RC controller tested and working.

**09:28 EDT**: Operator directional WiFi antenna mounted on mobile lab
roof, pointed ~65°. Launching boat.

**09:43 EDT**: Boat in water, RC-driven to loiter area outside pier,
placed in ArduPilot Loiter mode via RC. Beginning project11 autonomous
testing (survey lines).

**Controller override test**: Controller works from operator station.
Hover override in CAMP caused boat to move towards pier — may have
resumed a stale hover target from pier-side testing instead of
resetting to current position. Possible bug: hover should default to
current position when initiated, not reuse a previous target. Goto
override worked correctly — boat navigated to target and is hovering
at the goto location. **TODO**: Investigate stale hover target — CAMP
"Hover Here" context menu may not be resetting the goal to the clicked
position, or the nav stack is reusing a latched goal from the previous
session.

**WiFi bridge annunciator**: Showing -43 dBm +/- 3 — excellent signal.

**Survey lines**: Running well. Significant crabbing due to current but
CrabbingPathFollower keeping boat on the line. PID fix from 2026-04-16
holding up.

**Bag analysis — survey line failure**: Session bag at
`2026-04-21T13.18.20.995262455/`, topic
`/bizzy/marine/status/mission_manager`.

Survey #1 (pattern0000, 3 lines across current): All completed.
line0 13:53→13:56, line1 13:56→13:58, line2 13:58→14:01. ~3 min/line.

Survey #2 (pattern0001, 4 lines along current): Lines 0-2 completed
normally (~3-5 min each). Line 3 started at 14:28:33 UTC and mission
jumped to `done_hover` at 14:28:37 — only 4 seconds. The
`survey_line_set` was marked `(done)` but `line3` itself was never
marked `(done)`, still showing `type: survey_line`. Mission manager
declared the set complete with an incomplete line. Initial suspicion was the TF extrapolation / stale `header.stamp`
issue from 2026-04-16, but bag analysis shows a different root cause:

```
14:28:32.705 controller_server: Reached the goal!       (line 2 done)
14:28:34.303 controller_server: Received a goal [...]   (line 3 goal received)
14:28:36.304 controller_server: Costmap timed out waiting for update
14:28:36.304 controller_server: [follow_path] Aborting handle.
14:28:37.303 behavior_server: Running hover             (fallback)
```

**Root cause**: Local costmap timed out 2 seconds after line 3's goal
was accepted. Controller aborted the follow_path action, mission
manager treated the abort as survey-set complete, fell back to hover.
Line 3 was never executed. **TODO**: Investigate costmap timeout —
why did it stall between lines? Could be a timing issue where costmap
updates pause during line transitions, or the SeaSurfaceLayer segfault
workaround (removed from local costmap plugins) left insufficient
costmap update sources.

**Deep analysis** (bag + source code):

*Costmap timeout root cause*: Two compounding issues in S57Layer:

1. **Tile regeneration bounded by `update_timeout: 0.15s`** per
   costmap update cycle. When the rolling costmap window jumps to a
   new area (large inter-line transit), `matchSize()` clears all
   cached tiles. At 5 Hz costmap update rate, the layer gets at most
   ~5 × 0.15s = 0.75s of regeneration within the 1.0s controller
   `costmap_update_timeout` — insufficient for a cold tile cache.

2. **Chart grid data delivered asynchronously.** `generateTile()`
   returns `complete=false` when chart grids haven't been delivered
   yet (pending `get_datasets` service call + subscription). The
   costmap cannot become current until callbacks fire — took ~15s in
   this case (tide offset logged at 14:28:51, 15s after transition).
   No amount of timeout tuning fixes this.

*Why line 3 failed but lines 0–2 didn't*: Lines 0→1→2 had small
positional shifts (~2m), within the S57Layer's prefetch buffer
(2×5% outer buffer around costmap bounds). The ~97m jump to line 3's
start position moved outside the prefetched area, triggering a full
cold cache reload.

*Config*: `costmap_update_timeout` is 1.0s in `nav2_params.yaml`
(controller_server). `sea_surface_layer` confirmed removed from local
costmap plugins (segfault workaround), leaving only `chart_layer` +
`inflation_layer`. Planner_server also hit sustained costmap timeouts
later (14:38–14:39, ~16 failures over 1 min). Issue filed as
rolker/unh_marine_navigation#19.

*Fix options*: (a) increase `costmap_update_timeout` to 3–5s — helps
tile regen but not async data stall; (b) prefetch chart data for
upcoming waypoints before line transition; (c) allow controller to
proceed with stale costmap during transit (open water); (d) increase
S57Layer `update_timeout` for more work per cycle.

*BT abort handling bug*: Root cause is in `SurveyLineSetTask` BT
subtree in `run_tasks.xml` (lines 296–335). Uses
`KeepRunningUntilFailure` around the inner `Sequence(SurveyLineTask,
SetTaskDone)`. When `FollowPath` aborts, `SurveyLineTask` returns
FAILURE. `KeepRunningUntilFailure` converts FAILURE→SUCCESS (its
contract: run until failure, then signal completion), causing
`WhileDoElse` to exit the loop. The survey_line_set is then marked
done despite line 3 never completing. Fix: replace
`KeepRunningUntilFailure` with retry logic or a pattern that keeps
the loop running on navigation failures.

**Comms annunciator**: Yellow/WARN — 40% packet loss. Boat still on
line so autonomy unaffected, but degraded link quality despite good
WiFi signal (-43 dBm). SNR dropped to 20 dB — high noise floor
(~-63 dBm), likely channel interference causing the packet loss.

**Telemetry dropout**: Operator telemetry stopped arriving mid-survey.
Boat continued autonomously on survey line — confirmed visually via
johnny5 PTZ camera on mobile lab roof. Telemetry recovered when boat
reached end of third (final) survey line. Boat entered hover as
expected at end of mission. Autonomy operated correctly through the
comms dropout — good resilience test.

**WiFi antenna test**: Rotated operator directional antenna 90° CW
(pointing away from boat). WiFi bridge annunciator dropped to 19 dB
SNR (yellow/WARN), then recovered to 21 dB (grey/stale). Relatively
small drop for a 90° misalignment — suggests significant multipath
or the boat is close enough that sidelobes still provide usable signal.
Grey at 21 dB is odd — should be yellow or green, not stale.

**Link degradation** (antenna still misaligned): Various annunciators
flashing yellow intermittently. CAMP heartbeat status went red —
15 sec latency, recovered briefly to green, then red again at 30 sec
latency. Consistent with marginal WiFi link causing bursty packet
delivery. Goto command issued to test commanding through spotty
link — boat accepted and is moving. Commands getting through despite
degraded connection. Camera images in Foxglove still updating fine
despite link degradation.

**Antenna repointed to ~30°**: All annunciators green/grey, link
recovered. Mission annunciator resized itself off screen — same rqt
layout issue as earlier.

**Survey test #2**: 4 lines along the current (2 with, 2 against) to
test CrabbingPathFollower behavior in following vs opposing current.
First survey was 3 lines across the current.

**Survey test #2 result**: Boat completed 3 of 4 lines, then entered
hover instead of continuing to line 4. Same behavior as the TF
extrapolation issue from 2026-04-16 (stale `header.stamp` on per-line
goals)? Or a different bug. **TODO**: Investigate — check if the
field fix for multi-line surveys was actually committed and deployed,
or if this is a new failure mode.

**10:32 EDT**: Kongsberg M3 sonar arrived. Recovering boat for
installation.

**10:45 EDT**: Boat out of water.

**Kongsberg M3 sonar installation**: Sonar mounted with SBG IMU and
sound speed sensor connected via serial to mercat (Windows PC). Sound
speed sensor on COM3 at 9600 baud. SBG Ellipse on COM4 at 921600
baud, required null modem adapter. Both working. SSH enabled on
mercat.

**M3 network**: Sonar ships with a preconfigured static IP, not on
the boat's 192.168.20.0/24 subnet. Connected directly to a spare
ethernet port on mercat for now (point-to-point) so the M3 application
can reach it without touching the boat switch or the sonar's factory
config. Follow-up: reassign the M3 to a compatible address on the
boat subnet (or give mercat a second interface on the M3's factory
subnet) and move the cable to the PoE switch so the sonar is
reachable by gabby, not just mercat.

**14:33 EDT**: Session ended. Boat on trailer.

### Post-session bag analysis (2026-04-21 evening)

**Tide pipeline field validation — chart_datum_node working**:
Derived observed tide height from TF chain
`Z(map → map_tide) − Z(map → chart_datum)` and compared against a
sinusoidal fit to NOAA Portsmouth predictions (low −1.1 ft @ 12:48 UTC,
high +8.9 ft @ 19:00 UTC). Over the in-water window (13:43 → 14:34 UTC):

- Observed rise: **+1.24 ft**
- Predicted rise: **+1.36 ft**
- Per-sample residual: ≤ 0.15 ft

This is the first field cross-check of the chart-datum pipeline
against an independent tide prediction rather than just confirming
transforms publish. The S57 tide-offset applied to the costmap is
accurate enough for planning.

A ~4.70 ft constant offset (observed − predicted) remains after chain
math and represents GPS-antenna-above-waterline + geoid detail.
mru_transform still applies zero antenna offset on `raw/fix`
(the standing item from `project_tide_awareness.md`); that would
close the gap.

**Current structure — per-survey-line triangulation**:
Extracted the 6 completed survey-line segments (3 lines in pattern0000,
3 in pattern0001; line3 aborted at 4 s excluded). For each line, the
body-lateral component of ground velocity (perpendicular to heading) is
a clean observation of the current projected on that axis. Fitting a
single 2-D current vector to all 6 lateral observations by least
squares:

- **Current = 1.26 kt toward compass 101° (ESE)**
- Per-line residual ≤ 0.28 kt (most < 0.05 kt — excellent fit).
- Reciprocal-lane pairs (112°/228°) produce opposite-signed lateral
  components of matching magnitude, self-consistency check.

This is substantially stronger than the initial cmd_vel-based estimate
(0.46 kt toward 93°), because the lateral-component estimator doesn't
assume cmd_vel equals through-water velocity. Implied through-water
forward speeds from the fit are 1.7–2.7 kt for most lines. Median
|crab angle| during steady forward drive was 25.5°, symmetric around
0°, matching the "significant crabbing" description in the earlier
deployment note.

Caveat: no DVL / speed-through-water sensor on board — all estimates
are inferred from GPS + IMU + commanded velocity. The per-line lateral
method is the best we can do without one.

**Cross-check against NOAA current predictions**: Compared the
triangulated result against the three nearest NOAA current prediction
stations (queried via CO-OPS metadata + datagetter APIs):

| Station | Dist | Phase in window | Pred. direction | Fit |
|---|---:|---|---|---|
| ACT0731 Clark Island, south of | 1.05 km W | late ebb, slack 15:19 UTC | ebb 85° | **good — Δdir 16°, mag consistent** |
| ACT0726 Salamander Point, N of  | 0.65 km NW | late flood, slack 15:10 UTC | flood 257° | poor — 156° off |
| ACT0716 Wood Island, NW of      | 0.87 km SE | end ebb, slack 14:58 UTC | ebb 199° | poor — 98° off |

The measurement matches Clark Island (main entrance channel, E–W axis)
and **not** the geographically closest station (Salamander Point, side
pocket with a separate current cell, flood WSW). Proximity isn't a
reliable heuristic for current-station selection at Portsmouth Harbor —
channel topology is. Sinusoidal decay from Clark Island's max ebb
(-2.68 kt at 11:28 UTC) toward its 15:19 UTC slack predicts ~1.3–1.6 kt
at the window midpoint, matching the measured 1.26 kt.

Conclusion: the boat experienced **late-ebb flow exiting Portsmouth
Harbor at ~1.26 kt**, decaying toward slack. CrabbingPathFollower held
lines against a real, predicted current — not a controller artifact.

Analysis scripts + CSVs archived in ros2_agent_workspace
`.agent/scratchpad/`:
`tide_extract2.py`, `current_extract2.py`, `tide_current_plots.py`,
`tide_2026-04-21.csv`, `current_2026-04-21.csv`,
`tide_2026-04-21.png`, `current_timeseries.png`, `current_map.png`.


**Session summary**: Successful water test — 3-line survey completed,
4-line survey completed 3 of 4 (costmap timeout root-caused from bag
analysis). Annunciator stale-escalation fix verified. WiFi antenna
misalignment test showed graceful degradation. Commands work through
spotty link. Kongsberg M3 sonar arrived and installed with SBG + sound
speed sensor on mercat. BT retry fix merged
(rolker/unh_marine_navigation#20). Sim bag recording PR pending
(rolker/unh_marine_simulation#57).

**TODO for next session**:
- Dissect bag data from today's survey tests (beyond the line-3 /
  line-4 failures already root-caused in this log — more to review)
- M3 network integration: reassign M3 from factory static IP to boat
  subnet, move from mercat direct-connect to PoE switch so gabby can
  reach it
- M3 acquisition software setup
- PTP time sync on mercat
- Test BT retry fix on water (4+ line survey)
- Costmap timeout investigation — increase timeout and/or prefetch
- Annunciator rqt resize issue
- Investigate mystery red mission annunciator entry
- Commit CrabbingPathFollower PID YAML
- Commit TF extrapolation fix
- Disable flow offloading on operator router

### 2026-04-22

Planning session for hydro payload integration. Boat powered off — no
hardware activity today beyond scoping and documentation setup.

- Opened two sub-issues under [#57](https://github.com/rolker/unh_echoboats_project11/issues/57):
  - [#76](https://github.com/rolker/unh_echoboats_project11/issues/76) — *BizzyBoat hydro payload integration — M3, SBG, SVS on mercat*
    (software bring-up, NTRIP strategy, calibration planning; lists mercat NTP as blocker)
  - [#77](https://github.com/rolker/unh_echoboats_project11/issues/77) — *BizzyBoat hydro payload — physical install, offsets, URDF, SVG diagram*
    (extends `bizzyboat_reference_geometry.md`, adds `bizzyboat_offsets.svg`, updates URDF)
- Peer reference: [rolker/marine_tools#1](https://github.com/rolker/marine_tools/issues/1) (QINSy → ROS bridge)
- [rolker/marine_tools#2](https://github.com/rolker/marine_tools/issues/2) (direct M3 ROS driver) deferred pending evaluation of marine_tools#1
- AML winch sound speed profiler: deferred to a later issue
- Initialized detailed install log at
  [`bizzyboat_project11/docs/hydro_payload_install_log.md`](../../bizzyboat_project11/docs/hydro_payload_install_log.md) —
  hardware inventory, photo index, measurement log, and manual-cross-reference TODOs
- First measurement recorded: **SBG survey GPS antennas 2.05 m apart**
  (wider than the Cube's 1.67 m baseline; SBG uses its own antennas at the
  existing EchoBoat survey antenna positions)
- Summary entries for hydro payload work will be added here as sessions
  progress; day-to-day detail lives in the dedicated install log

**Housekeeping**:
- PR [#75](https://github.com/rolker/unh_echoboats_project11/pull/75) merged —
  earlier 2026-04-21 deployment log updates now on jazzy

### 2026-04-23

H.265 / `ffmpeg_image_transport` field test on salmon. Boat at the pier,
powered up. `oak_forward` publishing the H.265 stream and forwarded
over the wifi `udp_bridge` at 5 fps per
[PR #79](https://github.com/rolker/unh_echoboats_project11/pull/79)
(depends on [unh_marine_perception PR #5](https://github.com/rolker/unh_marine_perception/pull/5)).

**End-to-end H.265 decode confirmed on salmon.** The `/ffmpeg` topic
arrives over the wifi udp_bridge and is decodable on the operator
station with the `ffmpeg_image_transport` plugin installed.

Two operator-side gotchas worth recording:

1. **`ffmpeg_image_transport` is not a rosdep on any operator-side
   package.** Only `depthai_marine` (boat side) declares it. Installed
   `ros-jazzy-ffmpeg-image-transport` manually on salmon for now.
   Issue [rolker/rqt_operator_tools#20](https://github.com/rolker/rqt_operator_tools/issues/20)
   tracks the proper fix — a new `rqt_camera_grid` plugin in
   `rqt_operator_tools` will declare the dep so rosdep handles it on
   future operator-station installs.

2. **`rqt_image_view` does not list `image_raw/ffmpeg` topics
   directly.** Its topic discovery only knows
   `sensor_msgs/Image` and `sensor_msgs/CompressedImage`;
   `ffmpeg_image_transport_msgs/FFMPEGPacket` is invisible to it.
   The udp_bridge forwards only the `/compressed` and `/ffmpeg`
   sibling topics, never the base `image_raw`, so the usual
   transport-dropdown trick can't help. Workaround: run an
   `image_transport republish` node on salmon that subscribes via
   the `ffmpeg` transport and re-emits raw `sensor_msgs/Image`:

   ```
   ros2 run image_transport republish \
     --ros-args \
     -p in_transport:=ffmpeg -p out_transport:=raw \
     --remap in/ffmpeg:=/bizzy/sensors/cameras/oak_forward/image_raw/ffmpeg \
     --remap out:=/decoded/oak_forward/image_raw
   ```

   Then point `rqt_image_view` at `/decoded/oak_forward/image_raw`.
   (Note: positional `republish ffmpeg raw` syntax is stale — Jazzy
   reads `in_transport`/`out_transport` as ROS parameters. Wrong
   ordering silently spins up an FFMPEG *encoder* instead of a
   decoder.)

   The `rqt_camera_grid` plugin from #20 will subscribe through
   `image_transport` directly and skip the republisher entirely.

**Bitrate tuning** (commits `0b7a558`, `3c4aaec` on `feature/issue-78`,
both folded into PR #79):

- 4000 kbps default → visible block artifacts during udp_bridge byte
  drops on wifi.
- 2000 kbps → much better, occasional hiccups.
- 1000 kbps + `enable_video: False` (preview/JPEG/raw + camera_info
  publishers off) on all four OAKs, plus segmentation throttle
  (`period: 0.5`) removed from the wifi `udp_bridge` map → **solid
  front image, no more block artifacts observed.** Other three
  cameras pending visual confirmation as the operator UI is set up
  for them.

Orphaned udp_bridge entries from `enable_video: False` (the
`<cam>/image_raw/compressed`, `_raw`, and `_info` siblings) are
intentionally left in the wifi map — harmless when no publisher
exists, and a single-line revert restores the JPEG path if needed.
Cleanup deferred to a follow-up after a few sessions confirm we
don't miss them.

vpn `udp_bridge` sub-tree untouched — deferred per
[PR #79](https://github.com/rolker/unh_echoboats_project11/pull/79)
scope.

**Later in the session** the scope widened well past "step 1". All four
OAKs are now on H.265 @ 1000 kbps over both wifi and vpn (segmentation
throttled at 1 Hz on vpn to fit its ~1 MB/s budget), `enable_video: False`
is the default on every camera, and the orphaned `oak_<name>` /
`oak_<name>_info` / `oak_<name>_raw` udp_bridge entries were dropped
once the `FFMPEGPublisher`-is-not-lazy rationale made the "subscribe
to raw image to wake up the compressed publisher" trick unnecessary.
PR #79 merged as `ce2246f` on `jazzy`, title/body rewritten to match
the actual rollout.

### TM2000B lockup (first observed)

TM2000B NTP appliance (192.168.20.123) went unreachable during this
session — `ping` 100% loss from the boat router, ARP showing the
"tried to resolve, got silence" marker (`00:00:00:00:00:00`), DHCP
lease purged. L2 dead, not just L3, which ruled out firewall / lock
state.

Power-cycled the device. Came back immediately:

- ping: 0% loss, 0.8–2.8 ms RTT
- ARP: MAC `d4:e9:5e:06:15:63` resolved on `br-lan`
- DHCP: lease restored (hostname `time`, 12 h)

First lockup event since the 2026-04-10 install. Worth tracking
frequency — if this recurs, consider a scheduled reboot or a watchdog
on the PoE port (not available on the current unmanaged Trendnet
TI-PG80B switch, so it'd need manual or router-driven power cycling).
Follow-up: verify GPS 3D fix and NTP serving via the web UI and
downstream `chronyc sources` on gabby after recovery.

Gabby's `chronyc sources` later confirmed the TM2000B is back at
Stratum 1 with one successful poll 98 s in — reach will walk up as
polls accumulate. Also surfaced a separate, pre-existing issue:
**gabby sees `reach 0` / `LastRx -` for both `router.lan.bizzy.p11.lan`
and `router.lan.op.p11.lan`** — it has never had a successful NTP
poll from either RUTX11. Not caused by today's TM2000B outage; worth
its own investigation (likely ntpd listen-address or firewall on the
routers). Internet stratum-1 fallback (`50.205.57.38`) was selected
throughout, system-time offset stayed within 1 ms.

### Mercat COM4 stuck after reboot

Mercat rebooted during the session (Windows pending update). After
reboot, sbgCenter couldn't see the SBG Ellipse and TeraTerm reported
"Access denied" on COM4. A second power cycle (from the boat) did
not clear it.

Ran a layered diagnostic from the operator side over SSH to mercat:

- `Win32_SerialPort` showed COM4 as `Status: OK` on native on-board
  RS-232 (`ACPI\PNP0501\SMODULEC4`) — not a USB-adapter renumbering
  issue.
- `mode COM4` → "Device COM4 is not currently available."
- `.NET SerialPort.Open()` → "Access to the port 'COM4' is denied."
- Sysinternals `handle64.exe -accepteula -a COM4` / `Serial` /
  `Serial4` — **no matching handles** even from an elevated SSH
  session (`High Mandatory Level`). No user-mode process held the
  port.
- `lfsvc` (Windows Geolocation Service) was running and kept being
  re-triggered on "Manual" start type. Stopped and set to
  `StartupType Disabled` on suspicion it was probing COM ports for
  NMEA GPS. Did not release COM4.

The hold was below user-mode. Fix was a PnP device cycle:

```powershell
Disable-PnpDevice -InstanceId "ACPI\PNP0501\SMODULEC4" -Confirm:$false
Enable-PnpDevice  -InstanceId "ACPI\PNP0501\SMODULEC4" -Confirm:$false
```

Immediately after the enable, `.NET SerialPort.Open('COM4', 9600)`
returned `IsOpen=True`. sbgCenter able to proceed.

Recipe saved to memory (`reference_mercat_com4_stuck.md`) so next
mercat reboot that lands in the same state can go straight to the
disable/enable cycle rather than rediscovering the problem. Worth
opening a dedicated sub-issue under #76 if it recurs, to track whether
it's every reboot or a sporadic condition.

### Mercat service cleanup

With mercat already open over SSH, surveyed its running services and
the time-sync stack.

Disabled (Stopped + `StartupType Disabled`):

- **`lfsvc`** — Geolocation Service. No location-API consumer on a
  survey PC; was a suspected COM-port holder earlier in the session.
- **`DiagTrack`** — Connected User Experiences and Telemetry. Sends
  diagnostic/telemetry to Microsoft. Not useful here.
- **`CDPSvc`** — Connected Devices Platform. Pairs with phones/tablets
  (Your Phone, Continue on PC). Nothing to pair with.
- **`PDSSettimeService`** — Teledyne "Adjust computer time to GPS
  time" service from the Sonar UI installer. Was actively **fighting
  the Meinberg NTP daemon** — offset was -26.9 ms with 2.5 ms jitter
  while it was running, since it was stepping the clock from the
  DeltaT sonar's GPS feed behind ntpd's back.

Third-party services left running (verified legitimate): Meinberg `NTP`,
`hasplms` (QPS license), `PostgreSQL (QPS)`, `QpsHelpServer`,
`SQLWriter`, `TeamViewer`, Microsoft Defender trio.

### Mercat time-sync picture + PTP evaluation

Current stack:

- **Meinberg-style ISC `ntpd`** at `C:\Program Files (x86)\NTP`,
  service name `NTP`, pointed at `time.bizzy.p11.lan` (TM2000B).
- Config: `server time.bizzy.p11.lan iburst minpoll 6 maxpoll 7`.
- Windows `w32time` is **Stopped** — no conflict.
- `ntpq -pn` after the PDSSettimeService disable shows TM2000B
  selected (`*`, refid `.GPS.`, stratum 1, reach 377, delay 0.5 ms).
- Offset at the moment of capture was -26.9 ms (footprint of the
  now-disabled Teledyne service); ntpd will slew to near-zero over
  the next several polls.

**PTP evaluated and deferred.** Summary of the decision (full write-up
in `project_time_sync_ptp.md`):

- NIC: Intel I211 Gigabit — IEEE 1588 HW timestamping at the silicon
  level; Windows driver doesn't surface PTP knobs via
  `Get-NetAdapterAdvancedProperty` (common for Intel GbE).
- OS: Windows 11 Pro has no native PTP — that's Server-only.
  Third-party clients (Meinberg PTP add-on, Domain Time II,
  TimeKeeper) are commercial, ~$250-$400/seat.
- Path: unmanaged Trendnet TI-PG80B PoE switch caps PTP accuracy at
  ~10-100 μs (no transparent/boundary clock).
- Current NTP accuracy (~1 ms) is already ~2 mm at 4 kt — inside
  multibeam pulse bandwidth.
- Revisit PTP only if a future sonar / sync requirement drops below
  1 ms, or the PoE switch gets replaced anyway, or mercat moves to
  Windows Server.

All verification commands and the PTP decision criteria are captured
in `reference_mercat_time_sync.md` in memory.

### Other-agent PR activity on 2026-04-23

While this session focused on the boat (H.265 rollout, TM2000B
recovery, mercat COM4 + service cleanup), other agents landed /
opened PRs worth noting for the record:

- **[rolker/unh_marine_perception#5](https://github.com/rolker/unh_marine_perception/pull/5)
  (merged, +843/-62)** — the on-device H.265 encoder in
  `depthai_marine` that PR #79 depends on. Previously we were pulling
  the dev branch from `gitcloud/jazzy`; as of today it's on
  `origin/jazzy`, so a regular `git pull` on gabby (once its clock
  resets there) pulls everything end-to-end.
- **[rolker/rqt_operator_tools#21](https://github.com/rolker/rqt_operator_tools/pull/21)
  (merged, +191/-6)** — fixes the long-running annunciator
  window-resize bug (#19). The mission annunciator no longer blows out
  the rqt window horizontally when dragged taller. (Root cause:
  `QLabel.minimumSizeHint()` scaling with font metrics.)
- **[rolker/rqt_operator_tools#22](https://github.com/rolker/rqt_operator_tools/pull/22)
  (open, +3630)** — full `rqt_camera_grid` plugin implementation
  closing the #20 issue opened earlier in this session. 3.6 k lines —
  multi-pane grid with per-pane `(base_topic, transport_hint)` config
  and staleness border. When this merges, salmon will subscribe to
  `image_raw/ffmpeg` directly and the `image_transport republish`
  workaround logged above becomes obsolete.
- **[rolker/rqt_operator_tools#23](https://github.com/rolker/rqt_operator_tools/issues/23)
  / #24 (open, +559/-23)** — annunciator adaptive column widths +
  per-cell font fitting. Quality-of-life follow-up to #21.

### Open item for next mercat session — NTP convergence

After disabling `PDSSettimeService`, the Meinberg ntpd offset against
TM2000B **did not converge**. Two samples ~5 min apart:

- `offset -26.912 ms` (initial, right after disable)
- `offset -32.663 ms` (5 min later)

`reach 377`, `delay ~0.5 ms`, `jitter ~2.8 ms` both times — link and
measurement quality are fine, the clock is just drifting away. Most
likely ntpd's drift/frequency estimate got corrupted while
PDSSettimeService was stepping the clock behind its back; restarting
the NTP service would reset the PLL. Not pursued in this session —
mercat is being powered down for the day. Next session:

1. Check with `ntpq -pn` on boot and see what offset is.
2. If still drifting, `Restart-Service NTP` and observe for a few
   minutes (iburst will give 8 rapid polls).
3. If still drifting after restart, search for another clock-setter
   we missed (scheduled tasks, other services). `ntpq -c rv` will
   show ntpd's internal PLL state.

### 2026-04-24 — Queued for tomorrow's pier session

Operator-station software day. Boat not powered. Work done on
salmon (workspace machine) and pushed to both GitHub and gitcloud
so gabby + salmon can `make sync` in the morning and have the
changes.

**Queued for verification** (see "Next pier session" checklist at
the top of this log):

- **`rqt_camera_grid` plugin landed on `jazzy`** via
  [rolker/rqt_operator_tools PR #22](https://github.com/rolker/rqt_operator_tools/pull/22)
  ([merge `fd3bb3e`](https://github.com/rolker/rqt_operator_tools/commit/fd3bb3e)).
  Closes [rolker/rqt_operator_tools#20](https://github.com/rolker/rqt_operator_tools/issues/20).
  Multi-stream image_transport grid with per-pane staleness border,
  YAML perspective persistence, and a live-thumbnail config dialog
  (direction arrows + Clear, no `+` / `-`). Tested hands-on via the
  shipped webcam demo (`ros2 launch rqt_camera_grid demo_webcam_grid.launch.py`
  + `config/demo_webcam_grid.yaml`). Tomorrow's operator-side
  verification on salmon replaces the `image_transport republish`
  workaround documented in the 2026-04-23 session — rqt_camera_grid
  subscribes to the `ffmpeg` transport directly.
- **`package.xml` now declares all four image_transport plugins** as
  `exec_depend` — `compressed_image_transport`,
  `compressed_depth_image_transport`, `theora_image_transport`,
  `ffmpeg_image_transport`. Fresh `rosdep install` on salmon will
  pull everything the config dialog can select, closing the "operator
  station manual install" gap flagged on 2026-04-23.
- **`plan-task` skill guidance for implementation-phase plan edits**
  merged to workspace `main` via
  [rolker/ros2_agent_workspace PR #450](https://github.com/rolker/ros2_agent_workspace/pull/450)
  ([merge `8c92c6d`](https://github.com/rolker/ros2_agent_workspace/commit/8c92c6d)).
  Closes [rolker/ros2_agent_workspace#449](https://github.com/rolker/ros2_agent_workspace/issues/449).
  Documents inline-edit default + appended "Implementation Notes"
  for design pivots + commit discipline, with a worked example from
  PR #22's round-8 fix pass. Not a hardware change — affects how
  future plan-first PRs stay in sync with their plans.

**gitcloud push**: `./.agent/scripts/push_remote.py --remote gitcloud`
ran clean — 32 repos, 0 errors. Gabby and salmon pull from gitcloud
(see memory `reference_gitcloud.md`); `make sync` on either machine
will pull today's changes including the merged rqt_camera_grid.

**Also during the session**:

- Added a "Next pier session" checklist at the top of this log so
  it's the first thing a future-me sees when opening the deployment
  log. Hydro-payload specific items stay in `hydro_payload_install_log.md`;
  the top-of-deployment-log checklist covers boat-wide verification
  (sync, build, camera grid, time sync, network reach).
- Multi-round Copilot review on PR #22 (22 rounds, ~60 comments).
  41 valid findings addressed, 2 false positives dismissed. The
  experience prompted the workspace-level "Surface UX decisions
  before deciding" feedback memory — don't silently pick a side
  when a bot offers multiple reasonable UX options; ask first.

**Nothing to verify on the boat from today** — all changes are
operator-side / workflow-side. The verification happens when gabby
and salmon sync and we exercise the camera pipeline with the boat
powered up.

### 2026-04-24 — Pier session (actual)

Boat deployed at the pier, station-keeping next to it for sonar and
operator-station testing.

**VPN**: not working. (Details TBD — logging the fact now, diagnosis
pending.)

**ffmpeg image_transport**: looking great. The operator-side
verification queued yesterday is passing — `rqt_camera_grid`
subscribes to the `ffmpeg` transport directly and the video comes
through cleanly.

**`rqt_camera_grid`: crashed a few times while configuring the
layout.** Could not complete the intended 3x3 grid. Intended config:

| Row        | Pane 1        | Pane 2       | Pane 3        |
| ---------- | ------------- | ------------ | ------------- |
| Top        | port video    | fwd video    | starboard video |
| Middle     | port seg      | fwd seg      | starboard seg |
| Bottom     | johnny5       | aft video    | aft seg       |

The **port-seg and starboard-seg panes were the two that couldn't be
added** before the plugin crashed. Fwd seg + all three video streams +
johnny5 + aft pair apparently could be added. Repro details (sequence
of clicks, crash stack, ROS log) not yet captured — flagged for a
follow-up issue on `rqt_operator_tools` once we can get a stack /
console tail from salmon.

**Config dialog is a fixed size**, which clipped the topic dropdown
narrower than the actual topic names. Operator couldn't read full
topic paths while picking them — directly contributed to the
configuration difficulty and likely made the layout fight worse than
it had to be. Dialog should resize (and the combo's popup should be
as wide as the longest topic name, not capped to the combo's own
width). Separate bug from the crash; candidate for the same batched
PR.

#### Kongsberg M3 sonar — first-light config

M3 software up, **sonar is pinging** (first confirmed pings from the
loaner). Configuration is proving non-trivial:

- **Custom sensor flow is under-instrumented.** Trying to specify the
  sound-speed-sensor data format and the config UI is not surfacing
  enough debug info to tell whether a given format string is being
  accepted, rejected, or silently mis-parsed. Operator is flying
  blind on whether the SV input is actually landing.
- Actionable follow-up: capture which sensor flow / format paths
  were tried and which error (or silence) each produced, so we can
  either file with Kongsberg or, if the tooling is ours to extend,
  add the debug surface ourselves. (See workspace memory
  `project_kongsberg_m3.md` — M3 is Mesotech-lineage, not EM; no
  existing ROS driver applies yet.)

#### Hatch inspection at the floating dock

Broke off from station-keeping to run BizzyBoat down to the floating
dock. Tied up alongside **Ruby** (the support RHIB at the floating
dock) and opened the hatch to eyeball the bilge — **sanity check on
the sonar cable glands**, no specific leak suspected, just verifying
the new penetrations are sealing under use. (Water check result not
yet called out — if nothing further is said, assume dry.)

Returned to loiter afterward — currently **FCU-controlled loiter**,
not project11 autonomy.

#### Nav stack unhealthy — mission rejected

Tried to send a mission from project11 and the **nav stack is not
healthy at the moment**, so the mission didn't take. No diagnosis
yet — logging the fact. Follow-ups when we can look:

- Is this related to the earlier VPN issue (i.e. something upstream
  that couldn't reach gabby / the operator station), or is gabby's
  nav stack itself in a bad state?
- Which nav nodes are missing / faulted? (lifecycle states, TF
  health, costmap status — whichever tooling is on hand.)
- Does the FCU-loiter path still work cleanly while the project11
  nav side is down? (If so, good fallback; if not, that's a
  separate alarm.)

#### Manual control sanity check

Tested direct manual control with the **USB controller** — worked
fine. Returned the boat to loiter via the **RC controller**. So the
teleop path and the RC → FCU-loiter path are both healthy; the failure
is scoped to the project11 autonomy / nav stack, not to the underlying
vehicle control chain.

#### Screenshooter running on salmon

Activated the screenshooter on salmon to start capturing
operator-station state for the rest of the session.

#### Bag capture on gabby

Recording **2-minute bags on gabby** with video data included. Will
be useful for post-session playback to reproduce the `rqt_camera_grid`
crash offline on salmon and to have a reference sample of the ffmpeg
transport working end-to-end.

#### Recovery

Boat recovered. Session wrap-up.

**Outstanding from today — pick up post-session:**

- **VPN not working** — logged, no diagnosis yet.
- **Nav stack not healthy** — project11 mission dispatch rejected;
  FCU loiter and manual (USB/RC) paths are both clean, so the fault
  is scoped to the project11 autonomy side. No diagnosis yet.
- **`rqt_camera_grid` crashes during config** — port-seg and
  starboard-seg panes were the two that couldn't be added before the
  crash. Today's gabby bags should let us reproduce offline on salmon.
  Candidate for a follow-up issue on `rolker/rqt_operator_tools`.
- **`rqt_camera_grid` config dialog fixed size / narrow topic combo**
  — operator couldn't read full topic paths while configuring.
  Candidate for the same batched PR as the staleness fix (PR #26).
- **Kongsberg M3 custom sensor flow** under-instrumented for
  specifying the sound-speed-sensor data format. First pings
  successful; capture specific format attempts + errors next
  session so we can file with Kongsberg or extend our own tooling.
- **Staleness PR ([rolker/rqt_operator_tools#26](https://github.com/rolker/rqt_operator_tools/pull/26))**
  held in draft to batch with the other `rqt_camera_grid` fixes
  above.

**gitcloud push from gabby**: the on-boat agent pushed today's logs
to gitcloud at wrap-up, so `make sync` on salmon (and any other
gitcloud-connected machine) will pick them up.

**Staleness-tracker oversight — pre-deploy**: surfaced earlier today
that the new `rqt_camera_grid` staleness border was measuring arrival
time only, not `header.stamp`. That means a stream whose frames get
buffered upstream and arrive 15–30 s late would show a green/neutral
border while the image on screen reflects what the camera saw half a
minute ago — exactly the "trust this image or not" question the
border is supposed to answer, and it would have answered wrong.
Tracked in
[rolker/rqt_operator_tools#25](https://github.com/rolker/rqt_operator_tools/issues/25).
Fix implemented on branch `feature/issue-25`
([draft PR #26](https://github.com/rolker/rqt_operator_tools/pull/26)):
worst-of-both `max(arrival_age, stamp_age)` drives the border; invalid
stamps (zero or >60 s in the future) force Error + `[no stamp]` label
marker; pane label shows both ages (`rx Xs | hdr Ys`) so the operator
can see which side is driving. 19 gtests passing. **PR held open** to
batch with additional pier-session bug fixes before merging.
