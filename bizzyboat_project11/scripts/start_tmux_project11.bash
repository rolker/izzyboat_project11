#!/bin/bash

# called from cron @reboot using field's user crontab

DAY=$(date "+%Y-%m-%d")
NOW=$(date "+%Y-%m-%dT%H.%M.%S.%N")
LOGDIR="${P11_LOG_DIR:-/home/field/data/logs/bizzyboat}"

mkdir -p "$LOGDIR"
LOG_FILE="${LOGDIR}/autostart_${NOW}.txt"
{

echo ""
echo "#############################################"
echo "Running start_tmux_project11.bash"
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

# Core: mavros, mru_transform, UDP bridge, NTRIP
/usr/bin/tmux new-window -t project11 -n core
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_zenoh_cpp && export ROS_S57_ENC_ROOT=/home/field/data/ENC_ROOT" C-m
/usr/bin/tmux send-keys "ros2 launch bizzyboat_project11 core_launch.py" C-m

# Perception: cameras, sonar, logging
/usr/bin/tmux new-window -t project11 -n perception
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_zenoh_cpp" C-m
/usr/bin/tmux send-keys "ros2 launch bizzyboat_project11 perception_launch.py" C-m

# Nav: autonomy, helm, s57, nav2
/usr/bin/tmux new-window -t project11 -n nav
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_zenoh_cpp && export ROS_S57_ENC_ROOT=/home/field/data/ENC_ROOT" C-m
/usr/bin/tmux send-keys "ros2 launch bizzyboat_project11 nav_launch.py" C-m

} >> "${LOG_FILE}" 2>&1
