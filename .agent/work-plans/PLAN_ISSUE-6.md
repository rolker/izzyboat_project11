# Plan: Generate a network diagram

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/6

## Context

`docs/izzyboat_network.md` (produced by issue #2) documents the full IzzyBoat
network setup including subnets, devices, VPN NETMAP scheme, and router
configuration. This issue produces a Graphviz DOT diagram that illustrates the
key concepts visually: the two physical networks (boat and operator), the WiFi
backhaul link, and the VPN path with its NETMAP address translation.

The diagram intentionally uses role names (robot computer, Windows PC) rather
than hostnames so it remains accurate as hardware changes.

## Approach

1. **Create `docs/izzyboat_network.dot`** — Graphviz DOT source with:
   - `rankdir=LR` (operator left, boat right)
   - `cluster_operator`: operator LAN `192.168.13.0/24` — operator laptop,
     Windows PC (survey monitoring), development laptop, operator router
   - `cluster_boat`: onboard LAN `192.168.12.0/24` — robot computer (Linux),
     Windows PC, camera, POS MV, boat router; plus DeltaT sonar on its own
     subnet `192.168.0.0/24`; ArduPilot FCU shown as a USB edge on the robot
     computer (no IP)
   - WiFi backhaul `172.16.12.0/24` shown between the two routers, styled
     lightly as background infrastructure (dashed or grey)
   - VPN path shown arcing through an internet/cloud node, annotated with the
     NETMAP subnets: boat devices reachable at `192.168.14.x`, operator devices
     at `192.168.15.x`

2. **Generate `docs/izzyboat_network.svg`** — render the DOT source:
   ```bash
   dot -Tsvg docs/izzyboat_network.dot -o docs/izzyboat_network.svg
   ```
   Commit both source and generated SVG.

3. **Link from `docs/izzyboat_network.md`** — add a section near the top
   referencing the diagram:
   ```markdown
   ## Network Diagram
   ![IzzyBoat network diagram](izzyboat_network.svg)
   ```

4. **Link from `README.md`** — add or create a README at the repo root with
   a reference to the diagram and the network doc.

## Files to Change

| File | Change |
|------|--------|
| `docs/izzyboat_network.dot` | New — Graphviz DOT source |
| `docs/izzyboat_network.svg` | New — generated SVG (committed alongside source) |
| `docs/izzyboat_network.md` | Add diagram reference near top |
| `README.md` | Add or create; reference diagram and network doc |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| Only what's needed | One diagram, two small doc edits — no scope beyond the issue |
| A change includes its consequences | Both source and rendered output committed; referenced from both doc and README |
| Improve incrementally | Single PR, bounded change |
| Human control and transparency | Diagram makes the NETMAP addressing scheme explicit so operators understand path selection |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| 0002 — Worktree isolation | Yes | Worktree `feature/issue-6` created for this work |
| 0008 — ROS 2 conventions | No | Documentation only, no packages |

## Consequences

| If we change... | Also update... | Included in plan? |
|---|---|---|
| `docs/izzyboat_network.dot` | Regenerate `izzyboat_network.svg` | Yes — step 2 |
| Diagram content | `izzyboat_network.md` and `README.md` references | Yes — steps 3 & 4 |

## Open Questions

- None — format (Graphviz DOT), layout (side-by-side LR), content scope, and
  output placement (both network doc and README) are all decided.

## Estimated Scope

Single PR.
