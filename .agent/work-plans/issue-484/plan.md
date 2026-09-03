# Plan: bizzyboat bridge config: coverage_catalog needs durability: transient_local, or the latched catalog is relayed VOLATILE

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/484

## Context

`bizzyboat_project11/config/bizzyboat.yaml` relays `coverage_catalog` to the
operator station over both the wifi (`udp_bridge` remote `bizzy`, line 284)
and vpn (line 542) connections, at neither of which does the topic entry set
`durability`. `udp_bridge` defaults an unset topic to `VOLATILE`
(`udp_bridge/doc/qos_design.md` § Durability), but `cube_bathymetry_node.cpp`
publishes the catalog as `rclcpp::QoS(1).transient_local().reliable()` — a
late-joining `TRANSIENT_LOCAL` subscriber (CAMP's `sonar_live_cache_layer`,
`marine_web_view/coverage_renderer.py`) never matches a relayed `VOLATILE`
publisher and gets nothing until the next live message.

Both consumers broke on the water (2026-08-26 Appledore, `#467`) and were
patched in their own repos by downgrading the *subscriber* to `VOLATILE` —
a workaround, not the fix; both PRs say so explicitly. The correct fix is
one config value, set at both call sites (the parameter is per-connection,
and wifi/vpn already switch active paths between runs), in this repo.

`review-issue`'s prior entry (`.agent/work-plans/issue-484/progress.md`,
`## Issue Review`) source-verified every claim in the issue and flagged
three actions this plan folds in: (1) the fix needs an actual bench/field
latch-delivery observation, not just a source trace, (2) the coupled reverts
in `unh_marine_autonomy#363` and `camp#220` should be cross-linked as
follow-ups, (3) the rollout note must say explicitly that the
**operator-station** `udp_bridge` process needs the restart (it caches the
destination publisher's QoS on first message; the boat-side process does
not need one).

## Approach

1. **Add `durability: transient_local` to both `coverage_catalog` entries**
   in `bizzyboat_project11/config/bizzyboat.yaml` — line ~284 (wifi
   connection) and line ~542 (vpn connection). Exact key/value, verified
   against `udp_bridge`'s `qos_resolution.h`: `durability: transient_local`
   (underscore, not hyphen — a typo silently falls back to `VOLATILE` with
   no error, per the resolver's `else` branch, so this is worth a literal
   post-edit grep, not just a visual check).
2. **Add a short inline rationale comment at both edit sites**, matching
   this file's established convention (every other special-cased entry in
   the file — e.g. the `local_costmap_windowed` throttle comment at line
   ~274, the coverage_tiles link-budget comment at line ~535 — carries one).
   Reference #484 and state the late-joiner intent in one or two lines; keep
   it short, this is a one-line config fix, not a new subsystem.
3. **State the rollout requirement explicitly in the PR description**: the
   **operator-station** `udp_bridge` process must be restarted after this
   config lands (destination publishers are created once and cached per
   topic — `udp_bridge.cpp::publishItem` — so an already-running process
   keeps the old `VOLATILE` publisher until restarted). The boat-side
   process does not need a restart for this change.
4. **Cross-link the coupled reverts** in the PR body as tracked follow-ups
   (not folded into this PR — different repos, different maintainers'
   review queues):
   - `rolker/unh_marine_autonomy#363` — revert `coverage_renderer.py`'s
     `VOLATILE` downgrade back to `TRANSIENT_LOCAL` once this lands.
   - `rolker/camp#220` — same, for `sonar_live_cache_layer.cpp`.
5. **Verification (operator step, not implementation)**: because the fix is
   config-only and the change under test is a *relay durability behavior*
   spanning two live processes across a wifi/cell link, this cannot be
   exercised by the implementing agent — it requires the boat and/or an
   operator-station bridge process, and workspace rules forbid
   administering field/remote hosts. The PR's test plan records this as an
   **operator-performed** step, described precisely enough to execute
   without design judgment:
   - After deploying the config change and restarting the
     operator-station `udp_bridge`, start (or restart) a
     `TRANSIENT_LOCAL` subscriber to `coverage_catalog` at the operator
     station (e.g. CAMP, or `ros2 topic echo` with matching QoS) *before*
     the boat publishes its next catalog message.
     Confirm it receives the most recently published catalog immediately
     on subscribe (the "late-joiner" case), not just on the next live
     publish. Do this once on wifi and once on vpn (the connections are
     configured independently).
   - Negative check: confirm `ros2 topic info -v coverage_catalog` (or
     equivalent) at the operator station reports the relayed publisher's
     durability as `TRANSIENT_LOCAL`, not `VOLATILE`, on both paths.

