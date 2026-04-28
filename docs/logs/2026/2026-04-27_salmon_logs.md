# BizzyBoat deployment log — salmon — 2026-04-27

**Host**: salmon
**Operator**: Roland + Claude Code Agent (Claude Opus 4.7, 1M context)
**Mode**: field (gitcloud origin)
**Deployment**: [#94](https://github.com/rolker/unh_echoboats_project11/issues/94)

## Summary

Day's plan: troubleshoot the camera grid rqt plugin, then software
integration of the sonar and on-water testing. Session opens with a
quick NVIDIA driver currency check, followed by `make sync` + `make
build` — which brought in the new per-host deployment-log convention
(this file is the first instance on salmon) and the camera-grid plugin
changes that are today's first work item.

## 1. NVIDIA driver check

2026-04-27T09:51-04:00 — verified NVIDIA driver currency on salmon.

- Running `580.126.09` on RTX 3070 Ti Laptop GPU
- `apt-cache policy nvidia-driver-580`: candidate matches installed
  (`580.126.09-0ubuntu0.24.04.2`, from `noble-updates`)
- 580 is the current production branch in Ubuntu 24.04; nothing newer
  offered
- Aside: `nvidia-driver-550` package is still installed alongside 580
  (not the active driver). Could `sudo apt autoremove --purge
  nvidia-driver-550` to clean up — deferred, not blocking.

No driver update needed.

## 2. Workspace sync + build

2026-04-27T09:53-04:00 — `make sync` then `make build`.

Sync pulled:

- `unh_echoboats_project11` (`bdc4a1a..6da895d`): new
  `docs/logs/README.md` per-host deployment-log convention,
  `docs/roadmap.md`, `docs/bizzyboat_deployment_log.md` frozen with
  header pointer to the new convention, plus other doc updates.
- `rqt_operator_tools` (`fd3bb3e..9e08f49`): camera grid plugin
  changes — `staleness_tracker.{hpp,cpp}`, `camera_pane_widget.{hpp,cpp}`,
  expanded `test_staleness_tracker.cpp`. Today's troubleshooting target.

Build: all 7 layers (underlay, core, platforms, sensors, simulation,
ui, site), 90 packages OK, no warnings or errors.

## 3. Zenoh router + diagnostic rqt wrapper

2026-04-27T10:15-04:00 — set up isolated tmux session for today's
camera-grid debugging instead of bringing up the full operator stack.

### Zenoh router

- Session/window: `tmux attach -t rqt-debug`, window `zenoh`
- Command (matches `bizzyboat_project11/scripts/start_tmux_*.bash`):
  `ros2 run rmw_zenoh_cpp rmw_zenohd` after sourcing `/opt/ros/jazzy`
  + `layers/main/site_ws/install`, with `RMW_IMPLEMENTATION=rmw_zenoh_cpp`
- Verified healthy: `ros2 topic list` returns `/parameter_events` +
  `/rosout` (the rmw_zenoh-default pair) within ~1 s. PIDs 652593
  (`ros2 run` parent) / 652597 (`rmw_zenohd` binary).
- Note: router stdout is silent by default. To get router-side
  traffic logs, restart it with `RUST_LOG=zenoh=info` (or
  `zenoh=debug` — firehose). Not done yet; revisit if camera-grid
  symptoms point at transport issues.

### Diagnostic rqt wrapper

`/.agent/scratchpad/run_rqt_diag.sh` — wraps `rqt` with crash-friendly
diagnostics. Lives in workspace scratchpad (not project repo) since
it's a debugging tool, not project code.

What it captures, per run, into `~/data/logs/rqt_camera_grid/rqt_<TS>.*`:

- `*.meta.txt` — env snapshot up-front: `ROS*`/`RMW*`/`ZENOH*`/`QT*`
  vars, `nvidia-smi`, `free -h`, ros2 daemon status, zenoh router
  PIDs, camera-relevant topic list.
- `*.log` — full stdout+stderr stream (Qt warnings/critical, plugin
  load chatter from `QT_DEBUG_PLUGINS=1`, ROS log lines unbuffered).
- `*.postmortem.txt` (only on non-zero exit) — recent `dmesg`
  segfault lines, `coredumpctl list`, last 80 log lines, gdb hint.

Knobs the wrapper sets:

- `ulimit -c unlimited` — allow coredumps so systemd-coredump catches
  segfaults (default `ulimit -c` on this shell is `0`)
- `QT_LOGGING_RULES='*.warning=true;*.critical=true;qt.qpa.*=true'`
- `QT_DEBUG_PLUGINS=1`
- `RCUTILS_LOGGING_BUFFERED_STREAM=0`, `RCUTILS_COLORIZED_OUTPUT=0`
- `RUST_LOG=zenoh=info,zenoh_transport=warn` (overridable)

Usage examples:

```bash
.agent/scratchpad/run_rqt_diag.sh                              # full rqt
.agent/scratchpad/run_rqt_diag.sh --standalone rqt_camera_grid # plugin only
```

`--standalone rqt_camera_grid` is the recommended starting point —
fewer moving parts, log output stays on-topic.

## 4. Camera grid test — no-data run did not repro; live-data test still owed

2026-04-27T10:21–10:23-04:00 — first diag run: `--standalone
rqt_camera_grid`, 88 s session, no camera topics published.

### Result on the original issue — partial only

Operator loaded the previously-problematic perspective/config and used
the plugin normally — **no crash during use, but no data flowing
either**. Plugin loaded silently (zero Qt warnings/critical, zero
plugin-side log messages). This rules out a static-init or
config-parse crash, but **does not** confirm the original issue is
resolved — that bug was likely data-driven and needs a live-data
repro attempt before we call it. The two upstream `rqt_operator_tools`
commits brought in by today's sync are the candidate fix:

- `2335fc6` — staleness border now driven by
  `max(arrival_age, header.stamp_age)` instead of arrival-only, with
  invalid-stamp handling forcing `Level::Error`. Closes its
  `unh_echoboats_project11#25`.
- `6682d0c` — `update_label()` throttle requires `since_update >=
  0.0` so a backwards `use_sim_time` jump can't freeze the label;
  `level_at()` comment corrected to describe worst-of-both negative-
  age behavior.

Files: `rqt_camera_grid/{src,include/rqt_camera_grid}/{camera_pane_widget,staleness_tracker}.{cpp,hpp}`,
new tests in `test/test_staleness_tracker.cpp`.

### Separate finding — shutdown segfault (exit 139)

Operator closed the GUI normally; the wrapper caught a SIGSEGV during
teardown. Sequence in
`~/data/logs/rqt_camera_grid/rqt_2026-04-27T10.21.39.log`:

```
class_loader.ClassLoader: SEVERE WARNING!!! Attempting to unload library
while objects created by this loader exist in the heap! ...
zenoh::api::session: close session zid=f0c006573...
Segmentation fault (core dumped)
```

Classic pluginlib teardown ordering — `class_loader` unloads the
plugin `.so` while live objects from it remain on the heap; their
destructors then segfault on a now-dangling symbol. Likely upstream
(pluginlib / rqt_gui_cpp lifecycle), not the camera-grid plugin
itself. Process was exiting anyway, so functionally benign — but it
masks any real teardown bug we might introduce later, so worth
filing for someone to track down.

### Wrapper limitation surfaced

The post-mortem couldn't get a backtrace: `coredumpctl` is not
installed on salmon (`coredumpctl: command not found`), and `dmesg`
requires sudo. To capture stack traces from future segfaults:

```
sudo apt install systemd-coredump      # then re-run; coredumpctl gdb <PID>
```

Or run under gdb directly:

```
gdb --args rqt --force-discover --standalone rqt_camera_grid
# (gdb) run     # then on segfault: thread apply all bt full
```

### Teardown

2026-04-27T10:35-04:00 — stopped the dedicated `rqt-debug` tmux
session (zenoh router C-c'd cleanly, then `tmux kill-session`).
Operator switching to the project's normal start script
(`bizzyboat_project11/scripts/start_tmux_*.bash`) for the live-data
repro attempt — it brings up its own zenoh in its own tmux session.

## 5. Live-data repro — crash IS still there, and it's an abort not a segfault

2026-04-27T10:33-04:00 — operator launched the normal start script,
opened the bizzyboat rqt (`project11:ui` window, `rqt_gui -p
bizzyboat`), used the config dialog to add the **two side segmentation
streams**, closed the dialog. rqt died.

### What we caught (from the `project11:ui` tmux pane)

```
[FFMPEGSubscriber]: flushing decoder.        ← ×7
terminate called after throwing 'eprosima::fastcdr::exception::BadParamException'
  what():  The string contains null characters
[ERROR] [rqt_gui-1]: process has died [pid 655426, exit code -6, ...]
[INFO]  [rqt_gui-1]: process started with pid [656591]   ← launch respawn
```

- Exit code `-6` ⇒ killed by **SIGABRT**, not SIGSEGV. Different
  failure mode from the §4 shutdown segfault.
- `terminate()` from an uncaught `eprosima::fastcdr::BadParamException`
  ("The string contains null characters") — fastcdr's standard message
  for a string field with embedded `\0` during (de)serialization.
- The 7× `flushing decoder` immediately before is rqt_camera_grid
  tearing down the existing FFMPEGSubscribers as the apply replaces
  the camera-pane layout. The abort lands during the fresh
  re-subscribe / first-message-decode cycle.

### Working hypothesis

A string field of an incoming message on the new subscription contains
embedded nulls, and fastcdr deserialization aborts. Most likely
`header.frame_id` or another `std::string` field on the segmentation
or ffmpeg topic — possibly something on the publisher side that builds
a string from a fixed buffer without trimming at the terminator.
Less likely: rqt_camera_grid itself constructs a string with stray
nulls that gets round-tripped through DDS metadata.

The 4-camera layout already running (forward, port, starboard, aft)
did *not* trigger this — it's specifically the **add-and-apply** path
that does. So either (a) a particular topic newly subscribed in this
delta has the bad string and the existing 4 happen not to, or (b) the
re-subscription cycle for any topic is the trigger and we just hadn't
exercised it before today's repro.

### Self-inflicted gotcha — apport rate-limited

Diagnostic miss: the §4 shutdown segfault filled apport's quota for
`/opt/ros/jazzy/bin/rqt` with a `.crash` at 10:23. When the live-data
abort hit at 10:33, apport suppressed the duplicate. Result: no stack
trace captured for the actual bug.

Cleared `/var/crash/_opt_ros_jazzy_bin_rqt.1001.{crash,upload}` so
the next repro is captured. The shutdown-segfault coredump was
already unpacked to `/tmp/apport-rqt.pi51P3/CoreDump` (429 MB)
before clearing — preserved for later inspection if useful, gone on
reboot.

**Wrapper followup**: `.agent/scratchpad/run_rqt_diag.sh` should
`rm -f /var/crash/_opt_ros_jazzy_bin_rqt.*.crash` at start so it
never poisons the apport slot for the real repro that follows.

### Next step

Operator to repeat the same dialog action (add two side seg streams,
close to apply) on the respawned rqt. Apport will capture; we
`apport-unpack` and `gdb` the CoreDump for a backtrace through
`__cxa_throw` → fastcdr.

### Repro and diagnosis from pane output (no apport needed)

Apport actually didn't capture this one either (whoopsie still
flagging within its window even after we cleared the file), but the
respawn-launch printed the actual exception to the tmux pane:

```
terminate called after throwing 'rclcpp::exceptions::InvalidTopicNameError'
  what():  Invalid topic name: ... must not contain characters other than
           alphanumerics, '_', '~', '{', or '}':
  '/bizzy/sensors/cameras/oak_starboard/segmentation  [compressed]/compressed'
                                                     ^
```

Different exception type than the first crash (`fastcdr
BadParamException` vs. `rclcpp InvalidTopicNameError`) but **same root
cause**: the topic name contains the literal substring
`"  [compressed]"` — i.e. the human-readable dropdown label was used
as a topic name. So my §5 "string with null characters" hypothesis
was wrong; the first crash was the same bug surfacing through fastcdr
instead of rclcpp's name validator depending on transient state.

### Bug location

`rqt_camera_grid/src/config_dialog.cpp:610` —
`save_current_editor_to_config`:

```cpp
p.base = base_combo_->currentText().toStdString();
```

The combo populates items as `addItem(label, base)` where
`label = base + "  [" + transport + "]"` (line 271-272) and the clean
base lives in `itemData`. `currentText()` returns the line-edit text,
which is the **display label** — not the clean base.

The dropdown-pick path is wired so `onBaseEditChanged` calls
`setEditText(clean_base)` *before* committing — so most pick paths
save clean. But line 223 wires `lineEdit::editingFinished` directly
to `commit_current_editor`, bypassing `onBaseEditChanged`. On combo
popup-close, `editingFinished` can fire on some Qt platforms/styles
*before* `currentIndexChanged`, while the line edit still holds the
dirty display label. That commit saves dirty, `rebuild_thumbnail_cell`
constructs a `CameraPaneWidget` whose `subscribe()` passes
`config_.base = "<base>  [<transport>]"` to
`image_transport::subscribe`, the transport handler appends
`/compressed`, rclcpp validates → `InvalidTopicNameError` → uncaught
→ `terminate()` → SIGABRT.

### Proposed minimal fix

Three lines in `save_current_editor_to_config`:

```cpp
const int idx = base_combo_->currentIndex();
const QString edit = base_combo_->currentText();
if (idx > 0 && edit == base_combo_->itemText(idx)) {
  p.base = base_combo_->itemData(idx).toString().toStdString();
} else {
  p.base = edit.toStdString();
}
```

- Dirty-label commit path → line edit matches `itemText(idx)` → uses
  clean `itemData`
- Already-cleaned commit path (`setEditText(base)` ran) → line edit
  doesn't match `itemText` → uses the (clean) line edit
- Free-typed custom topic → `idx ≤ 0` → uses line edit verbatim

Plus a defensive fix worth considering separately: catch
`std::exception` from `subscribe()` in `CameraPaneWidget` and surface
the error in the pane border instead of letting it `terminate()` the
whole rqt process. A bad config in one pane should not take down the
entire camera grid — and any exception thrown from `subscribe()`
that bypasses our save-side validation will keep tripping
`terminate()` until then.

### Both fixes landed; partial result; moved on

2026-04-27T10:55-04:00 — applied both edits to
`rqt_operator_tools/rqt_camera_grid/`, rebuilt
(`colcon build --symlink-install --packages-select rqt_camera_grid`,
8.4 s, clean), committed as two atomic commits and pushed to
gitcloud (field mode, no PR):

- `b449acb fix(rqt_camera_grid): read base topic from itemData not display label`
- `7f1d78b fix(rqt_camera_grid): catch subscribe() exceptions to keep one pane from terminate()ing rqt`

Operator restarted the bizzyboat rqt window and re-ran the same
add-two-side-seg-streams + close dialog action. **Behavior changed**:

- No more `terminate called after throwing 'rclcpp::exceptions::InvalidTopicNameError'` line
- No more exit code `-6` (SIGABRT)
- Process now dies with exit code `-11` (SIGSEGV) during the same teardown sequence (8× `flushing decoder`, then segfault)

Read: the SIGABRT crash mode from §5 is genuinely fixed (the dialog
no longer leaks the dirty display label, and even if a bad config
slipped through, `subscribe()` would catch). What remains is a
**separate** segfault in the post-throw / re-subscribe lifecycle —
likely either a `sub_` left in a half-state by the caught throw, or
something downstream (ThumbnailCell?) that constructs its own
subscriber from the same `config_.base` and is unprotected.

Operator chose to commit the partial progress and move on rather
than continue debugging — they have what they need to operate
around the remaining issue. Worth a follow-up issue on
`rqt_operator_tools` for the dev side to pick up:

- Investigate the post-throw segfault path (CameraPaneWidget::sub_
  state after caught exception, ThumbnailCell own subscriber)
- Consider hardening populate_topic_combo's `preserved` capture too
  (it uses currentText() the same way line 610 did)
- Audit any other `currentText()`/`text()` reads on
  base_combo_/lineEdit for the same display-label-leak class of bug

A coredump should now be available for someone to chase the
SIGSEGV (apport file gets refreshed each crash since the SIGABRT
slot was freed earlier). `apport-unpack /var/crash/_opt_ros_jazzy_bin_rqt.1001.crash <dir>` then `gdb /opt/ros/jazzy/bin/python3 <dir>/CoreDump`.

## 6. Post-fix SIGSEGV — diagnosed via gdb-wrapped diag session

2026-04-27T11:18-04:00 — to capture the post-fix SIGSEGV with a
proper backtrace (no apport rate-limit games), wrote a gdb-wrapped
companion to the diag wrapper:

- `.agent/scratchpad/run_rqt_gdb.sh` — `gdb -batch` around rqt with
  auto `bt full` + `thread apply all bt` on signal/exit, output to
  `~/data/logs/rqt_camera_grid/rqt_<TS>_gdb.{log,bt,meta.txt}`.

Started in a dedicated `rqt-diag` tmux session running rqt with the
`bizzyboat` perspective and `__node:=rqt_diag` (so it doesn't
collide with the launch-respawned `__node:=rqt`). Operator
reproduced the dialog action; gdb caught a clean SIGSEGV and dumped
the backtrace before exiting.

### Bug #2 — use-after-free in CameraPaneWidget callback lambda

The crashing thread is a ROS spin thread (`rqt_gui_cpp::Nodelet
PluginProvider::RosSpinThread`) inside the C++ message-delivery
chain. Top frames:

```
#0  QObjectPrivate::maybeSignalConnected(unsigned int) const
#1  ??? in libQt5Core.so.5                                  (Qt signal-emit machinery)
#2  rqt_camera_grid::CameraPaneWidget::imageReceived(...)   ← `emit imageReceived(msg)`
#3  rqt_camera_grid::CameraPaneWidget::handleImage(...)
#4  rqt_camera_grid::CameraPaneWidget::subscribe()::lambda  ← `[this]` captured raw
#8  compressed_image_transport::CompressedSubscriber::internalCallback
#16 rqt_gui_cpp::...::RosSpinThread::run()
```

`CameraPaneWidget::subscribe` (`src/camera_pane_widget.cpp:121-129`)
captures raw `this` in the message callback lambda. On config-apply,
old panes are destroyed and new ones constructed; the old pane's
destructor calls `sub_.shutdown()`, but `image_transport::Subscriber::shutdown` is **not** a synchronous drain of
in-flight callbacks. A message already on the spin thread's
dispatch path enters the lambda after the widget has been
destroyed → `this->handleImage(msg)` → `emit imageReceived(...)` →
Qt walks the connection list of a corrupted QObject → SIGSEGV.

This is **a completely separate bug from §5's dialog-save bug**:
- §5 = dialog leaks display label into `config_.base` → `subscribe()`
  throws → terminate (SIGABRT). Fixed.
- §6 = even with a clean `config_.base`, the destroy-then-rebuild
  cycle on apply races with the executor delivering an in-flight
  message to the destroyed pane → SIGSEGV.

### Why this didn't show up on a different machine replaying data

A destroyed-pane callback only races when a message arrives during
the narrow destroy-then-recreate window. Live H.265 over zenoh on
salmon delivers hot frames every ~200 ms per stream — small window,
but achievable on apply. A bag replay at lower rate, paused, or with
different scheduling would miss the window most of the time.

### Fix shape (for the dev side)

Capture a `QPointer<CameraPaneWidget>` instead of raw `this` — Qt's
`QPointer` auto-nulls when the QObject is destroyed, so the lambda
can early-return when it observes null:

```cpp
#include <QPointer>
// ...
QPointer<CameraPaneWidget> self(this);
sub_ = it_->subscribe(
  config_.base, qos,
  [self](const sensor_msgs::msg::Image::ConstSharedPtr & msg) {
    if (self) {self->handleImage(msg);}
  },
  ...);
```

Two-line change. Should also audit `imageReceived` connections —
the slot side may need similar care if the connection target outlives
the source signaler.

Not landed today — operator chose to move on after gdb capture.
Filing as a follow-up issue alongside the dialog-side cleanup
already noted in §5.

### Update — fix landed

2026-04-27T~12:00-04:00 — operator delegated the fix while setting
up sonar on a different machine. Applied as described above:
QPointer capture in the subscribe() lambda with `if (!self) return`
early-exit, plus `#include <QPointer>` next to the existing Qt
includes. Built clean (7.5 s, single-package colcon).

Commit: `d936384 fix(rqt_camera_grid): guard subscriber lambda
against widget destruction race`. Pushed to gitcloud `jazzy`.

Three fixes today on this repo, in order:

- `b449acb` — bug #1, dialog dirty-save (SIGABRT)
- `7f1d78b` — defensive try/catch in subscribe (SIGABRT → SIGSEGV
  unmasking)
- `d936384` — bug #2, callback lambda use-after-free (SIGSEGV)

Verification of `d936384` requires the operator to restart the
bizzyboat rqt window when they're back from the sonar setup and
re-run the same dialog action. The rebuilt
`librqt_camera_grid.so` is already in
`layers/main/ui_ws/install/rqt_camera_grid/lib/`; respawn picks
it up automatically. Did **not** kill the running rqt — operator
restarts on their schedule (per the
[don't-kill-user-processes](feedback memory) rule learned earlier
this session).

Residual concern documented in the commit body: there's a narrow
race between `if (!self)` and the actual `self->handleImage(msg)`
deref if destruction begins concurrently. For bulletproof safety
the destructor needs to synchronize with the callback path
(mutex around the destroyed flag). Not done — accepting the
standard Qt+ROS idiom for now. If the SIGSEGV recurs in practice,
that's the next step.

### Verified

2026-04-27T~12:30-04:00 — operator restarted the bizzyboat rqt and
re-ran the same dialog action (add two side segmentation streams,
close to apply). **No crash.** Three commits land the camera-grid
work for today:

- `b449acb` dialog dirty-save → cured the SIGABRT
- `7f1d78b` defensive try/catch in subscribe → keeps one bad pane
  from taking down rqt going forward
- `d936384` QPointer in callback lambda → cured the SIGSEGV

Camera grid line item is closed. Moving to sonar.

## 7. Boat deployed — on-water phase

2026-04-27T12:35-04:00 — boat in the water. Sonar bring-up was
prepped on a separate machine while the camera-grid fix was being
applied (§6). On-water testing phase begins.

### CAMP freeze + udp_bridge wedge

2026-04-27T~12:40-04:00 — operator reported CAMP frozen, killed it;
launch respawned CAMP (new PID), but **all video feeds went dark**.

Diagnosis from `ros2 topic info` + tmux `core` pane:

- Camera topics still advertised, publisher = operator-side
  `udp_bridge` (`/operator/udp_bridge`)
- `ros2 topic hz` returned no samples on the forward ffmpeg topic
  *or* on `/diagnostics`, `/bizzy/marine/heartbeat` — so this was
  **not** camera-specific; the whole boat→operator UDP pipeline
  was silent on our side
- Crucially, `ss -ulnp` showed udp_bridge's socket had a
  **361 KB Recv-Q backup** — kernel receive buffer was filling up
  because the bridge wasn't draining it
- udp_bridge's last log line in the `core` pane was ~14 min stale;
  the process was alive (PID 675210) but had stopped processing
  entirely

So: link OK, kernel queuing UDP normally, but udp_bridge's reader
thread wedged — almost certainly back-pressure or a deadlock when
its republishes hit a (now-dead) CAMP-side subscriber during the
freeze + kill window. Discovery state never recovered after CAMP
respawned.

**Recovery**: operator killed PID 675210; `operator_core_launch`
respawned udp_bridge clean. Topics resumed flowing within seconds.

Worth filing as a follow-up against the udp_bridge / operator-launch
wiring: a single subscriber going away should not be able to wedge
the bridge's UDP reader thread. Either the publish path needs to
be non-blocking against any single subscriber, or the bridge needs
a watchdog that kicks the reader if Recv-Q grows beyond a
threshold for too long.

### Survey started

2026-04-27T~12:50-04:00 — survey running.

### Boat recovered — wrap-up

2026-04-27T~15:30-04:00 — boat recovered. End of on-water phase.

## 8. Day recap + handoff

### Net result

- Camera grid plugin: three real bugs found, all fixed and verified
  against live data. Plugin no longer crashes on dialog-apply with
  side seg streams.
- Sonar software integration + on-water survey: completed (set up on
  a different machine while camera-grid bug #2 was being fixed).
- One operational hiccup (CAMP freeze cascading into a wedged
  udp_bridge) recovered cleanly with a single respawn.

### Commits landed (all field-mode, all on `gitcloud:field/rqt_operator_tools.git`, branch `jazzy`)

- `b449acb` `fix(rqt_camera_grid): read base topic from itemData not display label`
  — bug #1, the SIGABRT crash from `InvalidTopicNameError` /
  `BadParamException` when the dialog leaks the formatted display
  label into `config_.base`.
- `7f1d78b` `fix(rqt_camera_grid): catch subscribe() exceptions to keep one pane from terminate()ing rqt`
  — defensive guard so any future bad pane config degrades to
  log + missing-data rather than terminate.
- `d936384` `fix(rqt_camera_grid): guard subscriber lambda against widget destruction race`
  — bug #2, the SIGSEGV use-after-free where the ROS spin thread
  delivers an in-flight image-transport callback to a destroyed
  CameraPaneWidget. QPointer auto-null in the lambda.

### Files touched (this repo)

- `docs/logs/2026/2026-04-27_salmon_logs.md` (new — this file)

### Files touched (other repos via gitcloud, push-only from salmon)

`rqt_operator_tools` — `rqt_camera_grid/src/{config_dialog,camera_pane_widget}.cpp`
(+ one `<QPointer>` include).

### Pending — for the dev side / next deployment

These are bounded enough to be issues, not roadmap items. Dev side
should pick them up via `/import-field-changes` against the three
commits above:

1. **Residual destruction race in `CameraPaneWidget::subscribe`'s
   QPointer lambda** — narrow window between `if (!self)` and the
   subsequent `self->handleImage(msg)` deref if destruction begins
   concurrently. Standard Qt+ROS idiom, accepted today, but a
   bulletproof fix is destructor-side synchronization (mutex around
   a destroyed flag, or shared_ptr ownership pattern that doesn't
   fight Qt's parent-child management). Open if/when SIGSEGV recurs.
2. **`ConfigDialog::populate_topic_combo` preserves dirty
   text on Refresh** — line 262 captures `currentText()` (could be
   the display label `"<base>  [<transport>]"`), then re-applies it
   after re-populate. Same class of bug as the line-610 fix but at
   a different trigger. Audit + fix similarly (use itemData lookup
   when preserved text matches a known item's label).
3. **udp_bridge wedge after subscriber death** — operator-side
   `udp_bridge` stopped draining its UDP receive buffer (kernel
   Recv-Q grew to ~361 KB) when CAMP died/was killed during the
   deployment. Likely back-pressure or deadlock on a publish to a
   dead subscriber. Either non-blocking publish, or a reader-thread
   watchdog that kicks the bridge if Recv-Q stays above threshold.
4. **`coredumpctl` not installed on salmon** — minor: would have
   given us a backtrace earlier without the apport-rate-limit
   detour. `sudo apt install systemd-coredump` on salmon. Also,
   `.agent/scratchpad/run_rqt_diag.sh` should clear
   `/var/crash/_opt_ros_jazzy_bin_rqt.*.crash` at start so a
   diagnostic run never poisons the apport slot for the real bug
   it's investigating.

No follow-up needed for: nvidia driver currency (already up-to-date),
zenoh router setup, the diag wrappers themselves
(`.agent/scratchpad/run_rqt_diag.sh`, `run_rqt_gdb.sh` — keep as
scratchpad tools, can be promoted to project repo if they prove
useful across sessions).

### What the GitHub deployment issue should reference

Per the logs convention, dev side opens a `Deployment YYYY-MM-DD:
<scope>` issue. For 2026-04-27 the scope was *camera grid bug
hunt + sonar integration + on-water survey*. This file is the
salmon-side host log; gabby's 2026-04-24 log is a different
deployment, not part of today.
