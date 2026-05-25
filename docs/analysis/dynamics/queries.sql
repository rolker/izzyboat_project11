-- Reference SQL for BizzyBoat performance characterization (#124 §2).
-- Run against a per-deployment extract, e.g. ~/data/logs/analysis/2026-05-01_deployment.db
-- All times are nanoseconds since Unix epoch (UTC) in t_ns columns.
-- The circle-fit / surge-fit analysis itself lives in dynamics.py /
-- dynamics_extra.py (it needs least-squares, not expressible in SQL);
-- these queries cover the parts that are.

-- ============================================================================
-- Throttle-channel identification
-- ============================================================================
-- ch_0/ch_1 are the two ESC (throttle) outputs and move together; ch_2/ch_3
-- are the vectored-thrust steering servos (sit near 1500 centre). ch_0 is the
-- throttle variable used throughout the analysis.
SELECT 'ch_0' AS chan, MIN(ch_0), ROUND(AVG(ch_0)) avg, MAX(ch_0) FROM t_bizzy_mavros_rc_out
UNION ALL SELECT 'ch_1', MIN(ch_1), ROUND(AVG(ch_1)), MAX(ch_1) FROM t_bizzy_mavros_rc_out
UNION ALL SELECT 'ch_2', MIN(ch_2), ROUND(AVG(ch_2)), MAX(ch_2) FROM t_bizzy_mavros_rc_out
UNION ALL SELECT 'ch_3', MIN(ch_3), ROUND(AVG(ch_3)), MAX(ch_3) FROM t_bizzy_mavros_rc_out;

-- ============================================================================
-- In-water window (where present)
-- ============================================================================
SELECT key, value FROM _bag_meta WHERE key IN ('launch_t_ns', 'recovery_t_ns');

-- ============================================================================
-- Heading-contamination demonstration (why current removal is required)
-- ============================================================================
-- At a FIXED full-throttle (ch_0 >= 1950) the raw speed-over-ground varies
-- 3x with heading, because tidal current adds/subtracts along the leg. This
-- is the artefact the circle fit removes: binning speed by PWM alone (the
-- 2026-04-24 method) is biased by whatever heading mix the mission ran.
-- COG bucket = compass octant of the gps_vel ENU vector (vel_x=E, vel_y=N).
SELECT
  CAST((DEGREES(ATAN2(vel_x, vel_y)) + 360) / 45 AS INTEGER) % 8 AS cog_octant,
  COUNT(*)                                         AS n,
  ROUND(AVG(SQRT(vel_x*vel_x + vel_y*vel_y)), 2)   AS sog_avg_ms,
  ROUND(MAX(SQRT(vel_x*vel_x + vel_y*vel_y)), 2)   AS sog_max_ms
FROM t_bizzy_mavros_global_position_raw_gps_vel gv
JOIN t_bizzy_mavros_rc_out rc
  ON rc.t_ns BETWEEN gv.t_ns - 100000000 AND gv.t_ns + 100000000
WHERE rc.ch_0 >= 1950
GROUP BY cog_octant
ORDER BY cog_octant;
