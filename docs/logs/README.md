# Deployment logs (BizzyBoat)

Per-deployment, per-host log files. Each agent writes its own file; no
coordination needed for parallel agents on different hosts.

> **This is the BizzyBoat-specific overlay.** The generic lifecycle,
> file-layout, urgency-contract, and what-to-write guidance lives in
> the workspace deployment-mode docs:
>
> - **[ADR-0014: Deployment Mode](https://github.com/rolker/ros2_agent_workspace/blob/main/docs/decisions/0014-deployment-mode.md)** — the decision record
> - **[`.agent/knowledge/deployment_mode.md`](https://github.com/rolker/ros2_agent_workspace/blob/main/.agent/knowledge/deployment_mode.md)** — operational reference (urgency contract, lifecycle phases, log-naming, timestamps, tides format, three-state detection, project-config schema)
> - **[`.claude/skills/start-deployment/SKILL.md`](https://github.com/rolker/ros2_agent_workspace/blob/main/.claude/skills/start-deployment/SKILL.md)** — the skill that does setup
>
> Start a deployment with `/start-deployment` (Claude Code). The skill
> reads [`.agents/deployment.yaml`](../../.agents/deployment.yaml) in
> this repo, branches on dev vs field via `field_mode.sh`, and either
> creates / first-activates / resumes the deployment.

## BizzyBoat-specific overrides

These are the platform-specific deviations from the workspace convention.
Everything not called out below follows the workspace docs.

### File location

```
docs/logs/<year>/<YYYY-MM-DD>_<label>_logs.md
```

Year sub-directory under `docs/logs/` is required (matches the existing
2026/ tree). Workspace skill's `log_dir: docs/logs` config picks this up;
the year sub-dir is created by the skill if missing.

### Sample logs

- [`2026/2026-04-24_gabby_logs.md`](2026/2026-04-24_gabby_logs.md) — strong reference for a field-side host log on a live deployment day. Shows the topic-section structure, timestamped entries, operator-quoted observations, and Issues-encountered diagnoses.
- [`2026/2026-05-22_dev_logs.md`](2026/2026-05-22_dev_logs.md) — dev-side log for a recent deployment, including pre-flight section and wrap-up flow.

### User-curated reflective sections

In addition to the workspace urgency-contract guidance, BizzyBoat logs
carry two **user-curated** sections at the top, filled in at wrap-up:

- **Summary** — 2–3 sentences with strong operator voice; what a human would say if asked "what was today about?" with the benefit of hindsight. Agents draft; the operator's wording governs.
- **Lessons Learned** — durable operator-level take-home messages worth remembering across deployments. Short, generalisable, opinionated. Distinct from the Timeline (event narrative) and Issues encountered (failure-mode diagnoses).

Agents can propose entries for both, but the operator makes the call about what belongs and how it's worded.

### Task-specific deep-dive logs

When a single topic warrants its own running log (multi-hour sonar
bring-up, deep network-issue investigation), spin off a deep-dive
alongside the base host log:

```
docs/logs/<year>/<YYYY-MM-DD>_<label>_<topic>_logs.md
```

The base host log gets a short summary entry pointing at the deep-dive
rather than carrying the full detail. Link both from the deployment
issue's `## Logs` section.

### Per-deployment / per-host scope

Each deployment is one GitHub issue (`Deployment YYYY-MM-DD: <scope>`),
with one per-host log file per active host. Field-host pushes go to
gitcloud; dev integrates summaries into the dev log at wrap-up and
merges one PR (`Closes #N`). Convention established in PR #93; first
deployment under it was #94.

## Anti-pattern: the monolithic log

`docs/bizzyboat_deployment_log.md` (frozen, see header at the top of
that file) is what this convention replaces. It accumulated 5 weeks of
content into 3500 lines, mixing per-session detail with umbrella-style
milestones. Hard to navigate, hard to scope changes against, hard to
close. The per-deployment / per-host model fixes this by giving each
unit of work its own bounded artifact.

## Where the recorded data actually lands (gabby)

Deployment recordings are split across **three** locations — analysts
regularly conclude "no imagery was recorded" because they only looked in the
first one:

| Data | Location | Naming |
|---|---|---|
| Nav / actuator / telemetry bags | `~/data/logs/bizzyboat/<timestamp>/` | UTC |
| Camera imagery + local costmap | `~/data/logs/bizzy_images/*_ffmpeg_seg/` | **local time** |
| Sonar | `~/data/logs/bizzyboat_sonar/` | UTC |

Camera index order in the imagery recordings: **0 = port, 1 = forward,
2 = starboard, 3 = aft**.

Recording is selective by design (e.g. no DeltaT, image streams chosen per
deployment) — absence of a topic from the nav bag is not evidence it wasn't
recorded elsewhere, and vice versa.

## And on the operator station

`operator_core_launch.py` records its own bag, so a deployment's recordings
are not all on the boat:

| Data | Location | Naming |
|---|---|---|
| Operator diagnostics / commands / bridge stats / AIS | `~/data/logs/operator/<YYYY-MM-DD>/bags/operator_<timestamp>/` | local time |

**These bags contain identifiable third-party vessel data.** Since #464 they
record the shore AIS feed (`/ais/nmea`, `/ais/contacts` — MMSI, IMO,
callsign, vessel name, destination for craft that are not ours), and
`/rosout` has always carried decoded AIS in `ais_parser` warnings. There is
no project-wide retention policy yet; until there is, keep these bags on
project hosts, don't attach them to a public issue, PR, or third-party
service, and re-write a copy (`ros2 bag convert`, dropping `/ais/*` and
`/rosout`) before it leaves the project.
