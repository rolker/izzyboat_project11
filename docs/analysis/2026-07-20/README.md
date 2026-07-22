# Camera-mast calibration from 2026-07-20 recorded camera data

Issue: [#380](https://github.com/rolker/unh_echoboats_project11/issues/380) —
refinement of the 2026-07-20 field URDF fix (single-frame estimate, mast pitch
-1.85°) using the 10-minute post-correction recording.

Data (data-of-record, not in repo):
`~/data/logs/bizzy_images/bag_2026-07-20T13.45.16_ffmpeg_seg` on gabby
(dev mirror: `~/data/logs/gabby/logs/bizzy_images/...`) — 599 s, ~3000 frames
per camera at ~5 Hz, 4× segmentation + camera_info + `/tf` + `/tf_static` +
latched post-correction `robot_description`.

## Method

1. **Waterline extraction** (`scripts/extract.py`): per-column water/non-water
   boundary from all four 128×96 segmentation streams (green=water argmax,
   sub-pixel via channel crossing → beats the ~0.6°/row quantization that
   limited the field estimate). 1.43 M observations kept (98.3%; aft-camera
   wake band rejected at elevation < -3°).
2. **Geometry** (`scripts/geometry.py`): each observation → gravity-frame
   elevation + world azimuth using bag camera_info (full rational_polynomial
   undistortion via `cv2.undistortPoints`), the bag's `/tf_static` camera
   chain, and slerped `/tf` attitude (`base_link_north_up → base_link`).
   Camera height above water 1.38 m (waterline frame; lake plane from bag
   median, std 2 cm).
3. **Two independent solves** (agree to ≤0.08°):
   - *Relative* (`scripts/solve.py`): per-camera elevation trim + in-view roll
     with the scene absorbed in (40 m position cell × 3° world azimuth)
     fixed-effect bins; Huber IRLS. Works because the boat swept 2579° of
     heading over a 553 m track, decoupling mast-fixed offsets from
     scene geometry.
   - *Absolute* (`scripts/shoreline_solve.py`): boat track georeferenced via
     the bag `earth→map` (ECEF) transform (`scripts/latlon.py`); rays cast to
     the real Lake Massabesic shoreline (OSM relation 240137, 6 outer ways +
     22 islands) → predicted elevation `-atan(h/R)`; robust fit of
     measured - predicted. This anchors the common mode that horizon-style
     methods cannot observe.
4. **Closed-loop verification** (`scripts/verify.py`, `scripts/refine.py`,
   final gate `scripts/verify_urdf.py` run against the xacro-expanded URDF):
   with the new URDF values, residuals on the same data close to
   **≤0.010° elevation and ≤0.007° in-view tilt** on all four cameras.

## Findings

Absolute per-camera elevation offsets before correction (reads-high positive,
systematic uncertainty ~±0.1°):

| camera | elevation offset | in-view roll |
|--------|------------------|--------------|
| forward | -0.005° | +0.38° |
| aft | +0.58° | -1.72° |
| port | -1.10° | -0.14° |
| starboard | +0.60° | -0.27° |

1. **Pitch**: the -1.85° field fix left the forward camera essentially perfect.
   Rigid-part refinement: mast pitch **-1.963°**.
2. **Roll** (unmeasured in the field): port/starboard antisymmetry 0.85° →
   mast roll **+0.947°**, cross-confirmed by forward/aft in-view tilts.
3. **The field's +0.47° common-mode residual is resolved**: it was finite
   shore distance, not miscalibration. The field method assumed the waterline
   sits at the horizon; at shore range R it is depressed by atan(h/R) — 0.47°
   at ~170 m for h = 1.38 m. Against the real shoreline the common mode is
   +0.01°, i.e. zero.
4. **The bracket is not rigid**: a ±0.24° twist mode (fwd+aft vs port+stbd)
   plus per-camera in-view rolls up to -1.7° (aft) → per-camera trims are
   in the URDF (`camera_trim_*` properties).
5. Yaw trims are unobservable from waterline elevation; mount yaws stay
   cardinal.

## Operational impact

The port camera reading -1.10° low projected waterline obstacles at 60–150 m
regardless of true shore range — a persistent false shore ring to port
(`shore_consistency2.png`, BEFORE panel; same failure class as the original
"shoreline at 35 m ahead" bug that prompted the field fix). Starboard reading
+0.60° high pushed far-shore returns above horizontal (discarded/over-ranged).
Both are removed by this calibration (AFTER panel: all four cameras land
consistently on the OSM shoreline).

`elevation_hist.png`: per-camera waterline elevation distributions, raw vs
corrected (raw starboard/aft sat above the physical 0° limit).

## Deployment

The URDF is loaded from the installed share path
(`install(DIRECTORY urdf ...)`; `publish_state_launch.py` reads the package
share), so the refined angles reach `/tf_static` — and therefore the
sea-surface projection layer — only after the field host (gabby) pulls,
**rebuilds**, and relaunches `robot_state_publisher`. Without the rebuild the
boat silently keeps running the old -1.85° mast with no roll.

## Reproduction

```bash
export CAMERA_CAL_WORKDIR=/tmp/camera_mast_calibration && mkdir -p $CAMERA_CAL_WORKDIR
export CAMERA_CAL_BAG=~/data/logs/gabby/logs/bizzy_images/bag_2026-07-20T13.45.16_ffmpeg_seg
# then, in order:
python3 scripts/extract.py && python3 scripts/latlon.py && python3 scripts/geometry.py
python3 scripts/solve.py && python3 scripts/shoreline_solve.py
python3 scripts/verify.py            # sign search + closure, hand-applied corrections
# One refinement iteration: paste verify.py's residuals into refine.py
# (they are manual snapshots, see comment there), then:
python3 scripts/refine.py && python3 scripts/verify.py
python3 scripts/plots2.py            # shore_consistency2.png + elevation_hist.png
xacro <pkg>/urdf/bizzyboat.urdf.xacro > /tmp/bizzyboat.urdf
python3 scripts/verify_urdf.py /tmp/bizzyboat.urdf   # final gate: PASS < 0.05°
```

Also needs `massabesic.json` in `$CAMERA_CAL_WORKDIR`: the OSM shoreline,
fetched with `curl -G 'https://overpass-api.de/api/interpreter'
--data-urlencode 'data=[out:json][timeout:90];relation(240137);out geom;'`.
Note the shoreline is the absolute reference of the solve — treat the fetched
file as an input worth eyeballing (point count, lake shape) before trusting
the numbers.

## Limitations

- Yaw (azimuth) trims unobservable from waterline elevation.
- ~±0.1° systematic (segmentation boundary bias, OSM shoreline accuracy,
  reservoir level).
- Single day and loading condition; hull-trim changes with payload appear as
  common-mode pitch — re-record and re-run this pipeline to separate them
  if the projection drifts again.
