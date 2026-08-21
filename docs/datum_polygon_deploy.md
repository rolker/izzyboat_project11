# Datum polygon deploy

Materializing the git-reviewed datum override polygons into the on-host world
tree. Implements work item 5 of
[unh_marine_autonomy#288](https://github.com/rolker/unh_marine_autonomy/issues/288)
and the deploy step promised by the ADR-0010 D3 amendment (2026-08-20).

## What it does

[`scripts/deploy_datum_polygons.sh`](../scripts/deploy_datum_polygons.sh)
copies `bizzyboat_project11/config/massabesic_datum_polygons.yaml` into
`~/data/world/datum/user/` on the target boat host (gabby / salmon):

```bash
# on the boat host, from the repo checkout:
scripts/deploy_datum_polygons.sh        # deploy (idempotent)
scripts/deploy_datum_polygons.sh -n     # dry run — report the action, change nothing
```

It is **idempotent** (safe on every deploy): it creates
`~/data/world/datum/user/` if absent, is a no-op when the copy already matches
git, installs atomically (stage + rename, so a discovering consumer never
reads a half-written file), and **fails loudly** if the source file is
missing. The test suite is
[`scripts/test_deploy_datum_polygons.sh`](../scripts/test_deploy_datum_polygons.sh)
(run in CI's "Test scripts" step).

## Why a copy exists

The runtime consumer — `mru_transform`'s `chart_datum_node` — reads the
polygon file from the **deployed `bizzyboat_project11` package share** via the
`datum_config_path` launch parameter (set in `bizzyboat_project11/launch/core_launch.py`).
It does **not** scan `world/datum/user/`. The world copy is the **discovery
surface**: the one canonical on-host home for datum support data, alongside
the grids under `datum/geoid/` and `datum/vdatum/` (ADR-0010 D3). It is where
the datum library, operators, and any future auto-discovery look.

## Git is the source of truth — the D1 exception

These polygons set the lake chart-datum height that the whole vertical
solution rides on, so they are **safety-relevant** and stay PR-reviewed in
this repo. `~/data/world/datum/user/` is the **one git-authored exception** to
ADR-0010 D1's regenerable-from-source invariant:

- the source of truth is the project repo (this file), not the world copy;
- the world copy is **regenerable from git** — re-run the script;
- it is **never hand-edited in place** and **never updater-authored**.

To enforce that last point, the script **overwrites** any in-place edit back
to the git content on every deploy. (The world grids under `datum/geoid/` and
`datum/vdatum/` are a separate, updater/provisioning concern — a queued
`s57_tools` follow-on — not covered by this script.)

## Deferred: operator-station (CAMP) provisioning

ADR-0010 D6 lists CAMP (the operator station) as a datum-library consumer that
also needs datum data on the operator side. That is **explicitly out of scope
here** — this step provisions the **boat host only**. Operator-station
provisioning remains deferred; see the #288 plan (item 5).
