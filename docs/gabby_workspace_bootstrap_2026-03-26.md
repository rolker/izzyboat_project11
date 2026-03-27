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

Ran `rosdep install` manually from `layers/main/`:
```bash
rosdep install -i --from-paths underlay_ws/src/ core_ws/src/ platforms_ws/src/ site_ws/src/
```

Installed ~244 system packages including ros-jazzy-angles, python3-pyproj, mavros,
nav2 stack, OpenCV, PCL, DepthAI, and (unnecessarily) Gazebo.

**Issue found**: `nav2_bringup` dependency in `ben_project11` and
`echoboat_project11` pulls in the full Gazebo stack (~900 MB). Filed:
- [rolker/ben_project11#12](https://github.com/rolker/ben_project11/issues/12)
- [rolker/seafloor_echoboat_project11#4](https://github.com/rolker/seafloor_echoboat_project11/issues/4)

Also fixed `izzyboat_project11/package.xml` — removed obsolete `<exec_depend>project11</exec_depend>`
(cherry-picked to gabby's jazzy branch).

### Build retry (success)

```bash
NONINTERACTIVE=1 make build BOOTSTRAP_URL='http://gitcloud/field/unh_echoboats_project11/raw/branch/jazzy/config/bootstrap.yaml'
```

All layers built successfully:

| Layer | Packages | Status |
|-------|----------|--------|
| underlay | 6/6 | ✅ |
| core | 24/24 | ✅ |
| platforms | 5/5 | ✅ |
| site | 1/1 | ✅ |

Compiler warnings only (no errors): geodesy parentheses, unused params in
marine_nav_crabbing_path_follower and mru_transform, CMake variable warnings.

### Sensors layer added

Pulled new sensors layer (rolker/unh_echoboats_project11#23, merged as PR #24) from
GitHub to gitcloud, then pulled on gabby. Re-ran `make build` (no `BOOTSTRAP_URL`
needed after initial setup). New layer built successfully:

| Layer | Packages | Status |
|-------|----------|--------|
| sensors | 3/3 | ✅ (depthai_marine, imagenex_deltat, sea_surface_segmentation) |

## Step 5: Verification

```bash
source layers/main/site_ws/install/setup.bash
ros2 pkg list | wc -l   # 394 packages
```

All workspace packages confirmed available, including:
- **underlay**: geodesy, geographic_info, ros2launch_gui, ros2launch_session, nmea_navsat_driver
- **core**: marine_autonomy, marine_nav_*, mission_manager, udp_bridge, marine_ais_*, s57_*, marine_charts
- **platforms**: echoboat_project11, izzyboat_project11, echo_helm, mru_transform
- **sensors**: depthai_marine, imagenex_deltat, sea_surface_segmentation
- **site**: ccomjhc_project11

## Summary

Workspace bootstrap and build on gabby complete. All 5 layers (39 packages) built
successfully from gitcloud sources using the echoboats boat manifest.

### Issues found during bootstrap
1. **Missing rosdep step** — `make build` doesn't run `rosdep install` between layer setup and build
2. **Obsolete `project11` dependency** in `izzyboat_project11/package.xml` — fixed (cherry-picked)
3. **`nav2_bringup` pulls in Gazebo** (~900 MB) — filed issues on ben_project11 and seafloor_echoboat_project11
