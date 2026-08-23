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

## Local Review
**Status**: complete
**When**: 2026-08-23 01:10 -04:00
**By**: Claude Code Agent (Claude Opus)
**Verdict**: changes-requested

**PR**: #453 at `7bef686`
**Mode**: post-PR
**Depth**: Deep (untrusted-input parser + cross-repo launch coupling + ~2070 insertions across 15 files)
**Must-fix**: 10 | **Suggestions**: 21

**Round**: 2. Round 1's two adversarial sub-passes stalled and never returned, so its 10 must-fix came from a single lead reading plus one focused logic pass plus the Copilot bot. This round split the adversarial work into four bounded, area-scoped passes (RTCM3 parser; test vectors; diagnostics nodes + calibration tool; launch/config wiring) and **all four completed**. The local Ollama cross-model specialist was deliberately skipped (it OOM'd on a diff this size twice and killed the llama-server); the Copilot specialist was not run (no `--copilot`). Findings below are the four passes plus lead-reviewer spot-checks executed against the real code.

### Findings
- [x] (must-fix) The reserved-bit pre-filter added in round 1 does NOT bound parser cost: `b"\xd3\x03\xff"` repeated passes the filter and claims length 1023, so every 3 bytes triggers a 1026-byte CRC. Measured 1.10 s in one `_on_rtcm` on a single 4116-byte buffer (`\xd3\x01\xff` 1.21 s, `\xd3\x00` 0.74 s) — the same executor-starving wedge round 1 thought it had closed, re-reachable with a different pattern. The all-`0xD3` case IS fixed (1.6 ms). Cap CRC work per callback or require a plausible following preamble — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:141-168`
- [x] (must-fix) `_on_fix` rejects NaN but not ±inf; an inf latitude reaches `math.sin(math.radians(inf))` in the timer callback, raising ValueError past `main()`'s KeyboardInterrupt-only guard. Process exits, `/diagnostics` goes silent, which the module docstring itself says reads as health. Use `math.isfinite` — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:505-508,231-233`
- [x] (must-fix) No framing test uses a payload over 255 bytes, so the top 2 bits of the 10-bit length field are never exercised: mutating `RTCM_RESERVED_MASK` from `0xFC` to `0xFF` passes all 77 tests while silently discarding real MSM7 frames (1077/1087/1097/1127 routinely exceed 255 bytes). Add a framing case at length 1023 — `bizzyboat_project11/test/test_rtcm_diagnostics.py` (framing section, 195-345)
- [x] (must-fix) `test_swapping_x_and_y_would_be_caught` is vacuous — it re-encodes with the test's own `llh_to_ecef` and asserts a property of `atan2` argument order, never re-decoding the frame. It PASSES under an X↔Y-swapped `parse_reference_station`. It is the one self-referential test sitting inside the "external check vectors" section, claiming independence it does not have — `bizzyboat_project11/test/test_rtcm_diagnostics.py:166`
- [x] (must-fix) Hard lockstep on an unmerged sibling branch: `ellipsoidal_fix_node` does not exist in `echo_helm` on origin/jazzy (only on `seafloor_echoboat_project11` `feature/issue-55`). If this branch reaches gabby before #55 is merged and echo_helm rebuilt, `core_launch.py` aborts at Node execute — the whole boat launch dies, it does not degrade. Neither the comment nor `<exec_depend>echo_helm</exec_depend>` expresses a version constraint — `bizzyboat_project11/launch/core_launch.py:226-247`
- [x] (must-fix) `sensor_msgs` is imported by the now-installed `rtcm_diagnostics_node.py` but is not an `exec_depend` (`rclpy` is `test_depend` only, a pre-existing gap this compounds). On a clean rosdep install the node dies on import and both the `NTRIP` and `RTK: corrections` tiles simply never publish — rendered as absence, not fault — `bizzyboat_project11/package.xml`
- [x] (must-fix) `v_acc`/`h_acc` are now published but never affect `status.level`, so the exact 2026-08-20 case (v_acc 1.750 m while fix_type read 6) still publishes OK/"RTK Fixed" and the tile stays green. The code comment says vertical accuracy "degrades long before fix_type does" and then nothing acts on it. Add `warn_v_acc_m`/`error_v_acc_m` that pass through on the not-reported sentinel — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py:121-141`
- [x] (must-fix) `main()` is unguarded and `core_launch.py` launches this node without `respawn`, unlike its neighbour: one exception (e.g. an int launch override against a float-typed parameter) permanently silences `/diagnostics` — reintroducing, one level up, the absence-reads-as-health failure this file exists to prevent. Round 1 moved construction inside `main()`'s try for `rtcm_diagnostics_node`; this sibling did not get the same treatment — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py:151-156`, `bizzyboat_project11/launch/core_launch.py:249-259`
- [x] (must-fix) Sign error in the printed correction instruction. ArduPilot's body frame is FRD, and this repo's own records have `GPS_POS1_Z = -0.890` for a URDF z of `+0.890`. The tool tells the operator both "should change by {c} mm", illustrated with the URDF value — applying `+c` to `-0.890` moves the FCU antenna the wrong way, injecting ~110 mm into the FCU vertical path instead of removing ~55 mm. Print the two targets with their own signs, and say that `GPS_POS2` (aft antenna) was never measured — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:222-224`
- [x] (must-fix) The tool's own uncertainty apparatus reads "perfect" on exactly the run it was written for: half-hourly buckets mean any corpus under 30 min lands in one bucket, so `max(drift)-min(drift)` is 0 and it prints "spread of half-hourly means: 0.0 mm -- this, not the sem, is the honest uncertainty"; and with one surviving sample `pstdev` and `sem` are both 0 and a confident millimetre figure still prints. The planned transit re-run is short. Require >=2 populated buckets and a minimum n/timespan, and name which gate failed — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:206-216,147-152,220`
- [x] (suggestion) `length = (buf[start+1] << 8) | buf[start+2]` omits the `& 0x03` mask; correct only as a side effect of the reserved-bit check three lines above, so any reordering re-opens megabyte-span CRCs — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:154`
- [x] (suggestion) Liveness reports `OK - receiving corrections` for a stream containing zero CRC-valid frames, because `_last_rtcm_time` is stamped from raw byte arrival before framing. Stamp a separate `_last_valid_frame_time` — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:449-453,529-549`
- [x] (suggestion) (cross-pass confirmed: RTCM + nodes passes) Ages are computed on the ROS system clock, so a backward clock step — routine on a GPS/NTP-disciplined boat after boot — makes every `age > timeout` comparison false and stale data read fresh. Clamp negatives and treat a negative delta as unknown — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:524-527`, `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py:112`
- [x] (suggestion) A legitimate VRS re-anchor beyond `station_switch_m` (1 km) is misread as a caster switch: tracking resets, `classify_station_kind` drops to `unknown (single report)`, and a spurious "Reference station changed" logs at the same station ID. Gate the reset on a station-ID change too — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:476,488`
- [x] (suggestion) All five parameters passed to the local `ellipsoidal_fix` Node are byte-identical to the node's own defaults, so the stated reason for keeping a local copy ("carrying this hull's topic parameters") does not hold. Deleting the local Node and the `enable_ellipsoidal_fix:=false` argument collapses the two-repo coupling and is also the cleanest resolution of the launch-abort must-fix — `bizzyboat_project11/launch/core_launch.py:230-236` (deferred: kept deliberately -- see the launch commit; deleting it makes the stale-echo_helm case silent instead of loud)
- [x] (suggestion) `water_line_frame` silent no-op confirmed against the checked-out mru_transform: the declaration lands in `58b7f97`, which is on `feature/issue-32` and `gitcloud/jazzy` but NOT origin/jazzy. The YAML comment documents this honestly; nothing enforces it. The other three keys in that block are declared and the `/**/sea_surface_estimator` wildcard matches exactly — `bizzyboat_project11/config/bizzyboat.yaml:941` (deferred: the enforcement belongs in mru_transform, a sibling repo this sub-agent may not edit)
- [x] (suggestion) The new 35/100 km baseline thresholds are tuned for MaCORS, but the credentials file they read (`ccomjhc_project11/configuration/bizzyboat_ntrip.yaml`) still points at the Delaware caster, so the tile goes straight to ERROR on the next NH boot. Arguably the feature working, but it is a cross-repo edit owed outside this PR — `bizzyboat_project11/launch/ntrip_launch.py:96-99` (deferred: the credentials file is in ccomjhc_project11, a sibling repo; recorded as a cross-repo item)
- [x] (suggestion) The credentials YAML is now loaded by a second node. Verified genuinely inert (the node declares only host/port/mountpoint; rclpy discards the rest), but splitting the non-secret host/port/mountpoint into their own file would remove the question — `bizzyboat_project11/launch/ntrip_launch.py:82` (deferred: the split belongs in ccomjhc_project11, a sibling repo; verified inert here)
- [x] (suggestion) `test_hostile_buffer_costs_no_more_than_a_few_milliseconds` asserts wall-clock under 0.03 s (measured 1.4-2.4 ms). The preceding test already proves the invariant deterministically via a monkeypatched CRC counter, so this one is a redundant flake source under coverage tracing or a contended runner — `bizzyboat_project11/test/test_rtcm_diagnostics.py:312`
- [x] (suggestion) `test_resync_from_a_mid_frame_start_recovers_the_next_frame` does not exercise resync — the tail it starts from contains no `0xD3`, so it is behaviourally identical to the leading-garbage test. Real resync IS covered by the corrupt-payload and embedded-false-preamble cases — `bizzyboat_project11/test/test_rtcm_diagnostics.py:252`
- [x] (suggestion) Untested edges: the `RTCM_MAX_BUFFER` trim (the unbounded-growth guard the docstring advertises), and a valid-CRC frame with a 0/1-byte payload (behaviour verified correct by hand) — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:455-457,158`
- [x] (suggestion) `test_1006_is_accepted` patches the message number into a 19-byte 1005-shaped payload; a real 1006 payload is 21 bytes (DF028 antenna height). The test never sees a realistically-shaped 1006 — `bizzyboat_project11/test/test_rtcm_diagnostics.py:371`
- [x] (suggestion) `eph`/`epv`/`satellites_visible` publish raw: per GPSRAW they are DOP scaled x100 with UINT16_MAX (and 255) meaning unknown, so HDOP 1.21 reads "121" and an unpopulated field reads "65535" — the same class the adjacent `accuracy_text()` was just written to prevent — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py:133-135`
- [x] (suggestion) ERROR fires on the first tick ~1 s after launch, before mavros has streamed anything, so the RTK tile flashes red on every boot. WARN "waiting for first message" until `stale_timeout` elapses — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py:97-109`
- [x] (suggestion) Key sets still diverge: the no-data branch carries `gps_raw_topic` and `fix_type`, every other path carries the accuracy/age keys and not `gps_raw_topic`. Emit the full key set on every path — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py:102-107,131-141`
- [x] (suggestion) `ok_min_fix_type`/`warn_min_fix_type` are unvalidated (a `warn_min > ok_min` override makes the WARN branch unreachable), and the 1 Hz publish period is hard-coded while `stale_timeout` is a parameter, so a sub-second timeout is unsatisfiable — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py:71-72,80`
- [x] (suggestion) `FCU_ANT`/`SBG_ANT` are a hand copy of the URDF that this tool's own output causes to change; they match `/tf_static` today, but the next run after anyone applies the correction is reduced with stale lever arms and nothing catches it. Read them from the bag's `/tf_static`, or at least print them beside the result. `lever_z` also drops the y component — safe only while both antennas are on the centreline; assert it — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:24-26,86-89`
- [x] (suggestion) Pairing is one-directional in read order (FCU/attitude always at-or-before the SBG fix) and the printed skew is `abs`-ed, so a systematic one-sided lag — precisely what would break the heave-cancels premise the skew print exists to check — is hidden. Print the signed mean alongside max absolute — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:109-143,132,175`
- [x] (suggestion) `latest` entries are never consumed, so one FCU/attitude sample can back several SBG-triggered samples when rates differ; `n`, `pstdev` and `sem` then treat correlated samples as independent, and the buckets over-weight stretches where rates diverge — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:99,127-134`
- [x] (suggestion) The quoted correction pools every bag while the odom section is deliberately split per bag because a config change landed mid-corpus. Print `v_s` per bag too — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:184-189,220,197-202`
- [x] (suggestion) No plausibility bound on the result: if the two altitude sources are ever on different datums the tool prints "should change by +27000 mm" in the same confident tone. Refuse above ~0.5 m and name the likely cause — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:220-224`
- [x] (suggestion) One message, 'no samples survived the quality gates', covers at least six distinct causes, several of them wrong-input rather than bad-data: no bags on the command line (no argparse, no --help), a directory with no `*.mcap` (non-recursive glob; a path to a single .mcap matches nothing), a bag from another namespace (`/bizzy` hard-coded), a missing topic, and `position_covariance_type = UNKNOWN` rejecting 100%. Count rejections by cause and report per-topic counts — `bizzyboat_project11/scripts/gnss_vertical_calibration.py:166-168`

