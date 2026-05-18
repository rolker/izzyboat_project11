# BizzyBoat deployment log — salmon — 2026-05-01

**Host**: salmon
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Deployment**: [#121](https://github.com/rolker/unh_echoboats_project11/issues/121)

## Summary

Debugged a regression where CAMP stopped seeing nav streams from the
boat after the recent `udp_bridge` QoS rework was deployed. Diagnosis
points at `BEST_EFFORT` subscribers (CAMP's `NavSource`) failing to
match the bridge's `BEST_AVAILABLE` destination publishers under
`rmw_zenoh_cpp` 0.2.9. Workaround applied on the CAMP side: swapped
`SensorDataQoS()` to `SensorDataQoS().reliability_best_available()`
on all seven nav-source subscribers in `nav_source.cpp`. Pending
restart of CAMP to verify.

## 1. Symptom and graph snapshot

**2026-05-01T17:55-04:00** — CAMP on salmon (`/operator/camp`, PID 35757)
shows heartbeat / mission-status / platforms updating, but the
per-platform nav widgets are not displaying boat position, heading,
or speed. Operator-side `udp_bridge` topic statistics show the
expected boat traffic flowing (`/bizzy/marine/heartbeat`,
`/bizzy/hover_visualization`, `/bizzy/local_costmap/costmap`,
`/bizzy/local_costmap/published_footprint`, etc.) with zero send
failures — data is on the wire. But on the operator graph,
`ros2 topic info` reports **0 publishers** for each of the bridged
topics CAMP subscribes to:

| Topic | Pub count | Sub count |
|---|---|---|
| `/bizzy/marine/heartbeat` | 0 | 2 (camp, joy_to_helm) |
| `/bizzy/marine/status/mission_manager` | 0 | 1 (camp) |
| `/marine/platforms` | 0 | 1 (camp) |
| `/bizzy/received_global_path` | 0 | 1 (camp) |

Every `ros2` invocation also spams stderr with `rmw_zenoh_cpp`
errors:

```
Error setting QoS values from strings: unordered_map::at, at ./src/detail/liveliness_utils.cpp:340
service's implementation is invalid, at ./src/rcl/service.c:427
[ERROR] [rmw_zenoh_cpp]: Received liveliness token with invalid qos keyexpr
```

## 2. Root cause hypothesis

Recent `udp_bridge` merge (PR #12, feature/issue-11; commit `7580ce9`
"Per-topic QoS config + MessageInternal extension") changed
`UDPBridge::decodeData` from creating destination publishers with the
default `rclcpp::QoS(1)` (RELIABLE) to a per-topic resolver that
defaults to `qos.reliability_best_available()`. See
`udp_bridge/include/udp_bridge/qos_resolution.h:35-36` and
`udp_bridge/doc/qos_design.md:35-72`.

The package's design doc claims `rmw_zenoh_cpp` maps `BEST_AVAILABLE`
through Zenoh's session-level QoS negotiation. In practice, the
installed `ros-jazzy-rmw-zenoh-cpp 0.2.9-1noble` throws
`unordered_map::at` when encoding/decoding the `BEST_AVAILABLE`
liveliness keyexpr — so publishers created with that profile never
become graph-visible to other nodes. The bridge's own internal
publishers (`bridge_info`, `topic_statistics`, `/diagnostics`) use
plain RELIABLE QoS and **are** visible — confirming the regression
is specific to the new resolver path.

Asymmetric symptom that motivated the CAMP-side fix: heartbeat /
mission status / platforms (RELIABLE subscribers) appear to
intermittently bind to the BEST_AVAILABLE-keyexpr-broken publisher
under Zenoh, while `NavSource`'s `SensorDataQoS()` (BEST_EFFORT)
subscribers do not. The two QoS profiles take different code paths
through Zenoh's negotiation; under this rmw, only the RELIABLE side
seems to make it through.

## 3. Workaround on CAMP

**2026-05-01T17:58-04:00** — In `layers/main/ui_ws/src/camp/` (gitcloud
origin, branch `jazzy`):

- Edited `src/camp/nav_source.cpp` lines 40, 45, 50, 62, 67, 79, 84:
  changed `rclcpp::SensorDataQoS()` to
  `rclcpp::SensorDataQoS().reliability_best_available()` on all seven
  `create_subscription` calls (NavSatFix position, GeoPointStamped
  position, GeoPoseStamped position, Imu orientation,
  QuaternionStamped orientation, TwistWithCovarianceStamped velocity,
  TwistStamped velocity).
- `colcon build --symlink-install --packages-select camp` clean
  (38.5s) — only pre-existing unused-parameter warnings on
  `NavSource::paint`, untouched by this change.

Rationale: per `udp_bridge/doc/qos_design.md:60-65`,
`BEST_AVAILABLE` on the subscriber side matches whatever the
publisher offers (RELIABLE or BEST_EFFORT). With both ends
`BEST_AVAILABLE`, the contract falls back to BEST_EFFORT — same
effective semantics as the prior `SensorDataQoS()`, no regression
for non-bridged local sensor publishers.

**2026-05-01T18:05-04:00** — CAMP restarted. Nav widgets still not
populating. `/operator/camp` node info confirms the broader symptom:
**zero `NavSatFix` / `Imu` / `Twist*` subscribers** in the graph at
all. The CAMP-side QoS swap was a misdiagnosis: the issue isn't that
the subscriptions fail to *match* the publisher — it's that
`NavSource::trySubscribe` (`nav_source.cpp:27`) calls
`node_->get_topic_names_and_types()` and **only** creates a
subscription if the topic is already in the discovery graph. The
bridge's BEST_AVAILABLE publisher never appears in graph discovery
under `rmw_zenoh_cpp` 0.2.9, so NavSource's retry loop never finds
the topic and never subscribes.

CAMP edits left in place — they're harmless (BEST_AVAILABLE on the
sub side matches whatever the pub offers). The actual fix is on the
bridge.

## 4. Bridge fix — switch resolver default to RELIABLE

**2026-05-01T18:10-04:00** — In `layers/main/core_ws/src/udp_bridge/`
(gitcloud origin, branch `jazzy`):

- Edited `udp_bridge/include/udp_bridge/qos_resolution.h:35-37`:
  rearranged the reliability resolution so the default falls through
  to `qos.reliable()` instead of `qos.reliability_best_available()`.
  Added an explicit `"best_available"` opt-in case so per-topic config
  can still request that profile once the rmw is fixed. Header doc
  comment updated to explain the rmw_zenoh constraint.
- Updated three unit tests in `test/test_qos_resolution.cpp` that
  asserted the old BEST_AVAILABLE default
  (`DestinationDefault_EmptyEmptyZero`,
  `DestinationUnrecognizedReliabilityFallsBackToDefault`,
  `OldSenderAllFieldsMissing_LooksLikeDefaults`).
- Added an "Operational note (2026-05-01)" admonishment to the top of
  `udp_bridge/doc/qos_design.md` explaining the temporary default
  switch — the rest of the doc still describes the design intent.
- `colcon build --symlink-install --packages-select udp_bridge`
  clean (27.4s) — only pre-existing sign-compare warnings.
- Test suite has one pre-existing failure
  (`QosMatchingIntegration.BestEffortPublisher_DoesNotMatchReliableSubscriber`)
  that's a separate rmw-quirk concern from this change; resolver unit
  tests not re-run before push per Roland's direction.

Commit `e6670ed` on `jazzy` → pushed to gitcloud.

**Pending on operator**: Operator-side bridge process is the OLD
build (salmon binary refreshed but the running process hasn't been
restarted). Restart needed once Roland is ready.

**Pending on gabby**: Boat side needs `git pull && make build`
(or `colcon build --packages-select udp_bridge` in `core_ws`),
followed by bridge restart. Both sides need the new code because the
sender stamps the QoS strings into `MessageInternal` and the receiver
applies them — coordinated redeploy is the supported configuration.

## Files touched

- `layers/main/ui_ws/src/camp/src/camp/nav_source.cpp` — seven
  `SensorDataQoS()` → `SensorDataQoS().reliability_best_available()`
  (CAMP repo, **uncommitted** local change, harmless to leave).
- `layers/main/core_ws/src/udp_bridge/udp_bridge/include/udp_bridge/qos_resolution.h`
  — flipped destination publisher reliability default (committed,
  pushed to gitcloud as `e6670ed`).
- `layers/main/core_ws/src/udp_bridge/udp_bridge/test/test_qos_resolution.cpp`
  — three default-expectation tests updated (same commit).
- `layers/main/core_ws/src/udp_bridge/udp_bridge/doc/qos_design.md`
  — operational note added (same commit).

## 5. Session wrap-up

**2026-05-01T18:47-04:00** — Boat recovered. Session ending without
operational verification of the bridge fix on running hardware: the
fix was pushed to gitcloud but gabby's bridge would have needed
`git pull && colcon build && restart` to pick it up. Whether that
happened during this session is not visible from salmon.
Carry-forwards for the dev side to handle on the wrap-up PR:

- **Verify the fix on the next deployment** — restart bridges on
  both sides on the new code and confirm CAMP nav widgets populate
  for bizzy. If they still don't, NavSource's `trySubscribe`
  discovery-gate logic itself is worth revisiting (subscribe
  unconditionally and let ROS deliver when a publisher appears,
  rather than polling `get_topic_names_and_types`).
- **Address the pre-existing
  `BestEffortPublisher_DoesNotMatchReliableSubscriber` test
  failure** in `udp_bridge/test/test_qos_matching_integration.cpp` —
  under `rmw_zenoh_cpp` 0.2.9 the match succeeds, contradicting the
  matrix in `qos_design.md:60-65`. Either an rmw bug to upstream or a
  doc correction.
- **Decide the long-term policy on the BEST_AVAILABLE default** —
  this commit's flip to RELIABLE is operational. Once
  `rmw_zenoh_cpp` handles BEST_AVAILABLE keyexpr correctly, revert
  to `qos.reliability_best_available()` so the design doc's
  intended behavior is restored.
- **CAMP `nav_source.cpp` `SensorDataQoS().reliability_best_available()`
  edits** are uncommitted on salmon. Harmless either way; if useful
  longer-term they can be picked up via `import-field-changes` from
  salmon's working tree.

End of salmon session.
