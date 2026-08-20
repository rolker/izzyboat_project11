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

# Per-station settings, optional and deliberately not in the repo: what a
# station has is a fact about the machine and where it is sitting, not about
# BizzyBoat. A station with no WiFi-bridge path or no Starlink dish sets
# OPERATOR_LAUNCH_ARGS here; a fully equipped one has no file and gets the
# defaults, so this script is identical on every station.
#
#     mkdir -p ~/.config/project11
#     cat > ~/.config/project11/station.env <<'EOF'
#     OPERATOR_LAUNCH_ARGS="wifi:=false op_starlink:=false"
#     EOF
#
# See config/station.env.example. Extra arguments passed to this script are
# appended, for one-off overrides without editing the file.
STATION_ENV="${STATION_ENV:-$HOME/.config/project11/station.env}"
if [ -f "$STATION_ENV" ]; then
    # shellcheck source=/dev/null
    source "$STATION_ENV"
    echo "Station settings: $STATION_ENV"
else
    echo "Station settings: none ($STATION_ENV absent) - full-equipment defaults"
fi
CORE_ARGS="${OPERATOR_LAUNCH_ARGS:-} $*"
UI_ARGS="${OPERATOR_UI_LAUNCH_ARGS:-}"
echo "operator_core_launch.py args: ${CORE_ARGS:-<none>}"
echo "operator_ui_launch.py args:   ${UI_ARGS:-<none>}"

set -v

export ROS_S57_ENC_ROOT=/home/field/data/ENC_ROOT
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

if /usr/bin/tmux has-session -t project11 2>/dev/null; then
    echo "WARNING: tmux session 'project11' already exists. Not starting a new one."
    echo "Use 'tmux attach -t project11' to connect, or run stop_tmux_project11.bash first."
    exit 0
fi

/usr/bin/tmux new -d -s project11
/usr/bin/tmux rename-window -t project11 shell

# Zenoh router: DISABLED 2026-06-18 — switched RMW to rmw_fastrtps_cpp (Fast DDS),
# which has no separate router daemon (discovery is built into the RMW). RMW is now
# rmw_fastrtps_cpp with ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST (set in ~/.bashrc).
# Reason: rmw_zenoh_cpp build skew caused 'invalid qos keyexpr' liveliness aborts
# (SIGABRT) that crashed CAMP + diagnostics rqt. To re-enable zenoh, restore the
# RMW exports to rmw_zenoh_cpp and uncomment the router lines below.
# /usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_zenoh_cpp" C-m
# /usr/bin/tmux send-keys "ros2 run rmw_zenoh_cpp rmw_zenohd" C-m
# Leave the first window as a plain sourced shell (handy for ros2 CLI checks).
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash" C-m

# Core: UDP bridge, diagnostic aggregator, network monitor, operator core, state publisher
/usr/bin/tmux new-window -t project11 -n core
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_fastrtps_cpp && export ROS_S57_ENC_ROOT=/home/field/data/ENC_ROOT" C-m
/usr/bin/tmux send-keys "ros2 launch bizzyboat_project11 operator_core_launch.py $CORE_ARGS" C-m

# UI: camp + three rqt instances (bizzyboat, bizzyboat-diagnostics, logger
# perspectives) + joystick, etc. The diagnostics and operator-log rqt windows
# are launched from operator_ui_launch.py rather than a separate tmux window.
/usr/bin/tmux new-window -t project11 -n ui
/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_fastrtps_cpp && export ROS_S57_ENC_ROOT=/home/field/data/ENC_ROOT" C-m
/usr/bin/tmux send-keys "ros2 launch bizzyboat_project11 operator_ui_launch.py $UI_ARGS" C-m

# Johnny5 PTZ camera (axis) from molab_hardware
# DISABLED 2026-06-15 (Lake Massabesic): Johnny5/mobile-lab not deployed at this
# site; the boat's USB front camera is used instead. Re-enable when the mobile
# lab / Johnny5 PTZ is present again.
#/usr/bin/tmux new-window -t project11 -n johnny5
#/usr/bin/tmux send-keys "source /opt/ros/jazzy/setup.bash && source /home/field/project11/layers/main/site_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_fastrtps_cpp" C-m
#/usr/bin/tmux send-keys "ros2 launch molab_hardware johnny5_launch.py" C-m

# Screenshooter: full-screen captures into ~/data/logs/operator_raw/...
# Ctrl-C in this window prompts to encode the day's PNGs to HEVC.
# SCREENSHOOTER_LABEL labels the encoded files so survey/other stations
# don't collide when archived together.
/usr/bin/tmux new-window -t project11 -n screenshooter
/usr/bin/tmux send-keys "SCREENSHOOTER_LABEL=operator /home/field/project11/layers/main/site_ws/install/ccomjhc_project11/share/ccomjhc_project11/scripts/screenshooter.bash" C-m
