#!/usr/bin/env bash
#
# test_build_bathy_store.sh — regression tests for build_bathy_store.sh,
# exercised against a synthetic bag tree with `ros2` stubbed on PATH
# (no ROS runtime, no containers; GDAL-dependent checks self-skip when
# python3-gdal is absent).
#
# Covers: date-window filtering, SKIP_BAGS exclusion, missing metadata.yaml
# (mid-rsync), unreadable metadata.yaml, no-detections / no-/tf gates,
# non-date directory exclusion, empty-selection failure, argument validation,
# provenance vocabulary, empirical-curve default + --bs-curve override,
# import_bag capability check, legacy-store / sentinel / tile-less-reference
# / survey-not-empty refusals, reference-store gating, --fresh archiving,
# real-run sentinel lifecycle, and the zero-tiles post-run guard.
#
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUT="$SCRIPT_DIR/build_bathy_store.sh"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PASS=0
FAIL=0
SKIP=0

check() {  # description condition...
  local desc="$1"; shift
  if "$@"; then
    echo "  ok: $desc"; ((++PASS))
  else
    echo "  FAIL: $desc"; ((++FAIL))
  fi
}

contains() { grep -qF -- "$2" <<<"$1"; }
not_contains() { ! grep -qF -- "$2" <<<"$1"; }

# --------------------------------------------------------------------------
# Stubs and fixtures
# --------------------------------------------------------------------------
mkdir -p "$TMP/bin"
cat > "$TMP/bin/ros2" <<'EOF'
#!/bin/bash
# import_bag capability probe: advertise --reference-store unless the test
# disables it to exercise the capability guard.
case "$*" in
  *"import_bag --help"*)
    if [[ "${ROS2_STUB_NO_REFSTORE:-0}" == 1 ]]; then echo "usage: import_bag"; else echo "usage: import_bag ... --reference-store ..."; fi
    exit 0 ;;
  *"pkg prefix"*) exit 1 ;;   # no deployed overlay in tests -> in-tree curve
esac
# Real-run import_bag call: write a survey tile into the -o store (and the
# --bs-store) unless the test wants the zero-tiles guard exercised.
out=""; bs=""; prev=""
for a in "$@"; do
  [[ "$prev" == "-o" ]] && out="$a"
  [[ "$prev" == "--bs-store" ]] && bs="$a"
  prev="$a"
done
if [[ -n "$out" && "${ROS2_STUB_WRITE_TILES:-1}" == 1 ]]; then
  mkdir -p "$out/survey" && touch "$out/survey/stub.tif"
  [[ -n "$bs" ]] && mkdir -p "$bs/survey" && touch "$bs/survey/stub.tif"
fi
exit 0
EOF
chmod +x "$TMP/bin/ros2"
export PATH="$TMP/bin:$PATH"

export BAG_ROOT="$TMP/bags"
export BATHY_STORE="$TMP/store/bathymetry"
export BS_STORE="$TMP/store/backscatter"
export CHART_TIF="$TMP/chart.tif"
export MIN_FREE_GB=0

DET_TOPIC="/bizzy/sensors/m3/detections"
SKIP_NAME="2026-06-27T23-58-21+00-00"   # matches the script's default SKIP_BAGS

write_meta() {  # dir det_count tf_count("-"=omit /tf entirely)
  local dir="$1" det="$2" tf="$3"
  mkdir -p "$dir"
  {
    echo "rosbag2_bagfile_information:"
    echo "  topics_with_message_count:"
    echo "    - topic_metadata:"
    echo "        name: $DET_TOPIC"
    echo "      message_count: $det"
    if [[ "$tf" != "-" ]]; then
      echo "    - topic_metadata:"
      echo "        name: /tf"
      echo "      message_count: $tf"
    fi
  } > "$dir/metadata.yaml"
}

write_meta "$BAG_ROOT/2026-06-15T14-00-00+00-00" 100 50   # good -> selected
write_meta "$BAG_ROOT/2026-06-01T09-00-00+00-00" 100 50   # before --since
write_meta "$BAG_ROOT/$SKIP_NAME"                100 50   # passes gates, skip-listed
mkdir -p  "$BAG_ROOT/2026-06-16T10-00-00+00-00"           # no metadata (mid-rsync)
mkdir -p  "$BAG_ROOT/2026-06-17T10-00-00+00-00"
echo '{{{ not: yaml' > "$BAG_ROOT/2026-06-17T10-00-00+00-00/metadata.yaml"  # corrupt
write_meta "$BAG_ROOT/2026-06-18T10-00-00+00-00" 0 50     # no detections
write_meta "$BAG_ROOT/2026-06-19T10-00-00+00-00" 100 -    # no /tf
mkdir -p  "$BAG_ROOT/m3_all"                              # non-date dir -> ignored

