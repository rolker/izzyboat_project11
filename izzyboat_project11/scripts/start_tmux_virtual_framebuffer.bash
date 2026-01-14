#!/bin/bash

NOW=$(date "+%Y-%m-%dT%H.%M.%S.%N")
LOGDIR="/home/field/project11/logs/izzyboat"
mkdir -p "$LOGDIR"
LOG_FILE="${LOGDIR}/autostart_virtual_framebuffer_${NOW}.txt"

{

echo ""
echo "#############################################"
echo "Running start_tmux_virtual_framebuffer.bash"
date
echo "#############################################"
echo ""
echo "Logs:"

source /opt/ros/jazzy/setup.bash
source /home/field/project11/jazzy_ws/install/setup.bash

set -v

export ROS_S57_ENC_ROOT=/home/field/data/ENC_ROOT
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST

# start virtual framebuffer

/usr/bin/tmux new -d -s xvfb
/usr/bin/tmux send-keys "Xvfb :0 -screen 0  1920x1080x24" C-m

echo "Wait 5 seconds before launching fluxbox..."
sleep 5

/usr/bin/tmux new -d -s fluxbox
/usr/bin/tmux send-keys "DISPLAY=:0 fluxbox" C-m

/usr/bin/tmux new -d -s x11vnc
/usr/bin/tmux send-keys "x11vnc -nopw -display :0 -forever" C-m

echo "Wait 5 seconds before launching ROS..."
sleep 5

/home/field/project11/jazzy_ws/src/izzyboat_project11/scripts/start_tmux_project11.bash

} >> "${LOG_FILE}" 2>&1
