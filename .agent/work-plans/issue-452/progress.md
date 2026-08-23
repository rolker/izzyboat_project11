---
issue: 452
---

# Issue #452 — Field import: unh_echoboats_project11 (2026-08-21)

## Local Review
**Status**: complete
**When**: 2026-08-23 00:19 -04:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: changes-requested

**PR**: #453 at `5773156`
**Mode**: post-PR
**Depth**: Deep (untrusted-input parser + cross-repo config coupling + 1270 lines)
**Must-fix**: 10 | **Suggestions**: 18

### Findings
- [x] (must-fix) Garbled/hostile RTCM stream wedges the executor: measured 3.4 s CPU in one `_on_rtcm` for an all-0xD3 buffer; 1 Hz timer starves and `/diagnostics` stops. Validate the 6 reserved header bits (`buf[start+1] & 0xFC`) before the CRC — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:121-142`
- [x] (must-fix) Station-staleness WARN returns before `classify_baseline`, so a 509 km caster reads WARN not ERROR once 1005/1006 stops — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:450-455`
- [x] (must-fix) VRS classification latches permanently; a real caster switch pins `reference_station_kind` to `virtual` for the process lifetime — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:353-363`
- [x] (must-fix) `_rover_fix` never expires and its age is never published; baseline computed against a frozen position can flip ERROR to OK after a transit — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:365-368,457-466`
- [x] (must-fix) `water_line_frame` is a silent no-op on the installed `sea_surface_estimator`; the PR body's claim that an undeclared parameter is a startup failure is verified false — `bizzyboat_project11/config/bizzyboat.yaml:932` (partially deferred: the PR-body correction is the host's; the underlying fact is now recorded in bizzyboat.yaml, and the false claim appears in no repo file)
- [x] (must-fix) New `ellipsoidal_fix` node sits in the nav position path with no annunciator tile; on failure mru_transform silently fails over to the SBG, which this same config documents as tilting the costmap ~2 deg — `bizzyboat_project11/config/bizzyboat_annunciator.yaml`
- [x] (must-fix) Public caster IP `(redacted):8005` and NTRIP account name land in a PUBLIC repo, against the policy in `docs/bizzyboat_network.md:6-7` — `docs/logs/2026/2026-08-21_gabby_logs.md:20` (deferred: already resolved -- the branch history was rewritten and force-pushed to redact both strings before this pass; the log now reads "(redacted)")
- [x] (must-fix) Reference-geometry doc still carries the 90 s / 38 mm preliminary figure superseded later in this same PR by -55 +/- 25 mm over 4.91 h — `bizzyboat_project11/docs/bizzyboat_reference_geometry.md:117`
- [x] (must-fix) Test suite is self-consistent, not verified: `frame()` uses the node's own CRC and `station_1005()` mirrors the decoder, so a swapped X/Y or bit-reversed CRC would pass — `bizzyboat_project11/test/test_rtcm_diagnostics.py`
- [x] (must-fix) Calibration tool pairs on bag receive timestamps with a 1 s tolerance, breaking its own "heave cancels" premise on the planned transit re-run — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:37,83`
- [x] (suggestion) Zero/placeholder ARP decodes to lat 90 / 5218 km and raises a false ERROR; reject implausible ECEF norms — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:173-192`
- [x] (suggestion) `_message_types` is cumulative and never decays; `msm` merges both casters after a mountpoint switch — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:299,422`
- [x] (suggestion) `reference_station_kind` asserts `physical` from a single observation — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:436-438`
- [x] (suggestion) Unrecognised `rtcm_message_package` silently falls through to mavros_msgs — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:310-316`
- [x] (suggestion) `publish_rate: 0.0` raises in `__init__`, outside `main()`'s try, so `rclpy.shutdown()` is skipped — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:270,323`
- [x] (suggestion) Unpopulated `h_acc`/`v_acc` (zero-filled MAVLink extension) publish as perfect accuracy — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py:119-120`
- [x] (suggestion) No-data branch omits `fix_type` while every other path includes it — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py:87-89`
- [x] (suggestion) No `respawn` on rtcm_diagnostics although its sibling ntrip_client has one — `bizzyboat_project11/launch/ntrip_launch.py:81`
- [x] (suggestion) Whole credentials YAML passed as parameters; no leak today (verified) but the invariant is undefended — `bizzyboat_project11/launch/ntrip_launch.py:85`
- [x] (suggestion) Comment says "Two maximum frames"; the constant is 4x — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:54-57`
- [x] (suggestion) `main()` runs at import; add a `__main__` guard — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:160`
- [x] (suggestion) flake8 F541 f-string without placeholders — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:156`
- [x] (suggestion) `0.890` hard-coded twice instead of `FCU_ANT[1]`, so a URDF update silently desyncs the tool — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:157`
- [x] (suggestion) mcap sort key raises ValueError on any stem not ending `_<int>` — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:51-52`
- [x] (suggestion) `b` is both the bag loop variable and the SBG-attitude mean; correct only by ordering — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:108,128`
- [x] (suggestion) Neither named resync test exercises the resync path — `bizzyboat_project11/test/test_rtcm_diagnostics.py:155-175`
- [x] (suggestion) Referenced photo `2026-04-22_GPS_antennas_aft.jpg` is not in the repo — `bizzyboat_project11/docs/bizzyboat_reference_geometry.md:92`
- [x] (suggestion) `.agents/README.md` says "Only test: test_retrofit_m3_bag.py" (now three suites) and its not-installed-scripts pitfall should name `gnss_vertical_calibration.py` — `.agents/README.md:128,153`
- [x] (suggestion) `gnss_vertical_calibration.py` omitted from `install(PROGRAMS ...)` with no explanatory comment, unlike the retrofit tools — `bizzyboat_project11/CMakeLists.txt:16`

