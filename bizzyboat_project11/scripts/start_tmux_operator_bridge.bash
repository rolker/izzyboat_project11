#!/bin/bash

# Minimal operator-side bring-up for bench/testing: zenoh router +
# operator core (udp_bridge, network monitor, marine_autonomy operator
# core, state publisher) with the bag recorder disabled. Skips the full
# operator station (UI/RViz/CAMP, johnny5 camera, screenshooter) that
# start_tmux_operator_project11.bash brings up.
#
# Uses its own tmux session ('operator_bridge') so it won't collide with
# a real 'project11' operator session. Stop with:
#   tmux kill-session -t operator_bridge   (or Ctrl-C each window first)

echo ""
echo "#############################################"
echo "Running start_tmux_operator_bridge.bash"
date
echo "#############################################"
echo ""
echo "Logs:"

source /opt/ros/jazzy/setup.bash
source /home/field/project11/layers/main/site_ws/install/setup.bash

set -v

export RMW_IMPLEMENTATION=rmw_zenoh_cpp

SESSION="operator_bridge"

if /usr/bin/tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "WARNING: tmux session '$SESSION' already exists. Not starting a new one."
    echo "Use 'tmux attach -t $SESSION' to connect, or 'tmux kill-session -t $SESSION' first."
    exit 0
fi

/usr/bin/tmux new -d -s "$SESSION"
/usr/bin/tmux rename-window -t "$SESSION" zenoh

# Zenoh router: must be up before any ROS node connects
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_zenoh_cpp" C-m
/usr/bin/tmux send-keys "ros2 run rmw_zenoh_cpp rmw_zenohd" C-m
sleep 2

# Operator core, logging disabled (no bag recorder)
/usr/bin/tmux new-window -t "$SESSION" -n core
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_zenoh_cpp" C-m
/usr/bin/tmux send-keys "ros2 launch bizzyboat_project11 operator_core_launch.py record_diagnostics:=false" C-m

echo ""
echo "Started tmux session '$SESSION'. Attach with: tmux attach -t $SESSION"
