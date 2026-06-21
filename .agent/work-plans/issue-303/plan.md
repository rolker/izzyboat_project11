# Plan: Bizzyboat sidescan URDF grazing tilt — SideVü #185 Stage 2

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/303

## Context

`bizzyboat_project11/urdf/sensors/sidescan.xacro` mounts `_port`/`_starboard`
as pure ±90° rotations about X (boresight horizontal, abeam). A placeholder
comment notes this is uncalibrated. Real side-scan fires 20–30° below
horizontal; for the SideVü 55° fan the boresight center should sit at
90° − fan/2 = 62.5° depression below horizontal (27.5° off nadir).

`_down` (ClearVü) is correct and unchanged.

**Coordinate convention** (from the file header):
- Per-channel range/boresight axis = frame's local +Z
- Mount frame: +X forward, +Y port, +Z up — same as base_link
- `_port` currently: rpy `${-pi/2} 0 0` → child +Z → +Y_parent (port, horizontal)
- `_starboard` currently: rpy `${pi/2} 0 0` → child +Z → −Y_parent (starboard, horizontal)

**Rotation math** — to tilt boresight DOWN by `grazing_deg` while keeping
`+X` forward (required by marine_sidescan_mosaic heading extraction, #200):
- Roll about mount-frame X by `−(π/2 + grazing_rad)` for port
- Roll about mount-frame X by `+(π/2 + grazing_rad)` for starboard

Result:
- port +Z direction in parent: `[0, cos(grazing_deg), −sin(grazing_deg)]` ✓
- stbd +Z direction in parent: `[0, −cos(grazing_deg), −sin(grazing_deg)]` ✓
- both +X directions in parent: `[1, 0, 0]` (forward, unchanged) ✓

Default: `grazing_deg = 62.5` (derived from 90 − 55/2 for the SideVü 55° fan;
the fan value is now published by the driver per marine_tools#62 and can be
used to refine this parameter post-calibration).

## Approach

1. **Add `grazing_deg` macro param** — append `grazing_deg:=62.5` to the
   `garmin_sidescan` param list; add a comment that the default is
   `90 − SideVü_fan/2 = 90 − 27.5 = 62.5°` and references marine_tools#62.

2. **Update `_port` joint rpy** — change `${-pi/2} 0 0` to
   `${-pi/2 - grazing_deg * pi / 180} 0 0`. Update the inline comment to
   describe the resulting frame orientation with tilt.

3. **Update `_starboard` joint rpy** — change `${pi/2} 0 0` to
   `${pi/2 + grazing_deg * pi / 180} 0 0`. Update comment symmetrically.

4. **Update the file header** — remove the PLACEHOLDER notice; replace with a
   concise description of the grazing angle, its derivation, and how to
   re-calibrate (`grazing_deg` param).

5. **Document a manual TF check** — no xacro unit-test harness exists in
   `bizzyboat_project11`. Add a comment block (or a minimal `check_sidescan.py`
   script in `bizzyboat_project11/scripts/`) describing how to verify:
   ```
   ros2 run xacro xacro sidescan.xacro name:=sidescan parent:=base_link \
     | robot_state_publisher --ros-args -p robot_description:="$(cat)"
   ros2 run tf2_ros tf2_echo base_link bizzy/sidescan_port
   # Expected: Z axis ~[0, 0.462, −0.887] in base_link frame (62.5° depression)
   ```

## Files to Change

| File | Change |
|------|--------|
| `bizzyboat_project11/urdf/sensors/sidescan.xacro` | Add `grazing_deg` param; update `_port`/`_starboard` rpy; update comments |

**Optional** (include if the check proves useful during review):

| File | Change |
|------|--------|
| `bizzyboat_project11/scripts/check_sidescan_tilt.py` | 10-line Python snippet: parse xacro output with `xacro` module, assert boresight Z-axis depression matches `grazing_deg` |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| Human control and transparency | `grazing_deg` is an explicit param; default is derived and documented; easy to override for field calibration |
| Capture decisions, not just implementations | Default derivation (90 − fan/2) and source (marine_tools#62) documented in the file header |
| A change includes its consequences | `_down` joint unchanged; `+X` forward preserved — no downstream breakage for marine_sidescan_mosaic (#200) |
| Only what's needed | One file changed; `_down` untouched; no new abstractions |
| Test what breaks | Manual TF check documented; optional assertion script if harness is feasible |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| 0008 — Follow ROS 2 conventions | Yes (URDF/xacro change) | xacro param syntax follows existing macro style; no new conventions introduced |

## Consequences

| If we change... | Also update... | Included in plan? |
|---|---|---|
| `_port`/`_starboard` boresight direction | `marine_sidescan_mosaic` heading extraction (unh_marine_autonomy#200) | Mitigated — `+X` stays forward; no API change needed |
| `grazing_deg` default | Field calibration notes / deployment docs | No — follow-up when measured |
| `garmin_sidescan` macro params | Any `.xacro` files that call the macro (need to verify no callers pass positional args beyond `x y z`) | Verify callers — `grazing_deg` has a default, so no breakage expected |

## Open Questions

- [x] Verify call sites of `garmin_sidescan` — `bizzyboat.urdf.xacro` is the
  only caller and uses keyword args (`parent`, `name`, `x`, `y`, `z`); the
  new defaulted `grazing_deg` param is safe.
- [ ] Confirm marine_sidescan_mosaic (#200) truly depends only on `+X`
  forward (not on `+Z` being horizontal) before merging.

## Estimated Scope

Single PR, 1 file changed (~10 lines).
