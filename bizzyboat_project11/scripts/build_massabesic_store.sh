#!/usr/bin/env bash
# Build the Massabesic bathy + backscatter stores from the M3 survey bags.
#
# FULL REGENERATION (cube_bathymetry#96 store redesign): stores are a regenerable
# cache over the bags. This script builds a complete store from scratch:
#   1. reference layer  — NH GRANIT contour-band midpoint prior (ccomjhc#75
#      2-band GeoTIFF: midpoint depth + half-band uncertainty), imported once
#      via marine_bathymetry_store's import_geotiff.
#   2. survey layer     — one import_bag pass over ALL survey bags (bathy CUBE
#      product into the bathy store + co-estimated backscatter into --bs-store),
#      gated against false-deep blunders by the reference prior
#      (--reference-store, cube#89/#96).
#
# The earlier incremental --append/--prior/ingest-ledger workflow is gone: #96
# collapsed draft/processed into a single `survey` layer and made the offline
# rebuild the authoritative product. Re-running this script = rebuilding the
# store; there is nothing to append and no ledger to keep.
#
# Why import_bag and not batch_regen_bag: batch_regen's scatter phase writes
# ~48 B per (sounding x touched tile) of scratch — ~100 GB for this survey.
# The whole lake spans only a few dozen GGGS level-10 tiles, far below
# import_bag's default --max-resident-tiles (256), so import_bag never evicts
# and its single pass is exactly the unbounded run batch_regen reproduces —
# with zero scratch disk. If a future survey outgrows RAM, either lower
# --max-resident-tiles (eviction keeps depth faithful; only revisited-tile
# uncertainty drifts) or free ~100 GB and switch to batch_regen_bag.
#
# Usage:
#   build_massabesic_store.sh [--reference-tif <wgs84_2band.tif>]
#                             [--out <bathy_store>] [--bs-out <bs_store>]
#
# The reference GeoTIFF comes from the ccomjhc_project11 Lake Massabesic
# project (build_bathymetry_geotiff.py, ccomjhc#75), reprojected to geographic
# WGS84 with NEAREST resampling (bilinear smears the discrete band midpoints —
# it smoothed max depth 16.76 m -> 13.72 m on the boat, unh_echoboats#364):
#   gdalwarp -r near -t_srs EPSG:4326 -dstnodata -9999 \
#       massabesic_bathy.tif massabesic_bathy_wgs84.tif
# If --out already holds a reference layer, --reference-tif may be omitted.
#
# Run AFTER sourcing the workspace (import_bag + import_geotiff on the path).
set -eo pipefail
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
set -u   # nounset only AFTER sourcing ROS (setup.bash trips on unbound vars)

# ---- paths / config ----------------------------------------------------------
STORE_BATHY="$HOME/data/stores/bathymetry"          # reference + survey
STORE_BS="$HOME/data/stores/backscatter"            # backscatter survey
REFERENCE_TIF=""
BAGS_DIR="$HOME/data/logs/gabby/logs/bizzyboat_sonar"
TOPIC=/bizzy/sensors/m3/detections
SURVEY_START="2026-06-12"   # floor: pre-survey bags have no M3 detections anyway
LAKE_DATUM_M=48.88          # full-pool lake surface, WGS84 ellipsoidal
                            # (massabesic_datum_polygons.yaml, unh_echoboats#278)

while [ $# -gt 0 ]; do
  case "$1" in
    --reference-tif) REFERENCE_TIF="$2"; shift 2;;
    --out)           STORE_BATHY="$2"; shift 2;;
    --bs-out)        STORE_BS="$2"; shift 2;;
    *) echo "ERROR: unknown argument '$1' (see header for usage)"; exit 1;;
  esac
done

# Deployed curve: prefer the installed share copy (workspace sourced), else fall
# back to this package's in-tree config — a deterministic sibling of scripts/.
# The curve is the tier-2 product ('# tl_removed: true' header), so import_bag
# also removes per-beam 2-way transmission loss (cube#87). (|| true: under set -e
# a failed `ros2 pkg prefix` in a command substitution would otherwise abort
# silently when the overlay isn't sourced.)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_PREFIX="$(ros2 pkg prefix bizzyboat_project11 2>/dev/null || true)"
CURVE="$PKG_PREFIX/share/bizzyboat_project11/config/m3_angular_response_curve.csv"
[ -f "$CURVE" ] || CURVE="$SCRIPT_DIR/../config/m3_angular_response_curve.csv"

# ---- preflight ---------------------------------------------------------------
echo "curve : $CURVE"; [ -f "$CURVE" ] || { echo "ERROR: curve not found"; exit 1; }
echo "bathy : $STORE_BATHY"
echo "bs    : $STORE_BS"

