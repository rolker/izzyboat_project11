# All outages ≥30s on CAMP-watched topics

In-water window: launch_t_ns=1777657709000000000, recovery_t_ns=1777674893000000000, duration=286.4 min
Topics scanned: 7
Total outage instances: 24

## Per-topic outage counts

| Topic | Count | Total s | Median s | Max s |
|---|---:|---:|---:|---:|
| `/bizzy/marine/heartbeat` | 4 | 303 | 71.9 | 147.0 |
| `/bizzy/marine/status/mission_manager` | 2 | 178 | 143.1 | 143.1 |
| `/marine/platforms` | 2 | 122 | 74.0 | 74.0 |
| `/bizzy/odom` | 4 | 412 | 108.2 | 185.7 |
| `/bizzy/hover_visualization` | 4 | 307 | 85.5 | 141.2 |
| `/bizzy/local_costmap/costmap` | 5 | 321 | 37.0 | 165.0 |
| `/bizzy/local_costmap/published_footprint` | 3 | 219 | 68.4 | 108.3 |

## Clustered 'all-red' events (4)

Outages within 30 s of each other are merged into one event.

| # | Start (EDT) | End (EDT) | Total dur (s) | N topics affected | Topics |
|---|---|---|---:|---:|---|
| 1 | 16:51:09 | 16:51:46 | 37.0 | 2 | costmap, odom |
| 2 | 16:54:59 | 16:55:36 | 37.0 | 1 | costmap |
| 3 | 17:22:41 | 17:23:18 | 37.0 | 2 | heartbeat, hover_visualization |
| 4 | 17:24:06 | 17:32:57 | 531.2 | 7 | costmap, heartbeat, hover_visualization, mission_manager, odom, platforms, published_footprint |

## Detail — events affecting ≥4 CAMP topics


### Event 1: 17:24:06 → 17:32:57 (min 216 after launch)

- `hover_visualization`: 17:24:50 → 17:25:36  (46.0 s)
- `hover_visualization`: 17:25:54 → 17:28:16  (141.2 s)
- `hover_visualization`: 17:31:09 → 17:32:34  (85.5 s)
- `costmap`: 17:24:06 → 17:24:39  (33.1 s)
- `costmap`: 17:26:55 → 17:29:40  (165.0 s)
- `costmap`: 17:32:02 → 17:32:53  (50.9 s)
- `published_footprint`: 17:28:17 → 17:29:25  (68.4 s)
- `published_footprint`: 17:30:07 → 17:30:49  (42.0 s)
- `published_footprint`: 17:31:09 → 17:32:57  (108.3 s)
- `heartbeat`: 17:24:50 → 17:25:37  (47.0 s)
- `heartbeat`: 17:26:49 → 17:29:16  (147.0 s)
- `heartbeat`: 17:31:41 → 17:32:53  (71.9 s)
- `mission_manager`: 17:26:26 → 17:27:00  (34.6 s)
- `mission_manager`: 17:27:11 → 17:29:34  (143.1 s)
- `odom`: 17:24:14 → 17:25:42  (87.4 s)
- `odom`: 17:26:23 → 17:29:29  (185.7 s)
- `odom`: 17:30:46 → 17:32:34  (108.2 s)
- `platforms`: 17:28:03 → 17:29:17  (74.0 s)
- `platforms`: 17:31:31 → 17:32:20  (48.5 s)
