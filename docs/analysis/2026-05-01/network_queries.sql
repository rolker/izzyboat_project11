-- Network analysis queries for 2026-05-01 BizzyBoat deployment.
-- Companion to unh_echoboats_project11#124 §1 (Networking / udp_bridge).
--
-- Run against: ~/data/analysis/2026-05-01_deployment.db
-- All time values are nanoseconds since Unix epoch (UTC) in t_ns columns.
-- The in-water window is _bag_meta.launch_t_ns ... _bag_meta.recovery_t_ns;
-- every analysis query filters to that window unless explicitly noted.
--
-- Convention: bps = bytes per second (×8 for bits per second). The udp_bridge
-- *_bytes_per_second fields are bytes/sec, NOT bits/sec.

-- ============================================================================
-- Setup: window bounds, named for reuse below.
-- ============================================================================

-- Sanity check — show the detected in-water window and bag inventory.
SELECT key, value FROM _bag_meta WHERE key IN
  ('launch_t_ns', 'recovery_t_ns', 'bag_count', 'robot_namespace');
SELECT * FROM _bags;

-- ============================================================================
-- §1.6  Bridge bandwidth vs. configured cap (SQLite-only)
-- ============================================================================
-- bizzyboat.yaml caps:
--   wifi:     1_500_000 B/s (12 Mbps)
--   vpn:        300_000 B/s ( 2.4 Mbps)   -- TODO: confirm exact figure
--   cellular:    50_000 B/s (   0.4 Mbps) -- TODO: confirm exact figure
-- wire_out_bytes_per_second already excludes the rate-limiter's dropped
-- bytes (per extractor docstring), so this is what actually hit the wire.

-- Q6a: 60-second-bucketed wire bandwidth + drop rate, full deployment.
WITH win AS (
  SELECT (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='launch_t_ns')   AS lo,
         (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='recovery_t_ns') AS hi
)
SELECT
  CAST((bi.t_ns - win.lo) / 60e9 AS INTEGER) AS bucket_min,
  ROUND(AVG(bi.wire_out_bytes_per_second), 0)      AS wire_out_bps_avg,
  ROUND(MAX(bi.wire_out_bytes_per_second), 0)      AS wire_out_bps_max,
  ROUND(AVG(ts.send_dropped_bytes_per_second), 0)  AS dropped_bps_avg,
  ROUND(MAX(ts.send_dropped_bytes_per_second), 0)  AS dropped_bps_max,
  ROUND(AVG(ts.send_failed_bytes_per_second), 0)   AS failed_bps_avg,
  COUNT(*)                                         AS n_samples
FROM t_bizzy_udp_bridge_bridge_info bi
JOIN t_bizzy_udp_bridge_topic_statistics ts
  ON ts.t_ns BETWEEN bi.t_ns - 500000000 AND bi.t_ns + 500000000
JOIN win
WHERE bi.t_ns BETWEEN win.lo AND win.hi
GROUP BY bucket_min
ORDER BY bucket_min;

-- Q6b: count of seconds spent in each wire-bandwidth band.
-- Helps visualise "how often did we saturate".
WITH win AS (
  SELECT (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='launch_t_ns')   AS lo,
         (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='recovery_t_ns') AS hi
),
banded AS (
  SELECT
    CASE
      WHEN wire_out_bytes_per_second <  100000 THEN '0  <100  kB/s'
      WHEN wire_out_bytes_per_second <  500000 THEN '1  100-500 kB/s'
      WHEN wire_out_bytes_per_second < 1000000 THEN '2  500-1000 kB/s'
      WHEN wire_out_bytes_per_second < 1400000 THEN '3  1000-1400 kB/s'
      ELSE                                          '4  >=1400 kB/s (saturated)'
    END AS band
  FROM t_bizzy_udp_bridge_bridge_info, win
  WHERE t_ns BETWEEN win.lo AND win.hi
)
SELECT band, COUNT(*) AS n_seconds
FROM banded
GROUP BY band
ORDER BY band;

-- ============================================================================
-- §1.4  Latency-event characterization (SQLite-only)
-- ============================================================================
-- "All red" episodes: stretches where outbound traffic collapsed.
-- Definition: messages_per_second went to near-zero for >= 20 s.

