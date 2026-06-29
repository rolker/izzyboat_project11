#!/usr/bin/env bash
# Incrementally build the Massabesic bathy + backscatter stores from the M3 bags.
#
# Unlike the original throwaway-store builder, this APPENDS to the canonical
# stores in place:
#   ~/data/stores/bathymetry   chart (fixed prior) + processed (M3 bathy)
#   ~/data/stores/backscatter  processed (M3 backscatter)
#
# Each run:
#   * seeds CUBE from the existing `processed` layer (import_bag --append) so new
#     soundings BLEND onto prior coverage instead of overwriting it,
#   * primes the predicted surface from the `chart` contour layer (--prior) for
#     false-deep blunder rejection,
#   * imports ONLY bags not already recorded in the ingest ledger
#     (~/data/stores/bathymetry/.ingested_bags.txt), so re-running never
#     double-counts already-ingested data.
#
# REQUIRES import_bag --append (cube_bathymetry#96). Until that PR lands the
# preflight below refuses to run, because pointing -o at the existing store
# WITHOUT --append would whole-tile-overwrite and lose prior coverage.
#
# Run AFTER sourcing the workspace and building cube_bathymetry (#96) +
# unh_echoboats_project11 (the angular-response curve).
set -eo pipefail
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
set -u   # nounset only AFTER sourcing ROS (setup.bash trips on unbound vars)

# ---- paths / config ----------------------------------------------------------
STORE_BATHY="$HOME/data/stores/bathymetry"          # chart + processed
STORE_BS="$HOME/data/stores/backscatter"            # backscatter processed
LEDGER="$STORE_BATHY/.ingested_bags.txt"
BAGS_DIR="$HOME/data/logs/gabby/logs/bizzyboat_sonar"   # <-- VERIFY corrected bags live here
TOPIC=/bizzy/sensors/m3/detections
SURVEY_START="2026-06-12"   # floor: never ingest pre-survey test bags (ISO names sort lexically)

# Deployed curve: prefer the installed share copy (workspace sourced), else fall
# back to this package's in-tree config — a deterministic sibling of scripts/,
# since this script lives at bizzyboat_project11/scripts/. (|| true: under set -e a
# failed `ros2 pkg prefix` in a command substitution would otherwise abort silently
# when the overlay isn't sourced.)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_PREFIX="$(ros2 pkg prefix bizzyboat_project11 2>/dev/null || true)"
CURVE="$PKG_PREFIX/share/bizzyboat_project11/config/m3_angular_response_curve.csv"
[ -f "$CURVE" ] || CURVE="$SCRIPT_DIR/../config/m3_angular_response_curve.csv"

# ---- preflight ---------------------------------------------------------------
echo "curve : $CURVE";          [ -f "$CURVE" ] || { echo "ERROR: curve not found"; exit 1; }
echo "store : $STORE_BATHY";    [ -d "$STORE_BATHY/chart" ] || { echo "ERROR: no chart layer at $STORE_BATHY/chart (no --prior gating)"; exit 1; }

# import_bag must support --append, or we'd silently overwrite the store.
# Capture --help to a var first: import_bag's usage() exits non-zero, which under
# `pipefail` would mask a grep match and cause a false "no --append" refusal.
IMPORT_HELP="$(ros2 run cube_bathymetry import_bag --help 2>&1 || true)"
if ! grep -q -- '--append' <<<"$IMPORT_HELP"; then
  echo "ERROR: this import_bag has no --append mode (cube_bathymetry#96)."
  echo "       Pointing -o at the existing store WITHOUT --append whole-tile-overwrites"
  echo "       and loses prior coverage. Refusing to run. Build the #96 PR first."
  exit 1
fi

