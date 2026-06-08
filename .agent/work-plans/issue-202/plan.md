# Work Plan — Issue #202: BizzyBoat operator manual (student-facing)

Issue: https://github.com/rolker/unh_echoboats_project11/issues/202

## Context & forcing function

Part of the Summer Hydro 2026 documentation push. Driver: **June 4 dev-freeze /
class start**; audience is **rotating student-operator cohorts** who will bring
the boat up, run surveys, and hand off. Three separate manuals total (this one,
CAMP `rolker/camp#61`, and the framework guide `rolker/unh_marine_autonomy#132`,
already drafted as PR #133). Decisions below were agreed with Roland 2026-06-01.

## Audience & scope decisions

- **Audience**: student operators (not engineers). Understanding-oriented.
- **Defer hardware/physical operation to the EchoBoat 240 vendor manual.** This
  manual covers the *project11 autonomy layer on top of the boat*, not the hull,
  thrusters, charging hardware, etc.
- **OUT of scope (explicit):**
  - **Launch & recovery** — site-specific (BizzyBoat launches by crane at Judd
    Gregg pier; that detail is not durable repo doc material).
  - **Multi-operator handoff section** — dropped.
  - Engineer setup/deployment — lives in the deployment guide (#18), not here.
  - Any mission-specific (site/customer) detail.
- **Troubleshooting = link to the framework guide**, not a symptom→cure cookbook.
  Roland: "a dive into the framework instead of symptom→cure."

## Outline

1. **Overview & safety** — BizzyBoat = EchoBoat 240, uncrewed, RC-override-anytime.
   Defer physical/hardware operation to the EchoBoat 240 manual.
2. **Readiness checks** — power state; battery charge (**charged in place, NOT
   field-swappable** — recharge-to-full is the cohort-cadence constraint); GPS/NTRIP
   lock; comms link check.
3. **Starting the stack** — power-on sequence; `gabby` (Linux/ROS) + `mercat`
   (Windows/QINSy) roles; confirming the boat is up (it should appear in CAMP —
   see framework guide §3 on `/marine/platforms`).
4. **Driving & autonomy** — manual joystick; **Standby** (→ MANUAL, instant RC
   handoff, drift is expected); **Hover** override; **Goto**; running a survey
   line; **heartbeat = command-applied ack** (lag = link saturation, not a UI bug).
5. **Comms & range** — WiFi backhaul + Starlink/VPN fallback; **OTH is normal**;
   link drop is **not an error**.
6. **Shutdown & post-run.**

Plus: **reconcile the stale `README.md`** — it currently describes IzzyBoat 160;
update to BizzyBoat 240 (fleet mapping: 240 = BizzyBoat deployed/current,
160 = IzzyBoat testing).

## Source-of-truth references (verify against, don't assume)

- Command semantics (Standby/Hover/Goto/heartbeat-as-ack), and the verified
  autonomous control chain (cmd_vel-only, Collision Monitor reflex, velocity_smoother
  off #170): see the framework guide `docs/how_the_stack_works.md` in
  `unh_marine_autonomy` (PR #133) and verify topic/behavior names there.
- BizzyBoat-specific operational facts to honor:
  - **No current meter** — `BatteryState.current` ~0.01 A placeholder; voltage is
    real. Never report current/watts.
  - **No battery swap** — charged in place; recharge time binds cohort cadence.
  - Imagery recorded selectively; DeltaT not installed; SBG Ellipse-D is a
    temporary class loaner (durable nav sources from mavros).
  - Bag streams split: `bizzy_images/*_ffmpeg_seg`, `bizzyboat_sonar/`, `operator/`.
- Config/launch to read before documenting power-on: `bizzyboat_project11/launch/`,
  `bizzyboat_project11/config/`.

## Cross-links

- Framework guide: `rolker/unh_marine_autonomy#132` / PR #133 (link to it for the
  "how it works" / troubleshooting-by-understanding material).
- CAMP user manual: `rolker/camp#61` (operator-station companion).
- EchoBoat fleet ↔ model mapping context lives in the project history (seafloor #3).

## Open items / notes

- ~~Confirm exact power-on sequence + which host launches what against the launch
  files before writing §3~~ **DONE** — verified against `scripts/start_tmux_project11.bash`
  (gabby, cron @reboot: zenoh → core → perception → nav) and
  `scripts/start_tmux_operator_project11.bash` (operator station, manual start).
- ~~Decide doc location/format~~ **DONE** — `docs/bizzyboat_operator_manual.md`,
  linked from README under Documentation.
- ~~Keep the README reconcile in this same PR~~ **DONE** — README rewritten
  160→240 (both packages listed, BizzyBoat as current/deployed), in this commit.

### Implementation notes
- Battery-message *type* and command *semantics* are not declared in this repo
  (they live in mavros / marine_autonomy); the manual states the operator-facing
  facts (voltage-only, no current/watts; Standby→MANUAL; heartbeat-as-ack) and
  links the framework guide for mechanism rather than asserting internals.
- No network SVG for BizzyBoat exists, so the README links the network *doc* only
  (the old `izzyboat_network.svg` image reference was dropped).
- Added **§4 "The operator station displays"** (annunciators + camera/segmentation
  imagery) — scope moved here from the CAMP manual at Roland's direction (CAMP is
  not where these are viewed; recurring agent confusion). Example screenshots in
  `docs/images/` cropped from the 2026-06-01 operator screenshooter capture
  (`~/data/logs/operator/2026-06-01/...`), **terminals excluded** (dev/agent
  screens); Roland approved the Portsmouth-pier content for these PUBLIC repos.

---
**Authored-By**: `Claude Code Agent`
**Model**: `Claude Opus 4.8 (1M context)`