CURVE_INTREE="$SCRIPT_DIR/../bizzyboat_project11/config/m3_angular_response_curve.csv"

reset_stores() { rm -rf "$TMP/store"; mkdir -p "$BATHY_STORE" "$BS_STORE"; }
reset_stores

# --------------------------------------------------------------------------
echo "== selection gates (dry run) =="
out=$(bash "$SUT" --dry-run --since 2026-06-10 --until 2026-06-30 2>&1); rc=$?
check "exits 0"                        [ "$rc" -eq 0 ]
check "selects only the good bag"      contains "$out" "selected 1 bags (skipped: 1 outside window, 1 skip-listed, 1 mid-rsync, 1 unreadable metadata, 1 no detections, 1 no /tf)"
check "good bag in import_bag command" contains "$out" "bags/2026-06-15T14-00-00+00-00"
check "skip-listed bag excluded"       not_contains "$out" "bags/$SKIP_NAME "
check "skip-listed reported"           contains "$out" "$SKIP_NAME skipped (SKIP_BAGS"
check "warns on mid-rsync bag"         contains "$out" "2026-06-16T10-00-00+00-00: no metadata.yaml"
check "warns on corrupt metadata"      contains "$out" "2026-06-17T10-00-00+00-00: metadata.yaml unreadable"
check "warns on missing /tf"           contains "$out" "2026-06-19T10-00-00+00-00: 100 detections but no /tf"
check "warns when no reference layer"  contains "$out" "WITHOUT blunder gating"
check "command has no reference flag"  not_contains "$out" "--reference-store"

echo "== provenance vocabulary (ADR-0005/0007) =="
check "platform bizzyboat"             contains "$out" "--platform bizzyboat"
check "sensor kongsberg-m3"            contains "$out" "--sensor kongsberg-m3"
check "campaign massabesic-jun2026"    contains "$out" "--campaign massabesic-jun2026"

echo "== backscatter curve default + override =="
if [[ -f "$CURVE_INTREE" ]]; then
  check "in-tree curve default (empirical)" contains "$out" "--backscatter-correction empirical"
  check "curve path in command"             contains "$out" "m3_angular_response_curve.csv"
else
  echo "  skip: in-tree curve not present"; ((++SKIP))
fi
echo "custom,curve" > "$TMP/mycurve.csv"
out=$(bash "$SUT" --dry-run --bs-curve "$TMP/mycurve.csv" 2>&1); rc=$?
check "--bs-curve override used"       contains "$out" "mycurve.csv"

echo "== SKIP_BAGS env override =="
out=$(SKIP_BAGS="2026-06-15T14-00-00+00-00" bash "$SUT" --dry-run --since 2026-06-10 --until 2026-06-30 2>&1); rc=$?
check "override skips the good bag"    not_contains "$out" "$BAG_ROOT/2026-06-15T14-00-00+00-00"
check "default skip bag now selectable" contains "$out" "$BAG_ROOT/$SKIP_NAME"
check "override reported as skip-listed" contains "$out" "2026-06-15T14-00-00+00-00 skipped (SKIP_BAGS"

echo "== empty selection fails =="
out=$(bash "$SUT" --dry-run --since 2027-01-01 2>&1); rc=$?
check "exits non-zero"                 [ "$rc" -ne 0 ]
check "reports no bags selected"       contains "$out" "no bags selected"

echo "== argument validation =="
out=$(bash "$SUT" --dry-run --since 15-06-2026 2>&1); rc=$?
check "bad date rejected"              [ "$rc" -ne 0 ]
out=$(bash "$SUT" --frobnicate 2>&1); rc=$?
check "unknown option rejected"        [ "$rc" -ne 0 ]
out=$(bash "$SUT" --dry-run --bs-curve "$TMP/nope.csv" 2>&1); rc=$?
check "missing --bs-curve file rejected" [ "$rc" -ne 0 ]
out=$(bash "$SUT" --dry-run --reference-tif "$TMP/nope.tif" 2>&1); rc=$?
check "missing --reference-tif rejected" [ "$rc" -ne 0 ]

echo "== import_bag capability guard =="
out=$(ROS2_STUB_NO_REFSTORE=1 bash "$SUT" --dry-run 2>&1); rc=$?
check "pre-#96 import_bag refused"     [ "$rc" -ne 0 ]
check "explains rebuild"               contains "$out" "Rebuild cube_bathymetry first"

echo "== legacy store refusal =="
mkdir -p "$BATHY_STORE/chart"
out=$(bash "$SUT" --dry-run 2>&1); rc=$?
check "legacy content refused"         [ "$rc" -ne 0 ]
check "names the legacy entry"         contains "$out" "pre-#96 legacy content ('chart')"
reset_stores

