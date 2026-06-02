# 2026-06-02 — salmon log (BizzyBoat deployment de8cdad)

Deployment issue: git-bug `de8cdad` — Deployment 2026-06-02: UNH pier shakedown — survey lines + sensor/sonar readiness + OTH (pre-class)
Host: salmon
Side: field
Started: 2026-06-02 13:01 -04:00

> Stamp this salmon-log link under the deployment issue's `## Logs` section
> from dev next time `/start-deployment` runs there (field side is read-only
> on the issue; git-bug has no edit verb here):
> `- [salmon log](docs/logs/2026/2026-06-02_salmon_logs.md)`

**2026-06-02 13:03 -04:00** — operator-side stack up (CAMP / operator app running on salmon).

**2026-06-02 13:06 -04:00** — controls checks done: both RC and USB (joystick) verified good.

**2026-06-02 13:09 -04:00** — ✅ costmap arriving at CAMP **without** the manual `rqt_udp_bridge` subscriber hack — validates costmap-over-bridge fix (#56 / PR #61, merged 2026-06-02). The hack remains the documented fallback if it regresses.

**2026-06-02 13:24 -04:00** — boat in the water (crane launch, UNH pier).

**2026-06-02 14:17 -04:00** — operator reports CAMP heartbeat monitor occasionally flashing red. Probe: `ping -c 10 gabby` from salmon = 0% loss, rtt min/avg/max 1.19/2.44/4.91 ms — link clean at this instant, no sustained loss. Momentary flash consistent with brief jitter (Wi-Fi/radio retransmit, publisher-side CPU spike, or DDS discovery churn) rather than link-down. Flash frequency TBD.

**2026-06-02 14:37 -04:00** — udp_bridge inspection (`/operator/udp_bridge/remotes/bizzy/bridge_info`) re: heartbeat flashes. Two connections to operator remote: `vpn` (salmon.vpn.bizzy.p11.lan) + `wifi` (salmon.op.p11.lan); heartbeat dual-homed on both, period 0.0.
- **No payload loss now:** `message.dropped` & `message.failed` = 0 B/s on both links.
- **VPN path noisy:** duplicate ≈ 6.65 kB/s of 16.5 kB/s received (~40%) — bridge retransmitting before original/ack arrives ⇒ VPN latency/jitter high. Wifi duplicates negligible (63 B/s).
- **Give-ups climbing:** `resend_giveup_count` 133253 → 135902 (+2,649) across ~104k packets (next_packet_number 4,959,494 → 5,063,687) ≈ 2.5% of packets exhaust resend budget — mostly the laggy VPN path; wifi covers the same data.
- **Assessment:** heartbeat flash = a heartbeat packet occasionally losing the resend race on VPN → CAMP shows stale heartbeat → recovers next packet/wifi copy. **Cosmetic while `message.dropped` stays 0.** Revisit only if dropped goes nonzero or it gates control. Deferred to wrap-up: investigate VPN-link latency source (Starlink? VPN MTU/overhead?).

**2026-06-02 14:40 -04:00** — operator: CAMP heartbeat **and GPS boat-position** displays freeze intermittently, but collision-avoidance boxes keep moving. Probe `ros2 topic hz` (operator side, ~9 s window):
- `/bizzy/marine/heartbeat`: steady **1.000 Hz**, min 0.981 / max 1.020 s, std dev 0.01 s — data arriving cleanly, NOT starved.
- `/bizzy/collision_monitor_state`: jittery, max gap ~1.0 s, std dev 0.4–0.7 s.
- **Revised read (corrects the 14:37 VPN lean):** heartbeat data is delivered steadily yet its display still freezes ⇒ freeze is **display/TF-side, not dropped comms**. Selective pattern fits a **frame stall**: heartbeat + GPS position render in the map frame (need the position/tide TF); collision polygons render in the robot frame and keep moving. Leading suspect: intermittent staleness in the **tide/chart_datum → map TF chain** — matches deployment watch items **#157** (`local_costmap` map_tide TF timeout) and **#138** (tide/chart-datum chain).
- **Operationally:** comms healthy; boat-side nav/control (runs onboard) unaffected — this is an operator-SA display issue. Decisive confirmation (deferred / operator's call): watch `map_tide`/`map`→`base_link` TF age for gaps coinciding with the freezes.

**2026-06-02 15:04 -04:00** — tide-TF gap watch + footprint inspection (operator asked: watch map_tide TF; then why no boat footprint in CAMP).
- **Tide TF NOT gapping:** custom watcher on `bizzy/map`→`bizzy/chart_datum` ran 140 s — steady **1.01 Hz**, max gap 1.027 s, **0 gaps >1.6 s**. So the display freezes are NOT a tide-TF stall. (Tide TF baseline rate is only 1 Hz, worth noting, but it's steady.) Freeze root cause still open — leans CAMP-side render; not chased further during live ops.
- **Footprint frame:** `/bizzy/local_costmap/published_footprint` stamped in `bizzy/map_tide`; `bizzy/map`→`bizzy/map_tide` resolves (pure Z −25.157 m, chart-datum offset). Frame is fine.
- **Footprint IS arriving at operator** at ~3.2 Hz (min 0.148/max 0.405 s) — data path healthy, not a comms/TF issue.
- **Likely cause = CAMP-side config / bridge forward-list mismatch.** Bridge forwards ONLY `/bizzy/local_costmap/published_footprint` (PolygonStamped, vpn+wifi). NOT forwarded (remotes: []): `/bizzy/local_costmap/footprint`, `/bizzy/global_costmap/published_footprint`, `/bizzy/global_costmap/footprint`. If CAMP's footprint display subscribes to a global or plain-Polygon footprint topic, it gets nothing.
- **Fix options (operator's call):** point CAMP footprint display at `/bizzy/local_costmap/published_footprint`, OR add CAMP's expected footprint topic to the bridge forward list; also confirm the footprint layer is enabled. Pending: operator to report which topic CAMP's footprint display targets.

**2026-06-02 15:07 -04:00** — footprint root cause found (operator didn't know CAMP's topic; looked it up).
- Running node `/operator/camp` subscribes to exactly: `/bizzy/collision_monitor/slowdown_polygon`, `/bizzy/collision_monitor/stop_polygon` (the boxes shown), `/bizzy/local_costmap/costmap_windowed`. **No footprint topic among them** (`published_footprint` shows Subscription count: 0).
- **CAMP source has ZERO `footprint` references** (grep across both `camp` and `camp2` trees). The collision boxes come from a **dedicated `collision_monitor_manager`** hardwired to the slowdown/stop polygon topics (`src/camp/collision_monitor/collision_monitor_manager.h`), NOT a generic PolygonStamped overlay. General polygon rendering (`geoviz_display.cpp`) consumes `geographic_visualization_msgs`, not nav2 `PolygonStamped`.
- **Conclusion: CAMP does not implement a boat-footprint display.** Not a misconfig, not comms/TF (footprint data healthy at salmon, 3.2 Hz). Showing it needs a small CAMP code change — a footprint display/manager subscribing to `/bizzy/local_costmap/published_footprint`, mirroring the collision-monitor manager.
- **WRAP-UP FOLLOW-UP (feature, not a field fix — sterile cockpit):** add boat-footprint display to CAMP (subscribe `/bizzy/local_costmap/published_footprint`, render as PolygonStamped in `bizzy/map_tide`). File issue against `camp` at wrap-up.

**2026-06-02 15:08 -04:00** — operator restarting CAMP (close → launch auto-restarts) to clear the partial display freeze (some topics frozen, not all). Mitigation; watching whether freeze recurs after re-subscribe.

**2026-06-02 15:11 -04:00** — CAMP back up. `/operator/camp` subscribed to full normal set incl. `/bizzy/marine/heartbeat`, `/bizzy/mavros/global_position/global` (GPS), imu, collision polygons + state, costmap_windowed, path viz, received_global_plan, survey_obstacle_avoidance. **No footprint subscription** in the unfiltered list → re-confirms CAMP footprint feature-gap (earlier "only 3 subs" was a grep-filtered view, not a real before/after — noted to avoid a false restart-fixed-subscriptions claim). Freeze resolution = operator visual confirmation pending (are heartbeat + boat-position updating live now?).

**2026-06-02 15:23 -04:00** — CAMP-overload investigation (operator hypothesis: new boat code raising data rates). Measured rate + bandwidth of all 13 CAMP-subscribed topics (operator side = CAMP input load).
- **Rates all normal** — ceiling 10 Hz: collision slowdown/stop polygons 10.1, GPS `global` 10.0, imu/data 10.0, velocity_body 10.0; heartbeat 1.0, mission_manager status 2.0; costmap_windowed 1.36; path_follower_viz 4.06, received_global_plan 4.0, survey_obstacle_avoidance 4.06; collision_monitor_state & hover_visualization idle. **Nothing flooding by frequency.**
- **Bandwidth — one dominant outlier:** `/bizzy/local_costmap/costmap_windowed` = **640 KB/msg × 1.36 Hz ≈ 953 KB/s**, vs next-heaviest received_global_plan 18 KB/s, survey_obstacle_avoidance 17 KB/s, path_follower_viz 8.6 KB/s, imu 3.4 KB/s, collision polygon 0.85 KB/s. Costmap ≈ **50× all other CAMP topics combined.**
- **Costmap grid:** 800×800 @ 0.25 m = 200 m × 200 m window, 640,000 cells = 640 KB (matches). Frame `bizzy/map_tide`. This is the costmap-over-bridge product (#56/#61, recent) — fits "new code" if window grew.
- **Why it fits the partial freeze:** 640 KB OccupancyGrid rasterized ~1.4×/s on CAMP's Qt thread blocks the event loop → 1 Hz displays (heartbeat/GPS) starve & freeze while 10 Hz collision polygons push through. Also re-explains bridge VPN resends/give-ups: 640 KB fragments into ~640 pkts at `maximum_packet_size` 1000 B (~870 pkt/s), lost fragments → retransmits.
- **Mitigation levers (operator's call):** (1) coarsen windowed costmap 0.25→0.5 m ⇒ 160 KB (4× smaller); (2) throttle bridge period to CAMP (vpn already 2 s; apply to wifi) — operator-side, reversible; (3) shrink window from 200 m. #1/#2 high-leverage. Pending operator decision; not changed during live ops.

**2026-06-02 15:46 -04:00** — boat recovered (out of water). End of on-water segment.

---

## Session wrap-up notes (salmon, 2026-06-02 16:09 -04:00)

**Scope of this host's session:** salmon was the operator station; today's salmon log is almost entirely **CAMP / operator-display diagnostics**. The deployment's stated goals (clean survey-line run, M3/SBG/SVS sensor readiness + recording, OTH re-test) are **not captured here** — if they were exercised they live in the boat-side / gabby log or weren't reached. **Operator to confirm goal outcomes at wrap-up** (this log can't speak to them).

**One root cause tied most display symptoms together — the windowed costmap.**
Confirmed: `/bizzy/local_costmap/costmap_windowed` is **640 KB/msg, ~950 KB/s, 800×800 @ 0.25 m (200 m window)** — ~50× all other CAMP topics combined. This single product plausibly drives:
- CAMP partial freeze (heavy rasterize on the GUI thread starves 1 Hz heartbeat/GPS displays while 10 Hz collision polygons push through),
- bridge VPN resends/give-ups (640 KB fragments into ~640 pkts at `maximum_packet_size` 1000 B).

**Confirmed facts (measured):**
- Costmap size/bandwidth above; all CAMP topic rates ≤10 Hz (nothing too *fast* — the issue is *size*).
- Tide TF `map→chart_datum` steady 1 Hz, **0 gaps >1.6 s in 140 s** → NOT the freeze cause.
- Footprint data healthy at operator (3.2 Hz, frame `map_tide` resolves); CAMP source has **zero footprint display** → footprint-missing is a feature gap, not a misconfig.
- Comms payload loss = 0 (`message.dropped`/`failed` = 0) throughout.

**Hypothesized / NOT proven (don't carry as fact):**
- That costmap render is *the* cause of the freeze — strongly consistent, but no direct observation of a render-block event. The restart "fix" is unconfirmed (restart re-subscribed everything; freeze recurrence not yet retested under load).
- That *new boat code* grew the costmap window — operator's hypothesis; needs a before/after config comparison (not done).
- **Methodology note for future debugging:** two leads were chased and dropped before landing here — first the VPN link (had real resends but they were a *symptom*), then a tide-TF stall (disproved by 140 s watch). Net lesson: measure *bandwidth*, not just rate, early; and a "frozen display" with steady upstream data is a consumer/render problem, not a comms one.

**Carry-forward / wrap-up follow-ups:**
1. **Reduce `costmap_windowed` load** (biggest lever): coarsen 0.25→0.5 m (160 KB, 4×) and/or throttle bridge period to CAMP (vpn already 2 s; apply to wifi). Confirm whether recent costmap-over-bridge work (#56/#61) set 800×800@0.25.
2. **CAMP footprint display** — feature issue against `camp`: subscribe `/bizzy/local_costmap/published_footprint` (PolygonStamped, `map_tide`), mirror the collision-monitor manager.
3. **CAMP render robustness** — confirm whether the OccupancyGrid is rasterized on the Qt main thread; if so, move off-thread so a big costmap can't starve other displays (defends against this class generally).
4. **Bridge fragmentation** — revisit `maximum_packet_size` 1000 B vs. large messages; larger packets / a size-aware path for big grids would cut fragment-loss-driven resends.
5. **Retest freeze under load** after #1 to confirm causation (couldn't prove it live).
6. Stamp this salmon log under the deployment issue's `## Logs` from dev (still pending from activation).
