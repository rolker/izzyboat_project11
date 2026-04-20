#!/bin/bash

# called from cron @reboot (or by hand) on the operator station

DAY=$(date "+%Y-%m-%d")
NOW=$(date "+%Y-%m-%dT%H.%M.%S.%N")
LOGDIR="${P11_LOG_DIR:-/home/field/data/logs/operator}"

mkdir -p "$LOGDIR"
LOG_FILE="${LOGDIR}/autostart_${NOW}.txt"
{

echo ""
echo "#############################################"
echo "Running start_tmux_operator_project11.bash"
date
echo "#############################################"
echo ""
echo "Logs:"

source /opt/ros/jazzy/setup.bash
source /home/field/project11/layers/main/site_ws/install/setup.bash

set -v

export ROS_S57_ENC_ROOT=/home/field/data/ENC_ROOT
export RMW_IMPLEMENTATION=rmw_zenoh_cpp

if /usr/bin/tmux has-session -t project11 2>/dev/null; then
    echo "WARNING: tmux session 'project11' already exists. Not starting a new one."
    echo "Use 'tmux attach -t project11' to connect, or stop it first."
    exit 0
fi

/usr/bin/tmux new -d -s project11
/usr/bin/tmux rename-window -t project11 zenoh

# Zenoh router: must be up before any ROS node connects
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_zenoh_cpp" C-m
/usr/bin/tmux send-keys "ros2 run rmw_zenoh_cpp rmw_zenohd" C-m
sleep 2

# Core: UDP bridge, diagnostic aggregator, network monitor, operator core, state publisher
/usr/bin/tmux new-window -t project11 -n core
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_zenoh_cpp && export ROS_S57_ENC_ROOT=/home/field/data/ENC_ROOT" C-m
/usr/bin/tmux send-keys "ros2 launch bizzyboat_project11 operator_core_launch.py" C-m

# Foxglove bridge: isolated so its chatter doesn't drown the core pane
/usr/bin/tmux new-window -t project11 -n foxglove
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_zenoh_cpp" C-m
/usr/bin/tmux send-keys "ros2 launch foxglove_bridge foxglove_bridge_launch.xml" C-m

# Foxglove Studio: desktop client that connects to the bridge above
/usr/bin/tmux new-window -t project11 -n studio
/usr/bin/tmux send-keys "foxglove-studio" C-m

# UI: camp + rqt (bizzyboat perspective) + joystick, etc.
/usr/bin/tmux new-window -t project11 -n ui
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_zenoh_cpp && export ROS_S57_ENC_ROOT=/home/field/data/ENC_ROOT" C-m
/usr/bin/tmux send-keys "ros2 launch bizzyboat_project11 operator_ui_launch.py" C-m

# Second rqt with bizzyboat-diagnostics perspective
/usr/bin/tmux new-window -t project11 -n rqt-diag
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_zenoh_cpp" C-m
/usr/bin/tmux send-keys "ros2 run rqt_gui rqt_gui -p bizzyboat-diagnostics" C-m

# Johnny5 PTZ camera (axis) from molab_hardware
/usr/bin/tmux new-window -t project11 -n johnny5
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_zenoh_cpp" C-m
/usr/bin/tmux send-keys "ros2 launch molab_hardware johnny5_launch.py" C-m

} >> "${LOG_FILE}" 2>&1
