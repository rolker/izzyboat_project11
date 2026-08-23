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
- [ ] (must-fix) Garbled/hostile RTCM stream wedges the executor: measured 3.4 s CPU in one `_on_rtcm` for an all-0xD3 buffer; 1 Hz timer starves and `/diagnostics` stops. Validate the 6 reserved header bits (`buf[start+1] & 0xFC`) before the CRC — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:121-142`
- [ ] (must-fix) Station-staleness WARN returns before `classify_baseline`, so a 509 km caster reads WARN not ERROR once 1005/1006 stops — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:450-455`
- [ ] (must-fix) VRS classification latches permanently; a real caster switch pins `reference_station_kind` to `virtual` for the process lifetime — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:353-363`
- [ ] (must-fix) `_rover_fix` never expires and its age is never published; baseline computed against a frozen position can flip ERROR to OK after a transit — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:365-368,457-466`
- [ ] (must-fix) `water_line_frame` is a silent no-op on the installed `sea_surface_estimator`; the PR body's claim that an undeclared parameter is a startup failure is verified false — `bizzyboat_project11/config/bizzyboat.yaml:932`
- [ ] (must-fix) New `ellipsoidal_fix` node sits in the nav position path with no annunciator tile; on failure mru_transform silently fails over to the SBG, which this same config documents as tilting the costmap ~2 deg — `bizzyboat_project11/config/bizzyboat_annunciator.yaml`
- [ ] (must-fix) Public caster IP `(redacted):8005` and NTRIP account name land in a PUBLIC repo, against the policy in `docs/bizzyboat_network.md:6-7` — `docs/logs/2026/2026-08-21_gabby_logs.md:20`
- [ ] (must-fix) Reference-geometry doc still carries the 90 s / 38 mm preliminary figure superseded later in this same PR by -55 +/- 25 mm over 4.91 h — `bizzyboat_project11/docs/bizzyboat_reference_geometry.md:117`
- [ ] (must-fix) Test suite is self-consistent, not verified: `frame()` uses the node's own CRC and `station_1005()` mirrors the decoder, so a swapped X/Y or bit-reversed CRC would pass — `bizzyboat_project11/test/test_rtcm_diagnostics.py`
- [ ] (must-fix) Calibration tool pairs on bag receive timestamps with a 1 s tolerance, breaking its own "heave cancels" premise on the planned transit re-run — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:37,83`
- [ ] (suggestion) Zero/placeholder ARP decodes to lat 90 / 5218 km and raises a false ERROR; reject implausible ECEF norms — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:173-192`
- [ ] (suggestion) `_message_types` is cumulative and never decays; `msm` merges both casters after a mountpoint switch — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:299,422`
- [ ] (suggestion) `reference_station_kind` asserts `physical` from a single observation — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:436-438`
- [ ] (suggestion) Unrecognised `rtcm_message_package` silently falls through to mavros_msgs — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:310-316`
- [ ] (suggestion) `publish_rate: 0.0` raises in `__init__`, outside `main()`'s try, so `rclpy.shutdown()` is skipped — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:270,323`
- [ ] (suggestion) Unpopulated `h_acc`/`v_acc` (zero-filled MAVLink extension) publish as perfect accuracy — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py:119-120`
- [ ] (suggestion) No-data branch omits `fix_type` while every other path includes it — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py:87-89`
- [ ] (suggestion) No `respawn` on rtcm_diagnostics although its sibling ntrip_client has one — `bizzyboat_project11/launch/ntrip_launch.py:81`
- [ ] (suggestion) Whole credentials YAML passed as parameters; no leak today (verified) but the invariant is undefended — `bizzyboat_project11/launch/ntrip_launch.py:85`
- [ ] (suggestion) Comment says "Two maximum frames"; the constant is 4x — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:54-57`
- [ ] (suggestion) `main()` runs at import; add a `__main__` guard — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:160`
- [ ] (suggestion) flake8 F541 f-string without placeholders — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:156`
- [ ] (suggestion) `0.890` hard-coded twice instead of `FCU_ANT[1]`, so a URDF update silently desyncs the tool — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:157`
- [ ] (suggestion) mcap sort key raises ValueError on any stem not ending `_<int>` — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:51-52`
- [ ] (suggestion) `b` is both the bag loop variable and the SBG-attitude mean; correct only by ordering — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:108,128`
- [ ] (suggestion) Neither named resync test exercises the resync path — `bizzyboat_project11/test/test_rtcm_diagnostics.py:155-175`
- [ ] (suggestion) Referenced photo `2026-04-22_GPS_antennas_aft.jpg` is not in the repo — `bizzyboat_project11/docs/bizzyboat_reference_geometry.md:92`
- [ ] (suggestion) `.agents/README.md` says "Only test: test_retrofit_m3_bag.py" (now three suites) and its not-installed-scripts pitfall should name `gnss_vertical_calibration.py` — `.agents/README.md:128,153`
- [ ] (suggestion) `gnss_vertical_calibration.py` omitted from `install(PROGRAMS ...)` with no explanatory comment, unlike the retrofit tools — `bizzyboat_project11/CMakeLists.txt:16`
