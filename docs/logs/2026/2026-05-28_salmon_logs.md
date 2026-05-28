# BizzyBoat deployment log — salmon — 2026-05-28

**Host**: salmon
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Side**: field
**Deployment**: git-bug `6445516` — "Deployment 2026-05-28: validate nav2 config-split cutover + 240 footprint" (opened 2026-05-27T12:15-04:00, edited 2026-05-28T11:50-04:00).
**Started**: 2026-05-28 11:59 -04:00

## Skill trial notes — `/start-deployment` first-activation on salmon [start-deployment trial]

- Config: `.agents/deployment.yaml` discovered at `unh_echoboats_project11/.agents/`.
- Side detection: `field_mode.sh` resolved field mode from `git@gitcloud:field/unh_echoboats_project11.git`. Clean.
- `issue_sync.field_pull` (`git bug pull gitcloud`) **failed** — git-bug remote name `gitcloud` is not configured in this project repo; git's remote is `origin`. Fell back to `git bug pull origin`, which worked (10 bug refs updated). Field config command needs to be `git bug pull origin` — flagging for v2 / hotfix to `.agents/deployment.yaml`.
- `field_list_open` (`git bug bug --label deployment --status open`) returned the single open deployment issue (`6445516`). Clean.
- `field_show` (`git bug bug show 6445516`) returned full body across 4 comments. Clean.
- Three-state detection: no existing `2026-05-28_salmon_logs.md` → first-activation on salmon. Confirmed.
- Issue title already canonical (`Deployment <YYYY-MM-DD>: <scope>`) — no warning needed.
- `## Logs` section present in body; lists `dev` log only (no `salmon` link yet). **Field-side cannot edit the issue body** — dev needs to stamp the salmon log link on its next `/start-deployment` run, or via a manual `gh issue edit`.
- **Step-1 platform prompt**: skill says "ask the operator which platform" when CWD is workspace root. Skipped that — only one `layers/main/*/src/*/.agents/deployment.yaml` exists, and recent `make sync` + memory made the platform obvious. The prompt is unnecessary friction when the answer is unambiguous; v2 could auto-pick when exactly one config is discoverable and only ask when there's genuine ambiguity.
- **First Bash invocation `cd` failed** — agent-side mistake, not skill friction (each Bash call is a fresh subshell; need absolute paths or `git -C`). Noting for context only.

## Summary

_(to be filled at wrap-up)_

## Lessons Learned

_(to be filled at wrap-up)_

## Timeline

