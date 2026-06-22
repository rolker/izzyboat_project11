# 2026-06-22 — salmon log (BizzyBoat deployment #309)

Deployment issue: https://github.com/rolker/unh_echoboats_project11/issues/309
<!-- backfilled at wrap-up: "ref TBD / unverified on field side" reconciled to #309 (Deployment 2026-06-22: Lake Massabesic survey). NOT #299 (that was 2026-06-18). -->
Host: salmon
Side: field
Started: 2026-06-22 (start time not recorded; first logged entry below)

> **Stamp this `salmon` log link under the deployment issue's `## Logs` section from dev next time `/start-deployment` runs there.** Field side is read-only on the issue (no `gh`).

## 2026-06-22


**2026-06-22 17:08 -04:00** — Back at the dock (operator-reported). Today's sonar data not yet available for XTF export; will export when operator gives the go-ahead. Note: latest synced bizzyboat_sonar bag on salmon is 2026-06-19; today's run not yet pulled.

**2026-06-22 17:17 -04:00** — Deployment mode was never formally started for today's run (no /start-deployment on salmon), hence no deployment issue/ID for this log. Stability notes (operator-reported): CAMP was solid throughout — no crashes (contrast with 2026-06-18 recurring zenoh RMW liveliness-keyexpr crashes). rqt echogram plugin tested and solid.

**2026-06-22 17:21 -04:00** — Re-exported sidescan XTF files for the Summer Hydro students. Re-ran bag_to_xtf (bag_analysis) over all bizzyboat_sonar bags since 2026-06-12 because the prior exports (written 06-18 19:15-19:22) predated the b5dcc07 PINGVerter/PING-Mapper ingestibility fix (landed 06-19 06:59) — all existing files were stale. Result: 11 files exported (standard layout) to ~/share/xtf/<date>/<timestamp>.xtf, 9.4 GB total; 5 bags skipped as they contained no sidescan data (port/starboard msgs=0). Not yet exported: today's (06-22) run, pending data pull. Out of scope: 3 bizzy_sidescan raw-debug bags (06-12 x2, 06-15) lack /tf so bag_to_xtf can't georeference them.

**2026-06-22 17:54 -04:00** — Today's data pulled and XTF-exported: bizzyboat_sonar/2026-06-22T13-22-29 -> ~/share/xtf/2026-06-22/2026-06-22T13-22-29+00-00.xtf (standard layout, 1.9 GB, 227247 pings, only 2 unpaired dropped, no TF drops). Summer Hydro XTF set now complete and current: 12 files / 12 GB in ~/share/xtf covering 2026-06-12 through 2026-06-22, all standard layout with the b5dcc07 ingestibility fix. Confirmed sonar bag logger uses mcap zstd_fast chunk compression (bizzyboat.yaml storage_preset_profile).

**2026-06-22 18:25 -04:00** — Clarification (operator): the 3 bizzy_sidescan bags (2026-06-12 x2, 2026-06-15) were debug/development captures, NOT official survey data. Intentionally excluded from the Summer Hydro XTF set — not a gap, do not re-export. (Supersedes the earlier 'out of scope, lacks /tf' note: they're out of scope by intent, georeferencing aside.)
