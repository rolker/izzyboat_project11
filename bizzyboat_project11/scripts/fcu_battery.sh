#!/bin/bash
# fcu_battery.sh — Print the FCU-reported battery voltage without the ROS stack.
#
# Talks MAVLink directly to the flight controller's serial port and reads one
# SYS_STATUS message. Handy for a quick battery check before launch, or any time
# MAVROS / the core stack is NOT running.
#
# Usage: ./fcu_battery.sh [device] [baud]
#   device: FCU serial device   (default: /dev/fcu)
#   baud:   serial baud rate     (default: 57600)
# These defaults match core_launch.py's fcu_url (/dev/fcu:57600).
#
# IMPORTANT: the FCU serial port is single-owner. If MAVROS is running it holds
# /dev/fcu, and this script will fail to open the port (or fight it). Only use
# this when the ROS stack is down — otherwise read /bizzy/mavros/battery instead.
#
# Requires pymavlink. It lives in the workspace .venv, not system python, so we
# auto-select an interpreter that can import it. Override with FCU_BATTERY_PYTHON.

set -eo pipefail

DEVICE="${1:-/dev/fcu}"
BAUD="${2:-57600}"

# --- pick a python interpreter that has pymavlink -------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
has_pymavlink() { "$1" -c 'import pymavlink' >/dev/null 2>&1; }

PYTHON=""
CANDIDATES=("$FCU_BATTERY_PYTHON" python3 python)
# Walk up from the script looking for a .venv (workspace root holds it).
dir="$SCRIPT_DIR"
for _ in 1 2 3 4 5 6 7 8; do
    CANDIDATES+=("$dir/.venv/bin/python")
    dir="$(dirname "$dir")"
    [ "$dir" = "/" ] && break
done

for cand in "${CANDIDATES[@]}"; do
    [ -n "$cand" ] || continue
    if command -v "$cand" >/dev/null 2>&1 && has_pymavlink "$cand"; then
        PYTHON="$cand"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "error: no python with pymavlink found." >&2
    echo "       install it (pip install pymavlink) or set FCU_BATTERY_PYTHON=/path/to/python" >&2
    exit 1
fi

if [ ! -e "$DEVICE" ]; then
    echo "error: FCU device '$DEVICE' not found." >&2
    exit 1
fi

# --- read one SYS_STATUS and print -----------------------------------------
exec "$PYTHON" - "$DEVICE" "$BAUD" <<'EOF'
import sys
from pymavlink import mavutil

device, baud = sys.argv[1], int(sys.argv[2])
m = mavutil.mavlink_connection(device, baud=baud)

if not m.wait_heartbeat(timeout=10):
    sys.exit("error: no MAVLink heartbeat (is the FCU powered? is MAVROS holding the port?)")

s = m.recv_match(type='SYS_STATUS', blocking=True, timeout=5)
if s is None:
    sys.exit("error: heartbeat seen but no SYS_STATUS within 5s")

volts = s.voltage_battery / 1000.0            # mV -> V
amps = "n/a" if s.current_battery == -1 else f"{s.current_battery / 100.0:.1f} A"
remaining = "n/a" if s.battery_remaining == -1 else f"{s.battery_remaining}%"
print(f"{volts:.2f} V  (current: {amps}, remaining: {remaining})")
EOF