## Implementation
**Status**: complete
**When**: 2026-08-23 00:55 -04:00
**By**: Claude Code Agent (Claude Opus)

**Branch**: feature/issue-452 at `cd946de`
**PR**: #453
**Addressed**: `## Local Review` (2026-08-23 00:19 -04:00, PR #453 at `5773156`) — 10 must-fix, 18 suggestions
**Commits**: `41d620e` `28169a7` `a7d1b4d` `30677e5` `523ad5b` `60f848c` `c21d127` `87b19ac` `44415c4` `0507580` `771a216` `a169eb2` `878681b` `cd946de`

### Actions — must-fix
- [x] Parser wedge on garbled/hostile RTCM: the 6 reserved header bits are now validated before the CRC (`RTCM_RESERVED_MASK`), so the all-`0xD3` case is linear instead of quadratic — `scripts/rtcm_diagnostics_node.py:120-165` (`41d620e`). Four regression tests pin the cost: zero CRC calls on that buffer, a wall-clock backstop, the `0xD3 0x00` case that legitimately still reaches the CRC, and a valid frame with a reserved bit set.
- [x] Staleness masking a bad baseline: classification now always runs, and `apply_station_staleness()` folds the stale note in by *raising* the level, never replacing it — a 509 km base stays ERROR with 1005/1006 stopped — `scripts/rtcm_diagnostics_node.py:206-221` (`28169a7`)
- [x] VRS classification latching across a caster switch: a station-ID change or a jump beyond `station_switch_m` (1 km) resets the motion tracking and logs it; the Delaware→MaCORS case is a unit test — `scripts/rtcm_diagnostics_node.py:387-425` (`30677e5`)
- [x] Rover fix never expiring: `fix_timeout` (10 s) ages it out, the status says `rover fix Ns old` rather than a stale distance, and `rover_fix_age_s` is published on every tick — `scripts/rtcm_diagnostics_node.py:365-380,470-520` (`a7d1b4d`)
- [x] `water_line_frame` silent no-op — `config/bizzyboat.yaml:932` (`60f848c`) (partially deferred: the PR-body correction is the host's. The underlying fact is now recorded where it matters: setting a parameter a node does not declare is a silent no-op, not a startup failure, so an mru_transform older than `58b7f97` loses the correction with no signal. The config carries the cross-repo dependency and the one-line `ros2 param get` check. The false claim appears in no repo file — verified by grep.)
- [x] No annunciator tile for the ellipsoidal-fix node: added, with the reason (its failure is a silent mru_transform failover to the SBG and its ~2 deg roll offset) — `config/bizzyboat_annunciator.yaml:68-78` (`523ad5b`). Scoped to this repo only; nothing touched in `seafloor_echoboat_project11`.
- [x] Public caster IP and NTRIP account name in a public repo — `docs/logs/2026/2026-08-21_gabby_logs.md:20` (deferred: already resolved before this pass — the branch history was rewritten and force-pushed to redact both strings; the log now reads "(redacted)". Verified absent from the tree; neither string appears in any file, commit message, or this entry.)
- [x] Superseded 90 s / 38 mm figure: replaced with the 4.91 h result (low by 55 ± 25 mm, the uncertainty being the spread of half-hourly means), plus why it is deliberately not applied and that the Shoals transit is the dataset that would settle it — `docs/bizzyboat_reference_geometry.md:117-131` (`c21d127`)
- [x] Self-referential test suite: added the catalogued CRC-24/LTE-A check value (`0xCDE703` over `123456789`) and a complete 1005 frame encoded outside this repo — it validates only against a bit-exact CRC, its CRC over frame-plus-checksum is zero, and its ARP decodes to a real place. A companion test shows the swap the old suite could not catch: X↔Y moves that point from Washington DC to the western Pacific — `test/test_rtcm_diagnostics.py:91-160` (`87b19ac`)
- [x] Calibration tool pairing on bag receive timestamps: pairs on message header stamps at 0.15 s, prints the observed skew so the heave-cancels premise is checkable, and counts/warns on messages with no header stamp — `scripts/gnss_vertical_calibration.py:36-60,86-160` (`44415c4`)

### Actions — suggestions
- [x] Implausible ECEF raising a false ERROR: reference points outside a plausible band around the ellipsoid are rejected, so a zero ARP reads "station unknown" instead of a 5218 km baseline — `scripts/rtcm_diagnostics_node.py:184-200` (`0507580`)
- [x] `_message_types` never decaying: types age out of `message_type_window` (60 s), so a mountpoint switch no longer merges two casters into one MSM4/5 claim (`0507580`)
- [x] `reference_station_kind` asserted from one observation: `classify_station_kind()` reports `unknown (single report)` until it has two (`30677e5`)
- [x] Unrecognised `rtcm_message_package` falling through to mavros_msgs: now raises (`0507580`)
- [x] `publish_rate: 0.0` skipping `rclpy.shutdown()`: construction moved inside `main()`'s try, and the rate validated with an explanatory message (`0507580`)
- [x] Unpopulated `h_acc`/`v_acc` publishing as perfect accuracy: they read `not reported` (`771a216`)
- [x] No-data branch omitting `fix_type`: publishes `-1` (`771a216`)
- [x] No `respawn` on rtcm_diagnostics: added, matching its sibling ntrip_client (`a169eb2`)
- [x] Credentials YAML invariant undefended: asserted at startup rather than assumed — the node refuses to run if a credential-shaped parameter is ever declared on it (`0507580`)
- [x] "Two maximum frames" comment: corrected to four (`41d620e`)
- [x] `main()` at import: `__main__` guard (`878681b`)
- [x] flake8 F541 (`878681b`)
- [x] `0.890` hard-coded twice: reads `FCU_ANT[1]` (`878681b`)
- [x] mcap sort key raising on a non-conforming stem: `mcap_sort_key()` sorts it last instead (`878681b`)
- [x] `b` shadowed between the bag loop and the SBG-attitude mean: both renamed (`878681b`)
- [x] Neither resync test exercising resync: replaced with a corrupt-frame-then-good-frame case and a mid-stream attach case (`87b19ac`)
- [x] Photo `2026-04-22_GPS_antennas_aft.jpg` not in the repo: it is local-only per the install-log photo index; the reference now says so rather than looking broken (`c21d127`)
- [x] `.agents/README.md` test inventory and not-installed-scripts pitfall: both updated (`cd946de`)
- [x] `gnss_vertical_calibration.py` omitted from `install(PROGRAMS ...)`: the reason is now stated in place, as the retrofit tools already did (`cd946de`)

### Verification
- `colcon`-registered pytest suites, run in the worktree: **128 passed** (`test_rtcm_diagnostics` 77, plus `test_retrofit_m3_bag` and `test_operator_core_launch` unchanged and green).
- `flake8 --select=E9,F,C90` clean across `scripts/`, `test/`, `launch/`. (The repo's pre-commit deliberately leaves full flake8 off; the remaining output is pre-existing ament D/I/Q style noise.)
- Live smoke test of the node under `rclpy`: fed the external 1005 frame plus a rover fix, and the provenance status came back `ERROR — station 2003, 713.7 km — fix not trustworthy`, with `reference_station_kind: unknown (single report)` and `rover_fix_age_s: 0.0`. The whole chain — framing, CRC, ARP decode, baseline, classification — runs end to end on a frame this repo did not produce.
- Pre-commit hooks ran on every commit; none bypassed.

### Noted, not actioned
- The 2026-08-21 field log (line 22) calls the Delaware stream "MSM7 1075/1085/1095/1125". 1075 is GPS **MSM5** (MSM7 is 1077), and `test_summarise_msm_delaware_shape` already pins the correct reading with a comment saying so. Left as-is: the log is a record of what was observed and said at the time, and correcting it in place was outside the review's findings. Worth an appended correction if the log is revisited.
