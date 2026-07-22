#!/usr/bin/env bash
#
# build_bathy_store.sh — rebuild the GGGS bathymetry/backscatter stores from
# recorded bizzyboat_sonar bags (Kongsberg M3 detections -> CUBE).
#
# Consolidates the field bag-selection tool (2026-07-21, unh_echoboats#378)
# with the hardened authoritative-regen procedure from the retired
# bizzyboat_project11/scripts/build_massabesic_store.sh (#352, validated by
# the 2026-07-02 canonical regen). See unh_echoboats#382.
#
# FULL REGENERATION (cube_bathymetry#96 store model): stores are a regenerable
# cache over the bags; one import_bag pass over ALL selected bags builds the
# authoritative `survey` layer (bathy CUBE product + co-estimated backscatter),
# gated against false-deep blunders by the `reference` chart prior. Re-running
# over an existing survey layer would double-count soundings, so the script
# refuses unless --fresh archives the old layer first.
#
# Bags with no metadata.yaml are skipped with a warning: rosbag2 writes it at
# close, so its absence usually means the bag is still mid-rsync — not crashed.
# Unparseable metadata is warned separately. Bags on the SKIP_BAGS list are
# excluded even though they carry detections + tf (default: 2026-06-27T23-58,
# whose per-ping stamps drift −7…−1 s during the mercat NTP re-slew and defeat
# retrofit_m3_bag's ping-count window, unh_echoboats#367 — its 7.3k pings
# would georeference up to ~10 m off).
#
# Requires a sourced ROS environment with cube_bathymetry and
# marine_bathymetry_store built (workspace setup.bash), and python3 GDAL
# bindings for the reference import (the gdalwarp CLI is not installed on
# salmon).
#
# Usage:
#   build_bathy_store.sh [options]
#   build_bathy_store.sh -n                          # list selection + command only
#   build_bathy_store.sh --reference-tif <2band.tif> --fresh \
#       --since 2026-06-12 --until 2026-07-01        # full canonical rebuild
#
# Options:
#   --since DATE       only bags recorded on/after this UTC date (YYYY-MM-DD)
#   --until DATE       only bags recorded on/before this UTC date (YYYY-MM-DD)
#   --reference-tif F  (re)build the reference layer from this chart-prior
#                      GeoTIFF before cubing. Prefer the ccomjhc#75 2-band
#                      product (band 1 midpoint depth, band 2 half-band
#                      uncertainty): it imports WITHOUT --uncertainty so the
#                      honest per-band values are read. A 1-band raster falls
#                      back to the constant CHART_UNCERTAINTY with a warning.
#                      Reprojected in-script to geographic WGS84 with NEAREST
#                      resampling (bilinear smears band midpoints — 16.76 m
#                      max read 13.72 m on 2026-07-01). Import is staged and
#                      atomically renamed: a partial reference layer never
#                      survives interruption.
#   --reference        same, using $CHART_TIF (default ~/data/massabesic_bathy.tif)
#   --fresh            archive existing survey layers (bathymetry AND
#                      backscatter stores) into <store>/_archive/<ts>/ so the
#                      CUBE pass rebuilds from scratch
#   --bs-curve FILE    empirical angular-response curve CSV (default: the
#                      deployed bizzyboat_project11 share copy, else the
#                      in-tree config sibling; if neither exists the import
#                      falls back to import_bag's auto correction, cube#102)
#   --limit N          stop after N pings (import_bag -l, debugging)
#   -n, --dry-run      print selection, guard status, and the import_bag
#                      command; change nothing
#   -h, --help         this help
#
set -euo pipefail

# --------------------------------------------------------------------------
# Configuration — env-overridable (VAR=... build_bathy_store.sh) for other
# hosts and the test harness; edit defaults here if topics or frames change.
# --------------------------------------------------------------------------
BAG_ROOT="${BAG_ROOT:-$HOME/data/logs/gabby/logs/bizzyboat_sonar}"
BATHY_STORE="${BATHY_STORE:-$HOME/data/stores/bathymetry}"
BS_STORE="${BS_STORE:-$HOME/data/stores/backscatter}"

