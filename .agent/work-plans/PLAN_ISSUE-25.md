# Plan: BizzyBoat URDF with sensor frame positions

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/25

## Context

The BizzyBoat (EchoBoat 240) currently has no URDF or robot description package.
IzzyBoat (`izzyboat_project11`) has a plain URDF with boxy primitives. This plan
creates a new `bizzyboat_project11` package with a modular xacro-based URDF,
improved hull visuals, and documented sensor frame positions.

The `base_link` reference point is the center screw hole in the hull floor, near
the center of gravity. Sensor positions are estimated from photos and the EchoBoat
240 manual; they will be refined with physical measurements later.

See `docs/bizzyboat_reference_geometry.md` (created by this plan) for the full
measurement reference and coordinate conventions.

## Approach

1. **Create `bizzyboat_project11` ROS 2 package** — `ament_cmake` package with
   `CMakeLists.txt`, `package.xml`, and install rules for `urdf/`, `meshes/`,
   `config/`, `launch/`, and `docs/` directories.

2. **Generate hull STL mesh** — Python script (`scripts/generate_hull_mesh.py`)
   using `trimesh` to create an approximate EchoBoat 240 hull shape (2.4m x
   0.9m, tapered bow, flat stern). Output to `meshes/hull.stl`. More detailed
   than IzzyBoat's box primitives while keeping the geometry simple.

3. **Create modular xacro URDF** — split into files:
   - `urdf/bizzyboat.urdf.xacro` — main entry, includes sub-files, defines
     `base_link` with hull mesh visual
   - `urdf/sensors/camera_oak.xacro` — reusable OAK-1 camera macro (camera
     link + optical frame with standard -90deg rotation)
   - `urdf/sensors/gnss.xacro` — GNSS antenna puck macro
   - `urdf/sensors/sonar.xacro` — DeltaT sonar link
   - `urdf/materials.xacro` — shared material/color definitions

4. **Instantiate sensor frames** with estimated positions (see reference doc):
   - 4x OAK-1 cameras: top of mast on 3D-printed bracket, 90deg apart
     (fwd/port/stbd/aft), tilted ~10deg downward
   - 2x GNSS antennas: black pucks on crossbar ends
   - 1x DeltaT sonar: below hull, approximate from manual diagram
   - 1x USB camera: on mast (factory position)

5. **Create `config/platform.yaml`** — hull dimensions matching URDF, with
   `reference_x`/`reference_y` offsets (format matching IzzyBoat's).

6. **Create launch file** — `launch/load_urdf_launch.py` following IzzyBoat's
   pattern but using `bizzyboat` namespace and xacro args.

7. **Write reference geometry document** — `docs/bizzyboat_reference_geometry.md`
   documenting `base_link` location, coordinate conventions, estimated sensor
   positions with sources (manual/photo/measurement), and what needs refinement.

## Files to Change

| File | Change |
|------|--------|
| `bizzyboat_project11/package.xml` | **New** — package manifest |
| `bizzyboat_project11/CMakeLists.txt` | **New** — build config, install dirs |
| `bizzyboat_project11/urdf/bizzyboat.urdf.xacro` | **New** — main URDF entry point |
| `bizzyboat_project11/urdf/materials.xacro` | **New** — color definitions |
| `bizzyboat_project11/urdf/sensors/camera_oak.xacro` | **New** — OAK camera macro |
| `bizzyboat_project11/urdf/sensors/gnss.xacro` | **New** — GNSS antenna macro |
| `bizzyboat_project11/urdf/sensors/sonar.xacro` | **New** — DeltaT sonar macro |
| `bizzyboat_project11/meshes/hull.stl` | **New** — generated hull mesh |
| `bizzyboat_project11/scripts/generate_hull_mesh.py` | **New** — mesh generation script |
| `bizzyboat_project11/config/platform.yaml` | **New** — platform dimensions |
| `bizzyboat_project11/launch/load_urdf_launch.py` | **New** — URDF launch file |
| `bizzyboat_project11/docs/bizzyboat_reference_geometry.md` | **New** — measurement reference |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| Documentation accuracy | All positions documented with source (manual/photo/estimated) and flagged for refinement |
| Only what's needed | New package is minimal — URDF, one launch file, one config. No unnecessary dependencies |
| A change includes its consequences | `platform.yaml` dimensions match URDF; reference doc captures what still needs measurement |
| Improve incrementally | Approximate positions now, refined later. Xacro macros make updates easy |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| ADR-0003 (workspace is project-agnostic) | No | Change is in the boat-specific project repo |
| ADR-0008 (ROS 2 conventions) | Yes | xacro + `robot_state_publisher`, REP-103/105 frame conventions, standard optical frame pattern |

## Consequences

| If we change... | Also update... | Included in plan? |
|---|---|---|
| New `bizzyboat_project11` package | Other packages may launch it | Yes — launch file included |
| Sensor frame names defined | Camera/GNSS/sonar driver configs must match | No — follow-up when drivers are configured |
| `platform.yaml` created | Launch files referencing platform config | Yes — consistent with IzzyBoat pattern |

## Open Questions

- **OAK camera down-tilt**: Estimated ~10deg — user will measure exact angle later.
- **DeltaT sonar position**: Using manual diagram approximation — exact mount position TBD.
- **USB camera**: Exact position on mast needs confirmation.
- **Mast height**: Estimated from air draft (1.32m) and photos — needs measurement.

## Estimated Scope

Single PR — all new files in a new package directory.