### Verified correct (checked, no finding)
- The reserved-bit test itself (`buf[start+1] & 0xFC`) is exactly right per RTCM3 framing and has **no false-negative path** — no conforming frame is ever dropped. It fixes the all-`0xD3` case it was written for (3.4 s -> 1.6 ms). It just is not a general cost bound (must-fix 1).
- **CRC-24/LTE-A vector VERIFIED.** An independently written MSB-first CRC gives `0xCDE703` over `123456789` for poly `0x1864CFB`/init 0/non-reflected/xorout 0, cross-checked against two other catalogue entries (OPENPGP `0x21CF02`, LTE-B `0x23EF52`). RTCM's CRC-24Q is parameterically identical to CRC-24/LTE-A, so the test cites the right entry and the right constant. A reflected variant gives `0x9AAC54` and an output-bit-reversal mutant fails 5 tests — it has teeth.
- **External 1005 frame VERIFIED.** Independently decoded with a from-scratch bit extractor: CRC computed `0x360B98` = CRC received, CRC over frame-plus-checksum is 0, 152/152 bits consumed, station 2003, ECEF matching the asserted constants, lat 38.80475943 / lon -77.06477360 / h 114.56 m — Arlington VA, a real place. **Not node-derived**: the test's own `station_1005()` helper hardcodes the constellation indicators to 1,1,1 while the captured frame carries 1,0,0. An X↔Y swap in the decoder makes two captured-frame tests fail. The round-1 self-referential finding is genuinely closed for the decode path.
- **Exactly ONE `ellipsoidal_fix_node` in the `bizzy` namespace with both branches applied.** The sibling launches it at `namespace=""` which resolves to `/bizzy`, so the collision was real and the suppression is necessary; `IfCondition(LaunchConfiguration(...))` evaluates the string `"false"` through launch's condition machinery, not Python truthiness, so it works. Passing the argument to an OLD sibling is a silent no-op, not an error (`include_launch_description.py:45-52`), and the include is inside a scoped GroupAction so nothing leaks. The failure mode is the reverse case — must-fix 5.
- **Topic parameters do reach the surviving node.** `ellipsoidal_fix` sits outside the `PushRosNamespace('mavros')` group, so its relative topics resolve correctly and are not double-prefixed; all five parameters are declared by the node; all ten `rtcm_diagnostics` parameters are declared with matching types; the credentials file is keyed `/**:` so host/port/mountpoint genuinely arrive and only the secret keys are ignored, as the comment claims.
- Annunciator strings match their publishers character-for-character (`GPS: ellipsoidal fix`, `RTK: corrections`, `NTRIP` preserved via `liveness_diagnostic_name`); no duplicate or orphaned indicator names.
- The retired `ntrip_diagnostics_node.py` has no live references anywhere — install list, launch, config and agent guide are all clean; remaining mentions are dated log entries and "retired" prose.
- RTCM 1005/1006 bit layout (152 bits = 19 bytes, zero slack), 38-bit two's-complement ECEF at 0.1 mm, frame arithmetic and CRC span, the loop's guaranteed advance, the 4116-byte buffer cap (a hostile stream cannot grow it), `ecef_to_llh` p==0 handling, the `[6.3e6, 6.5e6]` ECEF sanity band, and `apply_station_staleness` raising rather than replacing the level — all checked, all correct.
- Regression constants independently recomputed: UDEL baseline 508.76 km (asserted 509.2 +/- 1.0), MaCORS 27.44 km (27.4 +/- 0.5), one degree of latitude 111.195 km (111.2 +/- 0.5).
- Secret sweep clean: the 2026-08-21 log reads "(redacted)" for both the caster host and the account name, and neither string appears in any file or in any commit message on this branch.

