# 2026-08-03 — salmon log (bizzyboat deployment, Broadkill River DE)

Deployment issue: pending
Host: salmon
Side: field
Started: 2026-08-03 13:10 -04:00

## 2026-08-03

- 2026-08-03 13:10 -04:00: RTK corrections restored. Boat had no corrections (fix_type 3,
  h_acc ~1.6 m, dgps_age = never) — ntrip_client on gabby was still pointed
  at MassDOT MaCORS, which only serves MA. Switched
  `ccomjhc_project11/configuration/bizzyboat_ntrip.yaml` (gabby) to the
  UDEL Delaware TopNET-V caster: host 70.88.225.204, port 8005, mountpoint
  NET_MSM (network MSM, GGA echoback required), user UDEL3. Operator-recalled
  password needed a case fix (all-lowercase). Verified: caster streams RTCM3
  after GGA; `/bizzy/mavros/gps_rtk/send_rtcm` ~4.5 Hz; SBG relay
  `/bizzy/sensors/rtcm` ~5.5 Hz; GPS now **fix_type 6 (RTK fixed), h_acc
  14 mm**. Config edited on gabby main tree (field mode), not yet committed;
  salmon's copy of the yaml still has MaCORS — sync before next build/run
  from salmon.

- 2026-08-03 13:13 -04:00: split NTRIP configs: UDEL/Delaware credentials saved to new
  `configuration/bizzyboat_ntrip_udel.yaml` (both hosts);
  `bizzyboat_ntrip.yaml` restored to the NH/MaCORS default on salmon.
  On gabby the default file is deliberately left overwritten with the UDEL
  caster for the duration of the deployment — the running ntrip_client
  re-reads that path on respawn (cell dropouts trigger this), and restoring
  it there would silently revert the boat to MaCORS. Revert gabby's
  `bizzyboat_ntrip.yaml` at wrap-up.

**2026-08-03 13:17 -04:00** — deployment mode activated on salmon (session resume via /start-deployment; issue still pending — backfill from a dev host)

**2026-08-03 13:38 -04:00** — udp bridge health check: all 3 links up (boat->op: wifi ~606 kB/s, vpn ~490 kB/s, cell ~95 kB/s), 0 send failures; drops only on bulk streams (camera ffmpeg, collision pointcloud) on vpn/wifi — bandwidth shedding, control/telemetry topics clean

**2026-08-03 13:40 -04:00** — operator: SIM card removed from router to test in another system — cell should not be a usable data path. Checked bridge_info: 0 cell-only topics; all 12 cell-using topics also ride vpn (most also wifi), so no data loss expected. Note: earlier 'cell ~95 kB/s ok' stat was boat-side UDP send success, not delivery confirmation

**2026-08-03 13:46 -04:00** — operator: received video feeds mostly garbled, mostly when both wifi and vpn/starlink connected. Mitigation: pinned camera ffmpeg streams to vpn-only via /operator/udp_bridge/remove_subscribe (per operator choice). aft+starboard stuck; forward+port re-appear on wifi after removal — something (CAMP?) appears to re-subscribe them. Note: vpn camera drop rates roughly doubled with video concentrated there (port ~64 kB/s dropped) — bitrate reduction may be the real fix if garbling persists

**2026-08-03 13:53 -04:00** — resend check: heavy resend churn confirmed. Boat resending 106/153/250 kB/s (cell/vpn/wifi) with resend-queue DROPS ~1 MB/s each on vpn+wifi; on cell, resends exceed fresh data (106 vs 80 kB/s). Operator side: resend_giveup_count 19.0M, duplicates 517/940 kB/s on vpn, 283/1172 on wifi, 128/185 on cell (cell still delivering despite SIM removal — router likely failing over to another WAN, so all 3 'links' may share physical paths). Assessment: offered load (4 video streams x 2-3 links + resend traffic) oversubscribes links; losses trigger resend requests which add load — congestion spiral is the likely garbling mechanism

