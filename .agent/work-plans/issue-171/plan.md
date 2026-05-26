# Plan: Operator annunciator coverage gaps (#171) — field-execution prep

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/171

## Context

The operator annunciator (`bizzyboat_project11/config/bizzyboat_operator_annunciator.yaml`)
currently shows only network/link indicators — no battery, sound-speed, or FCU-system
health. During the 2026-05-22 drain-to-LVD test the operator got no battery, SV-failure,
or FCU-error warning. This is config-only: add three indicators to the operator config
(+ a sound-speed indicator to the boat config).

**Execution mode:** intended for **field execution during a deployment** — the indicators
key on exact diagnostic names / KeyValue casing / tuned thresholds that must be confirmed
against the live bus (the #173/#162 "don't guess the string" lesson). This file is the
prep so field time is verify + tune + commit, not authoring from scratch.

## Field verification checklist (run on the operator station with the stack up)

```bash
ros2 topic list | grep -i -E 'battery|diagnostic'      # confirm forwarded names
ros2 topic echo /diagnostics --once                    # read exact DiagnosticStatus.name + KeyValue keys
```
Confirm and record:
- [ ] Battery: exact `Voltage` KeyValue **casing** on `mavros: Battery` (engine fails loud as `Voltage?`/ERROR on mismatch, not silent green).
- [ ] FCU errors: the `mavros: System` status name (this is the one carrying "Battery N is low" + FCU ERRORs; `mavros: Heartbeat` is already the boat "FCU" row).
- [ ] Sound speed: the **exact** diagnostic name `sound_speed_bridge` publishes (and that it publishes one at all — see #163). Use `match_mode: substring` if the name has a host/instance suffix.
- [ ] Op-side **republished** name of `/bizzy/mavros/battery` — only needed for the topic-source battery fallback below.

## Indicators to add

**Operator config** (`bizzyboat_operator_annunciator.yaml`) — append after the link block:

```yaml
  # --- Boat health (forwarded over the link) ---
  - name: Battery            # PRIMARY: needs rqt_operator_tools#35 deployed to op station
    source: diagnostics
    diagnostic_name: "mavros: Battery"
    value_key: Voltage       # confirm casing live
    format: "{:.2f} V"
    thresholds:
      warn: "value < 23.0"   # FCU BATT_LOW_VOLT; tune vs Torqeedo Power 24-3500
      error: "value < 21.5"  # FCU BATT_CRT_VOLT
  - name: FCU System
    source: diagnostics
    diagnostic_name: "mavros: System"
    format: "{}"
  - name: Sound Speed
    source: diagnostics
    diagnostic_name: "sound_speed_bridge"
    match_mode: substring
    format: "{}"
    stale_timeout: 10.0
```

**Boat config** (`bizzyboat_annunciator.yaml`) — add the same `Sound Speed` indicator
(per #171, SV indicator on both boat + operator).

## Battery indicator: #36 dependency + fallback

- **Primary (above):** `source: diagnostics` + `value_key`/`thresholds` — consistent with the
  boat-side #162 fix, uses the known `mavros: Battery` name. **Requires the engine change
  [rqt_operator_tools#35](https://github.com/rolker/rqt_operator_tools/pull/36) deployed to
  the operator station's `rqt_operator_tools`.**
- **Fallback if #36 isn't deployed yet:** `source: topic` on the forwarded BatteryState —
  works on the *current* engine (topic-source value thresholds already exist). Needs the
  op-side republished topic name (checklist item) + `msg_type: sensor_msgs/msg/BatteryState`,
  `value_field: voltage`, same `thresholds`. FCU-System and Sound-Speed indicators have **no**
  #36 dependency either way.

## Field-mode flow (if the op-station checkout is gitcloud-origin)

Confirm mode first: `.agent/scripts/field_mode.sh --describe <repo>`. If field mode:
edit + commit + push to gitcloud directly (no worktree/PR), then reconcile to GitHub
post-deployment via `/import-field-changes` — the PR is still the quality gate. If the
op-station checkout is GitHub-origin, it's dev mode → use this branch / a normal PR.

## Consequences

| If we change... | Also update... | Status |
|---|---|---|
| `bizzyboat_annunciator.yaml` (add SV row) | overlaps #179's battery-row edit in the same file | Different rows; rebase/merge-order with #179 |
| operator battery uses `value_key`+thresholds | gated on rqt_operator_tools#35 deploy | Fallback documented above |

## Open Questions

- [ ] Battery threshold values: 23.0/21.5 (FCU params, matches #162) vs #171's suggested ~22.5/21.5 — tune against pack behavior in the field.

## Estimated Scope

Single config PR (or one field commit + reconciliation PR). No code; depends on #36 only for
the diagnostics-source battery variant.
