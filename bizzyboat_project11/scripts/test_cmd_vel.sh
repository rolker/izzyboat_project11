#!/bin/bash
# test_cmd_vel.sh — Timed cmd_vel test with auto-standby safety
#
# Usage: ./test_cmd_vel.sh [linear_x] [angular_z] [duration_secs]
#   linear_x:      forward velocity m/s (default: 0.0)
#   angular_z:     yaw rate rad/s (default: 0.0)
#   duration_secs: how long to publish (default: 3)
#
# Safety: automatically returns to standby (MANUAL) after the test duration,
# even if interrupted with Ctrl-C.

LINEAR_X="${1:-0.0}"
ANGULAR_Z="${2:-0.0}"
DURATION="${3:-3}"

NS="/bizzy"
STANDBY_TOPIC="${NS}/piloting_mode/standby/active"
CMD_VEL_TOPIC="${NS}/marine_autonomy/control/cmd_vel"
STATE_TOPIC="${NS}/mavros/state"

go_standby() {
    echo ""
    echo "=== RETURNING TO STANDBY ==="
    ros2 topic pub --once "$STANDBY_TOPIC" std_msgs/msg/Bool "{data: true}" 2>/dev/null
    sleep 1
    echo "Checking state..."
    ros2 topic echo "$STATE_TOPIC" --once 2>/dev/null
}

# Always return to standby on exit
trap go_standby EXIT

echo "=== Test Parameters ==="
echo "  linear.x:  ${LINEAR_X} m/s"
echo "  angular.z: ${ANGULAR_Z} rad/s"
echo "  duration:  ${DURATION} seconds"
echo ""

# Check current state
echo "=== Pre-test State ==="
ros2 topic echo "$STATE_TOPIC" --once
echo ""

# Clear any stale mission to prevent unintended navigation in GUIDED mode
echo "=== Clearing mission ==="
ros2 service call "${NS}/mavros/mission/clear" mavros_msgs/srv/WaypointClear 2>/dev/null
echo ""

# Activate (arm in GUIDED)
echo "=== ARMING (standby=false) ==="
ros2 topic pub --once "$STANDBY_TOPIC" std_msgs/msg/Bool "{data: false}"
sleep 1

# Verify armed
echo ""
echo "=== Post-arm State ==="
ros2 topic echo "$STATE_TOPIC" --once
echo ""

# Publish cmd_vel for duration
echo "=== Publishing cmd_vel for ${DURATION}s ==="
timeout "$DURATION" ros2 topic pub --rate 10 "$CMD_VEL_TOPIC" \
    geometry_msgs/msg/TwistStamped \
    "{twist: {linear: {x: ${LINEAR_X}}, angular: {z: ${ANGULAR_Z}}}}"

# EXIT trap handles standby
echo ""
echo "=== Test Complete ==="
