#!/bin/bash

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
    echo "Use 'tmux attach -t project11' to connect, or run stop_tmux_project11.bash first."
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

# Screenshooter: full-screen captures into ~/data/logs/operator_raw/...
# Ctrl-C in this window prompts to encode the day's PNGs to HEVC.
# SCREENSHOOTER_LABEL labels the encoded files so survey/other stations
# don't collide when archived together.
/usr/bin/tmux new-window -t project11 -n screenshooter
/usr/bin/tmux send-keys "SCREENSHOOTER_LABEL=operator /home/field/project11/layers/main/site_ws/install/ccomjhc_project11/share/ccomjhc_project11/scripts/screenshooter.bash" C-m
