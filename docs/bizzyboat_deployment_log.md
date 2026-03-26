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
| [unh_echoboats_project11#17](https://github.com/rolker/unh_echoboats_project11/issues/17) | Bootstrap and build on gabby | **blocked** | Gitcloud raw file URL for bootstrap.yaml returns 404. PR [#22](https://github.com/rolker/unh_echoboats_project11/pull/22) |

### Parallel Work

| # | Task | Status | Notes |
|---|------|--------|-------|
| [unh_echoboats_project11#13](https://github.com/rolker/unh_echoboats_project11/issues/13) | bizzyboat_project11 package | not started | |
| [CCOMJHC/ccomjhc_project11#6](https://github.com/CCOMJHC/ccomjhc_project11/issues/6) | Site-specific config | not started | |
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
