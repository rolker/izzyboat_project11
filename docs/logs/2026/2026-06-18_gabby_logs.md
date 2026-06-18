# 2026-06-18 — gabby log (BizzyBoat deployment #9fbace1)

Deployment issue: Deployment 2026-06-18: Lake Massabesic survey (git-bug 9fbace1)
Host: gabby
Side: field
Started: 2026-06-18 09:08 -04:00

## 2026-06-18

**2026-06-18 09:08 -04:00** — Deployment mode activated on gabby (field side) via `/start-deployment`. First-activation against existing issue #9fbace1. TODO (dev): stamp `- [gabby log](docs/logs/2026/2026-06-18_gabby_logs.md)` under the deployment issue's `## Logs` section, and add gabby to `## Hosts in use` (currently lists only deadpool/dev) — field side is read-only on the issue.

**2026-06-18 09:11 -04:00** — Operator reports salmon seeing errors/crashes possibly tied to zenoh versions. Ran `apt update`/`apt upgrade` on salmon and will reboot. (Reported from gabby; salmon has its own host log.)

**2026-06-18 09:20 -04:00** — Checked gabby's zenoh versions for comparison against post-upgrade salmon: `ros-jazzy-rmw-zenoh-cpp` 0.2.9-1noble.20260612.051713, `ros-jazzy-zenoh-cpp-vendor` 0.2.9-1noble.20260225.231114. Upstream zenoh version 0.2.9 on both; `RMW_IMPLEMENTATION=rmw_zenoh_cpp` active. If salmon's apt upgrade bumped past 0.2.9, the minor-version wire-protocol mismatch is a plausible cause of the errors/crashes.
