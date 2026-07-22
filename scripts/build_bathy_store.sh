#!/usr/bin/env bash
#
# build_bathy_store.sh — rebuild the GGGS bathymetry/backscatter stores from
# recorded bizzyboat_sonar bags (Kongsberg M3 detections -> CUBE).
#
# Goes through the synced bizzyboat_sonar bag directories, selects the ones
# that actually carry multibeam data (detections messages + /tf in
# metadata.yaml), and runs them through cube_bathymetry's import_bag in ONE
# multi-bag CUBE pass. Bags blend into a single `survey` layer (uma#248
# store model: survey = CUBE product, reference = chart prior).
#
# Bags with no metadata.yaml are skipped with a warning: rosbag2 writes it
# at close, so its absence usually means the bag is still mid-rsync from
# gabby — not crashed. Re-run after the sync completes.
#
# Requires a sourced ROS environment with cube_bathymetry and
# marine_bathymetry_store built (workspace setup.bash), and python3 GDAL
# bindings for --reference (the gdalwarp CLI is not installed on salmon).
#
# Usage:
#   build_bathy_store.sh [options]
#   build_bathy_store.sh -n                        # list selection + command only
#   build_bathy_store.sh --reference --fresh \
#       --since 2026-06-12 --until 2026-07-01      # full store rebuild
#
# Options:
#   --since DATE     only bags recorded on/after this UTC date (YYYY-MM-DD)
#   --until DATE     only bags recorded on/before this UTC date (YYYY-MM-DD)
#   --reference      (re)build the reference layer from the chart-prior
#                    GeoTIFF before cubing: nearest-neighbor reproject to
#                    geographic WGS84 (bilinear smooths the deep holes —
#                    16.76 m max read 13.72 m on 2026-07-01), then
#                    import_geotiff. Archives any existing reference layer.
#   --fresh          archive existing survey layers (bathymetry AND
#                    backscatter stores) first, so the CUBE pass rebuilds
#                    from scratch instead of blending into old tiles
#   --bs-curve FILE  empirical angular-response curve CSV; switches
#                    --backscatter-correction from auto to empirical
#   --limit N        stop after N pings (import_bag -l, debugging)
#   -n, --dry-run    print bag selection and the import_bag command; run nothing
#   -h, --help       this help
#
set -euo pipefail

# --------------------------------------------------------------------------
# Configuration — edit here if topics or frames change. Paths are
# env-overridable (BAG_ROOT=... build_bathy_store.sh ...) for other hosts
# and for the test harness.
# --------------------------------------------------------------------------
BAG_ROOT="${BAG_ROOT:-$HOME/data/logs/gabby/logs/bizzyboat_sonar}"
BATHY_STORE="${BATHY_STORE:-$HOME/data/stores/bathymetry}"
BS_STORE="${BS_STORE:-$HOME/data/stores/backscatter}"

DETECTIONS_TOPIC="/bizzy/sensors/m3/detections"
ODOM_TOPIC="/bizzy/odom"
RESOLUTION=1.0

# Offline projector frame overrides — must match the bags' namespaced frames
# or the grid comes out empty (import_bag only warns once).
BASE_LINK_FRAME="bizzy/base_link"
LEVEL_FRAME="bizzy/base_link_north_up"
TIDE_FRAME="bizzy/map_tide"

# Store-level provenance (uma#248 StoreMetadata; campaign = survey id).
PLATFORM=bizzy
SENSOR=m3
CAMPAIGN=massabesic_jun2026

# Chart prior for --reference: NH GRANIT Massabesic bathymetry,
# NAD83/UTM19N, positive-down depths below the full-pool lake surface.
CHART_TIF="${CHART_TIF:-$HOME/data/massabesic_bathy.tif}"
CHART_DEPTH_SCALE=-1     # positive-down depth -> up-positive ellipsoidal height
CHART_DEPTH_OFFSET=48.88 # full-pool lake-surface WGS84 ellipsoidal height:
                         # chart_datum_z in bizzyboat_project11/config/
                         # massabesic_datum_polygons.yaml (unh_echoboats#278)
CHART_UNCERTAINTY=1.524  # 5 ft — GRANIT stated accuracy
CHART_CELL_SIZE=1.0      # level 10; matches survey RESOLUTION
CHART_PLATFORM=nh-granit
CHART_SENSOR=edp-bathymetry-lakes
CHART_SURVEY=massabesic-2026

