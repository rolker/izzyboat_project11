#!/bin/bash

# Cameras-only bring-up for bench / dockside perception testing.
# Starts a zenoh router + the camera nodes (USB + OAKs) + the UDP bridge in a
# dedicated tmux session, WITHOUT the rest of the stack (no sonar/nav/mavros).
#
# Stop with:  stop_tmux_project11.bash camera_test
# Subset:     pass extra launch args, e.g.  start_tmux_camera_test.bash oak:=false
#
# Do NOT run alongside start_tmux_project11.bash: both start their own zenoh
# router and would contend for the same port. This is a standalone test tool.

SESSION="camera_test"
LAUNCH_ARGS="$*"

NOW=$(date "+%Y-%m-%dT%H.%M.%S.%N")
LOGDIR="${P11_LOG_DIR:-/home/field/data/logs/bizzyboat}"

mkdir -p "$LOGDIR"
LOG_FILE="${LOGDIR}/camera_test_${NOW}.txt"
{

echo ""
echo "#############################################"
echo "Running start_tmux_camera_test.bash"
date
echo "args: ${LAUNCH_ARGS:-<none>}"
echo "#############################################"
echo ""
echo "Logs:"

source /opt/ros/jazzy/setup.bash
source /home/field/project11/layers/main/site_ws/install/setup.bash

set -v

export RMW_IMPLEMENTATION=rmw_zenoh_cpp

if /usr/bin/tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "WARNING: tmux session '$SESSION' already exists. Not starting a new one."
    echo "Use 'tmux attach -t $SESSION' to connect, or run"
    echo "'stop_tmux_project11.bash $SESSION' first."
    exit 0
fi

/usr/bin/tmux new -d -s "$SESSION"
/usr/bin/tmux rename-window -t "$SESSION" zenoh

# Zenoh router: must be up before any ROS node connects
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_zenoh_cpp" C-m
/usr/bin/tmux send-keys "ros2 run rmw_zenoh_cpp rmw_zenohd" C-m
sleep 2

# Cameras + UDP bridge
/usr/bin/tmux new-window -t "$SESSION" -n cameras
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_zenoh_cpp" C-m
/usr/bin/tmux send-keys "ros2 launch bizzyboat_project11 camera_test_launch.py ${LAUNCH_ARGS}" C-m

} >> "${LOG_FILE}" 2>&1
