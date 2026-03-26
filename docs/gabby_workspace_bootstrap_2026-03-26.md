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

The workspace reads `configs/project_bootstrap.url` to find the manifest bootstrap
config. Default points to GitHub. Need to change it to point to gitcloud.

**Issue found**: Forgejo raw URL returns 404:
```
curl -sSLf http://gitcloud/field/unh_echoboats_project11/raw/branch/jazzy/config/bootstrap.yaml
# curl: (22) The requested URL returned error: 404
```

**Root cause**: Unknown — the `field` org exists on gitcloud and serves HTML pages,
but the raw file URL returns 404. Possible causes:
- The repo name on gitcloud may differ from `unh_echoboats_project11`
- The `jazzy` branch was not set as the default branch on gitcloud (another agent investigating)
- Need to check repo listing via Forgejo API: `curl -sS http://gitcloud/api/v1/repos/search?q=echoboats`

**Next steps**:
1. Confirm repo name on gitcloud (API search or browse web UI)
2. Verify jazzy branch and raw file access
3. Edit `configs/project_bootstrap.url` on gabby to point to gitcloud URL
4. Run `make build`

**Gap identified**: No mechanism to supply manifest URL via env var or CLI flag —
currently hardcoded to `configs/project_bootstrap.url`. Should open an issue for this.

## Step 3: Bootstrap and build

_Blocked on Step 2..._
