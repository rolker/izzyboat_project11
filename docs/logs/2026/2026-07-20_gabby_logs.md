# 2026-07-20 — gabby log (BizzyBoat deployment — issue pending)

Deployment issue: pending (backfill from a dev host)
Host: gabby
Side: field
Started: 2026-07-20 12:25 -04:00

**2026-07-20 12:26 -04:00** — Deployment mode activated on gabby (issue-less field start; backfill link from dev).

**2026-07-20 12:26 -04:00** — OAK cameras: reinstalled rotated one position (90 deg). Reassigned mx_id->direction in oak_cameras_launch.py so each slot points at the device now looking that way (fwd<-stbd, stbd<-aft, aft<-port, port<-fwd); per-view H.265 tuning stays keyed to direction. Operator relaunched and confirmed views correct. Committed 7c19742 on jazzy (not yet pushed to gitcloud).

**2026-07-20 12:26 -04:00** — M3 multibeam verified publishing + logging: /bizzy/sensors/m3/sonar_info live with pulse_lengths=[2.0e-05 s], bandwidths=[50000], tx_signal_types=[1/CW], model kongsberg-m3. sonar_logger writing to ~/data/logs/bizzyboat_sonar/2026-07-20T16-01-38+00-00/; sonar_info counts 0/0/51/62 across segments _0.._3, detections 0/0/5052/5389 — M3 came online ~12:11-12:16, first two segments have no M3 data.

**2026-07-20 12:38 -04:00** — Camera mast tilt investigation (operator: shoreline painted as obstacles ~35m ahead after new mast brace). Estimated tilt from fwd vs aft segmentation horizons vs TF. Design pitch both cams -5.16 deg vs hull; boat trim -1.47 deg bow-down (in TF). Image water-line elevation (gravity ref): fwd -4.30, aft -5.07. Offset (image-TF): fwd +2.32 (up), aft -1.38 (down) -> opposite-signed = rigid mast pitch. delta=(fwd-aft)/2 = ~1.85 deg bow-up (forward cam looks up ~1.8-1.9 deg vs URDF), under-projects shoreline to nearer range. Caveats: 96px seg output (~0.6 deg/row), single frame, both views look at land (no clean horizon), common-mode residual +0.47 deg. Real fix: +~1.85 deg pitch on camera mount in camera_oak.xacro (rebuild). Live mitigation: sea_surface_layer.maximum_range (currently 150) clip below 35.

**2026-07-20 12:58 -04:00** — Applied camera mast tilt correction to URDF (bizzyboat.urdf.xacro): added common bizzy/camera_mast frame (child of base_link at 0.31,0,1.41) with rpy pitch -0.0323 rad (-1.85 deg, bow-up); reparented all 4 OAK cameras to it (positions unchanged, zero offset). Net: forward down-tilt 5.16->3.31 deg (up 1.85), aft 5.16->7.01 deg (down 1.85), matching measured antisymmetric offset. Modeled at mast level (not cam_tilt) so aft correctly goes down not up. xacro expands OK. NOT committed. Requires rebuild (install(DIRECTORY) copies urdf; publish_state_launch loads from share path) before relaunch to take effect. Roll component unmeasured.

**2026-07-20 13:01 -04:00** — make build OK (all 5 layers success). Verified camera_mast + cam_mast_pitch (-1.85 deg) present in installed share xacro (platforms_ws/install/.../urdf/bizzyboat.urdf.xacro). Ready for operator relaunch to test tilt correction.

**2026-07-20 13:45 -04:00** — Started 10-min (600s) camera recording via record_camera_topics.sh -> ~/data/logs/bizzy_images/bag_2026-07-20T13.45.16_ffmpeg_seg (4x ffmpeg video + segmentation + camera_info, TF, robot_description, local_costmap). Captures post-URDF-tilt-correction state (robot_description now carries camera_mast -1.85 deg).

**2026-07-20 14:04 -04:00** — 10-min recording complete/clean: 599.3s, 396MB, 76518 msgs. fwd video 2996 / fwd segmentation 2997 (~5Hz), local_costmap 998, robot_description latched (post-correction geometry). Bag: ~/data/logs/bizzy_images/bag_2026-07-20T13.45.16_ffmpeg_seg.