DETECTIONS_TOPIC="${DETECTIONS_TOPIC:-/bizzy/sensors/m3/detections}"
ODOM_TOPIC="/bizzy/odom"
RESOLUTION=1.0

# Offline projector frame overrides — must match the bags' namespaced frames
# or the grid comes out empty (import_bag only warns once).
BASE_LINK_FRAME="bizzy/base_link"
LEVEL_FRAME="bizzy/base_link_north_up"
TIDE_FRAME="bizzy/map_tide"

# Store-level provenance (uma#248 StoreMetadata; ADR-0005/ADR-0007 vocabulary:
# platform by boat name, sensor by model, campaign = survey id). These MUST
# match the canonical store registry — bizzyboat/kongsberg-m3/massabesic-jun2026.
PLATFORM="${PLATFORM:-bizzyboat}"
SENSOR="${SENSOR:-kongsberg-m3}"
CAMPAIGN="${CAMPAIGN:-massabesic-jun2026}"

# Bags to skip even though they pass every metadata gate (space-separated
# directory names). Default: the unfixable-timing dock bag, see header.
SKIP_BAGS="${SKIP_BAGS:-2026-06-27T23-58-21+00-00}"

# Chart prior defaults for --reference: NH GRANIT Massabesic bathymetry,
# positive-down depths below the full-pool lake surface.
CHART_TIF="${CHART_TIF:-$HOME/data/massabesic_bathy.tif}"
CHART_DEPTH_SCALE=-1     # positive-down depth -> up-positive ellipsoidal height
CHART_DEPTH_OFFSET=48.88 # full-pool lake-surface WGS84 ellipsoidal height:
                         # chart_datum_z in bizzyboat_project11/config/
                         # massabesic_datum_polygons.yaml (unh_echoboats#278)
CHART_UNCERTAINTY=1.524  # 5 ft — GRANIT stated accuracy (1-band fallback ONLY;
                         # the 2-band product carries per-band uncertainty)
CHART_CELL_SIZE=1.0      # level 10; matches survey RESOLUTION
CHART_PLATFORM=nh-granit
CHART_SENSOR=edp-bathymetry-lakes
CHART_SURVEY=massabesic-2026

MIN_FREE_GB="${MIN_FREE_GB:-5}"  # refuse a ~1 h run that would ENOSPC mid-flush

# --------------------------------------------------------------------------
SINCE=""
UNTIL=""
REFERENCE_TIF=""
DO_REFERENCE=0
FRESH=0
BS_CURVE=""
LIMIT=""
DRY_RUN=0

err()  { printf 'build_bathy_store: %s\n' "$*" >&2; }
warn() { printf 'build_bathy_store: WARN: %s\n' "$*" >&2; }
die()  { err "$*"; exit 1; }

usage() {
  sed -n '3,/^set -euo pipefail/p' "$0" | sed '$d; s/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since)         SINCE="${2:?--since needs a value}"; shift 2 ;;
    --until)         UNTIL="${2:?--until needs a value}"; shift 2 ;;
    --reference-tif) REFERENCE_TIF="${2:?--reference-tif needs a value}"; DO_REFERENCE=1; shift 2 ;;
    --reference)     REFERENCE_TIF="$CHART_TIF"; DO_REFERENCE=1; shift ;;
    --fresh)         FRESH=1; shift ;;
    --bs-curve)      BS_CURVE="${2:?--bs-curve needs a value}"; shift 2 ;;
    --limit)         LIMIT="${2:?--limit needs a value}"; shift 2 ;;
    -n|--dry-run)    DRY_RUN=1; shift ;;
    -h|--help)       usage; exit 0 ;;
    *)               die "unknown option: $1 (try --help)" ;;
  esac
done

