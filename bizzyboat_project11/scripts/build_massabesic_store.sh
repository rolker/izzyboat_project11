#!/usr/bin/env bash
# Build the Massabesic bathy + backscatter stores from the M3 survey bags.
#
# FULL REGENERATION (cube_bathymetry#96 store redesign): stores are a regenerable
# cache over the bags. This script builds a complete store from scratch:
#   1. reference layer  — NH GRANIT contour-band midpoint prior (ccomjhc#75
#      2-band GeoTIFF: midpoint depth + half-band uncertainty), imported once
#      via marine_bathymetry_store's import_geotiff (staged, then atomically
#      renamed into place — a partial reference layer never survives).
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
# Interruption safety: the survey pass writes tiles into the target store
# progressively over ~1 h, so a `survey/.building` sentinel marks the run;
# it is removed only after import_bag succeeds AND the post-run tile check
# passes. A sentinel found at startup means a previous run died mid-write —
# the script refuses until the partial survey layer is deleted. tile-level
# atomicity is tracked separately (unh_marine_autonomy#256).
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
# Bags to skip even though they carry detections + tf. 06-27T23-58: overnight
# dock recording during the mercat NTP re-slew — per-ping stamps drift −7…−1 s
# and the sparse (~1 Hz) stream defeats retrofit_m3_bag's ping-count window
# (unh_echoboats#367), so its 7.3k pings would georeference ~up-to-10 m off.
SKIP_BAGS="2026-06-27T23-58-21+00-00"
LAKE_DATUM_M=48.88          # full-pool lake surface, WGS84 ellipsoidal
                            # (massabesic_datum_polygons.yaml, unh_echoboats#278)
MIN_FREE_GB=5               # refuse to start a ~1 h run that would ENOSPC mid-flush

while [ $# -gt 0 ]; do
  case "$1" in
    --reference-tif|--out|--bs-out)
      [ $# -ge 2 ] || { echo "ERROR: $1 requires a value"; exit 1; }
      case "$1" in
        --reference-tif) REFERENCE_TIF="$2";;
        --out)           STORE_BATHY="$2";;
        --bs-out)        STORE_BS="$2";;
      esac
      shift 2;;
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

# Disk headroom: the machine that runs this is chronically near-full, and an
# ENOSPC an hour in leaves exactly the partial store the sentinel guards
# against. Fail fast instead.
mkdir -p "$STORE_BATHY" "$STORE_BS"
free_gb=$(df --output=avail -B1G "$STORE_BATHY" | tail -1 | tr -d ' ')
if [ "$free_gb" -lt "$MIN_FREE_GB" ]; then
  echo "ERROR: only ${free_gb} GB free on the store filesystem (< ${MIN_FREE_GB} GB)."
  exit 1
fi

# Free space on the backscatter store too — it may sit on another filesystem.
free_bs_gb=$(df --output=avail -B1G "$STORE_BS" | tail -1 | tr -d ' ')
if [ "$free_bs_gb" -lt "$MIN_FREE_GB" ]; then
  echo "ERROR: only ${free_bs_gb} GB free on the backscatter-store filesystem (< ${MIN_FREE_GB} GB)."
  exit 1
fi

# Single instance: the guards below are check-then-act over a ~1 h write —
# two concurrent runs would both pass them and interleave tile writes. Lock
# BOTH stores: two runs with different --out but the same --bs-out must also
# exclude each other.
exec 9>"$STORE_BATHY/.build_lock"
exec 8>"$STORE_BS/.build_lock"
if ! flock -n 9 || ! flock -n 8; then
  echo "ERROR: another build holds a .build_lock in $STORE_BATHY or $STORE_BS."
  exit 1
fi

# A survey/.building sentinel means a previous run died mid-write: the tiles
# present are an unknown subset. Refuse until the operator clears them.
for d in "$STORE_BATHY" "$STORE_BS"; do
  if [ -e "$d/survey/.building" ]; then
    echo "ERROR: $d/survey/.building exists — a previous run was interrupted"
    echo "       mid-write. Delete $d/survey/ (it is regenerable) and re-run."
    exit 1
  fi
