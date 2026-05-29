# 2026-05-29 — gabby log (BizzyBoat deployment)

**Mode**: field (gitcloud origin)
**Deployment**: git-bug `5617368` — *Deployment 2026-05-29: validate graded
sea-surface costmap (perception #22)*
**Host**: gabby
**Side**: field
**Started**: 2026-05-29 12:42 -04:00
**Dev-side wrap-up TODO**: stamp this log's path under the deployment issue
body's `## Logs` section (field-side is read-only, per memory + skill 4b).
The dev log link is already present in the issue body; this gabby log needs
to be added there from a dev session.

## 1. Build freshness vs today's merges

**2026-05-29T12:42-04:00** — Stack is up. Checked install timestamps against
today's merges:

- **Perception #22 (graded sea-surface costmap)** — merged 11:42 EDT,
  `sensors_ws/install/sea_surface_segmentation` rebuilt 12:13 EDT.
  `libsea_surface_layer.so` is fresh. ✅
- **Navigation #46 / #48 hover fixes + #35 trackline re-send
  (`unh_marine_navigation`)** — merged 11:51 EDT,
  `core_ws/install/marine_nav_*` last built **Apr 8**. Source is on
  `jazzy` HEAD locally but **not in the install**. ❌

Implication: costmap focus is ready; hover/trackline checks will show old
behavior until `core_ws` is rebuilt. Flagged to operator.

## 2. core_ws rebuild

**2026-05-29T12:5x-04:00** — Operator requested rebuild. Ran
`colcon build --symlink-install --packages-select marine_nav_interfaces
marine_nav_utilities marine_nav_tasks marine_nav_behaviors
marine_nav_behavior_tree marine_nav_bt_task_navigator
marine_nav_crabbing_path_follower` from `core_ws`. All 7 finished in
8.25s, exit 0. `--allow-overriding` warning expected (rebuild into
existing install).

Install now has #46/#48/#35; running nodes still on old code until the
autonomy/BT launch group is relaunched.

**2026-05-29T12:5x-04:00** — Operator restarted the whole stack. Running
nodes now reflect today's `jazzy` HEAD for both perception #22 and
nav #46/#48/#35.

## 3. Windowed costmap not visible at operator station

**2026-05-29T13:xx-04:00** — Operator reported no windowed costmap on the
operator side. Initial hypothesis (mine) was the known zenoh
transient_local discovery race on `costmap_window` /
`local_costmap/costmap_windowed`. **Actual cause**: udp_bridge subscribe
entry for the local costmap had `period: -1`, which disables forwarding.
Operator caught and fixed it. Costmap now visible on operator side.

Note for follow-up: worth a quick check whether the `-1` was a stale
test value or intentionally there from a prior debugging session — if
it's lurking in committed config, others will hit it.

## 4. In the water

**2026-05-29T13:xx-04:00** — Boat in the water. First on-water command:
goto hover. Boat executed it successfully (went to the commanded
location and held).

Partial confirmation that the basic hover path is alive on today's
nav build. Still untested on-water:
- `#46` end-of-task hover landing at current location (not the first
  hover spot) — requires a task/mission ending into a hover
- Re-commanded hover re-targeting while already hovering — requires
  issuing a second hover from within a hover
- `#48` marker appearing on first hover without CAMP restart — need
  operator-side confirmation

## 5. Sea-surface layer tuning — buoys not marking on costmap

**Symptom**: buoys not appearing on the costmap. Direction: increase
sensitivity. Primary dial is `obstacle_prob_min` (default 0.35; lower
= more sensitive).

Defaults: `obstacle_prob_min=0.35`, `lethal_threshold=1.0`,
`max_evidence_step=0.85`, `free_threshold=0.0`, `clear_floor=-2.0`,
`obstacle_clamp=5.0`, `decay_half_life_s=30.0`.

| Time | Param | Old → New | Result | Notes |
|---|---|---|---|---|
| 13:23 | `obstacle_prob_min` | 0.35 → 0.25 | No buoys marking | First attempt |
| 13:26 | `obstacle_prob_min` | 0.25 → 0.20 | No buoys marking | Going further |

**2026-05-29T13:28-04:00** — Operator confirms buoy IS showing red in
segmentation image, but still not marking on costmap. Perception input
is good; chain is breaking downstream. Two sensitivity drops with zero
effect (not even soft cost) is consistent with the param not landing
on the right node, or the new graded layer not actually loaded.

**2026-05-29T13:28-04:00** — Diagnostic from gabby:
- `ros2 node list` shows `/bizzy/local_costmap/local_costmap`,
  `/bizzy/local_costmap/costmap_window`, `/bizzy/global_costmap/global_costmap`.
- Plugin list on `/bizzy/local_costmap/local_costmap`:
  `['chart_layer', 'sea_surface_layer', 'inflation_layer']` — new graded
  layer IS loaded.
- **`obstacle_prob_min` reads back as `0.35`** despite operator's two
  `param set` commands (0.25, then 0.20). Set commands silently no-op'd.
- rmw_zenoh QoS errors visible in param-service output ("Received
  liveliness token with invalid qos keyexpr"; "service's implementation
  is invalid") — plausible mechanism for the set going nowhere.

**2026-05-29T13:3x-04:00** — Source review of
`sea_surface_segmentation/src/sea_surface_layer.cpp`:

- `obstacle_prob_min` declared at `onInitialize` (line 107) → published
  on costmap node as `sea_surface_layer.obstacle_prob_min`.
- Dynamic param callback registered (line 239), validation in `(0, 1)`,
  atomic update under `costmap_mutex_` (line 706).
- `bufferPoints` reads `obstacle_prob_min_` per-frame (line 416) and
  passes it into `segments_projection` (line 453).

Wiring is correct. Layer would honor a dynamic update if it received one.
The fact that `ros2 param get` reads 0.35 after two `set` calls means
the set RPC never reached the callback — most likely rmw_zenoh's
param-service is silently dropping it (the QoS errors we saw on `get`
support this).

Mitigation: edit YAML default, relaunch nav2 group. Defer zenoh
param-service RCA to wrap-up.

**2026-05-29T13:5x-04:00** — Param later started landing (operator
confirmed). But tuning still produced no visible costmap change. Deeper
review of `project_observations_inverse` in `segments_projection.hpp`:
- `obstacle_prob_min` only gates which RGB pixels qualify
  (`px[0] >= obstacle_prob_min * 255`).
- Positive evidence is only pushed for **waterline contact pixels** —
  the lowest obstacle-ish pixel in each image column whose pixel
  directly below is NOT obstacle-ish. Body pixels above contact are
  silently skipped ("leave unobserved").
- So even with the dial at 0.20, if cells project to the buoy body
  rather than the contact row, nothing marks.

**TF / runtime verification on the running stack**:
- controller_server log (PID 52707, started 12:48): SeaSurfaceLayer
  initialized cleanly, buffer 1600x1600, no projection-failed warnings,
  no "Could not transform" / extrapolation errors. TF is fine.
- Control loop occasionally missing 5.0 Hz target (saw 3.84, 3.03 Hz) —
  noted, not pinned to the layer specifically.
- Loaded `.so` is `/home/field/project11/layers/main/sensors_ws/build/
  sea_surface_segmentation/libsea_surface_layer.so`, mtime 12:13:00,
  contains today's `project_observations_inverse` symbol and
  `obstacle_prob_min` strings. **Running code IS today's HEAD.**
  (Path is the build dir because `--symlink-install` symlinks install
  to build — same file.)
- Ruled out "wrong .so loaded" / "param not landing" / "TF broken" /
  "layer not initialized" classes of failure.

Remaining likely causes: (a) cells projecting to buoy body not
waterline contact (geometry); (b) segmentation lacking a clean
waterline transition at the buoy; (c) layer's segmentsCallback not
firing (subscription quietly broken — to be checked via
`/bizzy/sea_surface/lethal_grid` topic activity).

## 6. Topic flow verified — close-buoy blind spot confirmed

**2026-05-29T14:0x-04:00** — `ros2 topic hz` is unreliable under
rmw_zenoh (returns silence even on live topics). `ros2 topic echo
--once` confirmed both `/bizzy/sensors/cameras/oak_forward/segmentation`
(live `rgb8` images) and `/bizzy/sea_surface/lethal_grid` (recent
header stamp) ARE flowing. Layer is publishing.

Operator: "I see far targets, just not close ones." This matches the
contact-only marking rule's geometric weakness exactly: at close range
the cell-grid step is coarser than the angular tolerance to the
contact pixel row, so few or zero cells round to exact equality with
`contact_row[u]`. Far targets work because the angular tolerance is
wide.

## 7. Hot fix — per-column contact backstop

**2026-05-29T14:0x-04:00** — Implemented operator-requested fix in
`unh_marine_perception/sea_surface_segmentation/include/sea_surface_segmentation/segments_projection.hpp`,
`project_observations_inverse`:

After the cell loop, a second pass iterates the `contact_row` vector.
For each column with a detected contact pixel, back-project (col,
contact_row[col]) directly to z=plane_z and push one observation at
the contact's true world position (same range / grazing gates as the
cell loop). This guarantees ≥1 mark per detected contact column,
regardless of cell-grid alignment with the contact pixel row. No
radial false shadow — we mark only the contact's actual back-projection,
not the body's z=0 backprojection beyond the obstacle.

~40-line addition. Rebuild kicked off; operator will relaunch nav2
group when build completes. Commit + unit-test coverage deferred to
wrap-up (urgency contract).

## 8. Post-hot-fix observations

**2026-05-29T14:1x-04:00** — Operator relaunched. Reports: buoys
marking (including close ones — hot fix working), but two new issues:

1. **On-boat structures marking** — GPS antenna in aft camera frame
   producing false marks near the boat. Geometric reality: the
   column-iteration backstop back-projects each detected contact
   pixel to z=0, and a non-waterline on-boat object's bottom edge
   z=0 backprojection lands near the boat. Previously hidden by
   cell-loop discretization, now exposed.
2. **Buoys not persisting** — marks appear then disappear quickly.

Math: with defaults (`obstacle_clamp=5`, `max_evidence_step=0.85`,
~5 Hz / camera), a cell can drop from LETHAL to below `lethal_threshold=1.0`
in ~1 second of water-classified observations. That's why marks
vanish under boat motion.

### Tuning attempt — persistence

| Time | Param | Old → New | Result | Notes |
|---|---|---|---|---|
| 14:22 | `decay_half_life_s` | 30.0 → 120.0 | applied, awaiting observation | Slow natural decay 4x |
| 14:22 | `obstacle_clamp` | 5.0 → 10.0 | applied, awaiting observation | Double headroom vs water clearing |
| 14:32 | `max_evidence_step` | 0.85 → 2.0 | **too noisy — reverted** | Slamming evidence amplifies false positives along with real ones |
| 14:33 | `max_evidence_step` | 2.0 → 0.85 | reverted to default | Bump was net-worse for this scene |

## 10. Per-source image mask hot fix

**2026-05-29T14:4x-04:00** — Captured a frame from
`/bizzy/sensors/cameras/oak_aft/segmentation` (128x96 px, rgb8). GPS
antenna visible as dark blob at bottom-centre (rows ~75-92, cols ~50-78).

Added a per-source `image_mask_rects` parameter to the layer:
- Flat int array of `[x_min, y_min, x_max, y_max]` tuples (pixel coords).
- Runtime-tunable via `ros2 param set <node> sea_surface_layer.<src>.image_mask_rects '[...]'`.
- Pixels inside any masked rect are set to (0,0,0) before projection —
  black fails both the red-dominant obstacle gate and the green-dominant
  water gate, so masked pixels contribute zero observations (no positive,
  no clearing).
- ~70 lines across `Source` struct, `onInitialize`, `segmentsCallback`,
  `onParametersSet`, and a new `parseMaskRects` helper.

Pre-populated YAML mask for aft camera in
`unh_echoboats_project11/bizzyboat_project11/config/nav2_overlay.yaml`:
```yaml
aft:
  ...
  image_mask_rects: [40, 65, 90, 96]
```
Generous bottom-centre rect covering the GPS antenna. Operator can
adjust live without relaunch via param set.

Rebuilt sensors_ws/sea_surface_segmentation 14:45:55. Operator needs
to relaunch nav2 group to pick up the new .so AND the YAML change.

**2026-05-29T14:5x-04:00** — Operator confirmed after relaunch: "no
more gps trail." Mask hot fix working as designed. The
`[40, 65, 90, 96]` aft rect cleanly suppresses the GPS antenna without
visibly impacting buoy detection in the rest of the aft FOV.

### Tuning re-set after relaunch + second persistence pass

| Time | Param | Old → New | Result | Notes |
|---|---|---|---|---|
| 15:01 | `max_evidence_step` | 0.85 → 0.4 | applied | Slower water clearing (and slower marking) |
| 15:01 | `obstacle_clamp` | 5.0 → 20.0 | applied | 4x original headroom |
| 15:01 | `decay_half_life_s` | 30.0 → 120.0 | applied | Re-set; relaunch wiped earlier 120 |

**Important caveat**: relaunches wipe all runtime-set params back to
YAML defaults. The earlier persistence tuning got reset by the mask
hot-fix relaunch. For a durable change after the run, the operator
wants to commit the values into the nav2 YAML, not just live tuning.

## 11. Camera-info / NN aspect-ratio fix

**2026-05-29T15:1x-04:00** — Operator identified a deeper bug: camera
preview is 1280x720 (16:9), but the NN input shape is 512x384 (4:3)
and segmentation output is 128x96 (4:3). The current pipeline either
center-crops or stretches the preview without the camera_info modelling
which one. Side-FOV detections were either missing or geometrically wrong.

Fix per operator direction: keep 1280x720 preview (full sensor coverage),
explicitly STRETCH to NN input, update camera_info anisotropically.

Code change in
`unh_marine_perception/sea_surface_segmentation/src/sea_surface_segmentation.cpp`:

1. Added `image_manip->initialConfig.setKeepAspectRatio(false)` before
   the existing `setResize(512, 384)` — explicit stretch, not DepthAI
   default's aspect-preserving crop.
2. Rebuilt `segmentation_camera_info_` anisotropically:
   - Call `calibrationToCameraInfo(handler, CAM_A, preview_w, preview_h)`
     to get correct preview-resolution intrinsics from DepthAI's
     calibration handler.
   - Scale `fx`, `cx` by `seg_w / preview_w` (≈ 0.1 at 1280→128).
   - Scale `fy`, `cy` by `seg_h / preview_h` (≈ 0.133 at 720→96).
   - Set `width=128, height=96`.
   - Distortion coefficients left unchanged (small residual; aspect-ratio
     error dominates).

~40 lines. Rebuilt 15:1x. The sea_surface_layer's cameraInfoCallback
picks up the new intrinsics on the next CameraInfo message, so the
nav2 stack does NOT need to relaunch. **Operator needs to relaunch
the sensors_ws launch group** (the one with sea_surface_segmentation-4
through -7) for the camera nodes to pick up the new code.

**2026-05-29T15:2x-04:00** — Operator relaunched sensors. Verified new
camera_info for `oak_aft`:
- `fx = 76.81` (unchanged)
- `fy = 102.37` (was 76.78)
- Ratio fy/fx = 1.333 = 4/3, matching the squish from 16:9 preview
  to 4:3 NN input.

Initial "not seeing them yet" while layer presumably waited for fresh
camera_info; "they are back" confirmed once layer picked up new
intrinsics. Aspect-ratio fix verified live.

**2026-05-29T15:2x-04:00** — Operator confirmed "the stretch worked"
and asked to re-set persistence tuning. Verified: sensors-only
relaunch did NOT wipe the nav2 layer params (`max_evidence_step=0.4`,
`obstacle_clamp=20.0`, `decay_half_life_s=120.0` all still set as of
14:33 / 15:01). Re-applied as requested; no-op since values matched.

**2026-05-29T15:2x-04:00** — Verified GPS mask post-stretch. Fresh aft
segmentation frame shows the GPS antenna now as a red (obstacle-class)
blob at ~cols 50-66, rows 70-87. Two notes:

- The GPS is narrower than before (~15 px wide vs prior ~25 px) — the
  predicted result of the horizontal stretch (compression 0.1× width
  ratio vs the prior keep-aspect-ratio's effective ~0.133×).
- It is now red-classified by the NN (was dark/black before), so the
  mask is actively suppressing strong (not subtle) false marks.

Current mask `[40, 65, 90, 96]` cleanly contains the GPS with generous
margin (50-wide window vs ~15-wide signature). No adjustment needed;
margin protects against boat pitch shifts. Could tighten to e.g.
`[45, 68, 70, 90]` to recover ~3% more usable aft-camera real estate,
deferred — not worth the risk during live ops.

## 12. Goto re-commanding not taking effect

**2026-05-29T15:3x-04:00** — Operator observation: a goto command
issued while a goto is already in progress does NOT take effect. The
boat continues toward the original target.

This is the same class of "latched task" bug that PR #47 / issue #46
fixed for **hover** (re-commanded hover re-targets) and PR #35
addressed for **tracklines** (resending a different trackline switches
without `clear + resend`). Goto appears to still latch.

Plausibly: the BT decorator that fires on task-update-time for hover
(#46) and trackline (#35) may not be wired for goto, OR goto uses a
different task-change path that wasn't updated alongside #46/#35.

**Defer to wrap-up.** Not a live-ops blocker (operator can use
`clear + resend` workaround). Worth a follow-up issue against
`unh_marine_navigation` covering goto with the same fix pattern as
hover/trackline.

## 13. Forward red obstacle not marking — speck-hides-contact hypothesis

**2026-05-29T15:4x-04:00** — Operator: clear red obstacle in forward
segmentation isn't showing on costmap. Captured fresh frame — small
red blob at cols ~68-78, rows ~50-58, well separated from main shore
band; should back-project to ~16 m ahead.

State verification:
- Forward camera_info anisotropic (`fx=76.53, fy=102.00, cy=47.83`)
- controller_server PID 64138 started 14:46:41 → has the mask code
- `/bizzy/sea_surface/lethal_grid` actively publishing: 1600x1600 grid,
  **1454 lethal cells, 15910 non-zero** at check time. Layer is alive
  and marking lots — but not THIS obstacle.
- No new "projection failed" warnings since the post-mask relaunch.

Hypothesis: `project_observations_inverse` builds `contact_row[col]`
by scanning bottom-up and taking the LOWEST obstacle-ish pixel with
water directly below. Per-frame segmentation noise (tiny red specks
in the water region) wins the scan in columns that also contain the
real far obstacle — the speck back-projects to ~3-5 m, the real
obstacle at rows 50-58 never gets a contact recorded.

| Time | Param | Old → New | Result | Notes |
|---|---|---|---|---|
| 15:49 | `obstacle_prob_min` | 0.35 → 0.50 | **no observable improvement** — operator: "still not seeing much" | Specks must already be strongly classified, not weak; raise didn't filter them out. Kept at 0.5 (not reverted). |

## 14. 20-minute bag recording for offline review

**2026-05-29T15:5x-04:00** — Operator asked to record 20 min of video
for offline forensics on the forward-obstacle-not-marking issue. Used
the project's existing recorder script
`unh_echoboats_project11/bizzyboat_project11/scripts/record_camera_topics.sh`
(not a custom Python recorder — the project script bags ALL four
cameras' ffmpeg streams + segmentation + camera_info + TF +
local_costmap, which is what we need for end-to-end replay).

Command:
```bash
.../bizzyboat_project11/scripts/record_camera_topics.sh 1200
```

Output will land at `~/data/logs/bizzy_images/bag_<timestamp>_ffmpeg_seg/`
(mcap, zstd_fast). Will complete ~16:09.

Completed at 16:16 (script exited cleanly):
`~/data/logs/bizzy_images/bag_2026-05-29T15.56.42_ffmpeg_seg/`

Replay use cases:
- Reproduce the contact_row scan against the same frames offline; confirm
  whether speck pixels are winning over real obstacles per-column.
- A/B `obstacle_prob_min`, mask shapes, and any minimum-region-size
  filter on the recorded segmentation.
- Cross-check `/bizzy/local_costmap/costmap` against the segmentation
  frame-by-frame to see exactly where the layer marks vs. expects.

## 16. Boat recovered

**2026-05-29T16:13-04:00** — Operator: boat recovered. End of on-water
phase. The 20-min bag recording (started ~15:50) ran past the
recovery, so it captures the recovery transition as well.

Outstanding question from §15 (sailboat appearance in segmentation)
goes unanswered live; can be inspected offline from the bag.

## 15. Sailboat barely marking at close range

**2026-05-29T16:0x-04:00** — Operator observation: a sailboat is hardly
registering on the costmap at close range. Class-significant — close
sailboats are exactly the kind of obstacle the layer needs to mark
reliably.

Possible mechanisms (pending confirmation of how the sailboat appears
in segmentation):
- Same speck-hides-contact mechanism as §13 — but for a sailboat the
  hull spans many columns, so more chances for false-speck dominance
  per column.
- Hull/sail color not red-dominant in segmentation — white sails appear
  near (255,255,255) which passes the new `R >= obstacle_prob_min*255`
  gate but doesn't pass the green-water gate either; ends up as sky /
  ambiguous and contributes no observation. With current
  `obstacle_prob_min=0.5`, a hull with R=200 would just barely pass.
- NN classification softness at close range — large objects can degrade
  segmentation confidence.

Captured in the 20-min bag for offline A/B. Pending operator answer on
what the sailboat looks like in the live segmentation image to direct
the next tuning move.

## Open follow-ups for wrap-up

This section consolidates the items deferred during live ops; the dev-side
wrap-up log expands them into Summary / Lessons.

- **goto re-commanding latched task bug** (see §12): goto sibling of
  hover #46 / trackline #35 fixes — file issue against
  `unh_marine_navigation` with the same decorator pattern.
- **Forward obstacle not marking via costmap path** (see §13, §14):
  bag-replay analysis required. Likely needs a minimum-region-size
  filter in `project_observations_inverse`'s contact_row scan, OR
  spatial smoothing in the layer's accumulator.
- **GPS / close-aft-buoy mask overlap** (see §10 follow-up): the GPS
  is physically at the same angular elevation as 5-9 m aft buoys; the
  mask blinds both. Long-term: smaller / more-aggressive cropping
  + buoy detection by motion (GPS is fixed in camera frame).
- **Anisotropic distortion not corrected** (see §11): the stretch from
  16:9 preview to 4:3 NN input changes effective distortion model;
  per-pixel distortion correction is now slightly off. Layer
  projection is fine for small distortion; revisit if precision matters.
- **Runtime params not durable across nav2 relaunch**: every tuning
  result (decay_half_life_s=120, obstacle_clamp=20, max_evidence_step=0.4,
  obstacle_prob_min=0.5) needs YAML defaults updated in
  `seafloor_echoboat_project11/echoboat_project11/config/nav2_params.base.yaml`
  and/or `unh_echoboats_project11/bizzyboat_project11/config/nav2_overlay.yaml`.
- **Per-source `image_mask_rects` runtime tunability**: add similar
  param to `SeaSurfaceRelayLayer` (global_costmap) for consistency,
  or document why it's local-only.
- **Hot fix in `segments_projection.hpp` (per-column contact backstop)
  + per-source mask + anisotropic camera_info + explicit-stretch**:
  all uncommitted; needs commits + unit tests + PRs against
  `unh_marine_perception`.

## 9. Reflex collision avoidance worked ✓

**2026-05-29T14:3x-04:00** — Operator: "the collision avoidance worked,
made it go around an obstacle." Clarified by operator that this was
the **reflex `collision_monitor` path** (segments_to_pointcloud_reflex
→ collision_monitor → halt/slowdown/redirect), NOT the
costmap → global planner path. Reflex is independent of the graded
sea-surface layer (see memory: CA reads the reflex pointcloud, not
the costmap).

So what was validated here is the issue's "Reflex still stops"
must-verify item (under unchanged behavior) — the new graded costmap
didn't regress the existing reflex CA. The "Global route bends around
marks" item is still untested.

Open follow-up:
- Buoy persistence improving with the persistence tuning but still
  position-jitter-limited (per operator). Next options are
  `max_evidence_step` bump and/or `inflation_radius` increase if needed.
- GPS-in-aft-camera noise still present; recommend disabling aft source
  or adding `minimum_range` param post-deployment.

