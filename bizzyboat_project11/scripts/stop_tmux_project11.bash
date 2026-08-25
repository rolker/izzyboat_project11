#!/bin/bash

# Gracefully stop the project11 tmux session.
# Works for both boat-side and operator-side sessions.
# Sends SIGINT to each window, verifies exit, then kills the session.
#
# Usage: stop_tmux_project11.bash [session]   (default: project11)
#        e.g. stop_tmux_project11.bash camera_test

SESSION="${1:-project11}"
# Seconds to wait per window after Ctrl-C. Must exceed the longest
# shutdown grace any window's launch file grants a child: the rosbag2
# recorders in logging_launch.py use sigterm_timeout=15 + sigkill_timeout=5,
# so a window can legitimately take 20 s to go away. A shorter timeout here
# would let kill-session SIGHUP a recorder mid-mcap-finalization and truncate
# the boat's data of record (#458).
SHUTDOWN_TIMEOUT=25

if ! /usr/bin/tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "No tmux session '$SESSION' is running."
    exit 0
fi

echo "Stopping tmux session '$SESSION'..."

# Get list of windows (excluding zenoh — stopped last)
WINDOWS=$(/usr/bin/tmux list-windows -t "$SESSION" -F '#{window_name}' | grep -v '^zenoh$')

# Stop all non-zenoh windows first
for window in $WINDOWS; do
    echo "  Stopping window: $window"
    /usr/bin/tmux send-keys -t "${SESSION}:${window}" C-c 2>/dev/null
done

# Wait for non-zenoh processes to exit
echo "  Waiting for processes to exit (up to ${SHUTDOWN_TIMEOUT}s)..."
for window in $WINDOWS; do
    elapsed=0
    while [ $elapsed -lt $SHUTDOWN_TIMEOUT ]; do
        # Check if pane still has a running foreground process (not just a shell prompt)
        pane_pid=$(/usr/bin/tmux list-panes -t "${SESSION}:${window}" -F '#{pane_pid}' 2>/dev/null | head -1)
        if [ -z "$pane_pid" ]; then
            break  # window gone
        fi
        # Count children of the shell — if only the shell remains, process exited
        children=$(pgrep -P "$pane_pid" 2>/dev/null | wc -l)
        if [ "$children" -eq 0 ]; then
            break
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    if [ $elapsed -ge $SHUTDOWN_TIMEOUT ]; then
        echo "    WARNING: $window did not stop within ${SHUTDOWN_TIMEOUT}s"
    fi
done

# Now stop zenoh router
if /usr/bin/tmux list-windows -t "$SESSION" -F '#{window_name}' | grep -q '^zenoh$'; then
    echo "  Stopping zenoh router..."
    /usr/bin/tmux send-keys -t "${SESSION}:zenoh" C-c 2>/dev/null
    elapsed=0
    while [ $elapsed -lt $SHUTDOWN_TIMEOUT ]; do
        pane_pid=$(/usr/bin/tmux list-panes -t "${SESSION}:zenoh" -F '#{pane_pid}' 2>/dev/null | head -1)
        if [ -z "$pane_pid" ]; then
            break
        fi
        children=$(pgrep -P "$pane_pid" 2>/dev/null | wc -l)
        if [ "$children" -eq 0 ]; then
            break
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    if [ $elapsed -ge $SHUTDOWN_TIMEOUT ]; then
        echo "    WARNING: zenoh did not stop within ${SHUTDOWN_TIMEOUT}s"
    fi
fi

# Kill the tmux session
echo "  Killing tmux session..."
/usr/bin/tmux kill-session -t "$SESSION"
echo "Done. Session '$SESSION' stopped."
