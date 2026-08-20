#!/usr/bin/env bash
#
# deploy_datum_polygons.sh — materialize the git-reviewed datum override
# polygon config into the on-host world tree so the marine_vertical_datum
# precedence chain can discover it.
#
# Copies bizzyboat_project11/config/massabesic_datum_polygons.yaml into
# ~/data/world/datum/user/ on the target boat host (gabby/salmon). This is
# work item 5 of unh_marine_autonomy#288 and the deploy step promised by the
# ADR-0010 D3 amendment (2026-08-20).
#
# WHY a copy at all: the runtime consumer (mru_transform's chart_datum_node)
# reads the polygon file from the deployed bizzyboat_project11 package share
# via the `datum_config_path` launch param (core_launch.py) — it does NOT
# scan world/datum/user/. The world/ copy is the *discovery surface* for the
# datum library / operators / future auto-discovery: one canonical on-host
# home for datum support data (grids under datum/geoid + datum/vdatum, user
# override polygons under datum/user), per ADR-0010 D3.
#
# SOURCE OF TRUTH is git. These polygons are safety-relevant (they set the
# lake chart-datum height the whole vertical solution rides on), so they stay
# PR-reviewed in this repo. `datum/user/` is the one git-authored exception
# to ADR-0010 D1's regenerable-from-source invariant: the copy is regenerable
# from git (re-run this script), never hand-edited in place, never
# updater-authored. This script therefore OVERWRITES any in-place edit back
# to the git content on every deploy, restoring the invariant.
#
# DEFERRED: operator-station (CAMP) provisioning. ADR-0010 D6 lists CAMP as a
# datum-library consumer that also needs datum data on the operator station.
# That is out of scope here — this step provisions the boat host only. See
# docs/datum_polygon_deploy.md.
#
# Idempotent: safe to run on every deploy. Creates ~/data/world/datum/user/
# if absent; a no-op (with an "up to date" note) when the copy already
# matches git; fails loudly if the source file is missing.
#
# Usage:
#   deploy_datum_polygons.sh          # deploy (idempotent)
#   deploy_datum_polygons.sh -n       # dry run: report the action, change nothing
#   deploy_datum_polygons.sh -h       # this help
#
# Env overrides (VAR=... deploy_datum_polygons.sh) for other hosts / tests:
#   SRC       source polygon YAML (default: the in-tree bizzyboat config)
#   DEST_DIR  destination directory (default: ~/data/world/datum/user)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The git-reviewed file in this checkout is the source of truth (not the
# built package share, which is a derived artifact). Resolve it relative to
# this script so the deploy step needs no sourced ROS environment.
SRC="${SRC:-$SCRIPT_DIR/../bizzyboat_project11/config/massabesic_datum_polygons.yaml}"
DEST_DIR="${DEST_DIR:-$HOME/data/world/datum/user}"

DRY_RUN=0

err() { printf 'deploy_datum_polygons: %s\n' "$*" >&2; }
die() { err "$*"; exit 1; }

usage() {
  sed -n '3,/^set -euo pipefail/p' "$0" | sed '$d; s/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--dry-run) DRY_RUN=1; shift ;;
    -h|--help)    usage; exit 0 ;;
    *)            die "unknown option: $1 (try --help)" ;;
  esac
done

# Loud failure if the git source is missing: a silent skip would leave the
# boat running on a stale or absent datum config.
[[ -f "$SRC" ]] || die "source polygon config not found: $SRC
       git is the source of truth — run this from the repo checkout, or set SRC=<file>."

DEST="$DEST_DIR/$(basename "$SRC")"

# Already materialized and identical: nothing to do (the idempotent case).
if [[ -f "$DEST" ]] && cmp -s "$SRC" "$DEST"; then
  echo "up to date: $DEST already matches $SRC"
  exit 0
fi

if [[ $DRY_RUN -eq 1 ]]; then
  if [[ -f "$DEST" ]]; then
    echo "would update (differs from git): $SRC -> $DEST"
  else
    echo "would install: $SRC -> $DEST"
  fi
  exit 0
fi

mkdir -p "$DEST_DIR"

# Atomic install: stage a sibling temp file then rename over the
# destination, so a consumer discovering world/datum/user/ never reads a
# half-written polygon file.
tmp="$(mktemp "$DEST_DIR/.$(basename "$SRC").XXXXXX")"
trap 'rm -f "$tmp"' EXIT
cp "$SRC" "$tmp"
chmod 644 "$tmp"
mv -f "$tmp" "$DEST"
trap - EXIT

echo "deployed $SRC -> $DEST"
