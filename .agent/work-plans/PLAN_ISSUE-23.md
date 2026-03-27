# Plan: Add sensors layer to boat manifest (OAK cameras + DeltaT)

## Issue

https://github.com/rolker/unh_echoboats_project11/issues/23

## Context

The boat manifest (`unh_echoboats_project11`) currently defines four layers:
`underlay`, `core`, `platforms`, and `site`. There is no `sensors` layer, so
sensor packages (Luxonis OAK cameras, DeltaT sonar) are unavailable on gabby.

The main workspace manifest includes a full `sensors.repos` with six repos, but
the boat manifest only needs `unh_marine_perception` (OAK camera packages) and
`imagenex_deltat` (DeltaT sonar driver) for now.

The boat manifest uses `git@gitcloud:field/` URLs (not `https://github.com/rolker/`).

## Approach

1. **Create `config/repos/sensors.repos`** — add `unh_marine_perception` and
   `imagenex_deltat` entries using gitcloud URLs and `jazzy` branch, matching
   the format of existing `.repos` files in this manifest.

2. **Add `sensors` to `config/layers.txt`** — insert `sensors` after
   `platforms` and before `site` to match the main manifest layer ordering
   (underlay → core → platforms → sensors → site). The sensors layer depends
   on core packages and should be built before site.

3. **Verify gitcloud repos exist and have `jazzy` branches** — this is a
   prerequisite noted in the issue; both repos are reported as already pushed.
   The plan includes a verification step but this may need to be done on
   gabby or a machine with gitcloud access.

## Files to Change

| File | Change |
|------|--------|
| `config/repos/sensors.repos` | **New file** — two entries: `unh_marine_perception` and `imagenex_deltat` |
| `config/layers.txt` | Add `sensors` between `platforms` and `site` |

## Principles Self-Check

| Principle | Consideration |
|---|---|
| Only what's needed | Scoping to two repos instead of the full six-repo sensors layer — matches issue scope |
| A change includes its consequences | `layers.txt` must be updated alongside the new `.repos` file so the layer is actually built |
| Improve incrementally | Small addition of one layer; more sensor repos can be added later |
| Workspace vs. project separation | This is a boat-specific manifest change in the project repo — correct location |

## ADR Compliance

| ADR | Triggered | How addressed |
|---|---|---|
| ADR-0003 (workspace is project-agnostic) | No | Change is in the boat manifest (project repo), not the workspace |
| ADR-0008 (ROS 2 conventions) | No | Standard `.repos` format used |

## Consequences

| If we change... | Also update... | Included in plan? |
|---|---|---|
| `config/layers.txt` adds sensors | `config/repos/sensors.repos` must exist | Yes |
| sensors layer added | `depthai` / `depthai_bridge` dependencies needed at build time | No — noted as follow-up (rosdep or manual install on gabby) |

## Open Questions

- **Gitcloud default branches**: Are `jazzy` branches set as default on gitcloud for both `unh_marine_perception` and `imagenex_deltat`? (Issue says repos are pushed but doesn't confirm default branch.)
- **External dependencies**: `depthai` and `depthai_bridge` are not ROS packages — how should they be installed on gabby? Separate issue for rosdep keys or manual install?
- **Optional layer?**: Should `sensors` be added to `config/optional_layers.txt` so setup doesn't fail on machines without gitcloud access, similar to `site`?

## Estimated Scope

Single PR — two file changes (one new, one modified).
