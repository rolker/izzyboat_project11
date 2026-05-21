-- Per-topic / per-link / resend queries.
-- Run after 2026-05-01_network_perlink.py has populated:
--   per_topic_stats   (one row per (t_ns, source_topic) sample)
--   per_link_stats    (one row per (t_ns, remote_name, connection_id) sample)

-- ============================================================================
-- §1.1  Per-topic discarded-packet counts
-- ============================================================================
-- Q1a: ranked list of topics by total send_dropped bytes during in-water window.
-- send_dropped_bps is "rate-limiter killed these before they hit the wire".
WITH win AS (
  SELECT (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='launch_t_ns')   AS lo,
         (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='recovery_t_ns') AS hi
)
SELECT
  source_topic,
  COUNT(*)                              AS samples,
  ROUND(AVG(message_bytes_per_second), 0) AS avg_msg_bps,
  ROUND(MAX(message_bytes_per_second), 0) AS peak_msg_bps,
  ROUND(AVG(send_dropped_bps), 0)       AS avg_dropped_bps,
  ROUND(MAX(send_dropped_bps), 0)       AS peak_dropped_bps,
  ROUND(SUM(send_dropped_bps), 0)       AS total_dropped_byte_seconds,  -- proxy for "total dropped volume"
  ROUND(AVG(send_failed_bps), 0)        AS avg_failed_bps
FROM per_topic_stats, win
WHERE t_ns BETWEEN win.lo AND win.hi
  AND sample_origin = 'boat'  -- boat-side mirror is authoritative for outbound drops
GROUP BY source_topic
HAVING SUM(send_dropped_bps) > 0 OR SUM(send_failed_bps) > 0
ORDER BY total_dropped_byte_seconds DESC, peak_dropped_bps DESC
LIMIT 25;

-- Q1b: same idea but for topics that were *attempted* but barely got through
-- (high message_bps with high dropped_bps — the rate-limit pressure points).
WITH win AS (
  SELECT (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='launch_t_ns')   AS lo,
         (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='recovery_t_ns') AS hi
)
SELECT
  source_topic,
  ROUND(AVG(send_dropped_bps) / NULLIF(AVG(message_bytes_per_second + send_dropped_bps), 0), 3)
    AS drop_fraction,
  ROUND(AVG(message_bytes_per_second), 0) AS avg_thru_bps,
  ROUND(AVG(send_dropped_bps), 0)         AS avg_drop_bps,
  COUNT(*)                                AS samples
FROM per_topic_stats, win
WHERE t_ns BETWEEN win.lo AND win.hi
  AND sample_origin = 'boat'
GROUP BY source_topic
HAVING AVG(message_bytes_per_second + send_dropped_bps) > 100  -- ignore inactive topics
ORDER BY drop_fraction DESC, avg_drop_bps DESC
LIMIT 25;

-- ============================================================================
-- §1.3  Path attribution per minute (which physical link carried traffic)
-- ============================================================================
-- BridgeInfo's per-connection breakdown carries the link identity via
-- (host, ip_address, port) on each RemoteConnection. The connection_id is
-- the stable name we can group by. We don't have direct WiFi/Starlink/cellular
-- labels — Q3b is the lookup table you'd hand-curate once.

-- Q3a: minute-bucketed bandwidth per connection_id.
WITH win AS (
  SELECT (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='launch_t_ns')   AS lo,
         (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='recovery_t_ns') AS hi
)
SELECT
  CAST((t_ns - win.lo) / 60e9 AS INTEGER)              AS bucket_min,
  connection_id,
  ip_address,
  ROUND(AVG(message_success_bps + overhead_success_bps + resend_success_bps), 0)
    AS wire_bps_avg,
  ROUND(MAX(message_success_bps + overhead_success_bps + resend_success_bps), 0)
    AS wire_bps_max,
  ROUND(AVG(received_bps), 0)         AS received_bps_avg,
  ROUND(AVG(duplicate_bps), 0)        AS duplicate_bps_avg
FROM per_link_stats, win
WHERE t_ns BETWEEN win.lo AND win.hi
  AND sample_origin = 'boat'
  AND remote_name = 'operator'
GROUP BY bucket_min, connection_id
ORDER BY bucket_min, wire_bps_avg DESC;

