#!/bin/bash

# called from cron @reboot using field's user crontab

DAY=$(date "+%Y-%m-%d")
NOW=$(date "+%Y-%m-%dT%H.%M.%S.%N")
LOGDIR="/home/field/project11/logs/bizzyboat"
mkdir -p "$LOGDIR"
LOG_FILE="${LOGDIR}/autostart_${NOW}.txt"
LOGDIR_BAG="${LOGDIR}/${NOW}"
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
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST

/usr/bin/tmux new -d -s project11

/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST && export ROS_S57_ENC_ROOT=/home/field/data/ENC_ROOT" C-m

# Core: mavros, mru_transform, UDP bridge, NTRIP
/usr/bin/tmux send-keys "ros2 launch bizzyboat_project11 core_launch.py" C-m

# Perception: cameras, sonar, logging
/usr/bin/tmux new-window -t project11
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST" C-m
/usr/bin/tmux send-keys "ros2 launch bizzyboat_project11 perception_launch.py log_directory:=${LOGDIR_BAG}" C-m

# Nav: autonomy, helm, s57, nav2
/usr/bin/tmux new-window -t project11
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST && export ROS_S57_ENC_ROOT=/home/field/data/ENC_ROOT" C-m
/usr/bin/tmux send-keys "ros2 launch bizzyboat_project11 nav_launch.py" C-m

} >> "${LOG_FILE}" 2>&1
