# Starlink-only operation budget — over-horizon survey

Companion analysis to:
- [`rolker/unh_echoboats_project11#124`](https://github.com/rolker/unh_echoboats_project11/issues/124) — post-mission review of the 2026-05-01 deployment
- [`findings.md`](findings.md) — networking findings
- [`bandwidth_test_2026-05-18.md`](bandwidth_test_2026-05-18.md) — link calibration

**Goal context**: over-horizon survey work requires the boat to operate over Starlink only — WiFi will be out of range and we cannot count on it for control or visibility.

## What was measured (2026-05-01 deployment, VPN connection)

Demand split by category, summed across topics in each bucket. Numbers are
per-topic averages summed within the bucket; peaks per individual topic can
be ~10× higher because of H.264/H.265 IDR keyframes.

| Bucket | Topics on VPN | Avg offered | Drop % | Notes |
|---|---:|---:|---:|---|
| **A. camera ffmpeg** (forward, starboard, port) | 3 | **2.27 Mbps** | 2–3% | aft was WiFi-only |
| B. segmentation overlay (compressed) | 4 | 0.08 Mbps | <1% | low-rate |
| C. seg `camera_info` | 1 | 0.015 Mbps | 0% | trivial |
| E. mavros (FCU state) | 7 | 0.069 Mbps | <1% | |
| F. mission / heartbeat / status | 4 | 0.018 Mbps | <1% | |
| G. odom | 1 | 0.050 Mbps | 0% | |
| I. tf | 1 | 0.044 Mbps | 1% | |
| J. diagnostics | 1 | 0.133 Mbps | <1% | |
| K. plan / viz / hover | 2 | 0.057 Mbps | 0% | only when active |
| **Total VPN offered** | — | **~2.75 Mbps** | — | average; ignores keyframe-coincident peaks |

`/bizzy/local_costmap/*` (~6.4 Mbps avg combined) was **WiFi-only** by config; not
currently a Starlink-essential. Same for `oak_aft_ffmpeg` and several segmentation
streams.

## What Starlink delivers (2026-05-18 pier calibration)

`iperf3 -u -l 1400` UDP loss curve, 65 ms RTT (gabby → bencloud WireGuard → salmon):

| Offered | Loss |
|---:|---:|
| 5 Mbps | 0.19% |
| 8 Mbps (configured cap) | ~0.4% interpolated |
| 10 Mbps | 0.6% |
| 15 Mbps | 1.2% |
| 20 Mbps | 1.4% |

Loss is structural (present even far below cap), not capacity-bound. Loss rate climbs
roughly linearly with offered rate.

## Headroom analysis — what fits, what doesn't

Average demand (2.75 Mbps) sits well below the lossy knee (~5 Mbps). The problem is
peaks. Each individual ffmpeg camera *peaked* (single-second worst) at:

- oak_forward: 14.8 Mbps
- oak_port: 7.9 Mbps
- oak_starboard: 20.0 Mbps

These are H.264/H.265 IDR keyframes. Three cameras keyframing simultaneously can
spike combined demand to 30–40 Mbps on a link with ~10 Mbps "no-significant-loss"
capacity — which is exactly what produced the §1.1 starboard 1.06 MB/s peak drop in
the deployment data.

Current encoder config (verified 2026-05-19 in
[`bizzyboat_project11/launch/oak_cameras_launch.py`](../../../bizzyboat_project11/launch/oak_cameras_launch.py)
L9–18): **all four OAK cameras are at `h265_bitrate_kbps: 800`**, default
`h265_keyframe_frequency_frames: 30` and **`fps: 5`** (`camera_base.hpp:21`
default, no override) → **6 s GOP**, profile `H265_MAIN`. Rate control mode
is not set, inherits depthai property default **CBR**. The 2.27 Mbps VPN
average matches the configured target faithfully — the encoder is hitting
CBR, the peaks are IDR-keyframe bursts within the CBR budget (depthai's
CBR averages over a window, not per-frame; at 5 fps each frame carries
~160 kbits mean, and IDRs for busy scenes can run many ×).

Keyframe-burst mitigations:

1. **Stagger keyframes** across cameras via coprime
   `h265_keyframe_frequency_frames` — the depthai v2.x API has no explicit
   GOP-phase offset, but coprime intervals make IDR coincidences essentially
   impossible. Doesn't change average bitrate. At fps=5 this is **the
   primary lever**. **Landed in PR
   [#134](https://github.com/rolker/unh_echoboats_project11/pull/134)**
   (issue [#133](https://github.com/rolker/unh_echoboats_project11/issues/133))
   with per-camera intervals 23/29/31/37 frames (forward shortest, aft
   longest).
2. **Longer GOP** — already at 6 s. Going further (12+ s) is unattractive
   because viewer-recovery on packet loss is already at the upper edge of
   usable.
3. **CBR strictness** — already on CBR by default. No `capped-VBR` mode
   exists in depthai's API (`VideoEncoderProperties::RateControlMode` is
   `{CBR, VBR}` only; `maxBitrate` field exists but has no setter). No
   further lever here.
4. **Lower per-camera bitrate** — diminishing returns given averages already
   match the 800 kbps target. The win would be proportionally smaller IDR
   keyframes (rough rule of thumb: IDR ≈ 5–15× per-frame mean), not lower
   averages.

## Decision matrix — Starlink-only operating modes

| Mode | Avg demand | Fits Starlink? | Operator visibility |
|---|---:|---|---|
| **Essentials only** (no video) | ~0.4 Mbps | comfortable at any range | dashboards + plan + heartbeat |
| **Essentials + 1 camera** @ 800 kbps | ~1.2 Mbps | comfortable; minor keyframe drops | one camera live |
| **Essentials + 1 camera** @ 500 kbps | ~0.9 Mbps | very comfortable | one camera live |
| **Essentials + 3 cameras** (current config) | ~2.75 Mbps avg | works on average; keyframe coincidences blow past cap | all three live |
| **Essentials + segmentation overlays only** (no full video) | ~0.5 Mbps | very comfortable | segmentation rendered as overlay; no raw video |

**Operational essentials alone (0.4 Mbps) clear the Starlink budget by ~5× even
at the lossy 20 Mbps zone.** Control / telemetry over Starlink is not the
bottleneck — cameras are.

## Caveats — what this analysis doesn't know

1. **Pier ≠ underway.** Today's calibration was on the pier. Starlink Roam's
   well-known weakness is satellite-handoff events (5–60 s burst-loss). The pier
   sweep is 15 s windows; it won't catch handoffs.
2. **2026-05-01 had WiFi.** udp_bridge ran with both paths active and the design
   does not currently failover cleanly between paths. The deployment data tells us
   how the *combined* system behaved; it does not tell us how Starlink-only would
   behave with WiFi administratively unavailable.
3. **Resend-layer rework is in flight.** The 30% steady-state resend overhead from
   the deployment data is being addressed in a separate udp_bridge effort. After
   that lands, the effective wire-overhead picture changes and these budgets may
   need re-evaluation.
4. **bencloud is the dominant VPN latency**, not Starlink itself (35 ms of the
   65 ms RTT). If bencloud is overloaded or down, "Starlink only" doesn't apply
   the way we expect. Worth a bencloud-side iperf3 for an independent sanity check.

## Recommended next steps

1. **Sustained Starlink UDP test** — 5–10 min iperf3 at 1 Mbps and at 5 Mbps to
   characterize burst-loss events. Single 15 s windows hide satellite-handoff
   periodicity.
2. **WiFi-disabled rehearsal** — boat at pier, WiFi administratively down at the
   MikroTik, udp_bridge restricted to VPN only. Observe what dies, what survives,
   and what comes back after a forced 30 s VPN-only outage (simulated by killing
   bencloud reachability briefly).
3. **Keyframe-stagger config** — small win, immediate. Configure the OAK encoders
   so the three cameras' GOP starts are offset by ⅓ GOP. Reduces keyframe-coincident
   peaks without touching bitrates.
4. **Define the Starlink-only profile** — explicit config (separate `bizzyboat.yaml`
   profile or a runtime override) that turns off all non-essential topics and
   restricts the VPN topics list to the "essentials + 0/1 camera" set. Default is
   today's "everything everywhere"; an explicit profile makes Starlink-only ops
   a one-config-flag change rather than a per-deployment hand-curation.
5. **Operate-on-Starlink survey rehearsal** — pick a short hop (200 m, line of
   sight to operator), deploy with the Starlink-only profile, recover. Compare to
   today's per-topic outage budget.

The substantive blocker to over-horizon survey is item 4 — the **explicit
Starlink-only configuration profile**. Items 1–3 are calibration; item 5 is
validation.