### Static analysis
Run. `flake8 --select=E9,F,C90,E501` clean on every changed file (the only E501 hits are in untouched `ntrip_client_launch.py`). yamllint clean on both configs. The remaining ament D/I/Q/A003 output is repo-wide pre-existing style noise, and `.pre-commit-config.yaml` deliberately leaves black/flake8 off pending the license-header cleanup — dropped by the silence filter rather than reported.

### Existing review comments
Four Copilot reviews, nine inline comments. Eight are against superseded commits (`5773156`, `c558d87`, `f18c0da`) and were addressed by the round-1 fix pass — including the respawn-on-`ellipsoidal_fix` comment, which is stale: `respawn=True, respawn_delay=2` is present at HEAD. Its rationale does, however, apply verbatim to `gps_rtk_diagnostics` immediately below, which still has none — a cross-source confirmation of must-fix 8. The one comment at HEAD (test file, known-good CRC vector) is answered by the catalogued vector added in `87b19ac`, independently verified above. CI `build-and-test` is green.

### Plan adherence
No work plan exists at `.agent/work-plans/issue-452/plan.md` (field-import PR; only progress.md). Plan Drift specialist skipped.

## Implementation
**Status**: complete
**When**: 2026-08-23 17:43 -04:00
**By**: Claude Code Agent (Claude Opus)