-- Q3b: distinct connections seen during the deployment + their share of total
-- wire bytes. Use this to label which connection_id corresponds to which
-- physical link (cross-reference with the bizzyboat.yaml `connections:` block).
WITH win AS (
  SELECT (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='launch_t_ns')   AS lo,
         (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='recovery_t_ns') AS hi
)
SELECT
  connection_id,
  ip_address,
  host,
  port,
  maximum_bytes_per_second  AS cap_bps,
  COUNT(*)                  AS samples,
  ROUND(AVG(message_success_bps + overhead_success_bps + resend_success_bps), 0)
    AS avg_wire_bps,
  ROUND(MAX(message_success_bps + overhead_success_bps + resend_success_bps), 0)
    AS peak_wire_bps
FROM per_link_stats, win
WHERE t_ns BETWEEN win.lo AND win.hi
  AND sample_origin = 'boat'
GROUP BY connection_id
ORDER BY avg_wire_bps DESC;

-- ============================================================================
-- §1.5  Resend-layer activity
-- ============================================================================
-- The resend layer kicks in for missing-packet recovery (5 s window default).
-- Hypothesis from the deployment story: heartbeat 30 s alternation was caused
-- by the resend window firing on a flaky link. Confirm/refute by showing
-- resend bps as a fraction of total wire bps, time-bucketed.

-- Q5a: minute-bucketed resend bytes per connection.
WITH win AS (
  SELECT (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='launch_t_ns')   AS lo,
         (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='recovery_t_ns') AS hi
)
SELECT
  CAST((t_ns - win.lo) / 60e9 AS INTEGER) AS bucket_min,
  connection_id,
  ROUND(AVG(resend_success_bps), 0)       AS resend_success_bps,
  ROUND(AVG(resend_failed_bps), 0)        AS resend_failed_bps,
  ROUND(AVG(resend_dropped_bps), 0)       AS resend_dropped_bps,
  ROUND(AVG(resend_success_bps) /
        NULLIF(AVG(message_success_bps + overhead_success_bps + resend_success_bps), 0), 3)
    AS resend_fraction
FROM per_link_stats, win
WHERE t_ns BETWEEN win.lo AND win.hi
  AND sample_origin = 'boat'
  AND remote_name = 'operator'
GROUP BY bucket_min, connection_id
HAVING resend_success_bps > 0
ORDER BY bucket_min, resend_fraction DESC;

-- Q5b: episodes of sustained heavy resend (>= 10% of wire for >= 30 s).
-- Helps test the heartbeat-alternation hypothesis: when resend was hot,
-- did heartbeat publication go quiet on the other side?
WITH win AS (
  SELECT (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='launch_t_ns')   AS lo,
         (SELECT CAST(value AS INTEGER) FROM _bag_meta WHERE key='recovery_t_ns') AS hi
),
flagged AS (
  SELECT t_ns, connection_id,
         (resend_success_bps >
          0.10 * NULLIF(message_success_bps + overhead_success_bps + resend_success_bps, 0)) AS hot
  FROM per_link_stats, win
  WHERE t_ns BETWEEN win.lo AND win.hi
    AND sample_origin = 'boat'
    AND remote_name = 'operator'
),
runs AS (
  -- Tabibitosan run-grouping: per_link_stats publishes at ~1 Hz, so
  -- t_ns - ROW_NUMBER()*1e9 is constant across consecutive samples in
  -- a run. Matches the pattern in network_queries.sql Q4a (line 95).
  -- Computed in a CTE because SQLite doesn't allow window functions
  -- directly inside GROUP BY expressions.
  SELECT t_ns, connection_id,
         t_ns - ROW_NUMBER() OVER (PARTITION BY connection_id ORDER BY t_ns) * 1000000000 AS run_key
  FROM flagged
  WHERE hot = 1
)
SELECT
  connection_id,
  MIN(t_ns) AS start_t_ns,
  MAX(t_ns) AS end_t_ns,
  ROUND((MAX(t_ns) - MIN(t_ns)) / 1e9, 1) AS duration_s
FROM runs
GROUP BY connection_id, run_key
HAVING duration_s >= 30
ORDER BY start_t_ns;