done

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

# Refuse pre-#96 legacy stores (chart/draft/processed layers, ingest ledger):
# importing new-model layers next to a legacy `processed` layer of the SAME
# bags presents the data twice to a layer-priority consumer, and the legacy
# per-cell registry does not match the new StoreMetadata. Migrate or point at
# a fresh directory instead.
for d in "$STORE_BATHY" "$STORE_BS"; do
  for legacy in chart draft processed .ingested_bags.txt; do
    if [ -e "$d/$legacy" ]; then
      echo "ERROR: $d contains pre-#96 legacy content ('$legacy'). Refusing to"
      echo "       mix store models — use a fresh --out/--bs-out directory."
      exit 1
    fi
  done
done

# ---- reference layer ---------------------------------------------------------
if compgen -G "$STORE_BATHY/reference/*.tif" > /dev/null 2>&1; then
  # NOTE: tiles present = accepted as complete. A partial layer from a
  # pre-hardening interrupted import is indistinguishable by glob; if in
  # doubt, delete reference/ and re-import (it is regenerable).
  echo "reference: already present in $STORE_BATHY — skipping import"
  [ -n "$REFERENCE_TIF" ] && echo "  (NOTE: ignoring --reference-tif $REFERENCE_TIF)"
else
  if [ -d "$STORE_BATHY/reference" ]; then
    # A tile-less reference/ dir would make the mv below NEST the staged
    # layer (reference/reference/) — misfiling the prior and silently
    # disabling the blunder gate. Refuse instead.
    echo "ERROR: $STORE_BATHY/reference exists but holds no tiles (interrupted"
    echo "       earlier import?). Delete it and re-run."
    exit 1
  fi
  if [ -z "$REFERENCE_TIF" ]; then
    echo "ERROR: $STORE_BATHY has no reference layer and no --reference-tif given."
    echo "       Generate it (ccomjhc_project11 projects/2026-Lake_Massabesic/"
    echo "       scripts/build_bathymetry_geotiff.py), reproject with"
    echo "       'gdalwarp -r near -t_srs EPSG:4326', and pass it here."
    exit 1
  fi
  [ -f "$REFERENCE_TIF" ] || { echo "ERROR: $REFERENCE_TIF not found"; exit 1; }
  echo "reference: importing $REFERENCE_TIF (datum $LAKE_DATUM_M m, band-2 uncertainty)"
  # Stage into a temp sibling and rename into place: an interrupted import
  # must never leave a partial reference/ that a re-run would silently accept
  # as complete (the blunder gate would then be missing over part of the lake).
  # No --uncertainty: the 2-band product's own half-band-width band is read
  # (a constant would silently override the honest per-band value, ccomjhc#75).
  REF_STAGE="$(mktemp -d "$STORE_BATHY/.ref_stage.XXXXXX")"
  trap 'rm -rf "$REF_STAGE"' EXIT INT TERM
  ros2 run marine_bathymetry_store import_geotiff \
    "$REF_STAGE" reference "$REFERENCE_TIF" \
    --cell-size 1.0 \
    --depth-scale -1 --depth-offset "$LAKE_DATUM_M" \
    --platform nh-granit --sensor edp-bathymetry-lakes \
    --survey massabesic-2026
  # -T: rename onto the destination itself; fails loudly rather than nesting
  # if a reference/ dir appeared since the guard above.
  mv -T "$REF_STAGE/reference" "$STORE_BATHY/reference"   # atomic on same FS
  [ -e "$STORE_BATHY/registry.json" ] || mv "$REF_STAGE/registry.json" "$STORE_BATHY/registry.json"
  rm -rf "$REF_STAGE"; trap - EXIT INT TERM
fi

