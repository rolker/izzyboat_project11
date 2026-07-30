# 2026-07-29 — gabby log (BizzyBoat deployment #398)

Deployment issue: [#398](https://github.com/rolker/unh_echoboats_project11/issues/398) (backfilled at wrap-up from a dev host)
Host: gabby
Side: field
Started: 2026-07-29 13:01 -04:00

## Summary

Rainy-day survey session at Lake Massabesic, roughly 13:00–14:45. The
operator-side Starlink was down at the start — the dish subscription turned
out to be paused, and unpausing fixed it. Rain drops false-triggered the
collision-avoidance system several times, requiring manual takeovers, and the
udp_bridge return rate had to be raised again to keep costmap tiles flowing.

## Lessons Learned

- A paused Starlink subscription looks exactly like a backhaul outage from the
  router side — check subscription status before diagnosing hardware, and
  before heading out.
- Rain drops are another environmental false-positive trigger for collision
  avoidance (alongside whitecaps and glint) — expect manual takeovers in rain
  until the segmentation is hardened.

## 2026-07-29

**2026-07-29 13:01 -04:00** — Operator-side Starlink internet down. Diagnosed op router (Teltonika RUTX11, WAN eth1 -> Starlink router 192.168.1.1, dish 192.168.100.1): both reachable but 100% loss past the Starlink router (traceroute dies at hop 1, no 100.64.0.1 CGNAT hop, DNS dead) -> Starlink backhaul down, not an op-router fault. Boat (gabby) Starlink is a separate dish and was fully working throughout. Root cause: operator Starlink dish subscription was PAUSED. Operator unpaused -> resolved.

**2026-07-29 13:13 -04:00** — Weather: operator reports fairly heavy rain on site.

**2026-07-29 13:15 -04:00** — Weather (corrected station — KMHT/Manchester, inland site, not coastal Fort Point): KMHT 12:55 EDT obs = light rain + fog/mist, 64F, wind E ~4kt, vis ~4mi. NWS hourly forecasts SHOWERS AND THUNDERSTORMS 2-4 PM EDT (PoP 82-84%), then patchy fog into evening. Note lightning risk for on-water ops this afternoon.

**2026-07-29 14:25 -04:00** — Config: operator raised udp_bridge return rate to 1500000 (again) to let costmap tile updates through.

**2026-07-29 14:44 -04:00** — Phase: about to recover (operator-reported) — entering recovery.

**2026-07-29 (times unrecorded, operator-reported at wrap-up)** — Operator took manual
control a few times during the session: rain drops caused false positives in the
collision-avoidance system.

**2026-07-29 ~14:45 -04:00 (operator-reported)** — Recovery complete: boat out of the water, towed back to the lab, ready for shutdown.
<!-- corrected at wrap-up: entry was originally logged 2026-07-30 08:53 -04:00 when the field agent
     resumed for shutdown; operator reported recovery actually completed on 07-29 shortly after bag
     logging stopped (all recording streams end 14:44 EDT = ROS stack shutdown). -->

**2026-07-30 08:53 -04:00** — Field-side wrap-up: gabby shutdown-ready; logs committed and pushed to gitcloud.
