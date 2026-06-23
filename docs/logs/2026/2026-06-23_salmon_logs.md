# 2026-06-23 — salmon log (BizzyBoat deployment — issue pending)

Deployment issue: pending (backfill from a dev host)
Host: salmon
Side: field
Started: 2026-06-23 09:15 -04:00

**2026-06-23 09:18 -04:00** — Deployment mode activated on salmon (field side, issue-less start). Repo on jazzy, tree clean.

**2026-06-23 09:45 -04:00** — Controls check good. Departed dock, transiting.

**2026-06-23 13:31 -04:00** — Starlink diagnostics healthy during transit: 0.0% drop / 19ms ping, 0.20% obstructed, dish reachable, no thermal alerts. One WARN alert active: lower_signal_than_predicted (benign; link metrics good). Note: 'state not reported by dish' (cosmetic).

**2026-06-23 13:56 -04:00** — CAMP background geotiff all_lines_at_5_29pm_utc_26_6_23.tif (28032x4480, LZW, EPSG:32619, 2m px) appeared not to load but operator confirmed it does load, just slowly. Large dimensions = long decode/render. Georeferencing intact. No fix applied. Wrap-up idea: pre-downsample/retile oversized backgrounds for faster CAMP load.

**2026-06-23 17:07 -04:00** — POWER LOSS — boat ran out of power, towed to pier. Battery trend from operator bag (operator_2026-06-23T09.02.52, /diagnostics 'mavros: Battery'): 28.69V at depart (09:04) declining ~linearly to 20.6V at 15:52:22 where telemetry stopped (brownout). ~24V nominal pack, drop steepened last hour (23.0V@15:00 -> 20.6V@15:52). Remaining=-1 (no SOC%) and Current=0 (no draw) throughout — voltage was only gauge. Diagnostic level stayed OK(0) to 20.6V: NO low-battery WARN/ERROR ever fired. WRAP-UP: configure MAVROS battery low/critical voltage thresholds + pack capacity so SOC and low-batt alarm work; consider current sensing.

**2026-06-23 17:27 -04:00** — Boat recovered at pier, logs downloading. Wrap-up initiated from salmon (field side) — full /wrap-up-deployment must run on a dev host (no gh here). Committing + pushing this salmon log to gitcloud for dev-side collection. NOTE for dev wrap-up: this was an ISSUE-LESS start (#533) — header marker 'Deployment issue: pending'; backfill + create the deployment issue on dev before closing.

**2026-06-23 17:31 -04:00** — Reconcile note: gitcloud/jazzy fetch shows dev-side wrap-up already active for THIS deployment under issue #309 (power/V-drop analysis, GPS dock times cast-off 09:58 / docked 16:30, RCA #311/#312 — all matching today's power-loss). DEV WRAP-UP: link this salmon log AND gabby log to #309's ## Logs and clear their 'pending' markers — do NOT create a new deployment issue. My earlier 'create the issue' note is superseded by #309's existence. Battery brownout finding here (28.7V->20.6V, no low-batt alarm) corroborates #309 power RCA.
