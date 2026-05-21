# 2026-05-18 BizzyBoat link bandwidth + loss calibration

Companion to [`rolker/unh_echoboats_project11#124`](https://github.com/rolker/unh_echoboats_project11/issues/124).
Out-of-band measurement to feed the §1 networking interpretation in
[`findings.md`](findings.md).

## Conditions

- **Date/time**: 2026-05-18, ~20:00 EDT
- **Boat**: powered up on the pier, idle (udp_bridge running but no
  autonomy active, no cameras under load).
- **Operator host**: salmon, `iperf3 -s -p 5201` (default port).
- **Boat host**: gabby, iperf3 3.16 client.
- **Boat motion**: stationary at pier. Best-case WiFi conditions; results
  are **not representative of long-range / over-horizon operation**.

## Path topology

Both paths route from gabby through `enp7s0` to the boat router
(`192.168.20.1`), which policy-routes the egress based on destination
subnet.

| Path | Target on salmon | Boat-side hostname | mtr hops | Avg RTT |
|---|---|---|---|---|
| **WiFi** | 192.168.13.142 (`salmon_bb`) | `gabby_bb` (192.168.20.5) | gabby → router → WiFi-bridge → salmon | **9 ms** |
| **VPN / Starlink** | 192.168.22.142 (`salmon_bv`) | `gabby_v` (192.168.21.5, NETMAP) | gabby → router → bencloud (WireGuard relay) → salmon | **65 ms** |

mtr raw output:

```
=== mtr WiFi ===
  1.  router.lan.bizzy.p11.lan          0.0%  20    0.8   0.7   0.6   0.8   0.1
  2.  router.bizzy.wifi.op.p11.lan      0.0%  20    1.6   4.7   1.5  36.4   7.7
  3.  salmon.lan.op.p11.lan             0.0%  20   13.2   3.5   1.6  13.2   3.3

=== mtr VPN ===
  1.  router.lan.bizzy.p11.lan          0.0%  20    0.8   0.8   0.6   2.2   0.3
  2.  bencloud.wg.p11.lan               0.0%  20   36.0  35.2  24.6  51.7   8.6
  3.  salmon.vpn.bizzy.p11.lan          0.0%  20   58.3  65.1  48.7  83.2  10.8
```

## WiFi link (cap = 1.5 MB/s = 12 Mbps)

### TCP

| Test | Throughput | Retransmits |
|---|---|---|
| Single stream, 30 s, `-O 2` | **21.1 Mbps** sender / 21.0 Mbps receiver | 145 |
| 4 parallel, 30 s | **20.8 Mbps** sender / 20.1 Mbps receiver | 0 |

Per-stream parallel was 5 Mbps × 4 = 20.1 Mbps total; single-stream ran a
bit harder at 21.1 Mbps. **Link, not protocol, is the limit at ~21 Mbps
for TCP.**

### UDP — `iperf3 -u -b $rate -t 15 -l 1400 --get-server-output`

| Offered | Delivered | Loss | Jitter (one-way) |
|---|---|---|---|
| 5 Mbps | 5.00 Mbps | **0/6697 = 0%** | 0.74 ms |
| 10 Mbps | 10.0 Mbps | **0/13393 = 0%** | 0.12 ms |
| 15 Mbps | 15.0 Mbps | **1/20089 = 0.005%** | 0.47 ms |
| 20 Mbps | 20.0 Mbps | **0/26785 = 0%** | 0.51 ms |
| 25 Mbps | 25.0 Mbps | **0/33480 = 0%** | 0.45 ms |
| 30 Mbps | 30.0 Mbps | **0/40177 = 0%** | 0.45 ms |

`-l 1400` matches the udp_bridge wire-packet profile (1 MTU = realistic).

### WiFi verdict

- **Physical capacity at pier: ≥30 Mbps clean UDP, 21 Mbps TCP.**
- Configured cap: 12 Mbps — **link can do ~2.5× more** at this distance.
- Cap is *conservative on the pier*. The right cap-vs-distance behavior is
  a separate question (MikroTik radio rate tapers with range; static cap
  can't track).

## VPN / Starlink link (cap = 1.0 MB/s = 8 Mbps; brief 2.5 MB/s window in deployment)

### TCP

| Test | Throughput | Retransmits |
|---|---|---|
| Single stream, 30 s, `-O 2` | **16.6 Mbps** sender / 16.5 Mbps receiver | **3,739** |

The trailing 4 buckets ramped 15.7 → 32.5 Mbps as TCP discovered
bandwidth; the test averages 16.6 Mbps because of high retransmit
overhead.

### UDP

| Offered | Delivered | Loss | Jitter |
|---|---|---|---|
| 5 Mbps | 4.97 Mbps | **13/6697 = 0.19%** | 3.04 ms |
| 10 Mbps | 9.89 Mbps | **81/13393 = 0.6%** | 1.78 ms |
| 15 Mbps | 14.7 Mbps | **241/20088 = 1.2%** | 1.20 ms |
| 20 Mbps | 19.6 Mbps | **388/26785 = 1.4%** | 0.85 ms |

(Did not push to 25/30 Mbps — already clearly past the clean zone.)

### VPN verdict

- **Physical capacity exists past 20 Mbps** in burst, but with persistent
  packet loss. TCP 16.6 Mbps with 3,739 retransmits = lossy congestion
  control.
- Configured cap 8 Mbps sits ~2/3 of the way between the 0.19% and 0.6%
  loss points. **Interpolated loss at 8 Mbps ≈ 0.4%.**
- Loss is **structural, not capacity-related**: 0.19% UDP loss exists at
  5 Mbps, far below cap. Raising or lowering the cap won't eliminate it.
- RTT 65 ms with 8–11 ms jitter, 83 ms worst. Path goes via `bencloud`
  WireGuard relay (35 ms gabby → bencloud).

## Implications

1. **WiFi is heavily over-provisioned at close range.** A ~24 Mbps cap
   would still have headroom over the measured TCP ceiling and would
   give the camera streams meaningful breathing room (recall §1.1: OAK
   ffmpeg streams account for ~99% of rate-limiter drops in the
   2026-05-01 bag).
2. **The Starlink/VPN cap is set near a physical-link knee, not an
   arbitrary number.** Loss starts measurable at 5 Mbps and rises with
   offered rate. The 8 Mbps choice is a defensible "loss budget" point.
3. **The deployment's ~30% resend overhead is the expected steady state**
   for a 0.4% baseline-loss link under udp_bridge's existing
   retransmit design — not a bug, not an environmental anomaly. Reducing
   it requires either:
   - A different recovery strategy than resend (FEC, prioritized drop)
   - Reducing offered VPN load below the lossy knee (~5 Mbps), or
   - The in-progress udp_bridge resend-layer rework (out of scope here).

## Caveats and follow-up tests worth doing

- **Range sweep**: repeat at 100 / 300 / 500 / 800 m off the pier. The
  static WiFi cap is conservative *here* but may be aggressive at
  range. Without this data, raising the cap is not safe for autonomy.
- **Boat-load test**: repeat with udp_bridge actively pushing the four
  OAK ffmpeg streams. iperf3 vs. contention shows the rate-limiter's
  fairness behavior under real workload.
- **Sustained Starlink test**: 5-minute UDP at 5 Mbps and 8 Mbps to
  catch periodic loss bursts (single 15 s window may miss
  satellite-handoff events).
- **bencloud relay sanity**: the WireGuard relay is the only hop with
  more than ~5 ms latency; worth a quick bencloud-side iperf3 to
  confirm the relay isn't itself the lossy hop.
