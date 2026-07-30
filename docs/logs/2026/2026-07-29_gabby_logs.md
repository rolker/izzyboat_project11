# 2026-07-29 — gabby log (BizzyBoat deployment — issue pending)

Deployment issue: pending (backfill from a dev host)
Host: gabby
Side: field
Started: 2026-07-29 13:01 -04:00

## 2026-07-29

**2026-07-29 13:01 -04:00** — Operator-side Starlink internet down. Diagnosed op router (Teltonika RUTX11, WAN eth1 -> Starlink router 192.168.1.1, dish 192.168.100.1): both reachable but 100% loss past the Starlink router (traceroute dies at hop 1, no 100.64.0.1 CGNAT hop, DNS dead) -> Starlink backhaul down, not an op-router fault. Boat (gabby) Starlink is a separate dish and was fully working throughout. Root cause: operator Starlink dish subscription was PAUSED. Operator unpaused -> resolved.

**2026-07-29 13:13 -04:00** — Weather: operator reports fairly heavy rain on site.

**2026-07-29 13:15 -04:00** — Weather (corrected station — KMHT/Manchester, inland site, not coastal Fort Point): KMHT 12:55 EDT obs = light rain + fog/mist, 64F, wind E ~4kt, vis ~4mi. NWS hourly forecasts SHOWERS AND THUNDERSTORMS 2-4 PM EDT (PoP 82-84%), then patchy fog into evening. Note lightning risk for on-water ops this afternoon.

**2026-07-29 14:25 -04:00** — Config: operator raised udp_bridge return rate to 1500000 (again) to let costmap tile updates through.

**2026-07-29 14:44 -04:00** — Phase: about to recover (operator-reported) — entering recovery.

**2026-07-30 08:53 -04:00** — Recovery complete: boat out of the water, towed back to the lab, ready for shutdown. Wrapping up field side.