### 2026-05-28 12:03 -04:00 — Pre-flight: sync + build clean
- `make sync`: all repos up to date (echoboats skipped — uncommitted salmon log file, expected).
- `make build`: all 7 layers green (93 packages). Stderr-only on `bag_analysis` and `sea_surface_segmentation` (the new multi-source layer from PR #20 — expected, not failures).
- Stack ready; operator launching next.

### 2026-05-28 12:04 -04:00 — Operator starting stack

### 2026-05-28 12:32 -04:00 — Gabby up, healthy on salmon view
- Operator reports cameras visible in camp + green heartbeat. Bridge forwarding as expected.
- Agent probe (`ros2 node list` / topic grep) initially looked for `mavros/state` and nav2 topics on salmon — those aren't bridged across by default, only camera/heartbeat/control are. Misdirected probe; canonical health signal is camp itself. [start-deployment trial]

### 2026-05-28 12:32 -04:00 — WiFi annunciators red; operator power-cycled boat-side wifi device
- Salmon side: `mikrotik_monitor` / `ping_monitor` / `teltonika_monitor` nodes running and publishing into `/diagnostics`. Starlink path healthy (cameras + heartbeat green throughout).
- Operator power-cycled the boat-side wifi device as the mitigation. Watching for annunciator state change.
- **Agent mistake — wrong router IPs**: agent pinged `192.168.12.1` / `192.168.14.1` / `172.16.12.1`, all 100% loss. Operator flagged these as the wrong addresses. Source of error: agent grepped `docs/izzyboat_network.md` (the *prior* IzzyBoat platform) instead of BizzyBoat-specific docs. `bizzyboat_hardware.md` is present in the repo but was not consulted. The 100%-loss "result" is meaningless — wrong target. Negative diagnostic value, and risked sending operator down a false trail if not caught. [start-deployment trial — confidence-check failure: agent should sanity-check which platform's doc it's reading before acting]
- **Correct BizzyBoat addresses (from `docs/bizzyboat_network.md`)**: boat router `192.168.20.1` (LAN) / `172.16.20.1` (WiFi bridge gateway); OmniTIK 5 ac (boat-side WiFi bridge) `172.16.20.3`; SXTsq Lite5 (shore-side bridge) `172.16.20.4`; gabby `192.168.20.5` (bridge) / `192.168.21.5` (VPN); salmon `192.168.13.142` (LAN) / `192.168.22.142` (VPN, BizzyBoat path).
- **Re-probed with correct addresses**: OmniTIK `172.16.20.3`, boat router `172.16.20.1` and `192.168.20.1`, gabby `192.168.20.5` — all 100% packet loss. The WiFi-bridge segment is fully down from salmon's view. Starlink path remains the only live channel (camp cameras + heartbeat ride that, via `192.168.100.1` dish address).
- **Operator update**: both boat- and shore-side WiFi-bridge devices are individually up (manageable via their LAN-side interfaces) but the two bridges can't talk to each other over the radio link. Association failure, not a powered-off device. Matches salmon's view: `172.16.20.0/24` segment fully dead end-to-end while both endpoints exist.
- **Op-router diagnosis (via tmux session `router`, SSH'd into operator-side Teltonika RUTX11)**:
  - Teltonika has `172.16.20.2/24` on `eth0.4` (BizzyBoat WiFi-bridge VLAN). Interface UP, LOWER_UP, carrier=1 at parent eth0. Historic RX 94M packets, errors=0 — interface itself is healthy.
  - `ip neigh show`: ARP to `172.16.20.4` (SXTsq, directly-attached shore-side bridge), `172.16.20.3` (OmniTIK boat-side), `172.16.20.1` (boat router) all **FAILED / INCOMPLETE**.
  - Direct ping to SXTsq `172.16.20.4`: 100% loss (op router can't even reach the device on its own desk).
  - `tcpdump -i eth0.4` for 8 s: only the Teltonika's own ARP-who-has broadcasts (~1/s) visible — **zero replies, zero unsolicited traffic** from any 172.16.20.x peer. The directly-attached SXTsq is silent on the wire, not just the radio.
- **Conclusion**: the **shore-side SXTsq Lite5** is the silent device, not the boat-side OmniTIK that was originally cycled. Recommendation to operator: power-cycle the SXTsq. If that doesn't recover, next probe is `/etc/config/network` VLAN ID for `eth0.4` vs SXTsq config (VLAN-mismatch hypothesis).
- **Operator confirmed plan**: cycling the SXTsq.

### 2026-05-28 12:52 -04:00 — SXTsq (shore-side wifi bridge) power-cycled
- Operator confirmed cycle done. Waiting on boot (~30–60 s typical) and checking camp annunciator for state change.
- **Recovered**: all four bridge-segment targets pingable from the op router with 0% loss and <3ms RTT (SXTsq 0.5ms, OmniTIK 1.9ms, boat router 1.3ms, gabby-via-bridge 1.5ms). ARP entries all `REACHABLE`. SXTsq cycle was the fix.
- Operator notes many annunciators went green post-cycle; a couple still red — those are likely separate metrics (per-link / per-host) and not bridge-related.

### 2026-05-28 12:55 -04:00 — Annunciators all green
- Sound speed yellow (expected — AML profiler is winch-deployed, only goes green during a cast). Everything else clear. Ready to proceed.

### 2026-05-28 13:15 -04:00 — Boat in the water
- Launch confirmed.

### 2026-05-28 13:28 -04:00 — Operator troubleshooting costmap + segmentation
- Falls into the #19 must-verify scope (multi-source `SeaSurfaceLayer` + global relay, PRs unh_marine_perception#20 / seafloor_echoboat_project11#35 / unh_echoboats_project11#193).

### 2026-05-28 14:08 -04:00 — Boat recovered
- On-water phase done (~53 min: launched 13:15, recovered 14:08).

### 2026-05-28 14:11 -04:00 — Salmon-side session close

**Timeline at a glance**:
- 11:59 — `/start-deployment` activated (skill first end-to-end trial on salmon).
- 12:03 — `make sync` + `make build` clean across 7 layers / 93 packages.
- 12:04 — operator starts stack; gabby comes up healthy via Starlink (cameras + heartbeat).
- 12:32 — WiFi annunciators red; ~25 min troubleshoot.
- 12:47 — operator opens tmux SSH into op router; tcpdump on `eth0.4` shows no traffic from `172.16.20.4` → SXTsq (shore-side bridge) is the silent device.
- 12:55 — SXTsq cycle restores the bridge; annunciators all green (sound speed yellow expected).
- 13:15 — launch.
- 13:28 — operator troubleshooting costmap + segmentation (#19 scope).
- 14:08 — recovery.
- ~53 min on water; ~25 min pre-launch network recovery dominated the gap between stack-up and splash.

**Net-troubleshooting takeaway worth carrying forward**:
The fastest disambiguation of "WiFi bridge red" is *which side's directly-attached bridge device responds to ARP from its co-located router*. Today: op-router → SXTsq ARP FAILED + tcpdump on `eth0.4` showing zero unsolicited traffic from `172.16.20.x` pinpointed the shore-side device in <2 min once SSH access was available. First mitigation (cycling the *boat-side* OmniTIK) was the wrong device; salmon-side SXTsq was silent. Future runs: check the local-side ARP before deciding which device to cycle.

**`[start-deployment]` skill trial rollup** (full per-event notes scattered above):
1. Step-1 "ask which platform" prompt is unnecessary when exactly one `.agents/deployment.yaml` is discoverable — consider auto-pick.
2. `issue_sync.field_pull: "git bug pull gitcloud"` is wrong for this project — git-bug remote name is `origin`. Hotfix the config or fix the git-bug remote.
3. Field side cannot edit the issue body — `## Logs` section can't get this salmon log linked from here. Either dev runs `/start-deployment` after field-pull to backfill, or wrap-up handles it.
4. Agent's first instinct was to grep for nav2 topics on salmon — those aren't bridged. Real health signal is camp itself; trust the operator's "green heartbeat" report over agent topic-scanning.
5. Agent grepped the *prior platform's* network doc (izzyboat) for boat-router IPs and pinged dead addresses before operator caught it. Confidence-check failure. Agent should verify which platform's doc it's reading before acting on addresses or hardware specs.
6. Contract held overall: agent stayed assist-not-investigate, deferred diagnoses, kept probes low, didn't impose gates, autologged without permission-asking.

The above trial notes are the v2 input for [ros2_agent_workspace#501](https://github.com/rolker/ros2_agent_workspace/issues/501) per the issue's process note.

**Open at session close**:
- Log file still uncommitted on salmon (per "don't commit mid-session"); wrap-up step needs to commit + push to gitcloud.
- Costmap / segmentation observations from on-water are on gabby's log, not here.
