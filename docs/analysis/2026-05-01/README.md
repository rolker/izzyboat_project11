# 2026-05-01 BizzyBoat deployment — post-mission analysis

Companion to:

- [#121](https://github.com/rolker/unh_echoboats_project11/issues/121) — the deployment
- [#124](https://github.com/rolker/unh_echoboats_project11/issues/124) — post-mission review issue (this work covers §1 networking)
- [`../../logs/2026/2026-05-01_dev_logs.md`](../../logs/2026/2026-05-01_dev_logs.md) — dev-side deployment log (analysis trail summarised in the "Post-mission analysis" section)

## Contents

| File | Purpose |
|---|---|
| [`findings.md`](findings.md) | Full §1 networking analysis. Headlines: WiFi cap conservative by ~2× at pier; Starlink/VPN cap matched to lossy knee; 30% resend overhead is structural; one 9-min "all red" event explained as a resend storm triggered by mid-mission cap change. |
| [`outage_events.md`](outage_events.md) | Catalog of all per-topic outages ≥30 s on CAMP-watched topics during the in-water window; clustered into "events." |
| [`starlink_only_budget.md`](starlink_only_budget.md) | Camera vs essentials bandwidth split, decision matrix for Starlink-only over-horizon operation. |
| [`bandwidth_test_2026-05-18.md`](bandwidth_test_2026-05-18.md) | Pier iperf3 + mtr calibration of WiFi and Starlink/VPN, run on 2026-05-18 to feed the §1 interpretation. |
| [`network_queries.sql`](network_queries.sql) | SQL queries that produced §1.2 / §1.4 / §1.6 against the SQLite extract of the deployment bags. |
| [`network_perlink_queries.sql`](network_perlink_queries.sql) | Per-topic and per-link queries (§1.1 / §1.3 / §1.5) against the supplementary `per_topic_stats` and `per_link_stats` tables. |

## Issues filed from this analysis

- [`unh_echoboats_project11#130`](https://github.com/rolker/unh_echoboats_project11/issues/130) — Field validation: over-horizon Starlink-only operation
- [`unh_echoboats_project11#131`](https://github.com/rolker/unh_echoboats_project11/issues/131) — gabby: apply sysctl UDP receive-buffer tuning
- [`rolker/udp_bridge#19`](https://github.com/rolker/udp_bridge/issues/19) — Add per-topic priority/class scheduling to the rate-limiter

## Reproducibility — local-only artifacts

These files reference some artifacts that are **not** in this repo
because they are derived or oversized:

- **`2026-05-01_deployment.db`** (2.8 GB) — the merged SQLite extract
  of the two deployment bags. Regenerate with
  `ros2 run bag_analysis bag_to_sqlite` (and `--append` for the second
  bag); the exact bag paths used are recorded in `_bag_meta.source_bag_paths`
  inside the DB.
- **`network_perlink.py`** — the bag-walker that populates the
  supplementary `per_topic_stats` and `per_link_stats` tables. Currently
  lives at `~/data/analysis/2026-05-01_network_perlink.py` on the dev
  workstation; should move into
  [`rolker/marine_tools`](https://github.com/rolker/marine_tools)'s
  `bag_analysis` package as a reusable extractor (follow-up — see
  #124).
- **Bag files** — recorded on gabby during deployment; pulled to dev
  workstation under `~/data/logs/bizzyboat/2026-05-01T*` for analysis.

All of the analysis files in this directory are intended to be
self-contained for read-only reference. The data the queries operate on
can be regenerated; the prose conclusions stand on their own.