## Files to Change

| File | Change |
|------|--------|
| `bizzyboat_project11/config/bizzyboat.yaml` | Add `durability: transient_local` + rationale comment to the `coverage_catalog` entry at the wifi connection (~line 284) and the vpn connection (~line 542) |
| `.agent/work-plans/issue-484/progress.md` | `## Plan Authored` entry (this step) |

No source code changes — `udp_bridge` already implements and documents the
`durability` parameter; no package in this repo needs a code change.

## Principles Self-Check

| Principle | Consideration |
|---|---|
| Human control and transparency | Two-line diff, clearly rationale-commented at both sites; PR body states the rollout requirement (operator-station restart) explicitly so nobody applies the config and assumes it took effect immediately |
| A change includes its consequences | The coupled reverts (autonomy#363, camp#220) are a real consequence of this landing, correctly left out of *this* PR's diff (different repos) but cross-linked in the PR body per the Issue Review's Action item, so they don't quietly become permanent |
| Only what's needed | Config-value-only change; no new tooling, no new tests added to this repo (the durability *matching*/latch test gap belongs to `udp_bridge`, already tracked as `udp_bridge#79`, correctly out of scope here) |
| Test what breaks | Acceptance includes an explicit bench/field latch-delivery observation (Approach step 5) rather than resting on the source trace alone, per AGENTS.md's Quality Standard ("fix it completely... check the lifecycle transition") |
| Workspace vs. project separation | Deployment-specific bridge config stays in `unh_echoboats_project11`; no workspace-repo change |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| 0008 — ROS 2 conventions | No | Value-only config edit to an existing, already-documented `udp_bridge` parameter; no package/launch structural change |

## Consequences

| If we change... | Also update... | Included in plan? |
|---|---|---|
| `coverage_catalog` durability on wifi + vpn connections | `unh_marine_autonomy#363` (`coverage_renderer.py` VOLATILE downgrade) | No — cross-linked as a tracked follow-up in the PR body (separate repo, separate PR/review) |
| `coverage_catalog` durability on wifi + vpn connections | `camp#220` (`sonar_live_cache_layer.cpp` VOLATILE downgrade) | No — cross-linked as a tracked follow-up in the PR body (separate repo, separate PR/review) |
| `udp_bridge` durability matching/latch-delivery test coverage | `udp_bridge` test suite | No — already tracked as `rolker/udp_bridge#79`, correctly out of this issue's scope (mechanism repo, not this config repo) |

## Documentation & Instruction Impact

- **Stale docs** (must land in this PR): None — `udp_bridge/doc/qos_design.md`
  already documents the `durability` parameter and its default correctly;
  this PR only exercises the already-documented mechanism. No documentation
  in this repo describes the `coverage_catalog` topic's QoS today (it's a
  bare config entry), so nothing here goes stale.
- **Agent-instruction candidates** (proposals only — operator decides): The
  "receiving bridge caches the destination publisher's QoS on first message;
  a config change alone does not re-create it, the process must restart"
  behavior is a recurring field trap (the issue cites a near-identical
  2026-09-01 incident). Worth a one-line candidate for
  `.agent/knowledge/` or this repo's `.agents/README.md` Common Pitfalls
  section flagging "after any udp_bridge topic-QoS config edit, restart the
  *receiving* bridge process, not just redeploy the config" — proposed, not
  applied in this PR.

## Open Questions

- None — this is a source-verified, source-and-field-evidenced two-line
  config fix; the only genuinely open item (bench/field latch-delivery
  verification) is scoped as an operator-performed acceptance step in
  Approach step 5, not a design decision.

## Estimated Scope

Single PR. Config-only diff (2 keys + 2 comments) plus a PR body that
cross-links the coupled-repo follow-ups and states the rollout/restart
requirement and verification steps explicitly.