**Branch**: feature/issue-452 at `9bd0484`
**PR**: #453
**Addressed**: the round-2 `## Local Review` (2026-08-23 01:10 -04:00, at `7bef686`) — 10 must-fix, 21 suggestions
**Commits**: `1e695a5` `002196a` `47f563e` `f21964e` `b0ddc19` `cb2ced2` `83beb3a` `4bf161a` `8de44e3` `78faad9` `075f09a` `45433aa` `c37a98e` `9bd0484`

Test suite before writing this entry: **231 passed** (`pytest test/`, with the
platforms_ws overlay sourced — sourcing only `/opt/ros/jazzy` fails the eight
pre-existing `test_operator_core_launch.py` cases on `get_package_prefix`, which
is an environment artefact, not a regression). Was 77 at the start of round 2;
three new suites and 154 new cases. `flake8 --select=E9,F,C90,E501` clean on every
changed file.

### The parser wedge now has a work bound, not a better filter

`1e695a5`. The round-1 reserved-bit filter is correct and drops no conforming
frame, but it is a filter: `b"\xd3\x03\xff"` repeated passes it and declares a
1023-byte payload, so every 3 bytes bought a 1026-byte CRC. `iter_rtcm_frames`
now carries a CRC budget of `2 * len(buf) + RTCM_MAX_FRAME`.