**2026-08-03 14:05 -04:00** — operator: gabby-side agent is removing oak camera streams from wifi (boat-side fix — explains why operator-side remove_subscribe for forward/port kept re-appearing; boat config is authoritative). Standing down on salmon-side subscription changes

**2026-08-03 14:11 -04:00** — post-restart check: all 4 oak cameras now vpn-only (gabby fix took). Garbling persists because vpn is still oversubscribed: boat cap 1172 kB/s vs offered ~1.9 MB/s (707 fresh + 153 resent + 1052 resend-dropped, pre-restart figures); operator now receiving 1076 kB/s on vpn of which 622 kB/s duplicates; boat still shedding 16-32 kB/s per camera at send. Cell arriving ~100% duplicate. Recommendation to operator: cut camera encoder bitrate (~half) or reduce number of live feeds; resend churn should collapse once offered load < link cap

**2026-08-03 14:40 -04:00** — operator: cameras usable now (after vpn-only pinning + gabby-side load reduction). New observation: CAMP cube tiles show large blank areas, no bathy

**2026-08-03 14:55 -04:00** — CAMP blank cube tiles root-caused: after gabby stack restart, boat udp_bridge had NO subscription for coverage_catalog/coverage_tiles/manda_coverage_swath despite them being in bizzyboat.yaml vpn topics_list (0 rows in boat topic_statistics; config->bridge persistence of the 2026-06-29 live remote_advertise setup does not load on restart — RCA item for wrap-up). Sonar itself healthy (soundings 16 Hz, cube node catalog 0.2 Hz on boat). Mitigation: re-ran remote_advertise live on boat for catalog (vpn, q2), tiles (vpn, q2, period 0.5), swath (vpn, q2, period 1.0); catalog confirmed arriving on salmon at 0.2 Hz

**2026-08-03 17:50 -04:00** — operator: boat shut down quickly ahead of heavy rain. Operator report (times approximate, operator-reported): had difficulty steering, heard a strange noise from the boat, limped to the dock. Boat powered down; no further live telemetry. RCA items for wrap-up: steering difficulty + noise — pull mavros/rc/out, differential_drive, cmd_vel vs actual track, and battery/diagnostics from the boat bags + operator bags covering the return-to-dock window

**2026-08-03 17:53 -04:00** — operator context: boat was surveying the Broadkill River in strong currents. Operator theory (quote): 'the flight controller had pid issues'; operator concerned troubleshooting is limited by the quick shutdown. Data check: operator-side bag on salmon covers 10:42->~17:42 (345 MB, operator_2026-08-03T10.42.19), includes bridged rc/out, rc/in, mavros state, cmd_vel, GPS, IMU through the return leg. Additional RCA sources when boat next powers up: gabby boat-side bags + Cube Orange dataflash log (SD card, survives shutdown — best source for PID desired-vs-actual). RCA deferred to wrap-up

**2026-08-03 18:29 -04:00** — operator: boat powered back up, tied at dock; ROS stack NOT running. No ROS-side actions taken. Reminder queued: when stack launches, re-advertise coverage_catalog/tiles/swath on boat bridge (config-load bug)

**2026-08-03 18:32 -04:00** — operator: boat logs transferring (gabby -> storage); holding off on any bag reads until transfer completes (mid-rsync bags lack metadata.yaml and must not be touched)

**2026-08-03 18:46 -04:00** — field-end wrap-up: committing and pushing local changes. Plan: (1) salmon ccomjhc — commit new bizzyboat_ntrip_udel.yaml; (2) salmon unh_echoboats — commit this log; (3) gabby ccomjhc — revert working-tree bizzyboat_ntrip.yaml to NH/MaCORS default per plan-of-record and pull the committed udel file. NOTE: after the gabby revert, a future Delaware launch must point NTRIP at bizzyboat_ntrip_udel.yaml again or RTK will silently use MaCORS. RCA of steering difficulty/noise + coverage-tile config-load bug deferred to dev-side wrap-up
