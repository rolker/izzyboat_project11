# Bootstrap and build workspace on gabby

**Date**: 2026-03-26
**Issue**: rolker/unh_echoboats_project11#17
**Host**: gabby (Neousys Nuvo 9160GC, Ubuntu 24.04 Server)
**Operator**: Roland + Claude Code Agent

## Prerequisites completed

- Ubuntu 24.04 Server installed
- ROS 2 Jazzy base + dev tools installed (#16)
- Network: BizzyBoat LAN, operator network via WiFi bridge, ZeroTier, gitcloud SSH

## Step 1: Clone workspace

```bash
git clone git@gitcloud:field/ros2_agent_workspace.git project11
```

- Cloned from gitcloud Forgejo instance (`field` org)
- 5382 objects, 1.59 MiB

## Step 2: Configure manifest for gitcloud

This is the first test of using a different manifest (echoboats/gitcloud) instead
of the default unh_marine_autonomy/GitHub manifest.

### 2026-03-26: Blocked on Forgejo raw URL 404

The workspace reads `configs/project_bootstrap.url` to find the manifest bootstrap
config. Default points to GitHub. Forgejo raw URL returned 404. Identified need
for a `BOOTSTRAP_URL` override mechanism (filed as workspace issue #425).

### 2026-03-27: Resolved

Both blockers resolved since last session:
- **Gitcloud 404 fixed** — raw file access now works:
  ```
  curl -sSLf http://gitcloud/field/unh_echoboats_project11/raw/branch/jazzy/config/bootstrap.yaml
  # Returns: git_url: git@gitcloud:field/unh_echoboats_project11.git / branch: jazzy / layer: platforms
  ```
- **`BOOTSTRAP_URL` override** merged (workspace PR #426) — supports env var, CLI flag,
  and interactive prompt, with `configs/project_bootstrap.url` as fallback.

### First attempt (wrong manifest)

Ran `make build` before pulling latest workspace code. The old `setup_layers.sh` lacked
`BOOTSTRAP_URL` support, so it used the default GitHub manifest (`unh_marine_autonomy`).
Cloned ~358 MiB from GitHub before we caught it and Ctrl-C'd. Deleted workspace and
started fresh.

### Second attempt (correct)

Pulled latest workspace code (`git pull` brought in PR #426 changes), then re-cloned
from scratch:

```bash
git clone git@gitcloud:field/ros2_agent_workspace.git project11
cd project11
NONINTERACTIVE=1 make build BOOTSTRAP_URL='http://gitcloud/field/unh_echoboats_project11/raw/branch/jazzy/config/bootstrap.yaml'
```

Bootstrap correctly used the echoboats manifest from gitcloud:
- Manifest repo: `git@gitcloud:field/unh_echoboats_project11.git` (Pattern B, layer=platforms)
- Symlink: `configs/manifest -> ../layers/main/platforms_ws/src/unh_echoboats_project11/config`

## Step 3: Layer setup

All layers imported successfully via `vcs import`:

| Layer | Repos cloned |
|-------|-------------|
| underlay | geographic_info, nmea_navsat_driver, ros2launch_gui, ros2launch_session |
| core | (multiple repos) |
| platforms | ben_description, ben_project11, drix_description, lr30_project11, molab_description, mru_transform, seafloor_echoboat_project11, unh_echoboats_project11 |
| site | ccomjhc_project11 |

## Step 4: Build

Build started but failed on `geodesy` in the underlay layer:

```
CMake Error: Could not find a package configuration file provided by "angles"
```

Missing system dependency: `ros-jazzy-angles`.

**Fix**: Run `rosdep install` across all layer workspaces.

**Gap identified**: The `make build` pipeline runs bootstrap → manifest import →
layer setup → colcon build, but never runs `rosdep install` between layer setup
and build. On a fresh machine this means the first build will always fail if any
repo has system dependencies not already installed. Should open a workspace issue
to add a `rosdep install` step after layer setup completes.

**Status**: Running `rosdep install` manually, then will retry build...