| input, one full 4116-byte buffer | before | after |
|---|---|---|
| `\xd3\x03\xff` repeated | 1.10 s | **8.3 ms** |
| `\xd3\x01\xff` repeated | 1.21 s | **8.5 ms** |
| `\xd3\x00` repeated | 0.74 s | **6.5 ms** |
| `\xd3` repeated | 1.6 ms (round 1) | 1.2 ms |

Two properties make the budget safe rather than merely small. A conforming
stream needs at most one CRC pass over each byte it delivered — frames do not
overlap and a validated frame is skipped whole — so twice the buffer length
cannot reject a real frame; `test_the_budget_never_rejects_a_conforming_stream`
packs the buffer with back-to-back 1023-byte frames and checks all of them come
out. And the floor of one whole frame guarantees the head candidate is always
validated, so every call consumes at least one byte and a hostile stream cannot
stall the parser instead of wedging it.

The regression test is parametrized over all four patterns and asserts against
**two** ceilings: the declared budget, and an absolute `4 * RTCM_MAX_BUFFER`
that does not move when `RTCM_CRC_BUDGET_FACTOR` does — without the second,
widening the constant would have widened the test with it. Verified by mutation:
`RTCM_CRC_BUDGET_FACTOR = 100000` fails 4 tests.

### The calibration sign error

