# BizzyBoat deployment log — gabby — 2026-05-22

**Host**: gabby
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7 (1M context))
**Mode**: field (gitcloud origin)
**Deployment**: git-bug `1e4fe7d` — *Deployment 2026-05-22: battery drain to LVD + perception #14 in-water + costmap-over-Starlink* (GitHub link added dev-side at wrap-up)

## Summary

*To be filled at wrap-up (user-curated).*

## Lessons Learned

*To be filled at wrap-up (user-curated).*

## 1. Session start — git-bug pull + field-side state confirmation

**2026-05-22T15:35-04:00** — Roland asked whether today's deployment
issue was visible. `git bug bug --label deployment --by edit` returned
only the 2026-05-21 entry (`7d5b52c`, still showing open locally); no
2026-05-22 entry yet. Same SSH_AUTH_SOCK gap as 2026-05-19 / 2026-05-21
sessions — `git bug pull` exits with
`Error: error creating SSH agent: "SSH agent requested but SSH_AUTH_SOCK not-specified"`.
The persistent fix (systemd user `ssh-agent.service` / keychain) noted
as follow-up after the last two deployments still hasn't landed.

**2026-05-22T15:36-04:00** — Roland confirmed: apply the same inline
workaround. Same recipe as 2026-05-21 §1:

```bash
eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519_gitcloud
git -C <repo> bug pull
ssh-agent -k
```

First pull "already up-to-date" — confirmed today's deployment issue
hadn't been published to gitcloud yet from dev side. Roland asked to
verify the local repo state before pulling again.

**2026-05-22T15:38-04:00** — `git status` on field-mode project repos
turned up two uncommitted changes from the morning's prep:

- `unh_echoboats_project11/bizzyboat_project11/config/bizzyboat.yaml` —
  restored `oak_aft_ffmpeg` to the VPN nodes list and `topics_list`;
  removed the explanatory comments about the 2026-05-19 uplink-budget
  drop. Roland: aft was re-added to see how it'd fare on the pier after
  the udp_bridge work; stable, commit it.
- `seafloor_echoboat_project11/echoboat_project11/config/nav2_params.yaml` —
  restored the full 4-instance `sea_surface_layer` list
  (port/starboard/aft); removed the 2026-05-21 forward-only workaround
  comments. Roland: `unh_marine_perception#6` is fixed, commit it.

Committed with agent identity (`-c user.name=... -c user.email=...` per
[AGENTS.md](../../../../../../../../AGENTS.md) — env-var script doesn't
propagate across each Bash invocation's fresh subshell):

- `unh_echoboats_project11` `a83b416` — *bizzyboat.yaml: restore
  oak_aft_ffmpeg to VPN*
- `seafloor_echoboat_project11` `bf4da10` — *nav2_params.yaml: restore
  full 4-layer sea_surface_layer list*

**2026-05-22T15:40-04:00** — Push to gitcloud rejected on
`unh_echoboats_project11` — salmon agent had pushed
`85585e5 docs/logs: 2026-05-21 salmon deployment log` in the meantime.
No file conflict (different paths). Rebased local commit onto
`origin/jazzy`; new SHA `ac77860`. Push succeeded for both repos:

- `unh_echoboats_project11`: `ac77860` → `origin/jazzy`
- `seafloor_echoboat_project11`: `bf4da10` → `origin/jazzy`

**2026-05-22T15:42-04:00** — Ran `make sync` from the workspace root
(with ssh-agent inline). All repos up-to-date; `ros2_network_monitor`
picked up an update. No other workspace movement.

**2026-05-22T15:44-04:00** — Second `git bug pull` after sync surfaced
the day's deployment issue: `1e4fe7d` — *Deployment 2026-05-22: battery
drain to LVD + perception #14 in-water + costmap-over-Starlink*.
Reviewed in full; this log header references it. Per
[[feedback_deployment_issue_readonly]] the issue is read-only from
gabby — all observations land here.

### Field-side reconciliation note for wrap-up PRs

Two of the three "field A/B" items called out in the deployment issue
are already on `origin/jazzy` (gitcloud) as of `ac77860` and `bf4da10`:

- `seafloor_echoboat_project11` `#21` workaround revert — `bf4da10`.
- `unh_echoboats_project11` `bizzyboat.yaml` `oak_aft_ffmpeg` VPN
  restore — `ac77860`.

The third — the 4:3 preview+video A/B on `oak_cameras_launch.py` — has
not been applied yet (pending operator go-ahead during pre-launch).
