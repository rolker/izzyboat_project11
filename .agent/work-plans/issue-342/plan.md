# Plan: Retrofit M3 bag — TF offset + integer-second clock-skew correction

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/342

## Context

M3 bags recorded since the #77 install carry two defects that corrupt offline
bathy reprocessing:

1. **TF offset wrong** — `bizzy/m3` translation was `(-0.23, 0.0, -0.145)` at
   record time; corrected to `(-0.29, 0.0, -0.28)` in the URDF by #339/#341.
   Every historical M3 bag carries the old transform in its `/tf_static`.

2. **Integer-second clock-skew** — M3 detection `header.stamp` jumped to +6 s
   relative to bag receive-timestamp from Jun 24 onward (mercat Windows clock
   drift in whole-second steps while PPS kept the sub-second fraction correct).
   A 6 s offset causes ~9 m georef error at survey speed.

The fix follows the `retrofit_sidescan_bag.py` precedent: offline rosbag2
read→write (no replay, no ROS node, not installed) with byte-for-byte
passthrough except the two targeted topics.

One key difference from the sidescan script: boat bags are bare `.mcap` files
(not rosbag2 directories), so the script must detect the input type and set
`storage_id='mcap'` for bare files (vs. `storage_id=''` auto-detect for
directories).

A second difference: default mode is in-place replacement with backup (downstream
paths reference the original bag name), not a `_retrofit`-suffix sibling. The
sibling (`--out`) mode is also supported.

## Approach

1. **Create `retrofit_m3_bag.py`** in `bizzyboat_project11/scripts/`.
   - `parse_args()`: positional `in_bag`; `--out PATH`; `--report-only`;
     `--offset N` (force integer); `--no-tf`; `--no-timing`.
   - `detect_storage(path)`: return `'mcap'` for bare `.mcap` file,
     `''` (auto-detect) for directory.
   - `open_reader(path)`: `SequentialReader` using detected storage_id.
   - `open_writer(path, sid, topics)`: `SequentialWriter` preserving
     storage_id and all TopicMetadata (type, QoS, serialization format).
   - `rewrite_tf(msg)`: iterate `transforms`, match `child_frame_id ==
     'bizzy/m3'`, set translation to `(-0.29, 0.0, -0.28)`, rotation
     untouched. Return `(modified_msg, changed: bool)`.
   - `correct_stamp(header_stamp_ns, recv_ts_ns)`: compute
     `offset_s = (header_stamp_ns − recv_ts_ns) / 1e9`;
     `n = round(offset_s)`; emit WARN if `abs(offset_s − n)` is in
     `[0.3, 0.7]`; return `n`, corrected stamp, and `bool` warning flag.
   - `build_histogram(offsets: list[int]) -> dict[int, int]`: count-by-integer.
   - `print_histogram(hist)`: one line per integer offset key.
   - **Timing target topic (must-fix, Plan Review)**: the M3 detections topic is
     pinned as a module constant `M3_DETECTIONS_TOPIC = '/bizzy/sensors/m3/detections'`
     (type `marine_acoustic_msgs/SonarDetections`), from the recorder config in
     `bizzyboat.yaml`. `stream()` applies `correct_stamp` only to messages on this
     topic — mirroring the sidescan precedent's hardcoded `SONAR` target dict. The
     constant is documented so a namespace/topic-rename is a one-line change.
   - `stream(rd, wr_or_none, args)`: main loop — accumulate histogram,
     apply corrections (timing on `M3_DETECTIONS_TOPIC`, geometry on `/tf_static`),
     pass everything else through. Returns counters dict.
   - `main()`: orchestrate — open reader, determine output path (temp or
     `--out`), run `stream()`, then in-place swap if default mode.
   - **In-place swap**: write to `<in_bag>.tmp` (or `.tmp.mcap` for bare);
     only after fully written + `SequentialReader` can open the output: rename
     original → `<in_bag>.orig` (directory) / `<in_bag_stem>.orig.mcap`
     (bare file); rename temp → original name. Clean up temp on failure
     (no partial bag left behind).
   - Print histogram + counters; exit non-zero if `--report-only` and offsets
     detected (no write performed).

2. **Add test infrastructure to `CMakeLists.txt`**.
   - `find_package(ament_cmake_pytest REQUIRED)` inside `if(BUILD_TESTING)`.
   - `ament_add_pytest_test(test_retrofit_m3_bag test/test_retrofit_m3_bag.py)`.
   - `ament_cmake_pytest` is a test-only dep; add to `test_depend` in
     `package.xml`.