`002196a`. `correction_report()` now prints each target's own before/after value
with the frame that fixes its sign named beside it:

```
  URDF gnss_forward z   (base_link, z UP)             +0.890 -> +0.835 m  (-55 mm)
  GPS_POS1_Z            (ArduPilot body FRD, z DOWN)  -0.890 -> -0.835 m  (+55 mm)
```

and says `GPS_POS2_Z` was never measured. The arithmetic moved into
`corrected_antenna_height()` so the signs are testable without a bag;
`test_the_same_measurement_raises_gps_pos1_z_because_that_frame_is_down` pins
the naive application at `-0.945`, exactly `2 * |correction|` from the truth.
Mutating the function to `-urdf_z + correction_m` fails 5 tests.

### Vertical accuracy reaches the level

`47f563e`. `apply_vertical_accuracy()` with `warn_v_acc_m` 0.10 m and
`error_v_acc_m` 0.50 m. The 2026-08-20 case (fix_type 6, `v_acc` 1.750 m) is now
ERROR. It raises and never lowers, passes through on the not-reported sentinel,
and leaves STALE alone.

**A default worth your eye**: 0.10 / 0.50 m are my numbers, not measured ones. I
took them from what a working RTK fix on this hull reports (0.02–0.05 m) and from
0.10 m already being worse than the 55 mm lever-arm error this branch spent a day
chasing. They are parameters, but they decide when the tile goes amber.

### The two weak tests

`f21964e`. Both now fail under the mutation they claimed to catch:
`RTCM_RESERVED_MASK` `0xFC`→`0xFF` fails 4 tests (was 0), and an X↔Y swap in
`parse_reference_station` fails 7 (`test_swapping_x_and_y_would_be_caught` used
to pass under it — it never re-decoded anything). The replacement applies the
swap to the decoder itself via monkeypatch rather than asserting a property of
`atan2` alongside it.

### The judgement call: `core_launch.py` and echo_helm

`4bf161a`. **Kept the local Node; did not delete it.** Reasoning, since this
reverses the round-2 suggestion:

- **Verified, not assumed**, how `launch` treats an argument an included
  description does not declare: `IncludeLaunchDescription`'s own docstring says
  unmatched arguments "will still be set as Launch Configurations using the
  `SetLaunchConfiguration` action". A silent no-op, no error. So
  `enable_ellipsoidal_fix:=false` is harmless in **either** merge order.
- The `Node` is the half that is not harmless. `ExecutableInPackage.perform()`
  raises `SubstitutionFailure` when the executable is missing, at execute time,
  and that aborts the whole launch description.
- **Confirmed on this machine**: `ellipsoidal_fix_node` is on
  `seafloor_echoboat_project11` `feature/issue-55` only, not `origin/jazzy`, and
  the installed `echo_helm` ships only `echo_helm_node`. This branch aborts the
  boat launch here *today*.
- Neither end state is safe under both merge orders. Deleting the local Node
  makes the stale-echo_helm case **silent**: nothing publishes
  `mavros/global_position/global_ellipsoidal`, `mru_transform` has no FCU
  position, and the `GPS: ellipsoidal fix` tile is simply absent — and absence
  reading as health is the failure this entire PR exists to close. A boat that
  will not start beats a boat that floats with a dead vertical.

So the required order is made loud instead: a preflight `OpaqueFunction`, first
in the launch description so it fires before 130-odd nodes are part-way up. It
resolves the same `ExecutableInPackage` lookup `Node` uses — it cannot pass while
the Node it guards fails — and raises with the repo, the PR, the reason, and the
`colcon build --packages-select echo_helm` line. It stays useful after #56
merges, because a stale build on a boat is the same symptom.

