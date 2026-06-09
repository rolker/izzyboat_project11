#!/bin/bash
# record_sidescan_debug.sh — Ad-hoc bag capture of ALL Garmin GCV
# sidescan driver-node topics plus /diagnostics, for offline debugging
# of the `garmin_sidescan` driver.
#
# The driver only publishes its raw byte stream (the debug/raw* topics)
# when its `debug_raw` runtime param is true. This script enables it for
# the duration of the capture and restores it to false on exit (including
# on error or Ctrl-C, via a trap). `debug_raw` is set over the parameter
# service; under rmw_zenoh a `param set` can silently drop, so each set is
# verified with a `param get`.
#
# Usage: ./record_sidescan_debug.sh [duration_secs]
#   duration_secs: recording length in seconds (default: 60)
#
# Writes a zstd-compressed mcap bag to:
#   ~/data/logs/bizzy_sidescan/bag_<timestamp>_sidescan_raw/
#
# Shuts down via SIGINT so rosbag2 flushes the mcap cleanly.

set -eo pipefail

DURATION="${1:-60}"
NODE="/bizzy/sensors/sidescan/garmin_sidescan"

if ! command -v ros2 >/dev/null 2>&1; then
    echo "error: 'ros2' not on PATH — source the workspace environment first" >&2
    exit 1
fi

OUT_DIR="${HOME}/data/logs/bizzy_sidescan/bag_$(date +%Y-%m-%dT%H.%M.%S)_sidescan_raw"

# Every topic published or subscribed under the driver node, plus the
# global aggregated /diagnostics (the driver contributes its own
# DiagnosticArray there). change_state is the driver's command input —
# recorded so a capture shows both the commands issued and the device's
# response.
TOPICS=(
    /diagnostics
    "${NODE}/change_state"
    "${NODE}/debug/raw"
    "${NODE}/debug/raw_config"
    "${NODE}/debug/raw_status"
    "${NODE}/sonar_image_down"
    "${NODE}/sonar_image_port"
    "${NODE}/sonar_image_starboard"
    "${NODE}/state"
    "${NODE}/status"
    "${NODE}/transmitting"
)

# set_debug_raw <true|false> — set the param and confirm it took
# (rmw_zenoh can report success while silently dropping the RPC).
set_debug_raw() {
    local want="$1" got
    ros2 param set "${NODE}" debug_raw "${want}" >/dev/null 2>&1 || true
    got=$(ros2 param get "${NODE}" debug_raw 2>/dev/null \
        | grep -oiE 'true|false' | tr '[:upper:]' '[:lower:]')
    [[ "${got}" == "${want}" ]] && return 0
    echo "warning: debug_raw reads '${got:-unknown}', wanted '${want}'" >&2
    return 1
}

restore_debug_raw() {
    echo "=== restoring debug_raw=false ==="
    set_debug_raw false \
        || echo "warning: could not confirm debug_raw=false — check manually" >&2
}
trap restore_debug_raw EXIT

echo "=== enabling debug_raw on ${NODE} ==="
if ! set_debug_raw true; then
    echo "error: failed to enable debug_raw — is the driver node up?" >&2
    exit 1
fi

echo "=== Recording for ${DURATION}s to ${OUT_DIR} ==="

# `timeout` returns 124 when it fires the signal; that's the normal path.
# `--disable-keyboard-controls` keeps rosbag2 out of TTY mode — otherwise
# `timeout`'s new process group gets SIGTTOU-stopped on terminal access
# and the pending SIGINT never fires (see record_camera_topics.sh).
set +e
timeout --signal=INT "${DURATION}" ros2 bag record \
    --disable-keyboard-controls \
    -s mcap --storage-preset-profile zstd_fast \
    -o "${OUT_DIR}" \
    --topics "${TOPICS[@]}"
rc=$?
set -e

if [[ ${rc} -eq 0 || ${rc} -eq 124 ]]; then
    echo "=== Recording complete: ${OUT_DIR} ==="
    exit 0
fi

echo "error: ros2 bag record exited with code ${rc}" >&2
exit "${rc}"