3. **Create `test/test_retrofit_m3_bag.py`** with a synthetic bag fixture
   (create a small in-memory MCAP or a temp bag dir via `rosbag2_py` + rclpy
   serialization, or mock the reader/writer at the stream-function level).
   Tests:
   - `test_correct_stamp_healthy`: offset ~0.04 s → `n=0`, stamp unchanged,
     no warning.
   - `test_correct_stamp_six_second`: offset ~6.03 s → `n=6`, stamp shifted
     by 6 s, sub-second fraction preserved.
   - `test_correct_stamp_ambiguous`: offset ~0.5 s → WARN emitted (function
     returns `warning=True`).
   - `test_histogram`: given offsets `[0, 0, 6, 6, 6]` → `{0: 2, 6: 3}`.
   - `test_rewrite_tf_target_frame`: msg with `bizzy/m3` child → translation
     set to `(-0.29, 0.0, -0.28)`, rotation quaternion unchanged, `changed=True`.
   - `test_rewrite_tf_other_frame`: msg with unrelated child → not touched,
     `changed=False`.
   - `test_rewrite_tf_idempotent`: already-corrected translation → still
     `changed=True` (field set; the idempotency guarantee means re-running
     produces the same bag, not that it skips work).
   - `test_stream_passthrough`: with `--no-tf` and `--no-timing`, all messages
     pass unchanged; counters confirm zero rewrites.
   - `test_storage_qos_preserved` (suggestion, Plan Review): round-trip a bag
     through `main()` and assert the output's `storage_id` and every topic's
     `TopicMetadata` (name, type, serialization_format, offered_qos_profiles)
     match the input — covers review-issue action #1 (storage/QoS preservation),
     which message-byte checks alone do not.
   - `test_correct_stamp_only_target_topic`: a non-M3 topic carrying a stale
     stamp is left untouched (timing applies only to `M3_DETECTIONS_TOPIC`).
   - `test_inplace_swap_creates_backup`: after `main()` in default mode on a
     temp bag, the `.orig` backup exists, corrected bag exists at original path,
     and backup contents match the original pre-run input.

## Files to Change

| File | Change |
|------|--------|
| `bizzyboat_project11/scripts/retrofit_m3_bag.py` | New script (main deliverable) |
| `bizzyboat_project11/test/test_retrofit_m3_bag.py` | New unit test file |
| `bizzyboat_project11/CMakeLists.txt` | Add `BUILD_TESTING` block with `ament_cmake_pytest` |
| `bizzyboat_project11/package.xml` | Add `<test_depend>ament_cmake_pytest</test_depend>` |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| A change includes its consequences | Tests and docstring are in-scope (issue specifies both); CMakeLists + package.xml are updated to register tests |
| Only what's needed | No ROS node, no install entry, no new dependency beyond `ament_cmake_pytest` for test discovery |
| Test what breaks | Tests cover the non-obvious invariants: PPS rounding, ambiguous-band WARN, idempotent TF rewrite, backup atomicity |
| Capture decisions, not just implementations | Script docstring explains *why* `round(offset)` is correct (PPS-disciplined sub-second + whole-second Windows drift), per Issue Review action item |
| Improve incrementally | Single PR touching only this script and its tests; no broader refactor |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| ADR-0008 (ROS 2 conventions) | Yes | Script not installed (not a node); test dir follows `test/` convention; `package.xml` uses `<test_depend>` tag correctly |
| ADR-0009 (Python package management) | No — uses only packages already available in the sourced ROS 2 env (`rosbag2_py`, `rclpy`, `rosidl_runtime_py`) | No new pip installs; no requirements.txt change needed |

## Consequences

| If we change... | Also update... | Included in plan? |
|---|---|---|
| `scripts/retrofit_m3_bag.py` (new script) | CMakeLists — no install entry needed (not a node), but test infrastructure added | Yes |
| `CMakeLists.txt` test block | `package.xml` `<test_depend>` | Yes |
| `bizzy/m3` TF correction | Orientation unchanged (patch test still pending per URDF comment) | N/A — script leaves rotation untouched by design |

## Open Questions

- [x] **Resolved (Plan Review suggestion)** — bare `.mcap` write-validation gating
  the in-place backup atomicity: `validate_written(path)` opens a
  `SequentialReader` on the freshly-written output and reads one message. It is
  **fail-closed** — any failure aborts (no `size > 0` fallback), because in
  destructive in-place mode a validation failure must stop rather than be papered
  over. The in-place swap (rename original → `.orig`, install corrected → original)
  runs **only** after `validate_written` passes; if the final move fails, the
  original is rolled back from `.orig`, and the installed bag is re-validated
  (restored on failure), so a failed/partial write never replaces the original.
  **Bag form is preserved**: rosbag2's `SequentialWriter` only emits *directory*
  bags, so for a bare `.mcap` input the single inner segment is extracted to the
  original name (a multi-segment write aborts and asks for `--out`). The bare-file
  round-trip is covered by `test_inplace_bare_mcap_stays_bare`; still worth a
  smoke-test on a real boat bag before bulk use (noted in the PR body).

## Estimated Scope

Single PR.
