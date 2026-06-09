#!/bin/bash
# mavros_battery.sh — Print the battery state from the RUNNING ROS stack.
#
# Companion to fcu_battery.sh. Use this when MAVROS is up and holding /dev/fcu:
# the FCU serial port is single-owner, so a direct read would fight MAVROS for
# bytes. Instead we read MAVROS's published /bizzy/mavros/battery topic.
# battery_logger.sh picks between the two automatically based on whether the
# port is held (see that script).
#
# QoS note: MAVROS publishes battery with sensor-data QoS (BEST_EFFORT). A
# default RELIABLE subscriber silently matches nothing under that publisher, so
# we subscribe with --qos-profile sensor_data. Under rmw_zenoh a fresh process
# also pays a discovery/connection cost to reach the local zenoh router, so the
# read is bounded by both ros2's --timeout and an outer `timeout` backstop; if
# no sample arrives in time we print nothing and exit non-zero.
#
# Usage: ./mavros_battery.sh [--csv] [topic]
#   --csv:  emit "volts,amps,remaining" (empty fields when unmeasured/NaN),
#           matching fcu_battery.sh --csv. remaining is percent (0-100).
#   topic:  battery topic (default: /bizzy/mavros/battery)
#
# Env: sources the same ROS env the operator launch scripts use, so it works
# from a bare cron environment. Override the topic via the positional arg.

set -o pipefail

FORMAT="human"
if [ "${1:-}" = "--csv" ]; then
    FORMAT="csv"
    shift
fi
TOPIC="${1:-/bizzy/mavros/battery}"

# --- ROS env (matches start_tmux_project11.bash) ---------------------------
# Source before `set -e`/strict mode: ROS setup scripts reference unbound vars
# and can return non-zero benignly. site_ws is optional — guard it so a missing
# overlay doesn't break the base-ROS read (sensor_msgs lives in base ROS).
source /opt/ros/jazzy/setup.bash >/dev/null 2>&1 || true
SITE_SETUP=/home/field/project11/layers/main/site_ws/install/setup.bash
[ -f "$SITE_SETUP" ] && { source "$SITE_SETUP" >/dev/null 2>&1 || true; }
export RMW_IMPLEMENTATION=rmw_zenoh_cpp

if ! command -v ros2 >/dev/null 2>&1; then
    echo "error: ros2 not on PATH after sourcing ROS env" >&2
    exit 1
fi

# --- grab one sample --------------------------------------------------------
# Outer `timeout` is a hard backstop in case discovery wedges past ros2's own
# --timeout (which only counts once subscribed). One full-message echo, then
# parse the fields we want — cheaper than one discovery round per field.
MSG="$(timeout 12 ros2 topic echo --once --timeout 8 \
        --qos-profile sensor_data --no-arr "$TOPIC" 2>/dev/null)"
ECHO_RC=$?
# ros2 prints "WARNING: topic ... does not appear to be published yet" to
# STDOUT (not stderr) and exits non-zero when there's no publisher. Drop such
# notices and trust the exit code, so a no-publisher state can never be parsed
# as a message.
MSG="$(grep -v '^WARNING:' <<<"$MSG")"

if [ "$ECHO_RC" -ne 0 ] || [ -z "$MSG" ]; then
    echo "error: no battery sample from $TOPIC (stack down, or topic not publishing?)" >&2
    exit 1
fi

# Extract top-level fields. --no-arr drops the cell_voltage arrays, so these
# anchored matches are unambiguous. NaN -> empty.
parse() { awk -v key="$1:" '$1==key {print $2; exit}' <<<"$MSG"; }
clean() { case "$1" in ''|nan|.nan|NaN) echo "" ;; *) echo "$1" ;; esac; }

V="$(clean "$(parse voltage)")"
A="$(clean "$(parse current)")"
PCT_RAW="$(clean "$(parse percentage)")"   # BatteryState percentage is 0..1

if [ -z "$V" ]; then
    echo "error: battery sample had no usable voltage" >&2
    exit 1
fi

# Normalize: voltage 2dp, percentage 0..1 -> whole percent.
VOLTS="$(printf '%.2f' "$V")"
AMPS=""
[ -n "$A" ] && AMPS="$(printf '%.1f' "$A")"
REMAIN=""
[ -n "$PCT_RAW" ] && REMAIN="$(awk -v p="$PCT_RAW" 'BEGIN{printf "%d", p*100 + 0.5}')"

if [ "$FORMAT" = "csv" ]; then
    printf '%s,%s,%s\n' "$VOLTS" "$AMPS" "$REMAIN"
else
    a_disp="${AMPS:-n/a}"; [ -n "$AMPS" ] && a_disp="$AMPS A"
    r_disp="${REMAIN:-n/a}"; [ -n "$REMAIN" ] && r_disp="$REMAIN%"
    printf '%s V  (current: %s, remaining: %s)  [mavros]\n' "$VOLTS" "$a_disp" "$r_disp"
fi
