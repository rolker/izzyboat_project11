"""Operator-side rosbag2 recorder for BizzyBoat deployments.

Records the topics needed to debug operator-side wedge events: aggregated
diagnostics (boat-side forwarded over udp_bridge + salmon-local op-side
monitor nodes), operator-originated commands, udp_bridge's own stats
(top-level + per-remote), rosout, and TF.

The output directory is computed in this launch file (not a shell wrapper)
so the recorder can be auto-launched as part of operator_core_launch.py
the same way every other operator subsystem is. Layout:

    ~/data/logs/operator/<YYYY-MM-DD>/diagnostics_<HH.MM.SS>/

Per-day parent dir so multiple deployments in a day group naturally; one
bag-dir per launch. Path under ${HOME} so this runs without root.

Use ``record_diagnostics:=false`` to suppress recording (sim/dev). Default
is true: deployment-launches always record.

Storage is mcap + zstd_fast for parity with bizzyboat_project11/scripts/
record_camera_topics.sh; diagnostics is low-rate so the profile choice
doesn't change disk meaningfully, but consistency keeps later mcap
tooling work uniform across boat-side and op-side bags.

Lifecycle gotcha (carried over from record_camera_topics.sh): rosbag2
puts the terminal in TTY mode for its SPACE-to-pause feature. Without
``--disable-keyboard-controls``, a process-group SIGTTOU stops the
recorder when launch tries to shut it down and the bag never flushes.
"""

import os
from datetime import datetime

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration


# Topics: see PLAN_ISSUE-97.md for the why behind each entry.
RECORD_TOPICS = [
    '/diagnostics',
    '/bizzy/marine/command',
    '/bizzy/piloting_mode/manual/helm',
    '/operator/udp_bridge/topic_statistics',
    '/operator/udp_bridge/bridge_info',
    '/operator/udp_bridge/remotes/bizzy/topic_statistics',
    '/operator/udp_bridge/remotes/bizzy/bridge_info',
    '/rosout',
    '/tf',
    '/tf_static',
]


def generate_launch_description():
    record_diagnostics_arg = DeclareLaunchArgument(
        'record_diagnostics',
        default_value='true',
        description='Record operator-side diagnostics + command bag during this launch',
    )

    now = datetime.now()
    day_dir = now.strftime('%Y-%m-%d')
    bag_name = now.strftime('diagnostics_%H.%M.%S')
    out_dir = os.path.expanduser(
        f'~/data/logs/operator/{day_dir}/{bag_name}')

    record_cmd = [
        'ros2', 'bag', 'record',
        '--disable-keyboard-controls',
        '-s', 'mcap',
        '--storage-preset-profile', 'zstd_fast',
        '-o', out_dir,
        '--topics', *RECORD_TOPICS,
    ]

    bag_recorder = ExecuteProcess(
        cmd=record_cmd,
        name='operator_bag_recorder',
        output='screen',
        # Send SIGINT first so rosbag2 flushes the mcap cleanly. Generous
        # SIGTERM timeout because mcap finalization on a large bag can
        # take a few seconds.
        sigterm_timeout='15',
        sigkill_timeout='5',
        respawn=False,
        condition=IfCondition(LaunchConfiguration('record_diagnostics')),
    )

    return LaunchDescription([
        record_diagnostics_arg,
        bag_recorder,
    ])