**MERGE ORDER — needs your decision, not mine**: this branch must not reach a
boat before `rolker/seafloor_echoboat_project11#56` is merged and `echo_helm`
rebuilt. It is stated in `core_launch.py` at the include, in the preflight
message, and in `.agents/README.md`.

### Everything else

Remaining must-fixes: `b0ddc19` (`math.isfinite` plus a coordinate-range check
on the rover fix — ±inf reached `math.sin` in the timer and exited the process),
`cb2ced2` (`rclpy` + `sensor_msgs` as `exec_depend`), `83beb3a` (guarded
`main()` + `respawn` to match its two neighbours), `8de44e3` (uncertainty gates:
≥2 populated buckets, 30 samples, 1 h, each failure named; a single bucket prints
NOT MEASURED rather than 0.0 mm, and a failing corpus marks the report
PROVISIONAL — the 2026-08-21 corpus passes all three, so the result on record
stands).

Suggestions: `78faad9` (liveness stamped from CRC-valid frames rather than raw
bytes; negative clock deltas clamped in both nodes; VRS re-anchor no longer read
as a caster switch), `075f09a` (DOP scaling, first-tick WARN instead of a red
flash on every boot, one key set on every path, threshold and timeout
validation), `45433aa` (four test gaps), `c37a98e` (argparse + `--namespace`,
recursive mcap search, rejection counts by cause, signed skew, samples consumed
so they are independent, per-bag quoted quantity), `9bd0484` (agent guide).

