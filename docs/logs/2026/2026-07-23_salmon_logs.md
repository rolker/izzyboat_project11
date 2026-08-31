# 2026-07-23 — salmon log (bizzyboat deployment)

Deployment issue: https://github.com/rolker/unh_echoboats_project11/issues/386
Host: salmon
Side: field
Started: 2026-07-23 (retrospective — this log written 2026-07-24 07:10 -04:00 from post-run investigation)

## 2026-07-23

- ~evening (operator-reported): during live ops on Lake Massabesic, CAMP's live
  coverage display suddenly became very low resolution and stayed that way.

### Post-run investigation (logged 2026-07-24 07:10 -04:00)

Cause identified: CAMP's live-tile eviction (camp#160) fired and shed the fine
tiles to the overview pyramid.

Evidence and findings:

- Live tile cache on salmon:
  `~/.local/share/UNH-CCOMJHC/CCOMAutonomousMissionPlanner/live_tile_cache/%2Fbizzy%2Fsensors%2Fm3%2Fcube_bathymetry/`
  — 38 fine tiles + 45 overview tiles, all GeoTIFFs valid (full GDAL read),
  WGS 84, footprint 42.965–43.012°N / 71.344–71.394°W (Lake Massabesic). No
  stray tiles from other areas.
- The `overviews/` subdirectory was created 2026-07-23 19:30 local. In
  `sonar_live_cache_layer.cpp` that directory is written *only* by the
  eviction path (`evictIfOverBudget` → `foldIntoParent` → write-through), so
  eviction definitely fired during the session. CAMP's stderr should contain
  the one-shot warning "resident tile budget exceeded … shedding to the
  overview pyramid".
- Budget math is consistent with a legitimate trigger: tiles are 960×960 with
  3 Float32 bands (backscatter, depth, uncertainty) ≈ 11 MB CPU per tile plus
  ~3.7 MB GL texture. 38 fine tiles ≈ 420–560 MB resident, at the default
  `LiveTileCache/max_vram_bytes` = 512 MiB (no override in
  `~/.config/UNH-CCOMJHC/CCOMAutonomousMissionPlanner.conf`).
- Why one eviction became a full resolution collapse (the suspected camp bug,
  two parts):
  1. Folding a fine tile into its parent does not shrink it — overview tiles
     are the same pixel size (960×960 × 3 bands ≈ 11 MB each), the fold
     recurses to level 0, and overviews count toward the same budget. The 45
     overview tiles are ~500 MB by themselves, so phase-1 eviction gains
     almost no headroom and runs until essentially all fine tiles are gone.
  2. No in-session recovery: evicted fine tiles remain on disk and the
     reconciler still marks them possessed (anti-churn, camp#71), but nothing
     reloads them on zoom-in — only the startup warm-load does. Degradation
     persists until CAMP restarts.

Mitigation for next run: raise `LiveTileCache/max_vram_bytes` in
`~/.config/UNH-CCOMJHC/CCOMAutonomousMissionPlanner.conf` (or set 0 to
disable eviction — this survey is only ~1 GB fully resident) and restart
CAMP; the warm-load restores full resolution from the disk cache.

Wrap-up follow-ups (file against camp from a dev host):

- Overview tiles should be decimated in pixel size, or excluded/discounted in
  the eviction budget accounting, so folding actually frees memory.
- Add an on-demand disk reload path for evicted fine tiles.

Stamp this log's link under the deployment issue's `## Logs` section from dev
next time `/start-deployment` runs there.
