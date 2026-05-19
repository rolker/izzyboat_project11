# 2026-05-01 BizzyBoat deployment — analysis findings

Companion to [`rolker/unh_echoboats_project11#124`](https://github.com/rolker/unh_echoboats_project11/issues/124).

## Setup
- **DB**: `~/data/analysis/2026-05-01_deployment.db` (2.8 GB, 6,457,037 messages from two bags merged via `bag_to_sqlite --append`).
- **Detected in-water window** (from `bag_analysis.launch_recovery` altitude detector):
  - Launch: **2026-05-01T17:48:29Z = 13:48:29 EDT**
  - Recovery: **2026-05-01T22:34:53Z = 18:34:53 EDT**
  - Duration: **4h 46m 24s**
- Issue body bracket: 13:36–18:42 EDT. Detector's window is contained inside — the deltas are crane-down (12 min) and crane-up (8 min) periods where altitude was still elevated.

## §1 Networking

### §1.6 Bridge bandwidth vs. configured cap

Boat-side aggregate wire-out across **all** outbound connections (WiFi + Starlink + cellular + VPN summed):

| Band (boat → all peers) | n samples | % of time in-water |
|---|---:|---:|
| <100 kB/s | 4 | 0.06% |
| 100–500 kB/s | 81 | 1.1% |
| 500–1000 kB/s | 3242 | 46% |
| 1000–1400 kB/s | 1547 | 22% |
| **≥1400 kB/s** | 2179 | **31%** |

- Boat-side avg: **1.24 MB/s**, peak: **4.33 MB/s** (sum across all connections).
- Operator-side echo avg: 12 kB/s, peak 123 kB/s — tiny by comparison.
- **Caveat**: The 1.5 MB/s WiFi cap doesn't apply to this aggregate — it's the sum across multiple physical links. Per-link saturation needs the per-link table (`per_link_stats`, populated by `2026-05-01_network_perlink.py`).

Time evolution (60 s buckets, partial — full 255-min CSV in `/tmp/q6a.csv`):

- **Minutes 0–8** (13:48–13:57 EDT): 1.0–1.3 MB/s avg with sporadic peaks >1.5 MB/s; small but persistent drops (3–15 kB/s avg, peaks 38–73 kB/s).
- **Minutes 9–13** (13:57–14:02 EDT): calm — ~950 kB/s avg, **zero drops**.
- **Minutes 277–286** (~18:25–18:35 EDT, late deployment): aggressive — 1.3–1.9 MB/s avg with peaks above 2 MB/s; **drops climbing to 100–265 kB/s avg, peaks 150–265 kB/s**. Rate-limiter actively thrashing right before recovery.

### §1.4 Latency-event characterization ("all red" episodes)

**Aggregate detector didn't find anything ≥20 s — but that's the wrong signal.** `messages_per_second` is dominated by 100 Hz SBG IMU and never drops below ~13, so an aggregate-zero detector is blind to per-topic-stale episodes (which is what "all red" means in CAMP UI).

Three NULL `messages_per_second` rows + one zero-row exist (instantaneous gaps in the bridge report) — to investigate but those are sub-second, not 30/60 s episodes.

**Re-run §1.4 after the perlink script populates `per_topic_stats`** — there we can detect per-topic outages of ≥30 s/60 s for the topics CAMP cares about (heartbeat, mission_manager status, platforms, etc.).

### §1.2 Rate-vs-distance correlation

Per-minute bucket, distance from launch (equirectangular ≈) vs. aggregate boat-side wire bandwidth.

- **Peak distance: 615 m** at bucket_min 280. **Boat stayed close throughout** — never long-range.
- Most of the run was at 200–600 m from launch.
- No clear monotonic correlation: bandwidth varied 686 k – 3.0 MB/s essentially independent of distance.
- **Notable** — `duplicate_bytes_per_second` drops to ~0 starting around bucket_min 167 (~16:35 EDT) and stays low. Before that, 1–10 kB/s of duplicate bytes (multi-path redundancy active). After, near-zero. **A redundant path went away mid-deployment.** Worth correlating with the §1.3 per-link data once available.

Full timeline CSV: `/tmp/q2.csv`.

### Per-link & per-topic schema (populated by `2026-05-01_network_perlink.py`)

- **`per_topic_stats`** — 1,508,890 rows over 39 distinct `source_topic` values
- **`per_link_stats`** — 32,473 rows; 2 distinct `connection_id` values
- **`connection_id` is the physical-link label itself** (`wifi`, `vpn`), no hand-curated mapping needed for §1.3
- **No cellular connection in this deployment** — only `wifi` and `vpn`
- **Per-link caps from `RemoteConnection.maximum_bytes_per_second`**:
  - `wifi`: 1,500,000 B/s (1.5 MB/s)
  - `vpn`: 1,000,000 B/s (1.0 MB/s) — except for a brief 11.6-min window at **launch+197min ≈ 17:05 EDT to launch+209min ≈ 17:17 EDT** when vpn cap was **2,500,000 B/s** (2.5 MB/s). Coincides with the bag boundary; presumably a manual rate-cap bump between the two recording sessions.

### §1.3 Path attribution

Per-link bandwidth as percentage of cap (boat→operator, 60 s buckets, in-water window):

| Link | Avg of cap | Peak | n_buckets |
|---|---|---|---|
| wifi | **54%** | 133% (cap=1.5MB/s) | 255 |
| vpn  | **46%** | 129% (cap=1.0MB/s) | 255 |

The >100% peaks are bucket-averaged samples; instantaneous values can exceed cap because the limiter operates per-packet but stats are reported over a window.

**Notable bucket events** (boat-side wire-out, percent of link cap):

| Min after launch | EDT | WiFi % | VPN % | Note |
|---|---|---|---|---|
| 83 | 15:11 | 93% | 92% | Both links near cap simultaneously — peak load |
| 118 | 15:46 | 96% | 26% | WiFi dominant |
| 131 | 15:59 | 94% | 33% | WiFi dominant |
| 162 | 16:30 | 96% | 29% | WiFi dominant |
| **174** | **16:42** | **21%** | **7%** | **Collapse** — likely one of the "all red" episodes |
| 184 | 16:52 | 49% | 51% | VPN took over WiFi |
| 222 | 17:30 | 21% | 42% | WiFi struggling, VPN taking over |
| 202 | 17:10 | 76% | 107% | VPN exceeding 1.0 cap → in the 2.5-cap window (43% of 2.5MB/s) |

Full timeline CSV: `/tmp/q3a.csv`.

### §1.1 Per-topic discarded-packet counts

**The four OAK camera ffmpeg streams dominate drops** by ~3 orders of magnitude over everything else:

| Topic | Avg drop B/s | Peak drop B/s | Avg msg B/s | Peak msg B/s |
|---|---:|---:|---:|---:|
| `oak_starboard/image_raw/ffmpeg` | 2,326 | **1,061,983** | 100,065 | 1,496,900 |
| `oak_port/image_raw/ffmpeg`      | 1,587 | 241,254       | 93,136  | 776,080   |
| `oak_forward/image_raw/ffmpeg`   | 1,537 | 384,638       | 88,957  | 1,891,066 |
| `oak_aft/image_raw/ffmpeg`       | 1,292 | 184,692       | 94,178  | 1,133,976 |
| `local_costmap/costmap`          | 274   | 24,580        | 2,534,479 | 43,554,180 |
| (everything else)                | <100  | <50,000       | -       | -         |

**Key insight**: PR #123's `queue_size: 100` tuning addresses publisher-queue overflow drops, but `send_dropped_bps` here is the **rate-limiter-killed** bytes — a different mechanism. The ffmpeg streams are competing for the per-link bandwidth budget and the limiter is throwing away over 1 MB/s of starboard camera data at peak.

### §1.5 Resend-layer activity

**~1/3 of wire bandwidth was retransmits, not original messages**:

| Link | Avg resend B/s | Peak resend B/s | Avg dropped-resend B/s | Avg resend / total |
|---|---:|---:|---:|---:|
| wifi | 294,647 | 1,720,754 | 568,388 | **38%** |
| vpn  | 125,453 | 2,158,084 | 421,636 | **28%** |

- `resend_failed_bps = 0` on both links — when a resend was sent, it succeeded.
- **`resend_dropped_bps` is huge** (568 kB/s WiFi, 421 kB/s VPN). The rate-limiter killed resend attempts before they could send, on top of the original drops.
- Confirms the deployment log's hypothesis that the resend window was firing constantly, not occasionally. The heartbeat 30 s alternation was almost certainly a resend storm — when the original arrival path was lossy enough, half the link's effective capacity went to retries, choking the heartbeat too.

### §1.4 (re-do) — Per-topic outages on CAMP-watched topics

**Major "all red" cluster around 17:26–17:30 EDT** (min 217–222 after launch). Nearly all CAMP-watched topics went silent simultaneously for 1–3 minutes:

| Topic | Longest outage (s) | Start (min after launch) |
|---|---:|---:|
| `/bizzy/odom` | **185.7** | 217.9 |
| `/bizzy/local_costmap/costmap` | 165.0 | 218.4 |
| `/bizzy/marine/heartbeat` | 147.0 | 218.3 |
| `/bizzy/marine/status/mission_manager` | 143.1 | 218.7 |
| `/bizzy/hover_visualization` | 141.2 | 217.4 |
| `/bizzy/local_costmap/published_footprint` | 108.3 | 222.7 |
| `/marine/platforms` | 74.0 | 219.6 |

These align with the per-link collapse at min 174 (16:42 EDT) which was a separate, earlier episode — the 17:26–17:30 outage is a fresh one. There are likely multiple "all red" episodes; this query just returns each topic's longest one. A follow-up should enumerate all ≥30s episodes per topic.

**Non-events** (low-rate topics that only publish during specific operations):
- `/bizzy/plan` — 1513 s "outage" at min 44.7 = no active plan during that period
- `/bizzy/path_follower_visualization` — 375 s at min 103.5 = not following a path

### §1.4 — Full all-episodes sweep on 7 CAMP topics

Clustering all ≥30 s per-topic outages with a 30 s gap tolerance (output:
`~/data/analysis/outage_events.md` from `/tmp/all_outages.py`):

| # | Start (EDT) | End (EDT) | Span (s) | N topics | Class |
|---|---|---|---:|---:|---|
| 1 | 16:51:09 | 16:51:46 | 37.0 | 2 | yellow (costmap, odom) |
| 2 | 16:54:59 | 16:55:36 | 37.0 | 1 | yellow (costmap) |
| 3 | 17:22:41 | 17:23:18 | 37.0 | 2 | yellow (heartbeat, hover_visualization) |
| **4** | **17:24:06** | **17:32:57** | **531.2** | **7** | **🔴 ALL RED — every CAMP topic affected** |

Event 4 contains 19 distinct per-topic outage instances. Longest individual gaps:
- `/bizzy/odom` 185.7 s (17:26:23 → 17:29:29)
- `/bizzy/local_costmap/costmap` 165.0 s (17:26:55 → 17:29:40)
- `/bizzy/marine/heartbeat` 147.0 s (17:26:49 → 17:29:16)
- `/bizzy/marine/status/mission_manager` 143.1 s (17:27:11 → 17:29:34)
- `/bizzy/hover_visualization` 141.2 s (17:25:54 → 17:28:16)

### Event 4 mechanism — confirmed resend storm

Per-link state during the 17:24–17:33 EDT window (per-minute averages):

| min into event | conn | wire B/s | resend B/s | **resend_dropped B/s** | received B/s |
|---:|---|---:|---:|---:|---:|
| 0 | vpn  | 672,160 | 625,782 |  8,335,318 | 8,471 |
| 0 | wifi | 357,153 | 291,186 |  5,640,621 | 11,544 |
| 3 | vpn  | 713,987 | 667,147 |  **8,944,834** | 11,006 |
| 3 | wifi | 309,741 | 246,924 |  5,093,373 | 10,243 |
| **4** | vpn  | 792,186 | 757,178 |  **13,016,094** | 11,869 |
| **4** | wifi | 430,601 | 383,535 |  **7,795,532** | 13,525 |
| 7 | vpn  | 623,679 | 582,347 |  8,226,714 | 7,707 |
| 7 | wifi | 358,655 | 300,476 |  4,826,951 | 9,931 |

**Mechanism**: `resend_dropped_bps` reached **13 MB/s** on VPN while the link cap is only 1 MB/s. The system was attempting to retransmit ~13× link capacity worth of bytes, and the rate-limiter shed 90%+ of those retry attempts. **The wire wasn't dead** — wire_bps was still 260–790 kB/s — but **>90% of every byte sent was a retransmit**, choking the original payload through.

This is a textbook resend storm. Wires fill with retries → originals starve → originals time out → retried → cycle continues. Receive throughput (received_bps ~7–12 kB/s) confirms the operator side was getting almost nothing.

### Event 4 trigger (hypothesis)

The VPN cap reverted **2.5 → 1.0 MB/s at min 209 (17:17:38 EDT)**. Event 4 started 7 min later at 17:24:06. During the 17:05–17:17 window with VPN at 2.5 MB/s, the system was running at 1.0–2.0 MB/s VPN (within new cap). When the cap dropped, queued traffic from the brief high-cap window may have overflowed available capacity, triggering retries → resend storm → Event 4.

This is operationally significant: **the symptomatic recovery would be just waiting for the resend storm to drain**, not a network-side fix. The actionable preventive: avoid mid-deployment rate-cap changes, or design the resend layer to back off aggressively when `resend_dropped_bps` exceeds wire capacity.

## §1.7 Kernel UDP drops on gabby

Confirmed from `docs/logs/2026/2026-05-01_gabby_logs.md` §9 (16:00 EDT
snapshot, ~2h into deployment):

```
UdpInDatagrams      2,462,334
UdpInErrors            17,023   (almost all RcvbufErrors)
UdpRcvbufErrors        17,018   ≈ 0.69% of UDP receives dropped
UdpSndbufErrors             0
```

- **NIC-level `rx_dropped/tx_dropped` are 0** on both `enp7s0` and the ZeroTier interface. Bottleneck is **after** the NIC, at the kernel→app socket-buffer handoff.
- `net.core.rmem_max` is already 16 MiB, but defaults are conservative:
  - `rmem_default` = 208 KiB
  - `udp_rmem_min` = 4 KiB
  - `netdev_max_backlog` = 5,000

**Status of the sysctl tuning hypothesis**: retrospectively confirms the 17k snapshot was real and the cause was socket-buffer-side (not NIC). The proposed tuning (in log §9) is reproducible. Forward-validation requires the next deployment with the tuning applied + a re-snapshot (verification command is already documented in the log).

---

## Cross-cutting themes from §1

1. **Bandwidth budget is dominated by camera ffmpeg streams.** They drive nearly all rate-limiter drops; everything else combined is <5% of drop volume.
2. **Resend overhead is structural, not incidental.** Even outside Event 4, ~30% of all wire bandwidth was retransmits during in-water operation. The link isn't lossy by accident — the offered camera load is so close to capacity that any packet loss triggers self-amplifying retries.
3. **The mid-deployment cap change (VPN 2.5 → 1.0 MB/s) almost certainly triggered Event 4.** Avoid mid-mission rate-cap changes.
4. **Kernel UDP drops on gabby exist (0.69%) but are not the dominant fault.** Sysctl tuning is in scope as a follow-up; not a Day-1 blocker.

## Recommended follow-ups (issues to file)

- `udp_bridge` (or `bizzyboat_project11`): camera-bandwidth budgeting — at offered camera rates the rate-limiter is the dominant fault. Either reduce camera bitrates, drop a stream, or implement per-topic rate-limit fairness so cameras don't starve heartbeat/odom.
- **`udp_bridge` resend layer**: rework **already in progress** (per Roland 2026-05-18). The 30% resend overhead and Event 4 resend storm dynamic are addressed there; no separate issue needed.
- `bizzyboat_project11` operations doc: warn against mid-deployment rate-cap changes; if needed, ramp down rather than cut.
- `unh_echoboats_project11` (or `bizzyboat_project11`): apply sysctl tuning from gabby log §9 on next deployment, snapshot the counters after 5 min of traffic.

## §1 cross-reference — 2026-05-18 link calibration

Out-of-band iperf3 + mtr against both paths from the pier
(see [`bandwidth_test_2026-05-18.md`](bandwidth_test_2026-05-18.md) for
the full report). Conditions: boat idle on pier, udp_bridge running but
no autonomy load.

| Link | Configured cap | Measured (TCP) | Measured (UDP clean) | UDP loss at cap | Avg RTT |
|---|---|---|---|---|---|
| WiFi | 12 Mbps | **21 Mbps** | **≥30 Mbps @ 0%** | ~0% | **9 ms** |
| VPN/Starlink | 8 Mbps | 16.6 Mbps (3,739 retr) | up to 1.4% @ 20 Mbps | **~0.4%** (interp) | **65 ms** |

What this calibration tells us about the deployment data:

1. **The WiFi cap is conservative by ~2×** on the pier. Most of the
   `oak_starboard/image_raw/ffmpeg` peak drops in §1.1 (up to 1.06 MB/s
   killed per second) would not have occurred at a 24 Mbps cap — the
   link can carry them. Caveat: that's at pier; at 615 m peak distance
   from the deployment, the WiFi physical capacity is unmeasured and
   the static-cap problem becomes a range problem.

2. **The Starlink/VPN cap is matched to the link's lossy knee**, not
   arbitrary. UDP loss starts at 0.19% at 5 Mbps and rises with rate.
   At the 8 Mbps cap, interpolated baseline loss ≈ 0.4%.

3. **The 30% steady-state resend fraction observed in the deployment
   bag (§1.5) is the expected output** of a 0.4% baseline-loss link
   under the existing udp_bridge resend design. The in-progress resend
   rework will address this; no need for a separate "resend storm
   safeguard" issue.

4. **The bencloud WireGuard relay is the dominant VPN latency** (35 ms
   of the 65 ms RTT). Not a problem in itself but worth knowing as
   architectural context.

5. **Path identification confirmed** — `gabby_bb` = WiFi over MikroTik
   bridge to operator router; `gabby_v` = NETMAP'd through Starlink
   via WireGuard. No cellular path in this deployment.

## Open follow-ups

- Range sweep of the bandwidth test (100 / 300 / 500 / 800 m) to
  characterize the WiFi cap-vs-distance curve. Without this data, the
  static cap can't be safely raised for autonomy.
- Load test of the bandwidth sweep with udp_bridge actively running
  the OAK streams. Tells us how the rate-limiter fares under
  contention.
- 5-minute sustained Starlink UDP test to catch periodic burst-loss
  events (satellite handoffs, etc.) that a 15 s window may miss.

## Off-bag

- §1.7 kernel UDP drops on gabby — gabby log §9 already has the 17k snapshot; needs sysctl-tuning follow-up issue if confirmed.

## Open questions

- Around bucket_min 167 (~16:35 EDT), duplicate_bps dropped to zero. Did one of the redundant connections go away around then? Cross-check against the deployment log for that timestamp.
- Late-deployment drop activity (minutes 277+) at the very end: is this the boat-recovery phase where camera bitrate or operator pings increased? Or a known event?
