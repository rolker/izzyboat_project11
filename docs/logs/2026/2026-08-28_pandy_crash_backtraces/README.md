# camp crash backtraces — 2026-08-28, pandy

Verbatim copies of the `#217` crash-handler output for the four camp
crashes during the 2026-08-28 BizzyBoat deployment. Copied from pandy's
`~/.ros/log/` (field host, not reachable from dev) so the evidence
survives for wrap-up RCA.

| File | PID | Instance ran | Signal |
|---|---|---|---|
| `camp_crash_877631.log` | 877631 | 06:59:18 – 08:23:43 | SIGSEGV |
| `camp_crash_892001.log` | 892001 | 08:23:53 – 09:10:43 | SIGABRT |
| `camp_crash_899410.log` | 899410 | 09:10:53 – 12:33:53 | SIGSEGV |
| `camp_crash_931758.log` | 931758 | 12:34:03 – 13:16:53 | SIGABRT |

A fifth instance (pid 938645) started 13:17:01 and was still running at
16:25 with no crash log.

Start times are decoded from the epoch in the matching
`CCOMAutonomousMissionPlanner_<pid>_<epoch>.log` filename; end times are
that file's mtime. Times are local (`-04:00`).

Backtraces are mangled — pipe through `c++filt` to read them.

All four share one signature: `rcl_subscription_fini` →
`rcl_node_type_cache_unregister_type` →
`type_description_interfaces__msg__TypeDescription__destroy`, dying in
`free` (SIGSEGV) or a glibc malloc abort (SIGABRT). `899410` and
`931758` name the subscription being destroyed:
`rclcpp::Subscription<marine_nav_interfaces::msg::TaskFeedback>`.
`877631` shows it under `rclcpp::Executor::wait_for_work` on a
`MultiThreadedExecutor` worker — a live waitset rebuild, not shutdown.

Binary: `ui_ws/build/camp/CCOMAutonomousMissionPlanner`, built
2026-08-27 09:20:35 (carries 532b6df, af5e378, 0fc6408). No camp rebuild
happened on 2026-08-28.

See `../2026-08-28_pandy_logs.md` for the full entry.
