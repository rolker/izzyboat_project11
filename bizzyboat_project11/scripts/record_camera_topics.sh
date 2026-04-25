#!/bin/bash
# record_camera_topics.sh — Ad-hoc bag capture of OAK camera ffmpeg +
# segmentation/compressed topics, plus /diagnostics and /tf[_static].
#
# Usage: ./record_camera_topics.sh [duration_secs]
#   duration_secs: recording length in seconds (default: 120)
#
# Writes an mcap bag (zstd_fast) to:
#   ~/data/logs/bizzy_images/bag_<timestamp>_ffmpeg_seg/
#
# Shuts down via SIGINT so rosbag2 flushes the mcap cleanly.

set -eo pipefail

DURATION="${1:-120}"

if ! command -v ros2 >/dev/null 2>&1; then
    echo "error: 'ros2' not on PATH — source the workspace environment first" >&2
    exit 1
fi

OUT_DIR="${HOME}/data/logs/bizzy_images/bag_$(date +%Y-%m-%dT%H.%M.%S)_ffmpeg_seg"

TOPICS=(
    /diagnostics
    /tf
    /tf_static
    /bizzy/sensors/cameras/oak_forward/image_raw/ffmpeg
    /bizzy/sensors/cameras/oak_starboard/image_raw/ffmpeg
    /bizzy/sensors/cameras/oak_aft/image_raw/ffmpeg
    /bizzy/sensors/cameras/oak_port/image_raw/ffmpeg
    /bizzy/sensors/cameras/oak_forward/camera_info
    /bizzy/sensors/cameras/oak_starboard/camera_info
    /bizzy/sensors/cameras/oak_aft/camera_info
    /bizzy/sensors/cameras/oak_port/camera_info
    /bizzy/sensors/cameras/oak_forward/segmentation/compressed
    /bizzy/sensors/cameras/oak_starboard/segmentation/compressed
    /bizzy/sensors/cameras/oak_aft/segmentation/compressed
    /bizzy/sensors/cameras/oak_port/segmentation/compressed
    /bizzy/sensors/cameras/oak_forward/segmentation/camera_info
    /bizzy/sensors/cameras/oak_starboard/segmentation/camera_info
    /bizzy/sensors/cameras/oak_aft/segmentation/camera_info
    /bizzy/sensors/cameras/oak_port/segmentation/camera_info
)

echo "=== Recording for ${DURATION}s to ${OUT_DIR} ==="

# `timeout` returns 124 when it fires the signal; that's the normal path here.
set +e
# `--disable-keyboard-controls` prevents rosbag2 from putting the terminal into
# TTY mode for its SPACE-to-pause feature. Without it, `timeout` places the
# recorder in a new process group and the kernel SIGTTOU-stops the recorder
# the moment it touches the terminal — the pending timeout signal never fires.
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
