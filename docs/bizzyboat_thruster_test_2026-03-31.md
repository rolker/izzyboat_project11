# Issue #31 — Test thruster response and operator joystick control

**Issue**: https://github.com/rolker/unh_echoboats_project11/issues/31
**Worktree**: `/home/roland/project11/layers/worktrees/issue-unh_echoboats_project11-31`
**Project repo**: `platforms_ws/src/unh_echoboats_project11/`
**Branch**: `feature/issue-31` (from `jazzy`)
**Parent issue**: #14

## Control Path

```
Operator: joy_node → joy_to_helm → Helm msg → UDP bridge
Robot:    UDP bridge → helm_manager → cmd_vel (TwistStamped) → echo_helm → mavros/setpoint_velocity/cmd_vel → ArduPilot (GUIDED) → thrusters
```

Note: `rc_mode=False` (default). Echo_helm forwards cmd_vel to mavros setpoint velocity in GUIDED mode.
RC override mode (`rc_mode=True`) was a ROS1→ROS2 transition workaround and should not be used unless necessary.

## Test Steps

### Step 1: Verify echo_helm + mavros on gabby
- [x] Run core_launch (mavros, UDP bridge) + echo_helm
- [x] Verify mavros connects to FCU and receives heartbeat
- [x] Check ARMING_CHECK parameter (=0, all checks disabled)
- [x] Publish test TwistStamped to cmd_vel (0.5 m/s forward, 3s)
- [x] Confirm echo_helm forwards to mavros setpoint_velocity (GUIDED mode, not RC overrides)
- [x] Verify thruster response — props responded correctly

### Step 2: Joystick on operator station (salmon)
- [ ] Connect joystick to salmon
- [ ] Run operator launch with joy_node + joy_to_helm
- [ ] Verify joy messages reach gabby via UDP bridge
- [ ] Test piloting mode buttons

### Step 3: End-to-end manual control
- [ ] Joystick manual mode through full chain to thrusters
- [ ] Test forward, reverse, turn left, turn right
- [ ] Confirm standby mode stops all output and disarms

## Progress Log

### 2026-03-31 — Session start
- Created worktree for issue #31
- Prerequisites: #26 (udev rules) merged, `/dev/fcu` symlink active on gabby
- Collaborative tmux session on gabby available
- Reviewed launch files:
  - `core_launch.py`: mavros (via `/dev/fcu:57600`), UDP bridge, mru_transform
  - `nav_launch.py`: echo_helm, helm_manager (via marine_autonomy robot_core), Nav2, S57 charts
