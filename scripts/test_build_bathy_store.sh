#!/usr/bin/env bash
#
# test_build_bathy_store.sh — regression tests for build_bathy_store.sh's
# bag-selection and CLI logic, exercised via --dry-run against a synthetic
# bag tree (no ROS runtime needed; `ros2` is stubbed on PATH).
#
# Covers: date-window filtering, missing metadata.yaml (mid-rsync),
# unreadable/corrupt metadata.yaml, no-detections and no-/tf gates,
# non-date directory exclusion, empty-selection failure, argument
# validation, and reference-store gating of the import_bag command.
#
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUT="$SCRIPT_DIR/build_bathy_store.sh"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PASS=0
FAIL=0

check() {  # description condition...
  local desc="$1"; shift
  if "$@"; then
    echo "  ok: $desc"; ((++PASS))
  else
    echo "  FAIL: $desc"; ((++FAIL))
  fi
}

contains() { grep -qF -- "$2" <<<"$1"; }

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------
mkdir -p "$TMP/bin"
printf '#!/bin/sh\nexit 0\n' > "$TMP/bin/ros2"
chmod +x "$TMP/bin/ros2"
export PATH="$TMP/bin:$PATH"

export BAG_ROOT="$TMP/bags"
export BATHY_STORE="$TMP/store/bathymetry"
export BS_STORE="$TMP/store/backscatter"
export CHART_TIF="$TMP/chart.tif"

DET_TOPIC="/bizzy/sensors/m3/detections"

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
mkdir -p  "$BAG_ROOT/2026-06-16T10-00-00+00-00"           # no metadata (mid-rsync)
mkdir -p  "$BAG_ROOT/2026-06-17T10-00-00+00-00"
echo '{{{ not: yaml' > "$BAG_ROOT/2026-06-17T10-00-00+00-00/metadata.yaml"  # corrupt
write_meta "$BAG_ROOT/2026-06-18T10-00-00+00-00" 0 50     # no detections
write_meta "$BAG_ROOT/2026-06-19T10-00-00+00-00" 100 -    # no /tf
mkdir -p  "$BAG_ROOT/m3_all"                              # non-date dir -> ignored

# --------------------------------------------------------------------------
echo "== selection gates (dry run) =="
out=$(bash "$SUT" --dry-run --since 2026-06-10 --until 2026-06-30 2>&1); rc=$?
check "exits 0"                        [ "$rc" -eq 0 ]
check "selects only the good bag"      contains "$out" "selected 1 bags (skipped: 1 outside window, 1 mid-rsync, 1 unreadable metadata, 1 no detections, 1 no /tf)"
check "good bag in import_bag command" contains "$out" "bags/2026-06-15T14-00-00+00-00"
check "warns on mid-rsync bag"         contains "$out" "2026-06-16T10-00-00+00-00: no metadata.yaml"
check "warns on corrupt metadata"      contains "$out" "2026-06-17T10-00-00+00-00: metadata.yaml unreadable"
check "warns on missing /tf"           contains "$out" "2026-06-19T10-00-00+00-00: 100 detections but no /tf"
check "warns when no reference layer"  contains "$out" "WITHOUT blunder gating"
check "command has no reference flag"  bash -c "! grep -qF -- --reference-store <<<'$out'"

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

echo "== reference-store gating =="
mkdir -p "$BATHY_STORE/reference" "$BATHY_STORE/survey" "$BS_STORE/survey"
out=$(bash "$SUT" --dry-run --fresh 2>&1); rc=$?
check "exits 0"                        [ "$rc" -eq 0 ]
check "reference layer enables gating" contains "$out" "--reference-store"
check "--fresh archives bathy survey"  contains "$out" "would archive $BATHY_STORE/survey"
check "--fresh archives bs survey"     contains "$out" "would archive $BS_STORE/survey"
check "--fresh keeps reference layer"  bash -c "! grep -qF 'would archive $BATHY_STORE/reference' <<<'$out'"

echo "== --reference dry run =="
touch "$CHART_TIF"
out=$(bash "$SUT" --dry-run --reference 2>&1); rc=$?
check "exits 0"                        [ "$rc" -eq 0 ]
check "announces reference rebuild"    contains "$out" "would rebuild $BATHY_STORE/reference"
check "archives existing reference"    contains "$out" "would archive $BATHY_STORE/reference"

# --------------------------------------------------------------------------
echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