# ---- select survey bags --------------------------------------------------------
# Dated dirs at/after SURVEY_START carrying M3 detections + dynamic /tf
# (anchored: '/tf' alone would also match /tf_static). ISO-8601 names sort
# lexically, so a string compare on the date prefix is a correct floor.
BAGS=()
skipped_pre=0; skipped_notopic=0; skipped_listed=0
for b in "$BAGS_DIR"/*/; do
  b="${b%/}"
  name="$(basename "$b")"
  [[ "$name" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2} ]] || continue
  if [[ " $SKIP_BAGS " == *" $name "* ]]; then
    echo "  - $name skipped (SKIP_BAGS: unusable timing, see script comment)"
    skipped_listed=$((skipped_listed+1)); continue
  fi
  if [[ "${name:0:10}" < "$SURVEY_START" ]]; then skipped_pre=$((skipped_pre+1)); continue; fi
  if [ ! -f "$b/metadata.yaml" ]; then
    # rosbag2 writes metadata.yaml at clean shutdown; data without it is
    # usually an outage-truncated recording (salvageable — do not silently
    # lump it in with topic-less bags).
    if compgen -G "$b/*.mcap" > /dev/null 2>&1; then
      echo "WARNING: $name has .mcap data but no metadata.yaml (truncated"
      echo "         recording?) — SKIPPED. Recover/reindex it and re-run."
    fi
    skipped_notopic=$((skipped_notopic+1)); continue
  fi
  if ! { grep -qE "name: ${TOPIC}\s*$" "$b/metadata.yaml" && \
         grep -qE 'name: /tf\s*$' "$b/metadata.yaml"; }; then
    skipped_notopic=$((skipped_notopic+1)); continue
  fi
  BAGS+=("$b")
done
n_bags=${#BAGS[@]}

echo "bags  : $n_bags to import (skipped: $skipped_pre pre-$SURVEY_START, $skipped_notopic no metadata/detections/tf, $skipped_listed skip-listed)"
if [ "$n_bags" -eq 0 ]; then echo "ERROR: no survey bags found under $BAGS_DIR"; exit 1; fi
printf '  + %s\n' "${BAGS[@]#"$BAGS_DIR"/}"

# ---- survey pass ---------------------------------------------------------------
# ONE invocation over all bags: full CUBE hypothesis state is kept across them
# (chronological order — the glob is lexical = chronological for ISO names).
# The reference prior only gates blunders; it is never settled as data.
# Provenance vocabulary per ADR-0005/ADR-0007: platform bizzyboat,
# sensor kongsberg-m3 (model-named), campaign massabesic-jun2026.
mkdir -p "$STORE_BATHY/survey" "$STORE_BS/survey"
touch "$STORE_BATHY/survey/.building" "$STORE_BS/survey/.building"
trap 'echo "ERROR: survey pass did not complete — partial tiles remain under
       $STORE_BATHY/survey and $STORE_BS/survey (marked by .building).
       Delete both survey/ dirs (regenerable) before re-running." >&2' ERR

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
  --platform bizzyboat --sensor kongsberg-m3 --campaign massabesic-jun2026 \
  "${BAGS[@]}"

# Post-run: an exit-0 import that produced nothing must not be announced as
# success (topic drift or all-dropped pings would otherwise ship an empty
# authoritative store).
n_bathy=$(find "$STORE_BATHY/survey" -maxdepth 1 -name '*.tif' | wc -l)
n_bs=$(find "$STORE_BS/survey" -maxdepth 1 -name '*.tif' | wc -l)
echo "tiles : $n_bathy bathy survey, $n_bs backscatter survey"
if [ "$n_bathy" -eq 0 ]; then
  echo "ERROR: import_bag exited 0 but wrote no bathy survey tiles — check -d"
  echo "       topic ($TOPIC) and the frame overrides against the bags."
  exit 1
fi
trap - ERR
rm -f "$STORE_BATHY/survey/.building" "$STORE_BS/survey/.building"

echo "=== done -> $STORE_BATHY (reference + survey) + $STORE_BS ($n_bags bags) ==="
