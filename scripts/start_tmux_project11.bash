#!/bin/bash

# called from cron @reboot using field's user crontab
# inspired by: https://answers.ros.org/question/140426/issues-launching-ros-on-startup/

DAY=$(date "+%Y-%m-%d")
NOW=$(date "+%Y-%m-%dT%H.%M.%S.%N")
LOGDIR="/home/field/project11/logs"
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
source /home/field/project11/jazzy_ws/install/setup.bash

set -v

export ROS_S57_ENC_ROOT=/home/field/data/ENC_ROOT
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST

#wait for dora to be pingable by self
while ! ping -c 1 -W 1 dora; do
    echo "Waiting for ping to dora..."
    sleep 1
done



# start virtual framebuffer

/usr/bin/tmux new -d -s xvfb
/usr/bin/tmux send-keys "Xvfb :0 -screen 0  1920x1080x24" C-m

/usr/bin/tmux new -d -s fluxbox
/usr/bin/tmux send-keys "DISPLAY=:0 fluxbox" C-m

/usr/bin/tmux new -d -s x11vnc
/usr/bin/tmux send-keys "x11vnc -nopw -display :0 -forever" C-m

echo "Wait 5 seconds before launching ROS..."
sleep 5

/usr/bin/tmux new -d -s project11 
/usr/bin/tmux send-keys "DISPLAY=:0 ros2 launch -g izzyboat_project11 izzyboat_launch.py logDirectory:=${LOGDIR}" C-m

} >> "${LOG_FILE}" 2>&1