for d in "$SINCE" "$UNTIL"; do
  [[ -z "$d" || "$d" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || die "bad date '$d' (want YYYY-MM-DD)"
done
[[ -n "$BS_CURVE" && ! -f "$BS_CURVE" ]] && die "--bs-curve file not found: $BS_CURVE"
[[ $DO_REFERENCE -eq 1 && ! -f "$REFERENCE_TIF" ]] && die "reference GeoTIFF not found: $REFERENCE_TIF"
command -v ros2 >/dev/null || die "ros2 not on PATH — source the workspace setup.bash first"
[[ -d "$BAG_ROOT" ]] || die "bag root not found: $BAG_ROOT"

# --------------------------------------------------------------------------
# Preflight guards
# --------------------------------------------------------------------------
# import_bag must speak the #96 store model (--reference-store). Capture
# --help to a var first: usage() exits non-zero, which under pipefail would
# mask a grep match and cause a false refusal.
IMPORT_HELP="$(ros2 run cube_bathymetry import_bag --help 2>&1 || true)"
if ! grep -q -- '--reference-store' <<<"$IMPORT_HELP"; then
  die "this import_bag predates the cube_bathymetry#96 store redesign (no --reference-store). Rebuild cube_bathymetry first."
fi

# Refuse pre-#96 legacy stores (chart/draft/processed layers, ingest ledger):
# mixing store models presents the same data twice to a layer-priority
# consumer and the legacy per-cell registry mismatches the new StoreMetadata.
for d in "$BATHY_STORE" "$BS_STORE"; do
  for legacy in chart draft processed .ingested_bags.txt; do
    if [[ -e "$d/$legacy" ]]; then
      die "$d contains pre-#96 legacy content ('$legacy') — refusing to mix store models; use a fresh BATHY_STORE/BS_STORE directory"
    fi
  done
done

# A survey/.building sentinel means a previous run died mid-write: the tiles
# present are an unknown subset. Refuse until the operator clears them.
for d in "$BATHY_STORE" "$BS_STORE"; do
  if [[ -e "$d/survey/.building" ]]; then
    die "$d/survey/.building exists — a previous run was interrupted mid-write. Delete $d/survey/ (it is regenerable) and re-run."
  fi
done

if [[ $DRY_RUN -eq 0 ]]; then
  mkdir -p "$BATHY_STORE" "$BS_STORE"

  # Disk headroom on BOTH stores (they may sit on different filesystems): an
  # ENOSPC an hour in leaves exactly the partial store the sentinel guards
  # against. Fail fast instead.
  for d in "$BATHY_STORE" "$BS_STORE"; do
    free_gb=$(df --output=avail -B1G "$d" | tail -1 | tr -d ' ')
    if [[ "$free_gb" -lt "$MIN_FREE_GB" ]]; then
      die "only ${free_gb} GB free on $d (< ${MIN_FREE_GB} GB)"
    fi
  done

  # Single instance: the guards here are check-then-act over a ~1 h write —
  # two concurrent runs would both pass them and interleave tile writes.
  # Lock BOTH stores so runs sharing either store exclude each other.
  exec 9>"$BATHY_STORE/.build_lock"
  exec 8>"$BS_STORE/.build_lock"
  if ! flock -n 9 || ! flock -n 8; then
    die "another build holds a .build_lock in $BATHY_STORE or $BS_STORE"
  fi
fi

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
archive_layer() {  # store_dir layer — reversible mv into <store>/_archive/<ts>/
  local store="$1" layer="$2"
  [[ -d "$store/$layer" ]] || return 0
  local dest="$store/_archive/$(date +%Y%m%d-%H%M%S)"
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "would archive $store/$layer -> $dest/$layer"
  else
    mkdir -p "$dest"
    mv "$store/$layer" "$dest/"
    echo "archived $store/$layer -> $dest/$layer"
  fi
}

has_tiles() {  # dir — any .tif directly inside?
  compgen -G "$1/*.tif" > /dev/null 2>&1
}

bag_topic_counts() {  # metadata.yaml -> "<detections_count> <tf_count>"
  python3 - "$1" "$DETECTIONS_TOPIC" <<'PY'
import sys, yaml
info = yaml.safe_load(open(sys.argv[1]))["rosbag2_bagfile_information"]
det = tf = 0
for t in info.get("topics_with_message_count", []):
    name = t["topic_metadata"]["name"]
    if name == sys.argv[2]:
        det += t.get("message_count", 0)
    elif name == "/tf":
        tf += t.get("message_count", 0)
print(det, tf)
PY
}

# --------------------------------------------------------------------------
# Backscatter correction: deployed empirical curve by default (tier-2
# product with per-beam 2-way TL removed, cube#87); import_bag's auto
# correction (cube#102) only as fallback when no curve exists.
# --------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "$BS_CURVE" ]]; then
  # || true: under set -e a failed `ros2 pkg prefix` in a command substitution
  # would otherwise abort silently when the overlay isn't sourced.
  PKG_PREFIX="$(ros2 pkg prefix bizzyboat_project11 2>/dev/null || true)"
  CANDIDATES=("$SCRIPT_DIR/../bizzyboat_project11/config/m3_angular_response_curve.csv")
  [[ -n "$PKG_PREFIX" ]] && CANDIDATES=("$PKG_PREFIX/share/bizzyboat_project11/config/m3_angular_response_curve.csv" "${CANDIDATES[@]}")
  for c in "${CANDIDATES[@]}"; do
    if [[ -f "$c" ]]; then BS_CURVE="$c"; break; fi
  done
fi
if [[ -z "$BS_CURVE" ]]; then
  warn "no angular-response curve found — falling back to import_bag auto backscatter correction"
fi

# --------------------------------------------------------------------------
# Reference layer (chart prior)
# --------------------------------------------------------------------------
HAVE_REFERENCE=0
if has_tiles "$BATHY_STORE/reference"; then
  # Tiles present = accepted as complete (the staged import below can no
  # longer leave a partial layer). If in doubt, delete reference/ and
  # re-import — it is regenerable.
  if [[ $DO_REFERENCE -eq 1 ]]; then
    echo "reference: already present in $BATHY_STORE — skipping import"
    echo "  (NOTE: ignoring --reference-tif $REFERENCE_TIF; delete reference/ to rebuild)"
    DO_REFERENCE=0
  fi
  HAVE_REFERENCE=1
elif [[ -d "$BATHY_STORE/reference" ]]; then
  # A tile-less reference/ dir would make the staged mv below NEST the layer
  # (reference/reference/) — misfiling the prior and silently disabling the
  # blunder gate. Refuse instead.
  die "$BATHY_STORE/reference exists but holds no tiles (interrupted earlier import?). Delete it and re-run."
else
  HAVE_REFERENCE=$DO_REFERENCE
fi

if [[ $DO_REFERENCE -eq 1 ]]; then
  # Per-band uncertainty needs the ccomjhc#75 2-band product; a 1-band chart
  # falls back to the constant — loudly, because a constant silently
  # overriding honest per-band values was the documented failure mode.
  BANDS=$(python3 - "$REFERENCE_TIF" <<'PY'
import sys
from osgeo import gdal
gdal.UseExceptions()
print(gdal.Open(sys.argv[1]).RasterCount)
PY
)
  UNC_ARGS=()
  if [[ "$BANDS" -lt 2 ]]; then
    warn "$REFERENCE_TIF has $BANDS band(s) — no per-band uncertainty; using constant $CHART_UNCERTAINTY m (prefer the ccomjhc#75 2-band product)"
    UNC_ARGS=(--uncertainty "$CHART_UNCERTAINTY")
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "would rebuild $BATHY_STORE/reference from $REFERENCE_TIF ($BANDS band(s), nearest-neighbor WGS84 reproject, staged + atomic rename)"
  else
    echo "=== reference layer: $REFERENCE_TIF -> $BATHY_STORE (staged) ==="
    tmp_tif=$(mktemp --suffix=.tif)
    # Stage into a temp sibling and rename into place: an interrupted import
    # must never leave a partial reference/ that a re-run would silently
    # accept as complete (the blunder gate would then be missing over part
    # of the lake).
    REF_STAGE="$(mktemp -d "$BATHY_STORE/.ref_stage.XXXXXX")"
    trap 'rm -f "$tmp_tif"; rm -rf "$REF_STAGE"' EXIT
    # nearest-neighbor preserves band values (bilinear smooths the deep
    # holes); import_geotiff requires a geographic WGS84 raster. Prints
    # source vs reprojected min/max so a smoothed reproject is visible
    # immediately.
    python3 - "$REFERENCE_TIF" "$tmp_tif" <<'PY'
import sys
from osgeo import gdal
gdal.UseExceptions()
src = gdal.Open(sys.argv[1])
out = gdal.Warp(sys.argv[2], src, dstSRS="EPSG:4326", resampleAlg="near")
for name, ds in (("source", src), ("reprojected", out)):
    lo, hi, *_ = ds.GetRasterBand(1).ComputeStatistics(False)
    print(f"  {name}: min={lo:.2f} max={hi:.2f}")
out = None
PY
    ros2 run marine_bathymetry_store import_geotiff \
      "$REF_STAGE" reference "$tmp_tif" \
      --cell-size "$CHART_CELL_SIZE" \
      --depth-scale "$CHART_DEPTH_SCALE" --depth-offset "$CHART_DEPTH_OFFSET" \
      ${UNC_ARGS[@]+"${UNC_ARGS[@]}"} \
      --platform "$CHART_PLATFORM" --sensor "$CHART_SENSOR" --survey "$CHART_SURVEY"
    # -T: rename onto the destination itself; fails loudly rather than
    # nesting if a reference/ dir appeared since the guard above.
    mv -T "$REF_STAGE/reference" "$BATHY_STORE/reference"   # atomic on same FS
    [[ -e "$BATHY_STORE/registry.json" ]] || mv "$REF_STAGE/registry.json" "$BATHY_STORE/registry.json"
    rm -f "$tmp_tif"; rm -rf "$REF_STAGE"; trap - EXIT
  fi
fi

# --------------------------------------------------------------------------
# Bag selection
# --------------------------------------------------------------------------
BAGS=()
n_window=0 n_nometa=0 n_badmeta=0 n_nodet=0 n_notf=0 n_listed=0
for bag in "$BAG_ROOT"/*/; do
  bag="${bag%/}"
  name=$(basename "$bag")
  day="${name:0:10}"
  [[ "$day" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || continue   # m3_all etc.
  if [[ " $SKIP_BAGS " == *" $name "* ]]; then
    echo "  - $name skipped (SKIP_BAGS: unusable timing, see script header)"
    ((++n_listed)); continue
  fi
  if [[ -n "$SINCE" && "$day" < "$SINCE" ]] || [[ -n "$UNTIL" && "$day" > "$UNTIL" ]]; then
    ((++n_window)); continue
  fi
  if [[ ! -f "$bag/metadata.yaml" ]]; then
    warn "skipping $name: no metadata.yaml (likely still mid-rsync from gabby)"
    ((++n_nometa)); continue
  fi
  if ! counts=$(bag_topic_counts "$bag/metadata.yaml" 2>/dev/null); then
    warn "skipping $name: metadata.yaml unreadable (corrupt or unexpected schema — NOT the mid-rsync case)"
    ((++n_badmeta)); continue
  fi
  read -r det tf <<<"$counts"
  if [[ "$det" -eq 0 ]]; then
    ((++n_nodet)); continue
  fi
  if [[ "$tf" -eq 0 ]]; then
    warn "skipping $name: $det detections but no /tf (projector would produce an empty grid)"
    ((++n_notf)); continue
  fi
  BAGS+=("$bag")
done

echo "=== bag selection ($BAG_ROOT) ==="
printf '  %s\n' "${BAGS[@]##*/}"
echo "selected ${#BAGS[@]} bags (skipped: $n_window outside window, $n_listed skip-listed, $n_nometa mid-rsync, $n_badmeta unreadable metadata, $n_nodet no detections, $n_notf no /tf)"
[[ ${#BAGS[@]} -gt 0 ]] || die "no bags selected"

# --------------------------------------------------------------------------
# CUBE pass
# --------------------------------------------------------------------------
if [[ $FRESH -eq 1 ]]; then
  archive_layer "$BATHY_STORE" survey
  archive_layer "$BS_STORE" survey
else
  # Full regeneration only: a second pass over the same bags into an existing
  # survey layer double-counts soundings (#96 dropped the ingest ledger that
  # used to guard this). --fresh archives reversibly.
  for d in "$BATHY_STORE/survey" "$BS_STORE/survey"; do
    if has_tiles "$d"; then
      die "$d already has tiles — this script does FULL regeneration; re-run with --fresh (archives the old layer) or point at fresh store dirs"
    fi
  done
fi

cmd=(ros2 run cube_bathymetry import_bag
  -o "$BATHY_STORE"
  --bs-store "$BS_STORE"
  -d "$DETECTIONS_TOPIC"
  --odom-topic "$ODOM_TOPIC"
  -r "$RESOLUTION"
  --base-link-frame "$BASE_LINK_FRAME"
  --level-frame "$LEVEL_FRAME"
  --tide-frame "$TIDE_FRAME"
  --platform "$PLATFORM" --sensor "$SENSOR" --campaign "$CAMPAIGN")

# Gate false-deeps against the chart prior whenever a reference layer exists
# (or will, once a --reference-tif dry-run is executed for real).
if [[ $HAVE_REFERENCE -eq 1 ]]; then
  cmd+=(--reference-store "$BATHY_STORE")
else
  warn "no reference layer in $BATHY_STORE — running WITHOUT blunder gating (use --reference-tif)"
fi
if [[ -n "$BS_CURVE" ]]; then
  cmd+=(--backscatter-correction empirical --backscatter-curve "$BS_CURVE")
fi
[[ -n "$LIMIT" ]] && cmd+=(-l "$LIMIT")
cmd+=("${BAGS[@]}")

if [[ $DRY_RUN -eq 1 ]]; then
  echo "=== would run ==="
  printf '%q ' "${cmd[@]}"; echo
  exit 0
fi

# Interruption safety: the survey pass writes tiles progressively over ~1 h;
# the sentinel marks the run and is removed only after import_bag succeeds
# AND the post-run tile check passes.
mkdir -p "$BATHY_STORE/survey" "$BS_STORE/survey"
touch "$BATHY_STORE/survey/.building" "$BS_STORE/survey/.building"
trap 'err "survey pass did not complete — partial tiles remain under
       $BATHY_STORE/survey and $BS_STORE/survey (marked by .building).
       Delete both survey/ dirs (regenerable) before re-running."' ERR

echo "=== CUBE pass: ${#BAGS[@]} bags -> $BATHY_STORE (bs: $BS_STORE) ==="
"${cmd[@]}"

# Post-run: an exit-0 import that produced nothing must not be announced as
# success (topic drift or all-dropped pings would otherwise ship an empty
# authoritative store).
n_bathy=$(find "$BATHY_STORE/survey" -maxdepth 1 -name '*.tif' | wc -l)
n_bs=$(find "$BS_STORE/survey" -maxdepth 1 -name '*.tif' | wc -l)
echo "tiles : $n_bathy bathy survey, $n_bs backscatter survey"
if [[ "$n_bathy" -eq 0 ]]; then
  die "import_bag exited 0 but wrote no bathy survey tiles — check -d topic ($DETECTIONS_TOPIC) and the frame overrides against the bags"
fi
trap - ERR
rm -f "$BATHY_STORE/survey/.building" "$BS_STORE/survey/.building"

echo "=== done -> $BATHY_STORE (reference + survey) + $BS_STORE (${#BAGS[@]} bags) ==="
