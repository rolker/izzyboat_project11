#!/bin/bash

# Gracefully stop the project11 tmux session.
# Works for both boat-side and operator-side sessions.
# Sends SIGINT to each window, verifies exit, then kills the session.
#
# Usage: stop_tmux_project11.bash [session]   (default: project11)
#        e.g. stop_tmux_project11.bash camera_test

SESSION="${1:-project11}"
# Seconds to wait for the non-zenoh windows to exit after their Ctrl-C, as one
# shared wall-clock budget (they are all Ctrl-C'd before the wait begins, so
# they shut down concurrently -- a per-window budget would multiply this by the
# window count for no benefit). Must exceed the longest shutdown grace any
# window's launch file grants a child: the rosbag2 recorders in
# logging_launch.py use sigterm_timeout=15 + sigkill_timeout=5, so a window can
# legitimately take 20 s to go away (#458).
#
# This is a grace, not a guarantee: if the budget runs out the script warns and
# kill-sessions anyway, which SIGHUPs whatever is still finalizing. The warning
# is the signal that a bag may be truncated -- if you see it, check the bag
# before trusting the run rather than assuming the wait covered it.
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

# Wait for non-zenoh processes to exit. One shared deadline for all of them:
# every window already has its Ctrl-C, so their shutdowns overlap.
echo "  Waiting for processes to exit (up to ${SHUTDOWN_TIMEOUT}s)..."
SECONDS=0
for window in $WINDOWS; do
    while [ $SECONDS -lt $SHUTDOWN_TIMEOUT ]; do
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
    done
    if [ $SECONDS -ge $SHUTDOWN_TIMEOUT ]; then
        echo "    WARNING: $window still running after ${SHUTDOWN_TIMEOUT}s;" \
             "killing the session will truncate anything it is still writing"
    fi
done

# Now stop zenoh router
if /usr/bin/tmux list-windows -t "$SESSION" -F '#{window_name}' | grep -q '^zenoh$'; then
    echo "  Stopping zenoh router..."
    /usr/bin/tmux send-keys -t "${SESSION}:zenoh" C-c 2>/dev/null
    # Its own budget: zenoh is Ctrl-C'd only once the rest are down.
    SECONDS=0
    while [ $SECONDS -lt $SHUTDOWN_TIMEOUT ]; do
        pane_pid=$(/usr/bin/tmux list-panes -t "${SESSION}:zenoh" -F '#{pane_pid}' 2>/dev/null | head -1)
        if [ -z "$pane_pid" ]; then
            break
        fi
        children=$(pgrep -P "$pane_pid" 2>/dev/null | wc -l)
        if [ "$children" -eq 0 ]; then
            break
        fi
        sleep 1
    done
    if [ $SECONDS -ge $SHUTDOWN_TIMEOUT ]; then
        echo "    WARNING: zenoh did not stop within ${SHUTDOWN_TIMEOUT}s"
    fi
fi

# Kill the tmux session
echo "  Killing tmux session..."
/usr/bin/tmux kill-session -t "$SESSION"
echo "Done. Session '$SESSION' stopped."
