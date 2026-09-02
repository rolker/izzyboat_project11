# 2026-09-02 — gabby log (BizzyBoat deployment — issue pending)

Deployment issue: pending (backfill from a dev host)
Host: gabby
Side: field
Started: 2026-09-02 09:49 -04:00

## 2026-09-02

**2026-09-02 09:49 -04:00** — Deployment mode activated on gabby (field side, origin git@gitcloud:field/unh_echoboats_project11.git). Issue-less start per operator - no git-bug lookup run, header carries the pending marker for dev-side backfill. NOTE two gabby logs now await backfill, this one and 2026-09-01; one dev-side pass covers both. unh_echoboats_project11 on jazzy, in sync with origin/jazzy at session start.

**2026-09-02 09:49 -04:00** — SCOPE FOR TODAY, operator's words: 'Plan is to map more at Massabesic before having to return the M3.' So the run is additional bathymetric coverage at Lake Massabesic, and the M3's pending return is a hard schedule constraint on how much survey time is left with that sonar.

**2026-09-02 09:49 -04:00** — SHORE-SIDE STARLINK OUTAGE FROM 2026-09-01 IS RESOLVED - root cause was A BAD POWER CABLE, found by the operator troubleshooting at home overnight, and the operator reports having worked around it. That closes out yesterday's outage, which had taken the vpn connection down (salmon.vpn 192.168.22.142 unreachable, last_rx_age_s -1) and forced the day onto the router-to-router wifi link. NOT RECORDED HERE: the specifics of the workaround - whether the cable was replaced, bypassed or temporarily patched - because the operator did not state them and inferring would be fabrication. Worth capturing at wrap-up, since whether the fix is permanent or temporary determines if this can recur mid-run.

**2026-09-02 09:49 -04:00** — BRIDGE PATH SWITCHED BACK TO VPN ahead of today's run: connections_list in bizzyboat.yaml now reads wifi commented out, vpn active, cell active. This reverses yesterday's field switch to wifi, which existed only because the Starlink was down; with the shore link restored the vpn is the intended path again. cell stays enabled - the SIM refitted 2026-09-01 is still in. Coverage is NOT lost by the switch: the vpn connection block carries its own coverage_catalog and coverage_tiles entries independently of the wifi block, so CUBE coverage still reaches CAMP. Change was already present in the working tree at session start and is committed as part of this session's opening batch.
