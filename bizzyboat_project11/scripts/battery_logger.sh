#!/bin/bash
# battery_logger.sh — Append one battery sample to a daily CSV. Cron-driven.
#
# Designed to run every minute from cron and keep a continuous battery record
# regardless of whether the ROS stack is up:
#
#   * /dev/fcu FREE  (stack down) -> read the FCU directly  (fcu_battery.sh)
#   * /dev/fcu BUSY  (stack up)   -> read MAVROS's topic     (mavros_battery.sh)
#   * neither yields a reading     -> log nothing (a gap in the series)
#
# The port-held check (`fuser`) is the gate: "stack up" == "something holds
# /dev/fcu". Reading the FCU directly while MAVROS holds the port would steal
# bytes from the live link, so we never do — we switch to the ROS topic instead.
#
# Output: ~/data/logs/bizzy_battery/battery_YYYY-MM-DD.csv
#   columns: timestamp,voltage_v,current_a,remaining_pct,source
#   timestamp is ISO-8601 with offset; source is "fcu" or "mavros".
#   NOTE: BizzyBoat has NO current sensor — current_a is not a real measurement.
#   It is blank from the FCU (reports -1/unknown) and may be blank, 0, or NaN
#   from MAVROS. Do not treat current_a as valid; voltage_v is the real signal.
#
# A flock guards against overlapping runs: an FCU-off read can block several
# seconds waiting for a heartbeat, longer than nothing, so a slow run must not
# pile up under the per-minute schedule.
#
# Usage: ./battery_logger.sh        (intended for cron; safe to run by hand)
# Cron:  * * * * * /home/field/project11/layers/main/platforms_ws/src/unh_echoboats_project11/bizzyboat_project11/scripts/battery_logger.sh

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVICE="${BIZZY_FCU_DEVICE:-/dev/fcu}"
LOG_DIR="${BIZZY_BATTERY_LOG_DIR:-$HOME/data/logs/bizzy_battery}"
LOCK_FILE="${TMPDIR:-/tmp}/bizzy_battery_logger.lock"
HEADER="timestamp,voltage_v,current_a,remaining_pct,source"

# --- never overlap ----------------------------------------------------------
exec 9>"$LOCK_FILE"
flock -n 9 || exit 0   # a previous run is still going; skip this tick

# --- pick a source based on who holds the port ------------------------------
# fuser -s: exit 0 if any process has the device open, 1 if none. We treat a
# held port as "stack up -> read MAVROS". A missing device (FCU unplugged) is
# neither held nor readable directly, so we still fall to the FCU branch, which
# reports the device-missing case and yields no sample (-> gap), as intended.
if fuser -s "$DEVICE" 2>/dev/null; then
    SOURCE="mavros"
    CSV="$("$SCRIPT_DIR/mavros_battery.sh" --csv 2>/dev/null)" || CSV=""
else
    SOURCE="fcu"
    CSV="$("$SCRIPT_DIR/fcu_battery.sh" --csv "$DEVICE" 2>/dev/null)" || CSV=""
fi

# --- log nothing if we got nothing ------------------------------------------
# Require a non-empty leading voltage field; an empty/garbled read is a gap.
VOLT_FIELD="${CSV%%,*}"
if [ -z "$CSV" ] || [ -z "$VOLT_FIELD" ]; then
    exit 0
fi

# --- append (creating the dated file with a header) -------------------------
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/battery_$(date +%F).csv"
if [ ! -s "$LOG_FILE" ]; then
    printf '%s\n' "$HEADER" >>"$LOG_FILE"
fi
printf '%s,%s,%s\n' "$(date -Is)" "$CSV" "$SOURCE" >>"$LOG_FILE"