# --------------------------------------------------------------------------
SINCE=""
UNTIL=""
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
    --since)     SINCE="${2:?--since needs a value}"; shift 2 ;;
    --until)     UNTIL="${2:?--until needs a value}"; shift 2 ;;
    --reference) DO_REFERENCE=1; shift ;;
    --fresh)     FRESH=1; shift ;;
    --bs-curve)  BS_CURVE="${2:?--bs-curve needs a value}"; shift 2 ;;
    --limit)     LIMIT="${2:?--limit needs a value}"; shift 2 ;;
    -n|--dry-run) DRY_RUN=1; shift ;;
    -h|--help)   usage; exit 0 ;;
    *)           die "unknown option: $1 (try --help)" ;;
  esac
done

for d in "$SINCE" "$UNTIL"; do
  [[ -z "$d" || "$d" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || die "bad date '$d' (want YYYY-MM-DD)"
done
[[ -n "$BS_CURVE" && ! -f "$BS_CURVE" ]] && die "--bs-curve file not found: $BS_CURVE"
command -v ros2 >/dev/null || die "ros2 not on PATH — source the workspace setup.bash first"
[[ -d "$BAG_ROOT" ]] || die "bag root not found: $BAG_ROOT"

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
# Reference layer (chart prior)
# --------------------------------------------------------------------------
if [[ $DO_REFERENCE -eq 1 ]]; then
  [[ -f "$CHART_TIF" ]] || die "chart prior not found: $CHART_TIF"
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "would rebuild $BATHY_STORE/reference from $CHART_TIF (nearest-neighbor WGS84 reproject)"
    archive_layer "$BATHY_STORE" reference
  else
    echo "=== reference layer: $CHART_TIF -> $BATHY_STORE ==="
    archive_layer "$BATHY_STORE" reference
    tmp_tif=$(mktemp --suffix=.tif)
    trap 'rm -f "$tmp_tif"' EXIT
    # nearest-neighbor preserves depth extremes; import_geotiff requires
    # a geographic WGS84 raster. Prints source vs reprojected min/max so a
    # smoothed reproject is visible immediately.
    python3 - "$CHART_TIF" "$tmp_tif" <<'PY'
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
    ros2 run marine_bathymetry_store import_geotiff "$BATHY_STORE" reference "$tmp_tif" \
      --cell-size "$CHART_CELL_SIZE" --uncertainty "$CHART_UNCERTAINTY" \
      --depth-scale "$CHART_DEPTH_SCALE" --depth-offset "$CHART_DEPTH_OFFSET" \
      --platform "$CHART_PLATFORM" --sensor "$CHART_SENSOR" --survey "$CHART_SURVEY"
  fi
fi

# --------------------------------------------------------------------------
# Bag selection
# --------------------------------------------------------------------------
BAGS=()
n_window=0 n_nometa=0 n_badmeta=0 n_nodet=0 n_notf=0
for bag in "$BAG_ROOT"/*/; do
  bag="${bag%/}"
  name=$(basename "$bag")
  day="${name:0:10}"
  [[ "$day" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || continue   # m3_all etc.
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
echo "selected ${#BAGS[@]} bags (skipped: $n_window outside window, $n_nometa mid-rsync, $n_badmeta unreadable metadata, $n_nodet no detections, $n_notf no /tf)"
[[ ${#BAGS[@]} -gt 0 ]] || die "no bags selected"

# --------------------------------------------------------------------------
# CUBE pass
# --------------------------------------------------------------------------
[[ $FRESH -eq 1 ]] && { archive_layer "$BATHY_STORE" survey; archive_layer "$BS_STORE" survey; }

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

# Gate false-deeps against the chart prior when the reference layer exists
# (with --dry-run --reference it will exist by the time the real run happens).
if [[ -d "$BATHY_STORE/reference" || ( $DRY_RUN -eq 1 && $DO_REFERENCE -eq 1 ) ]]; then
  cmd+=(--reference-store "$BATHY_STORE")
else
  warn "no reference layer in $BATHY_STORE — running WITHOUT blunder gating (use --reference)"
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

echo "=== CUBE pass: ${#BAGS[@]} bags -> $BATHY_STORE (bs: $BS_STORE) ==="
"${cmd[@]}"
echo "=== done: ${#BAGS[@]} bags cubed into $BATHY_STORE ==="