# import_bag must speak the #96 store model (--reference-store). Capture --help
# to a var first: usage() exits non-zero, which under pipefail would mask a grep
# match and cause a false refusal.
IMPORT_HELP="$(ros2 run cube_bathymetry import_bag --help 2>&1 || true)"
if ! grep -q -- '--reference-store' <<<"$IMPORT_HELP"; then
  echo "ERROR: this import_bag predates the cube_bathymetry#96 store redesign"
  echo "       (no --reference-store). Rebuild cube_bathymetry first."
  exit 1
fi

# Full regeneration only: refuse to write a survey layer on top of an existing
# one. A second pass over the same bags would double-count (that is what the
# old ledger guarded); a fresh dir keeps the semantics trivially correct.
for d in "$STORE_BATHY/survey" "$STORE_BS/survey"; do
  if compgen -G "$d/*.tif" > /dev/null 2>&1; then
    echo "ERROR: $d already has tiles. This script does FULL regeneration —"
    echo "       point --out/--bs-out at a fresh directory (swap it into place"
    echo "       after verifying) or remove the old survey layer first."
    exit 1
  fi
done

# ---- reference layer ---------------------------------------------------------
if compgen -G "$STORE_BATHY/reference/*.tif" > /dev/null 2>&1; then
  echo "reference: already present in $STORE_BATHY — skipping import"
  [ -n "$REFERENCE_TIF" ] && echo "  (NOTE: ignoring --reference-tif $REFERENCE_TIF)"
else
  if [ -z "$REFERENCE_TIF" ]; then
    echo "ERROR: $STORE_BATHY has no reference layer and no --reference-tif given."
    echo "       Generate it (ccomjhc_project11 projects/2026-Lake_Massabesic/"
    echo "       scripts/build_bathymetry_geotiff.py), reproject with"
    echo "       'gdalwarp -r near -t_srs EPSG:4326', and pass it here."
    exit 1
  fi
  [ -f "$REFERENCE_TIF" ] || { echo "ERROR: $REFERENCE_TIF not found"; exit 1; }
  echo "reference: importing $REFERENCE_TIF (datum $LAKE_DATUM_M m, band-2 uncertainty)"
  # No --uncertainty: the 2-band product's own half-band-width band is read
  # (a constant would silently override the honest per-band value, ccomjhc#75).
  ros2 run marine_bathymetry_store import_geotiff \
    "$STORE_BATHY" reference "$REFERENCE_TIF" \
    --cell-size 1.0 \
    --depth-scale -1 --depth-offset "$LAKE_DATUM_M" \
    --platform nh-granit --sensor edp-bathymetry-lakes \
    --survey massabesic-2026
fi

# ---- select survey bags --------------------------------------------------------
# Dated dirs at/after SURVEY_START carrying M3 detections + /tf. ISO-8601 names
# sort lexically, so a string compare on the date prefix is a correct floor.
BAGS=""
skipped_pre=0; skipped_notopic=0
for b in "$BAGS_DIR"/*/; do
  b="${b%/}"
  name="$(basename "$b")"
  [[ "$name" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2} ]] || continue
  if [[ "${name:0:10}" < "$SURVEY_START" ]]; then skipped_pre=$((skipped_pre+1)); continue; fi
  if ! { grep -qE 'm3/detections' "$b/metadata.yaml" 2>/dev/null && \
         grep -q '/tf' "$b/metadata.yaml" 2>/dev/null; }; then
    skipped_notopic=$((skipped_notopic+1)); continue
  fi
  BAGS="$BAGS $b"
done
BAGS=$(printf '%s\n' $BAGS | sed '/^$/d')
n_bags=$(printf '%s\n' "$BAGS" | grep -c .)

echo "bags  : $n_bags to import (skipped: $skipped_pre pre-$SURVEY_START, $skipped_notopic no detections/tf)"
if [ "$n_bags" -eq 0 ]; then echo "ERROR: no survey bags found under $BAGS_DIR"; exit 1; fi
printf '  + %s\n' $BAGS | sed "s#$BAGS_DIR/##"

# ---- survey pass ---------------------------------------------------------------
# ONE invocation over all bags: full CUBE hypothesis state is kept across them
# (chronological order — the glob is lexical = chronological for ISO names).
# The reference prior only gates blunders; it is never settled as data.
ros2 run cube_bathymetry import_bag \
  -o "$STORE_BATHY" \
  --reference-store "$STORE_BATHY" \
  --bs-store "$STORE_BS" \
  -d "$TOPIC" \
  --odom-topic /bizzy/odom \
  -r 1.0 \
  --backscatter-correction empirical \
  --backscatter-curve "$CURVE" \
  --base-link-frame bizzy/base_link \
  --level-frame bizzy/base_link_north_up \
  --tide-frame bizzy/map_tide \
  --platform bizzy --sensor m3 --campaign massabesic_jun2026 \
  $BAGS

echo "=== done -> $STORE_BATHY (reference + survey) + $STORE_BS ($n_bags bags) ==="
