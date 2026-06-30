# 2026-06-30 — gabby log (BizzyBoat deployment — issue pending)

Deployment issue: pending (backfill from a dev host)
Host: gabby
Side: field
Started: 2026-06-30 09:25 -04:00


**2026-06-30 09:26 -04:00** — deployment mode activated on gabby (field side, issue-less start #533); repo on jazzy, clean tree

**2026-06-30 10:10 -04:00** — mru_transform live active source = fcu on all three (/bizzy/nav/active_sensor/orientation, position, velocity all report 'fcu'). No fail-over to SBG. Matches config sensor_names=[fcu,sbg].

**2026-06-30 10:28 -04:00** — OPERATOR: testing manda coverage again.

**2026-06-30 11:03 -04:00** — OPERATOR: battery draining faster during manda coverage; turning seems to command higher speeds sometimes, likely contributing to the higher drain.

**2026-06-30 11:06 -04:00** — Battery (/bizzy/mavros/battery) at time of note: voltage 26.78 V. current reads ~0.01 A and charge/capacity/percentage are NaN/zero -> no current-sensor telemetry, so instantaneous draw is NOT available from this topic; voltage is the only usable drain indicator.

**2026-06-30 11:14 -04:00** — CONFIRMING DATA — /bizzy/cmd_vel_nav, 94 samples over 20s during manda coverage. Commanded speed min 0.00 / mean 1.62 / max 1.87 m/s; |yaw_rate| up to 1.41 rad/s. Binned: near-straight (|w|<0.05) mean speed 1.48 m/s vs hard-turn (|w|>0.20) mean speed 1.64 m/s. Controller is NOT slowing for turns — commanded speed is slightly HIGHER in turns than on straight legs, at high yaw rates. Supports operator hypothesis: coverage turning holds/raises speed -> high differential thrust both sides -> faster drain. (Single 20s window, small straight-leg n=12.)

**2026-06-30 11:35 -04:00** — ISSUE (wrap-up RCA candidate): manda coverage draws too much power. Supporting data this session — controller does NOT slow for turns; /bizzy/cmd_vel_nav mean speed 1.48 m/s straight vs 1.64 m/s in hard turns (|yaw| up to 1.41 rad/s), so high differential thrust on both sides through the many coverage turnarounds. Survey speed was 3.0 kn, sent WITH the mission (not boat config); levers for later = lower mission speed to 2.5 kn, or override target_speed on the controller (an agent did this in a prior session). MITIGATION NOW: switched to traditional planning for the rest of this run. RCA deferred to post-deployment.

**2026-06-30 12:52 -04:00** — Controller speed param read live: FollowPath.default_speed = 1.4404432 m/s = exactly 2.80 kn (already a hand-set override BELOW the mission's 3.0 kn — matches operator's recollection of a prior agent override). avoid_speed=0.0 (no maneuver slowdown), max_yaw_rate=pi (~uncapped). KEY for RCA: measured turn commanded speed (up to 1.87 m/s / ~3.6 kn) EXCEEDS default_speed 1.44 m/s -> turns add forward speed on top of the straight-line default, so the power sink is in turn handling (uncapped yaw rate + speed overshoot through coverage turnarounds), not just the base survey speed. Lowering default_speed alone wouldn't fully fix it.

**2026-06-30 12:53 -04:00** — ACTION (operator-directed): set FollowPath.default_speed 1.4404432 -> 1.5433333 m/s (2.80 -> 3.00 kn) live on /bizzy/controller_server. Read-back verified 1.5433333 (not a zenoh silent-drop). Runtime override only — a full nav2 relaunch reverts it to YAML; not persisted to nav2_overlay.yaml.

**2026-06-30 12:55 -04:00** — ACTION (operator-directed): set FollowPath.default_speed 1.5433333 -> 1.2861111 m/s (3.00 -> 2.50 kn) live on /bizzy/controller_server. Read-back verified 1.2861111 (not a zenoh silent-drop). Runtime override only — reverts on full nav2 relaunch; not persisted to YAML.

**2026-06-30 12:59 -04:00** — ACTION (operator-directed): set FollowPath.default_speed 1.2861111 -> 1.6462222 m/s (2.50 -> 3.20 kn) live on /bizzy/controller_server. Read-back verified 1.6462222 (not a zenoh silent-drop). Runtime override only — reverts on full nav2 relaunch; not persisted to YAML. Note: 3.2 kt is inside the current pid p=-13 + gain-scheduling validated-stable band (3.0-3.75 kt per config history); watch cross-track weave.

**2026-06-30 12:59 -04:00** — ACTION (operator-directed): set FollowPath.default_speed 1.6462222 -> 1.2861111 m/s (3.20 -> 2.50 kn) live on /bizzy/controller_server. Read-back verified 1.2861111. Runtime override only — reverts on full nav2 relaunch; not persisted to YAML.

**2026-06-30 13:08 -04:00** — Started 10-min (600s) camera capture via record_camera_topics.sh -> ~/data/logs/bizzy_images/bag_2026-06-30T13.08.05_ffmpeg_seg (4 OAK cams ffmpeg+segmentation raw/compressed, TF, diagnostics, robot_description, local_costmap). Began 13:08:05, auto-stops ~13:18. Context: running at FollowPath.default_speed 2.5 kn on traditional planning.

**2026-06-30 13:18 -04:00** — 10-min camera capture complete + verified: 388 MB mcap, clean close. 76521 msgs total; all 4 OAK cams ~2997 msgs each on ffmpeg + segmentation raw/compressed (~5 Hz x 600s, no dropped camera), TF 18578, local_costmap 998. Bag: ~/data/logs/bizzy_images/bag_2026-06-30T13.08.05_ffmpeg_seg.

**2026-06-30 13:32 -04:00** — RCA FINDING (manda coverage waypoint timing): manda_coverage does NOT set times or velocities at survey waypoints. SurveyPath::sendPath (manda_coverage/src/SurveyPath.cpp:384-415) builds each PoseStamped with only frame_id + position.x/y + orientation (adjustPathOrientations); no per-pose header.stamp, no velocity, and path-level stamp also unset. => the survey path carries no speed info and cannot override target speed; FollowPath.default_speed is the sole effective speed source (consistent with our live param changes taking effect). The turn-speed overshoot (commanded > default_speed in turns) therefore comes from controller turn handling (CrabbingPathFollower/AvoidanceController + uncapped max_yaw_rate=pi), not from waypoint timing. RCA should target controller turn behavior.

**2026-06-30 13:53 -04:00** — Started 2-min (120s) camera capture via record_camera_topics.sh -> ~/data/logs/bizzy_images/bag_2026-06-30T13.52.57_ffmpeg_seg. Began 13:52:57, auto-stops ~13:55. Context: FollowPath.default_speed 2.5 kn, traditional planning.

**2026-06-30 13:55 -04:00** — 2-min camera capture complete + verified: 79 MB, clean close, 15259 msgs total; oak_forward ~598 ffmpeg/597 seg (~5 Hz x 120s, cameras nominal). Bag: ~/data/logs/bizzy_images/bag_2026-06-30T13.52.57_ffmpeg_seg.

**2026-06-30 14:41 -04:00** — Started 2-min (120s) camera capture via record_camera_topics.sh -> ~/data/logs/bizzy_images/bag_2026-06-30T14.41.20_ffmpeg_seg. Began 14:41:20, auto-stops ~14:43. Context: FollowPath.default_speed 2.5 kn, traditional planning.

**2026-06-30 14:44 -04:00** — 2-min camera capture complete + verified: 79 MB, clean close, 15244 msgs total; oak_forward ~597 ffmpeg/597 seg (cameras nominal). Bag: ~/data/logs/bizzy_images/bag_2026-06-30T14.41.20_ffmpeg_seg.

**2026-06-30 17:02 -04:00** — Back at the dock (operator-reported) — on-water ops ending, recovery phase.
