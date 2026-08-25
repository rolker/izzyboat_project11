# Agent Guide: unh_echoboats_project11

> ROS 2 configuration and launch files for UNH CCOM's EchoBoats: BizzyBoat
> (EchoBoat 240, current deployed platform) and IzzyBoat (EchoBoat 160, older
> testing platform). This is a **platform-configuration repo** — per-boat
> launch files, parameter overlays, and URDFs — not an algorithm repo. The
> nodes it launches live in other repos.

## Workflow

**When this repo is checked out as part of a
[ROS 2 Agent Workspace](https://github.com/rolker/ros2_agent_workspace)**,
workflow rules (worktree vs. field mode, branch naming, etc.) are defined in
the workspace `AGENTS.md`. To determine the active mode before editing, run
the detection script **from the workspace root**:

```bash
.agent/scripts/field_mode.sh --describe layers/main/platforms_ws/src/unh_echoboats_project11
```

- **Dev machine**: `origin` is GitHub (`rolker/unh_echoboats_project11`),
  default branch **`jazzy`** — worktree + PR workflow applies. A `gitcloud`
  remote (`git@gitcloud:field/unh_echoboats_project11.git`) mirrors to the
  field share.
- **Field hosts** (gabby, salmon): clones have a gitcloud `origin` — field-mode
  rules apply (direct commits to `jazzy` allowed; reconcile later via the
  workspace `/import-field-changes` skill).
- CI (`.github/workflows/ci.yml`) and pre-commit (`.pre-commit-config.yaml`)
  run colcon build + test, URDF validation, and YAML/CMake/whitespace lint.
  The `no-commit-to-branch` hook is disabled repo-wide (2026-07-29): it
  blocked field-mode commits to `jazzy`. Dev clones rely on GitHub branch
  protection + the workspace worktree/PR workflow instead; the hook can be
  re-enabled locally without committing (see the comment block in
  `.pre-commit-config.yaml`).

**Standalone use** (cloned outside the workspace): only this repo's own
conventions apply.

## Package Inventory

| Package | Language | Description |
|---------|----------|-------------|
| `bizzyboat_project11` | ament_cmake (launch/config/URDF + a few Python scripts) | BizzyBoat (EchoBoat 240): full bring-up — core, nav, perception, sim, operator side — plus URDF with measured sensor offsets and hydro-payload serial bridges |
| `izzyboat_project11` | ament_cmake (launch/config/URDF) | IzzyBoat (EchoBoat 160): older testing platform; camera/NN experiments, plain (non-xacro) URDF |

## Repository Layout

```
unh_echoboats_project11/
├── bizzyboat_project11/     # launch/, config/, urdf/, meshes/, scripts/, docs/, test/
├── izzyboat_project11/      # launch/, config/ (incl. NN blob configs), urdf/, scripts/
├── config/                  # NOT a ROS package — boat-side workspace bootstrap manifests
│   ├── bootstrap.yaml       #   this repo's own gitcloud URL + branch (jazzy) + layer (platforms)
│   ├── layers.txt           #   layer order: underlay, core, platforms, sensors, site
│   ├── optional_layers.txt  #   layers allowed to fail setup (site — private repo)
│   └── repos/*.repos        #   vcs-import manifests per layer, all gitcloud field URLs
├── docs/                    # boat/network/ops docs, roadmap.md, analysis/, logs/YYYY/
├── scripts/pull_boat_logs.sh  # operator-station rsync pull from gabby/mercat (not installed)
├── .agents/                 # deployment.yaml (deployment-mode skill config) + this guide
└── AGENTS.md                # thin Copilot-review context; references workspace rules
```

`config/` at the repo root is the **boat/operator workspace manifest set**: it
defines what the field workspace clones (all from gitcloud, branch `jazzy`).
Editing these files changes what code ends up on the boat — treat with the
same care as launch files.

## Architecture Overview

- **`bizzy` and `izzy` are ROS namespaces, not hostnames.** BizzyBoat's
  computers are **gabby** (Linux/ROS 2, RMW = zenoh) and **mercat**
  (Windows/QINSy, also hosts the Garmin Marine Network proxy and receives the
  M3 sound-speed/ZDA serial feeds). The operator station is a separate host
  (e.g. salmon), running the `operator` namespace.
- **Bring-up chain (BizzyBoat)**: `launch/core_launch.py` is the boat-side
  entry point — mru_transform, sea-surface estimator + chart datum (from
  `mru_transform`), mavros (FCU), udp_bridge, `marine_autonomy`
  robot core, `echo_helm`, s57 charts, network monitor, sound-speed/ZDA
  serial bridges, Garmin sidescan (on by default, `sidescan:=false` to
  disable), URDF via `publish_state_launch.py`, NTRIP, SBG INS.
  `nav_launch.py` (Nav2 via shared `echoboat_project11` bringup, model 240 +
  `config/nav2_overlay.yaml`), `perception_launch.py` (cameras, sonar) and
  `logging_launch.py` (the two rosbag2 recorders, `logger` and `sonar_logger`,
  writing to `/home/field/data/logs/...`) run alongside. The recorders live in
  `logging_launch.py`, NOT in `perception_launch.py` — they were split out in
  #458 so recording can be stopped and restarted without taking the perception
  chain down, and each launch mints a fresh timestamped bag directory. tmux
  session scripts under `scripts/start_tmux_*.bash` tie these together on the
  hosts, giving logging its own window.
- **Sim**: `bizzyboat_sim_core_launch.py` reuses the REAL `bizzyboat.yaml`
  and layers `bizzyboat_sim.yaml` on top (`is_simulator`), excluding hardware
  drivers — sim and field share one config source.
- **Frames**: the URDF (`urdf/bizzyboat.urdf.xacro`) hardcodes the `bizzy/`
  prefix in link names and carries the **measured sensor offsets** (M3,
  Garmin GCV-20, GNSS antennas, SBG, cameras) published to `/tf_static` via
  robot_state_publisher. Never guess or "round" these values — they are
  survey-grade measurements with dated provenance in the comments.
- **Nav sourcing — two arbiters, different orders** (`config/bizzyboat.yaml`):
  `mru_transform` (drives nav/TF) is **FCU primary, SBG fallback** — reverted
  2026-06-29 after a ~2° SBG roll offset tilted the costmap; the yaml comment
  block carries the full rationale. `platform_sender` (operator display feed)
  still lists `[sbg, fcu]`. Read the `mru_transform` section as authoritative
  for what steers the boat; don't "harmonize" the two orders without checking
  that history.
- **Operator side**: `operator_core_launch.py` + `operator_ui_launch.py` with
  `config/operator.yaml` (udp_bridge remotes: wifi / vpn / cell paths).

## Key Files to Read First

1. `bizzyboat_project11/launch/core_launch.py` — boat bring-up; comments carry
   most of the operational rationale
2. `bizzyboat_project11/config/bizzyboat.yaml` — namespace-wide parameter
   overlay (nav sources, helm limits, platform footprint)
3. `bizzyboat_project11/urdf/bizzyboat.urdf.xacro` — frames + measured offsets
4. `config/bootstrap.yaml`, `config/layers.txt`, `config/repos/` — what the
   boat workspace is made of
5. `docs/roadmap.md` — current direction (Isles of Shoals, late Aug 2026);
   `docs/bizzyboat_operator_manual.md` — how the boat is actually operated
6. `.agents/deployment.yaml` — deployment-mode skill config (git-bug issue
   sync over gitcloud, tide/current/weather station defaults)

## Build & Test

```bash
# From the platforms layer workspace (layers/main/platforms_ws/)
colcon build --symlink-install --packages-select bizzyboat_project11 izzyboat_project11
source .agent/scripts/setup.bash && cd layers/main/platforms_ws && \
  colcon test --packages-select bizzyboat_project11 && colcon test-result --verbose
```

- The heavy boat runtime deps (mavros, sbg_driver, mru_transform, …) are
  `exec_depend` only — building needs little beyond ament_cmake + xacro.
  First-party exec_depends have no rosdep keys; CI uses `rosdep install -r`.
- Six pytest suites, all registered in `bizzyboat_project11/CMakeLists.txt`:
  - `test/test_retrofit_m3_bag.py` (500+ lines) covering
    `scripts/retrofit_m3_bag.py` — integer-second clock-skew correction
    (windowed-max envelope), `/tf_static` M3-offset rewrite, histogram
    reporting, and bag path/format handling. Integration cases self-skip if
    message packages are missing.
  - `test/test_operator_core_launch.py` — station-agnostic wiring in
    `operator_core_launch.py` (`return_host` derivation, the `wifi:=false`
    overlay); both fail silently in the field if broken.
  - `test/test_rtcm_diagnostics.py` — RTCM3 framing and CRC, the 1005/1006
    reference-point decode, baseline classification, and the cost bound on
    garbled input. Note the "external check vectors" section: most cases build
    their own frames and so are self-consistent rather than verified, and those
    vectors are what pin the implementation to something outside this repo.
    The cost bound is a CRC budget per callback, not just the reserved-bit
    pre-filter: the filter drops false preambles, but a candidate declaring a
    maximum-length payload passes it, and that was 1.10 s in one callback.
  - `test/test_gps_rtk_diagnostics.py` — `fix_type` to diagnostic level, and
    the vertical-accuracy override that catches the 2026-08-20 case (`RTK
    Fixed`, OK, green, with `v_acc` 1.750 m beside it). Also the GPSRAW
    sentinel fields (`eph`/`epv` are DOP x100; 255/65535 mean unknown).
  - `test/test_core_launch.py` — the cross-repo preflight in `core_launch.py`.
    `echo_helm`'s `ellipsoidal_fix_node` exists only on
    seafloor_echoboat_project11 #56, so a stale `echo_helm` must fail at
    startup with a message naming the repo to rebuild. **Merge order is not
    optional**: this launch file does not run on an `echo_helm` that predates
    #56.
  - `test/test_gnss_vertical_calibration.py` — the sign of the correction
    `scripts/gnss_vertical_calibration.py` prints. The URDF is z-up and
    ArduPilot's `GPS_POS*` are z-down (FRD), so the two edits it recommends
    carry opposite signs; it is the line an operator copies. Also the honesty
    gates on the corpus, so a run too short to show drift cannot report 0.0 mm
    of it.
- CI also runs `xacro ... | check_urdf` on both boats' URDFs — a URDF that no
  longer parses means no `/tf_static` on the boat.

## Cross-Layer Dependencies (launch includes / FindPackageShare)

| Used by | Package | Repo (layer) |
|---------|---------|--------------|
| core/nav launches | `echoboat_project11`, `echo_helm` | seafloor_echoboat_project11 (platforms) — shared EchoBoat base |
| core_launch | `mru_transform` | mru_transform (platforms) |
| core/operator launches | `udp_bridge`, `marine_autonomy`, `s57_grids` | core layer |
| oak_cameras_launch | `sea_surface_segmentation` | unh_marine_perception (sensors) |
| ntrip_launch | `ccomjhc_project11` (NTRIP credentials) | site layer (private) |

## Common Pitfalls

- **Changes take effect on a live boat.** Topic/param/frame renames ripple
  into field operations; field-tuned overlay values deliberately differ from
  upstream defaults ("differs from default" is not a bug).
- **The offline bag tools are NOT installed.** `retrofit_m3_bag.py`,
  `retrofit_sidescan_bag.py` and `gnss_vertical_calibration.py` are run
  manually from the source tree; the test imports `retrofit_m3_bag.py` by relative path via importlib, so
  moving/renaming the script silently orphans the test target. Only the tmux
  scripts and three diagnostics/relay Python nodes are installed
  (see `bizzyboat_project11/CMakeLists.txt`).
- **mavros config layering**: bizzy's mavros node stacks four param files —
  mavros defaults, shared `echoboat_project11/config/mavros.yaml`, then
  `bizzyboat_project11/config/mavros.yaml`. Per-plugin overrides (frame_ids)
  MUST live in a yaml with `/**/plugin_name:` patterns, not an inline dict —
  each mavros plugin runs as its own node.
- **mavros frame bridges**: mavros's local_position plugin emits bare
  `map`/`odom`/`base_link` frames; core_launch publishes identity static
  transforms tying them under `bizzy/`. Don't "clean up" these bridges.
- **Launch-arg namespace is global within a launch tree**: `zda_launch.py`
  prefixes its args (`zda_device`, `zda_baud`) because a bare `device` would
  inherit `sound_speed_launch.py`'s `/dev/ttyS0` default. Follow that pattern
  when adding composable launches.
- **`frame_prefix` and `namespace` are separate args**, and the URDF link
  names hardcode `bizzy/` — launching under another namespace does NOT
  re-prefix URDF frames (oak_cameras_launch also hardcodes
  `bizzy/<name>_optical` to match the URDF).
- **gabby serial-port map is load-bearing**: ttyS0 = AML SVS (RX-only, its TX
  side is faulty — fine for RX), ttyS1 = SBG (needs bidirectional), ttyS2 =
  ZDA out to M3. `sound_speed_launch.py`'s docstring is the authoritative
  writeup; keep launch-file comments in sync with it when ports move.
- **Sidescan reaches the GCV-20 through mercat**: the driver on gabby points
  at mercat's proxy (192.168.20.8), not the GCV itself; transmit is
  interlocked on a valid sound-speed topic.
- **`docs/logs/YYYY/` are raw per-host field records** — never polish or
  reformat them; they are data-of-record for deployments.
- **Root `config/` edits reconfigure the boat workspace** (gitcloud vcs
  manifests), not any ROS node — a wrong URL/branch here breaks field
  bootstrap, and nothing in CI exercises it.
