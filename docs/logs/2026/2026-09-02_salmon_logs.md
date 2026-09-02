# 2026-09-02 — salmon log (BizzyBoat deployment — issue pending)

Deployment issue: pending (backfill from a dev host)
Host: salmon
Side: field
Started: 2026-09-02 10:08 -04:00

**2026-09-02 10:09 -04:00** — Pre-session: salmon top-left monitor (DisplayPort-1-1, AMD reverse-PRIME output) froze; recovery attempt (xrandr PRIME Synchronization set on the wedged output) hung the X server; host rebooted 09:56, all displays + operator apps (bizzyboat/diagnostics/logger/bizzy_sonar rqt, CAMP) back up. PRIME Synchronization on DisplayPort-1-1 still 0 (post-reboot set did not stick); durable fix = move that monitor to an NVIDIA-wired port — wrap-up item.

**2026-09-02 10:10 -04:00** — Operator on the monitor freeze: 'I think that was caused by the laptop power being unplugged. All seems good now that the laptop is plugged in.' Consistent with observed state pre-reboot: GPU pinned at ~90% of a 23W/25W power budget while the top-left display (reverse-PRIME path) stalled.

**2026-09-02 10:36 -04:00** — make sync + make build at operator request (CAMP outdated): sync pulled new camp commits (crash handler, sonar-live tests) among others; build green, 17 packages / 4m18s (stderr-only noise from camp + rqt_marine_radar). CAMP restart pending to pick up new build.

**2026-09-02 16:58 -04:00** — Deployment over, boat on trailer (operator report). Operator skipped the screenshooter Ctrl-C encode; running encode_day from screenshooter.bash now for 2026-09-02 (594 frames, 13:33-18:45 UTC) and 2026-09-01 (328 frames, rollover encode never fired) -> ~/data/logs/operator/<date>/screenshots/operator_<date>.mp4.
