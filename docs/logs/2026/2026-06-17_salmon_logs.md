# 2026-06-17 — salmon log (BizzyBoat deployment #295)

Deployment issue: https://github.com/rolker/unh_echoboats_project11/issues/295
Host: salmon
Side: field
Started: 2026-06-17 09:43 -04:00

> Relocated by the dev-side #295 wrap-up: salmon re-attached to the prior day's deployment (#6a53346, git-bug) and appended this session to `2026-06-16_salmon_logs.md`; the entries are 2026-06-17 / #295.

## 2026-06-17

**2026-06-17 09:43 -04:00** — New survey day; salmon session re-attached to deployment #6a53346 (multi-day). Field side, jazzy clean. `git bug pull origin` failed (SSH_AUTH_SOCK unset) — working from local git-bug refs.

**2026-06-17 09:43 -04:00** — udp_bridge: new **cell** link is live and carrying data. Operator-side bridge stats for remote bizzy, `cell` connection (salmon.cell.bizzy.p11.lan:4200, 192.168.24.142): received ~10.4 KB/s; message payload ~21.5 KB/s success, **0 failed / 0 dropped**; cap 300 KB/s. Topics routing over cell incl. marine/heartbeat, marine/status/mission_manager, mavros/battery, mavros/global_position/global, mavros/gpsstatus/gps1/raw, collision_monitor_state, local_costmap/published_footprint. (vpn ~10.5 KB/s, wifi ~52 KB/s also live.) Note: remote-wide resend_giveup_count 86822 — worth watching, but the cell leg itself is clean right now.

**2026-06-17 10:57 -04:00** — Converted yesterday's (2026-06-16) sidescan bags to XTF with `bag_to_xtf` (marine_tools/bag_analysis). Source: gabby `bizzyboat_sonar` bags; output `/home/field/data/xtf/2026-06-16/`. 4 sessions, 235,969 pings total, all clean (no malformed; no_tf drops 0–4 per session; converter used latest-TF fallback within max-tf-age for ~half the pings — expected, not an error):
- 14-17-37 → 52,004 pings (443 MB)
- 15-52-45 → 743 pings (6.3 MB)
- 15-54-20 → 132,108 pings (1.13 GB)
- 19-47-06 → 51,114 pings (435 MB)
Note: I first ran via `python3 install/bag_analysis/lib/bag_analysis/bag_to_xtf …` after wrongly expecting a bare `bag_to_xtf` on PATH. Correction — that was operator error, not a defect: ROS 2 ament_python installs console_scripts to `lib/<pkg>/` to be run via `ros2 run bag_analysis bag_to_xtf --bag … --output …` (documented in bag_analysis/README.md). No PATH fix needed.

**2026-06-17 11:10 -04:00** — Also converted 2026-06-15 sidescan bags to XTF (`ros2 run bag_analysis bag_to_xtf`). Source: gabby `bizzyboat_sonar`; output `/home/field/data/xtf/2026-06-15/`. 2 of 4 sessions held real sidescan data:
- 14-06-30 → 30,427 pings (259 MB)
- 15-03-45 → 259,695 pings (2.21 GB)
- 12-52-33 → SKIPPED: no sonar_image topics recorded (pre-survey)
- 13-35-03 → SKIPPED: sonar_image topics present but Count=0 (sonar not pinging)
Data-quality note: ALL 06-15 sessions had **no nadir_depth** messages → converter wrote altitude=0 for every ping. (06-16 bags had nadir_depth.) Downstream tools relying on XTF altitude for slant-range/bottom-track correction need altitude supplied another way for the 15th. Worth a dev-side follow-up on why nadir_depth was absent on the 15th.

**2026-06-17 11:21 -04:00** — Moved XTF output dir from `/home/field/data/xtf` → `/home/field/share/xtf` (physical mv, same filesystem) so it sits inside the Samba `[share]` root and is visible to clients. Earlier symlink/bind-mount approach abandoned (symlink into the share was a Samba *wide link* — blocked by default; wide links also force-disabled while `unix extensions=yes`). New canonical write location for XTF: `~/share/xtf/<YYYY-MM-DD>/`. No smbd/config change made.

**2026-06-17 12:31 -04:00** — Added field helper `~/bin/convert_new_sonar_xtf.sh` (salmon) to batch-convert new sidescan bags to XTF on demand. Wraps `ros2 run bag_analysis bag_to_xtf`; scans gabby `bizzyboat_sonar` pull dir → writes `~/share/xtf/<date>/<session>.xtf`. Idempotent (skips already-converted by .xtf presence; no-sidescan bags get a marker in `~/share/xtf/.state/` so they are not retried); skips sessions changed within 5 min (pull/recording may be in flight). Paths overridable via env (BAG_ROOT/XTF_ROOT/etc). Default date floor `--since 2026-06-15` baked in (pass `--since ''` for full ~100-session backlog). Personal field script, not yet committed — candidate to PR into marine_tools (dev side) if we want it tracked/reusable.

**2026-06-17 15:02 -04:00** — Operator reports CAMP (operator app) crashed again (recurring). Captured below for later RCA; not diagnosed live.

**2026-06-17 15:07 -04:00** — CAMP crash detail: already relaunched and healthy (PID 53939, started ~15:00). Crashed instance (PID 38122) ROS log `~/.ros/log/CCOMAutonomousMissionPlanner_38122_*.log` ends mid-run with NO error/exception/terminate/stack — silent death, consistent with segfault or OOM-kill (neither writes to the app ROS log). New instance shows only a benign startup TF transient (frame `bizzy/map_tide` timestamp earlier than transform cache). RCA deferred to wrap-up: check `dmesg`/`journalctl -k` for OOM/segfault around 15:00, and enable core dumps to catch the next one (recurring crash).

**2026-06-17 17:08 -04:00** — Boat at the dock (operator-reported).