**One reconciliation you should know about.** Round 1 added
`test_same_id_at_a_wholly_different_position_also_resets` ("two casters can serve
the same station number; the jump is the tell"); round 2 said a 1 km jump
threshold misreads a legitimate VRS re-anchor. Both are right, so rather than
overwrite one with the other I split the threshold: a changed station ID always
resets, and an unchanged one resets only past a new `same_id_switch_m` (50 km).
The 509 km Delaware→MaCORS case still resets; a 4 km re-anchor no longer does.
Round 1's test still passes unmodified.

### Actions
- [x] (must-fix) CRC budget bounds parser cost per callback; 1.10 s → 8.3 ms — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py:141-200`
- [x] (must-fix) `fix_position_usable()` rejects ±inf and out-of-range coordinates — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py`
- [x] (must-fix) Framing tested across the whole 10-bit length field; the mask mutation now fails 4 tests — `bizzyboat_project11/test/test_rtcm_diagnostics.py`
- [x] (must-fix) The X↔Y test now applies the swap to the decoder; the mutation fails 7 tests — `bizzyboat_project11/test/test_rtcm_diagnostics.py`
- [x] (must-fix) echo_helm lockstep made loud and self-explaining; local Node kept deliberately — `bizzyboat_project11/launch/core_launch.py`
- [x] (must-fix) `rclpy` + `sensor_msgs` declared `exec_depend` — `bizzyboat_project11/package.xml`
- [x] (must-fix) `warn_v_acc_m` / `error_v_acc_m` raise the level, pass through on the sentinel — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py`
- [x] (must-fix) `main()` guarded and the node respawned like its siblings — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py`, `bizzyboat_project11/launch/core_launch.py`
- [x] (must-fix) Correction printed per target with each frame's own sign; `GPS_POS2` named as unmeasured — `bizzyboat_project11/scripts/gnss_vertical_calibration.py`
- [x] (must-fix) Uncertainty gates on buckets, n and timespan, each failure named — `bizzyboat_project11/scripts/gnss_vertical_calibration.py`
- [x] (suggestion) Length field masked with `0x03` explicitly — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py`
- [x] (suggestion) `_last_valid_frame_time` + `last_valid_frame_age_s` — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py`
- [x] (suggestion) Negative clock deltas clamped in both nodes — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py`, `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py`
- [x] (suggestion) VRS re-anchor split from a caster switch via `same_id_switch_m` — `bizzyboat_project11/scripts/rtcm_diagnostics_node.py`
- [x] (suggestion) Delete the local `ellipsoidal_fix` Node (deferred: kept deliberately — deleting it makes the stale-echo_helm case silent instead of loud; see the judgement above) — `bizzyboat_project11/launch/core_launch.py`
- [x] (suggestion) `water_line_frame` silent no-op (deferred: enforcement belongs in `mru_transform`, a sibling repo this sub-agent may not edit) — `bizzyboat_project11/config/bizzyboat.yaml:941`
- [x] (suggestion) Baseline thresholds vs the Delaware credentials (deferred: the credentials file is in `ccomjhc_project11`, a sibling repo — see cross-repo items) — `bizzyboat_project11/launch/ntrip_launch.py`
- [x] (suggestion) Split the credentials YAML (deferred: belongs in `ccomjhc_project11`; verified inert here) — `bizzyboat_project11/launch/ntrip_launch.py`
- [x] (suggestion) Redundant wall-clock test dropped; one backstop kept on the pattern with the 1.10 s history — `bizzyboat_project11/test/test_rtcm_diagnostics.py`
- [x] (suggestion) The mid-frame resync test now contains a candidate preamble — `bizzyboat_project11/test/test_rtcm_diagnostics.py`
- [x] (suggestion) Buffer-cap and 0/1-byte-payload cases added — `bizzyboat_project11/test/test_rtcm_diagnostics.py`
- [x] (suggestion) `station_1006()` builds a realistic 21-byte payload — `bizzyboat_project11/test/test_rtcm_diagnostics.py`
- [x] (suggestion) `hdop`/`vdop` scaled, sentinels honoured — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py`
- [x] (suggestion) First tick WARNs instead of flashing red on every boot — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py`
- [x] (suggestion) One key set on every path — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py`
- [x] (suggestion) Thresholds and `stale_timeout` validated; `publish_rate` is a parameter — `bizzyboat_project11/scripts/gps_rtk_diagnostics_node.py`
- [x] (suggestion) Lever arms printed beside the result; centreline asserted (deferred in part: reading them from the bag's `/tf_static` is the real fix and is not done) — `bizzyboat_project11/scripts/gnss_vertical_calibration.py`
- [x] (suggestion) Signed mean skew printed alongside max absolute — `bizzyboat_project11/scripts/gnss_vertical_calibration.py`
- [x] (suggestion) Sample sets consumed, so `n`/`pstdev`/`sem` see independent samples — `bizzyboat_project11/scripts/gnss_vertical_calibration.py`
- [x] (suggestion) The quoted quantity printed per bag too — `bizzyboat_project11/scripts/gnss_vertical_calibration.py`
- [x] (suggestion) Plausibility bound at 0.5 m, naming the likely cause — `bizzyboat_project11/scripts/gnss_vertical_calibration.py`
- [x] (suggestion) Empty-corpus report names which of the six causes happened — `bizzyboat_project11/scripts/gnss_vertical_calibration.py`

### Deferred, and why
- **Delete the local `ellipsoidal_fix` Node** — reversed after verifying the
  failure modes on both sides. The full reasoning is in the judgement section
  above and in `4bf161a`'s message. This is the one place I did not follow the
  review, so it deserves your eye.
- **`/tf_static` lever arms** in the calibration tool — the cheap half is done
  (printed beside the result, with a note that they are a hand copy that this
  tool's own output invalidates). Reading them from the bag is a real change to
  the read loop and belongs in its own issue.

### Cross-repo items (recorded, not edited — sub-agent scope)
- `rolker/seafloor_echoboat_project11#56` — **must merge and `echo_helm` must be
  rebuilt before this branch reaches a boat.** Nothing in this repo can enforce
  that; the preflight makes it loud rather than preventing it.
- `ccomjhc_project11/configuration/bizzyboat_ntrip.yaml` still points at the
  Delaware caster, so the new 35/100 km baseline thresholds will take the tile
  straight to ERROR on the next NH boot. Arguably the feature working, but it is
  an edit owed outside this PR.
- Splitting the non-secret host/port/mountpoint out of that same credentials
  file would remove the question of a second node loading it. Verified inert
  today (the node declares only those three keys; rclpy drops the rest).
- `mru_transform` declares `water_line_frame` only on `feature/issue-32` and
  `gitcloud/jazzy`, not `origin/jazzy`. The YAML comment documents the silent
  no-op honestly; nothing enforces it.
