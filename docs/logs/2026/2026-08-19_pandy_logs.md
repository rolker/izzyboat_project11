# 2026-08-19 — pandy log (BizzyBoat pre-deployment, Shoals survey prep)

Deployment issue: none open — this is pre-deployment (phase [0]) prep ahead of the
Isles of Shoals survey. Work stream tracked in
[`docs/roc_operator_setup_2026-08-19.md`](../../roc_operator_setup_2026-08-19.md).
Host: pandy
Side: field (origin `git@gitcloud:field/unh_echoboats_project11.git`)
Started: 2026-08-19 15:49 -04:00

Scope of this log: standing pandy up as the primary ROC operator station for
BizzyBoat, mirroring salmon (which stays untouched as warm standby).

## 2026-08-19

**2026-08-19 15:49 -04:00** — Workspace manifest bootstrapped on pandy. salmon's
`configs/project_bootstrap.url` still points at the GitHub `unh_marine_autonomy`
manifest, but salmon's actual checkout is the gitcloud site manifest — the URL
documented in `ccomjhc_project11/documentation/SettingUpOperatorStation.md`. Used
that: `BOOTSTRAP_URL=http://gitcloud/field/ccomjhc_project11/raw/branch/jazzy/config/bootstrap.yaml`,
giving manifest repo `ccomjhc_project11` (branch `jazzy`, site layer). All 7 layers
imported: 44 repos, verified by diff against salmon to be the identical repo set on
identical branches.

**2026-08-19 15:49 -04:00** — Remote-alias difference from salmon, deliberate: salmon's
project-repo remotes use `gitcloudap`, which has no DNS entry from pandy's current
network. pandy's remotes use `gitcloud` (10.242.5.191, reached over ZeroTier). Worth
revisiting if pandy is ever operated from a network where the AP alias is the
correct path.

**2026-08-19 15:55 -04:00** — System dependencies: 91 packages missing, installed by
operator via apt. One rosdep gap found — `rqt_marine_sonar` declares
`libqt5opengl5-dev`, which has **no rosdep key on noble**, so a plain
`rosdep install` over the workspace fails outright on it. The apt package itself
exists and installs fine. Workaround in use: install it directly and pass
`--skip-keys libqt5opengl5-dev`. This will block anyone bootstrapping a fresh
24.04 operator station the documented way — candidate follow-up against the
manifest or `rqt_marine_sonar`.

**2026-08-19 15:59 -04:00** — `make build` started (all layers, `--symlink-install`).

**2026-08-19 16:13 -04:00** — Build green: all 7 layers, 121 packages, 0 failures
(underlay 22, core 40, platforms 12, sensors 19, simulation 10, ui 17, site 1).
`bizzyboat_project11` installed and resolvable, with `operator_core_launch.py`,
`operator_ui_launch.py`, `bag_recorder_operator_launch.py` and
`network_monitor_operator_launch.py` all present. Matches salmon's 121-package
count from its 2026-08-05 rebuild.

**2026-08-19 16:15 -04:00** — `make sync` clean no-op — all 44 repos already at
current HEAD on their manifest branches, nothing dirty or diverged (expected;
they were cloned ~25 min earlier).

**2026-08-19 16:20 -04:00** — Shell environment mirrored from salmon into pandy's
`~/.bashrc` (backup at `~/.bashrc.bak-*`): `source ~/project11/.agent/scripts/setup.bash`,
`ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`, `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`,
`ROS_S57_ENC_ROOT=${HOME}/data/ENC_ROOT`. salmon's CUDA / nvidia-offload lines
deliberately not copied — host-specific hardware.

**2026-08-19 16:20 -04:00** — `rosdep init` + `rosdep update` run by operator, so
plain `rosdep` now works on this host. (Workspace bootstrap had been marked
skipped via `make skip-bootstrap`, since ROS 2 Jazzy, colcon, vcstool and tmux
were already installed on the machine.)

**2026-08-19 16:23 -04:00** — Name resolution: **no local `/etc/hosts` entries added,
by operator decision.** The ROC operator router serves DNS and already carries the
relevant fleet names (the pandy static lease and `pandy.op` / `pandy.vpn.bizzy` /
`pandy.cell.bizzy` / `pandy.zt` names deployed to both routers on 2026-08-19, per
`roc_operator_setup_2026-08-19.md`). Operator-reported verification from pandy:
ping and ssh to gabby over the VPN both succeed. Not independently re-checked in
this session.

**2026-08-19 16:23 -04:00** — ENC chart data deliberately **not** downloaded to
`~/data/ENC_ROOT`, pending the automated path. Note the two consumers are
distinct: `ROS_S57_ENC_ROOT` feeds the runtime `s57_grids/grid_publisher` reading a
raw ENC corpus, whereas `enc_updater` (new in core as of salmon's 08-05 sync) is
offline cron tooling driven by its own `region.yaml` `corpus_dir`, regenerating the
bathymetry store's `chart` layer with a nav-down interlock. If `enc_updater` is the
path adopted for the ROC, no manual ENC download is needed and the env var stays
inert. `~/data/ENC_ROOT` does not currently exist on pandy.

**2026-08-19 16:23 -04:00** — Gap found for field-side deployment mode on this host:
**`git-bug` is not installed on pandy.** `.agents/deployment.yaml` makes
`field_pull` / `field_list_open` / `field_show` hard-required on the field side
(no `gh` fallback), and all three are `git bug` invocations — so `/start-deployment`
would stop at issue lookup here. The workspace bootstrap step that installs git-bug
was skipped on this machine. Needs installing before pandy runs a live deployment
session.

### Outstanding for pandy before the survey

Not started in this session — carried from the handoff in
`roc_operator_setup_2026-08-19.md`:

- ROC config variants in `bizzyboat_project11` (create, don't modify salmon's
  working set): `operator_roc.yaml` (drop `wifi`, `return_host:` → pandy),
  `ping_targets_operator_roc.yaml`, ROC annunciator variant, review of
  `network_monitor_operator.yaml` / `teltonika_monitor_operator.yaml`, plus a
  launch-selection mechanism (config paths are hard-coded in
  `operator_core_launch.py` and `network_monitor_operator_launch.py`).
- `git-bug` install (above).
- ssh key auth to the boat from pandy (`ssh-copy-id`) — salmon has the alias set
  up, pandy may not.
- Dockside/pre-departure rehearsal from the ROC: full bridge load from pandy plus a
  concurrent RDP session to mercat, watching udp_bridge resend rates against the
  vpn/cell budgets.

**Not verified in this session**: nothing has been confirmed to actually exchange
ROS traffic with the boat from pandy. The operator udp_bridge has not been run
here — and must not be run while salmon's bridge is up (only one operator bridge
at a time; the boat learns its return path from whichever bridge advertises).