-- Q4a: continuous outage spans (>= 20 s with messages_per_second < 1.0).
-- Uses the windowing trick: rank by run id derived from gap-detection.
WITH win AS (
  SELECT (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='launch_t_ns')   AS lo,
         (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='recovery_t_ns') AS hi
),
flagged AS (
  SELECT t_ns, messages_per_second,
         (messages_per_second < 1.0) AS in_outage
  FROM t_bizzy_udp_bridge_topic_statistics, win
  WHERE t_ns BETWEEN win.lo AND win.hi
),
runs AS (
  SELECT t_ns, messages_per_second, in_outage,
         t_ns - ROW_NUMBER() OVER (PARTITION BY in_outage ORDER BY t_ns) * 1000000000 AS run_key
  FROM flagged
)
SELECT
  in_outage,
  MIN(t_ns)                                 AS start_t_ns,
  MAX(t_ns)                                 AS end_t_ns,
  ROUND((MAX(t_ns) - MIN(t_ns)) / 1e9, 1)   AS duration_s,
  COUNT(*)                                  AS samples,
  ROUND(AVG(messages_per_second), 2)        AS avg_msgs_per_s
FROM runs
WHERE in_outage = 1
GROUP BY in_outage, run_key
HAVING duration_s >= 20
ORDER BY start_t_ns;

-- Q4b: bandwidth + drops just before, during, and after each detected outage.
-- (Run after Q4a to pick specific start_t_ns values to drill into.)
-- Template — substitute :outage_start_t_ns:
--   SELECT t_ns, messages_per_second, message_bytes_per_second,
--          send_dropped_bytes_per_second, send_failed_bytes_per_second
--   FROM t_bizzy_udp_bridge_topic_statistics
--   WHERE t_ns BETWEEN :outage_start_t_ns - 30000000000
--                  AND :outage_start_t_ns + 90000000000
--   ORDER BY t_ns;

-- ============================================================================
-- §1.2  Rate-vs-distance correlation (SQLite-only)
-- ============================================================================
-- Distance from launch position vs. bridge bandwidth.
-- Uses mavros/global_position/global to compute geodesic distance from the
-- launch fix. ASSUMES launch position ≈ first FIX_2D-or-better sample.

-- Q2: 60-s bucketed distance from launch vs. average bridge bandwidth.
-- Note: SQLite has no haversine — approximate with equirectangular at
-- this latitude (Portsmouth NH, ~43.07°N, 1° lat ≈ 111 km, 1° lon ≈
-- cos(43.07°) × 111 km ≈ 81 km). Good to ±0.5% for sub-km distances.
WITH win AS (
  SELECT (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='launch_t_ns')   AS lo,
         (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='recovery_t_ns') AS hi
),
fix AS (
  SELECT t_ns, latitude, longitude
  FROM t_bizzy_mavros_global_position_global, win
  WHERE t_ns BETWEEN win.lo AND win.hi
    AND latitude IS NOT NULL AND longitude IS NOT NULL
    AND ABS(latitude) > 0.001 AND ABS(longitude) > 0.001
),
launch_fix AS (
  SELECT latitude AS lat0, longitude AS lon0 FROM fix ORDER BY t_ns LIMIT 1
),
dist AS (
  SELECT
    f.t_ns,
    -- equirectangular distance in metres
    SQRT(
      POWER((f.latitude  - lf.lat0) * 111000, 2) +
      POWER((f.longitude - lf.lon0) * 111000 * 0.731, 2)
    ) AS dist_m
  FROM fix f, launch_fix lf
)
SELECT
  CAST((bi.t_ns - win.lo) / 60e9 AS INTEGER) AS bucket_min,
  ROUND(AVG(d.dist_m), 1)                          AS dist_m_avg,
  ROUND(MAX(d.dist_m), 1)                          AS dist_m_max,
  ROUND(AVG(bi.wire_out_bytes_per_second), 0)      AS wire_out_bps_avg,
  ROUND(AVG(bi.duplicate_bytes_per_second), 0)     AS duplicate_bps_avg
FROM t_bizzy_udp_bridge_bridge_info bi
JOIN dist d ON d.t_ns BETWEEN bi.t_ns - 500000000 AND bi.t_ns + 500000000
JOIN win
WHERE bi.t_ns BETWEEN win.lo AND win.hi
GROUP BY bucket_min
ORDER BY bucket_min;