# A non-empty processed layer with no ledger means we cannot tell what is already
# ingested -> appending the same bags would double-count. Refuse rather than guess.
processed_tiles=$(ls "$STORE_BATHY"/processed/*.tif 2>/dev/null | grep -Ec '/[0-9]+_[0-9]+_[0-9]+\.tif$' || true)
if [ "$processed_tiles" -gt 0 ] && [ ! -f "$LEDGER" ]; then
  echo "ERROR: $STORE_BATHY/processed has data but $LEDGER is missing."
  echo "       Cannot tell which bags are already ingested -> appending would double-count."
  echo "       Seed the ledger with the already-ingested bag dir names first."
  exit 1
fi

# ---- select bags to ingest ---------------------------------------------------
# Candidates: dirs at/after SURVEY_START, carrying M3 detections + /tf, not yet
# in the ledger. ISO-8601 dir names sort lexically, so a string compare on the
# date prefix is a correct chronological floor.
declare -A INGESTED=()
if [ -f "$LEDGER" ]; then
  while IFS= read -r line; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    INGESTED["$line"]=1
  done < "$LEDGER"
fi
echo "ledger: ${#INGESTED[@]} bag(s) already ingested"

NEW=""
skipped_ingested=0; skipped_notopic=0; skipped_pre=0
for b in "$BAGS_DIR"/*/; do
  b="${b%/}"
  name="$(basename "$b")"
  # date prefix is the first 10 chars (YYYY-MM-DD); ignore non-dated dirs
  [[ "$name" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2} ]] || continue
  if [[ "${name:0:10}" < "$SURVEY_START" ]]; then skipped_pre=$((skipped_pre+1)); continue; fi
  if [[ -n "${INGESTED[$name]:-}" ]]; then skipped_ingested=$((skipped_ingested+1)); continue; fi
  if ! { grep -qE 'm3/detections' "$b/metadata.yaml" 2>/dev/null && grep -q '/tf' "$b/metadata.yaml" 2>/dev/null; }; then
    skipped_notopic=$((skipped_notopic+1)); continue
  fi
  NEW="$NEW $b"
done
NEW=$(printf '%s\n' $NEW | sed '/^$/d')

echo "new   : $(printf '%s\n' "$NEW" | grep -c .) bag(s) to ingest"
echo "        (skipped: $skipped_ingested already-ingested, $skipped_pre pre-$SURVEY_START, $skipped_notopic no detections/tf)"
if [ -z "$NEW" ]; then echo "Store is up to date — nothing to ingest."; exit 0; fi
printf '  + %s\n' $NEW | sed "s#$BAGS_DIR/##"

# ---- run incremental import --------------------------------------------------
ros2 run cube_bathymetry import_bag \
  --append \
  -o "$STORE_BATHY" \
  --bathy-layer processed \
  --bs-store "$STORE_BS" \
  --prior "$STORE_BATHY" \
  -d "$TOPIC" \
  --odom-topic /bizzy/odom \
  -r 1.0 \
  --backscatter-correction empirical \
  --backscatter-curve "$CURVE" \
  --base-link-frame bizzy/base_link \
  --level-frame bizzy/base_link_north_up \
  --tide-frame bizzy/map_tide \
  --platform bizzy --sensor m3 --sensor-class kongsberg-m3 --campaign massabesic_jun2026 \
  $NEW

# ---- record ingested bags in the ledger (only on import success) -------------
# All new bags go through ONE import_bag invocation (best CUBE fidelity: full
# hypothesis state is kept across them). set -e means the ledger is updated only
# if that invocation succeeds. Caveat: if import_bag fails AFTER mutating the
# store (e.g. mid-run tile eviction), those partial writes persist but the bags
# are not ledgered, so a re-run would re-feed them. The durable fix is atomic
# append in import_bag (tracked on cube_bathymetry#96); on a failure here,
# inspect the store before re-running.
for b in $NEW; do basename "$b"; done >> "$LEDGER"
echo "=== done -> appended $(printf '%s\n' "$NEW" | grep -c .) bag(s) to $STORE_BATHY (+ $STORE_BS); ledger updated ==="