echo "== sentinel refusal =="
mkdir -p "$BS_STORE/survey" && touch "$BS_STORE/survey/.building"
out=$(bash "$SUT" --dry-run 2>&1); rc=$?
check "interrupted-run sentinel refused" [ "$rc" -ne 0 ]
check "points at the sentinel"         contains "$out" "survey/.building exists"
reset_stores

echo "== tile-less reference dir refusal =="
mkdir -p "$BATHY_STORE/reference"
out=$(bash "$SUT" --dry-run 2>&1); rc=$?
check "empty reference dir refused"    [ "$rc" -ne 0 ]
check "explains nesting hazard"        contains "$out" "holds no tiles"
reset_stores

echo "== reference-store gating + --fresh =="
mkdir -p "$BATHY_STORE/reference" "$BATHY_STORE/survey" "$BS_STORE/survey"
touch "$BATHY_STORE/reference/ref.tif" "$BATHY_STORE/survey/s.tif" "$BS_STORE/survey/s.tif"
out=$(bash "$SUT" --dry-run --fresh 2>&1); rc=$?
check "exits 0"                        [ "$rc" -eq 0 ]
check "reference layer enables gating" contains "$out" "--reference-store"
check "--fresh archives bathy survey"  contains "$out" "would archive $BATHY_STORE/survey"
check "--fresh archives bs survey"     contains "$out" "would archive $BS_STORE/survey"
check "--fresh keeps reference layer"  not_contains "$out" "would archive $BATHY_STORE/reference"

echo "== survey-not-empty refusal without --fresh =="
out=$(bash "$SUT" --dry-run 2>&1); rc=$?
check "existing survey tiles refused"  [ "$rc" -ne 0 ]
check "points at --fresh"              contains "$out" "re-run with --fresh"
reset_stores

echo "== --reference dry run (GDAL band probe) =="
if python3 -c 'from osgeo import gdal' 2>/dev/null; then
  python3 - "$CHART_TIF" <<'PY'
import sys
from osgeo import gdal
gdal.UseExceptions()
drv = gdal.GetDriverByName("GTiff")
ds = drv.Create(sys.argv[1], 4, 4, 1, gdal.GDT_Float32)
ds.SetGeoTransform([0, 1, 0, 0, 0, -1])
ds.GetRasterBand(1).Fill(5.0)
ds = None
PY
  out=$(bash "$SUT" --dry-run --reference 2>&1); rc=$?
  check "exits 0"                      [ "$rc" -eq 0 ]
  check "announces staged rebuild"     contains "$out" "would rebuild $BATHY_STORE/reference"
  check "1-band constant fallback warns" contains "$out" "no per-band uncertainty"
  python3 - "$TMP/chart2.tif" <<'PY'
import sys
from osgeo import gdal
gdal.UseExceptions()
drv = gdal.GetDriverByName("GTiff")
ds = drv.Create(sys.argv[1], 4, 4, 2, gdal.GDT_Float32)
ds.SetGeoTransform([0, 1, 0, 0, 0, -1])
ds.GetRasterBand(1).Fill(5.0)
ds.GetRasterBand(2).Fill(0.5)
ds = None
PY
  out=$(bash "$SUT" --dry-run --reference-tif "$TMP/chart2.tif" 2>&1); rc=$?
  check "2-band product accepted"      [ "$rc" -eq 0 ]
  check "no constant-uncertainty warn" not_contains "$out" "no per-band uncertainty"
else
  echo "  skip: python3-gdal not available"; ((SKIP+=5))
fi
reset_stores

echo "== real run: sentinel lifecycle + success =="
out=$(bash "$SUT" --since 2026-06-10 --until 2026-06-30 2>&1); rc=$?
check "exits 0"                        [ "$rc" -eq 0 ]
check "reports done"                   contains "$out" "=== done ->"
check "bathy sentinel removed"         [ ! -e "$BATHY_STORE/survey/.building" ]
check "bs sentinel removed"            [ ! -e "$BS_STORE/survey/.building" ]
check "survey tile present"            [ -e "$BATHY_STORE/survey/stub.tif" ]
reset_stores

echo "== real run: zero-tiles guard =="
out=$(ROS2_STUB_WRITE_TILES=0 bash "$SUT" --since 2026-06-10 --until 2026-06-30 2>&1); rc=$?
check "exits non-zero"                 [ "$rc" -ne 0 ]
check "reports empty import"           contains "$out" "wrote no bathy survey tiles"
check "sentinel left as evidence"      [ -e "$BATHY_STORE/survey/.building" ]
reset_stores

# --------------------------------------------------------------------------
echo
echo "$PASS passed, $FAIL failed, $SKIP skipped"
[ "$FAIL" -eq 0 ]