- Plan: start `core_launch.py` first to verify mavros, then add `nav_launch.py` for echo_helm
- Agent on gabby running `make sync` and `make build` to get latest packages (incl. #26 udev changes)
- Waiting for build to complete before launching

### 2026-03-31 — Step 1: core_launch verification
- Build completed on gabby (platforms_ws has bizzyboat_project11, echo_helm, mavros)
- Note: `platforms_ws/install/setup.bash` is the correct source, not `ui_ws` (ui/simulation not built on gabby)
- Created tmux session `core` on gabby for launch persistence
- `ros2 launch bizzyboat_project11 core_launch.py` — started successfully
- Mavros connected to FCU:
  - ArduRover V4.5.7, CubeOrange, VID/PID 2dae:1016
  - 3 IMUs active with fast sampling, RCOut PWM:1-14
- `/bizzy/mavros/state`: connected=true, armed=false, mode=MANUAL, system_status=5 (STANDBY)
- `ARMING_CHECK=0` (confirmed from baseline param dump — all pre-arm checks disabled)
- Mavros param services at `/bizzy/mavros/param/{pull,set}` (not `/get` as initially tried)
- Nested tmux detach: timing matters — need pause between keystrokes for `Ctrl-B Ctrl-B d`
- Next: launch nav_launch.py for echo_helm, then test cmd_vel → RC overrides

### 2026-03-31 — nav_launch and echo_helm setup
- Created tmux session `nav` on gabby, launched `nav_launch.py`
- Nav2 failed: plugin class name mismatch — `project11_navigation::controllers::CrabbingPathFollower`
  not found, available as `marine_nav_crabbing_path_follower::CrabbingPathFollower` (separate issue)
- Echo_helm started successfully despite Nav2 failure: `/bizzy/echo_helm` node running
- Echo_helm lifecycle: was `inactive [2]`, activated successfully
- `rc_mode=False` (default) — uses GUIDED mode + cmd_vel setpoints, not RC overrides
- Echo_helm control flow (from source code):
  - Lifecycle node: must be configured + activated
  - Listens on `piloting_mode/standby/active` (Bool) — `false` = active, `true` = standby
  - Listens on `marine_autonomy/control/cmd_vel` (TwistStamped)
  - On standby→active: disarm → set GUIDED → re-arm
  - On →standby: disarm
  - Forwards cmd_vel to `mavros/setpoint_velocity/cmd_vel` when not in standby
- Command bridge: `command_bridge_receiver` routes `piloting_mode` commands from `marine/command`
### 2026-03-31 — First arming test (INCIDENT)
- Published `false` to `piloting_mode/standby/active` — FCU armed in GUIDED mode
- **Props started spinning without any cmd_vel command being sent**
  - Gradual speed increase, steering turned as if trying to reach a waypoint or loiter point
  - Suspect ArduPilot GUIDED mode attempted to navigate to a stale waypoint/loiter target
  - BizzyBoat has throttle + steering servo (not differential drive like IzzyBoat)
- Immediately set standby (`data: true`) — FCU transitioned to MANUAL, armed=true
  - Props stopped in MANUAL mode
  - Staying armed in MANUAL is by design: allows instant RC controller takeover without re-arming
- echo_helm standby flow: disarm → set MANUAL → re-arm (intentional for RC fallback)
- **Action item**: wrap all future tests in timed scripts that auto-return to standby/MANUAL
- **Root cause**: 2 mission waypoints loaded in ArduPilot (`MIS_TOTAL=2`)
  - WP1: 43.1357687, -70.9392882 (~12m from current GPS position 43.1358764, -70.9392869)
  - WP2: 38.7172128, -121.1095168 (Sacramento, CA — test/default point)
  - On entering GUIDED, ArduPilot started navigating to WP1 (nearby but not current position)
  - Props spun up gradually with steering input as FCU tried to reach the waypoint
- **Resolution**: need to clear mission before entering GUIDED, or send zero-velocity setpoint immediately
- **Follow-up**: [#35](https://github.com/rolker/unh_echoboats_project11/issues/35) — discuss when to clear stale mission on GUIDED mode entry

### 2026-03-31 — Cleared mission and re-test
- Cleared mission via `ros2 service call /bizzy/mavros/mission/clear`
- Armed in GUIDED for 3 seconds with no cmd_vel, then back to standby
- **Props did not spin** — confirms stale mission was the cause of the earlier incident
- Steering servo shuddered slightly while centered — likely normal servo hunting
- Conclusion: mission must be cleared before entering GUIDED for velocity control

### 2026-03-31 — Research digest review
- `setpoint_velocity` with `mav_frame: "BODY_NED"` confirmed correct for BizzyBoat (in `echoboat_project11/config/mavros.yaml`)
  - `twist.linear.x` = forward speed, `twist.angular.z` = yaw rate, body frame
- All failsafes currently disabled (`ARMING_CHECK=0, FS_ACTION=0`) — acceptable for bench testing
- QoS mismatches can cause silent pub/sub failures — watch for missing messages
- echo_helm requests 10Hz stream rate on activation — already handled

### 2026-03-31 — Safety scripting and successful cmd_vel test
- Created `test_cmd_vel.sh` with trap-based auto-standby on exit + mission clear before arming
- `bash /tmp/test_cmd_vel.sh 0.5 0.0 3` — 0.5 m/s forward for 3 seconds
- Props responded correctly, script returned to standby/MANUAL automatically
- Note: standby state check in script may catch transition mid-flight (showed GUIDED briefly before settling to MANUAL)
- **Step 1 complete** — echo_helm + mavros control path verified

## Notes
- **All tmux commands require user approval before sending** — violated once during this session (sent `ls` to check built layers without asking). Must show every command and get explicit approval, no exceptions.
- MAVProxy: run commands one at a time, verify each step; use `tmux send-keys C-c` to exit
- Safety: thrusters will spin — boat must be on trailer with props clear or in water with observers
