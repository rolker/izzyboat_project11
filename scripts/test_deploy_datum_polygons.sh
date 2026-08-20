#!/usr/bin/env bash
#
# test_deploy_datum_polygons.sh — regression tests for
# deploy_datum_polygons.sh. Self-contained: no ROS runtime, no ~/data writes
# (SRC/DEST_DIR are redirected into a temp tree).
#
# Covers: dry-run (install + update variants) changing nothing, real install
# into a fresh dir, git-content match, idempotent re-run, in-place-edit
# correction (the ADR-0010 D1 "never hand-edited in place" invariant),
# basename preservation, atomic-install temp-file cleanup, missing-source
# loud failure, unknown-option rejection, --help, and that the default SRC
# resolves to the real in-tree bizzyboat polygon config.
#
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUT="$SCRIPT_DIR/deploy_datum_polygons.sh"
REAL_SRC="$SCRIPT_DIR/../bizzyboat_project11/config/massabesic_datum_polygons.yaml"

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

# A synthetic source keeps the behavioural tests independent of the real
# config's contents; a separate case below exercises the real default SRC.
SRC="$TMP/src/my_polygons.yaml"
mkdir -p "$TMP/src"
printf 'datum_polygons:\n  - name: "Test"\n    override: true\n    chart_datum_z: 1.0\n' > "$SRC"
DEST_DIR="$TMP/world/datum/user"
DEST="$DEST_DIR/my_polygons.yaml"

export SRC DEST_DIR

# --------------------------------------------------------------------------
echo "== dry run into a fresh dir changes nothing =="
out=$(bash "$SUT" --dry-run 2>&1); rc=$?
check "exits 0"                     [ "$rc" -eq 0 ]
check "announces install"           contains "$out" "would install"
check "creates no dest dir"         [ ! -e "$DEST_DIR" ]

echo "== real install into a fresh dir =="
out=$(bash "$SUT" 2>&1); rc=$?
check "exits 0"                     [ "$rc" -eq 0 ]
check "reports deployed"            contains "$out" "deployed"
check "created the user dir"        [ -d "$DEST_DIR" ]
check "basename preserved"          [ -f "$DEST" ]
check "content matches source"      cmp -s "$SRC" "$DEST"
check "no leftover temp files"      [ -z "$(find "$DEST_DIR" -name '.my_polygons.yaml.*' -print -quit)" ]

echo "== idempotent re-run is a no-op =="
out=$(bash "$SUT" 2>&1); rc=$?
check "exits 0"                     [ "$rc" -eq 0 ]
check "reports up to date"          contains "$out" "up to date"

echo "== dry run when already up to date =="
out=$(bash "$SUT" --dry-run 2>&1); rc=$?
check "exits 0"                     [ "$rc" -eq 0 ]
check "reports up to date"          contains "$out" "up to date"

echo "== in-place edit is corrected back to git (D1 invariant) =="
printf '\n# tampered in place\n' >> "$DEST"
out=$(bash "$SUT" --dry-run 2>&1)
check "dry-run flags the drift"     contains "$out" "would update"
out=$(bash "$SUT" 2>&1); rc=$?
check "exits 0"                     [ "$rc" -eq 0 ]
check "reports deployed"            contains "$out" "deployed"
check "restored to git content"     cmp -s "$SRC" "$DEST"

echo "== missing source fails loudly =="
out=$(SRC="$TMP/does_not_exist.yaml" bash "$SUT" 2>&1); rc=$?
check "exits non-zero"              [ "$rc" -ne 0 ]
check "names the missing file"      contains "$out" "does_not_exist.yaml"
check "explains source of truth"    contains "$out" "git is the source of truth"

echo "== argument handling =="
out=$(bash "$SUT" --frobnicate 2>&1); rc=$?
check "unknown option rejected"     [ "$rc" -ne 0 ]
out=$(bash "$SUT" --help 2>&1); rc=$?
check "help exits 0"                [ "$rc" -eq 0 ]
check "help shows usage"            contains "$out" "Usage:"

echo "== default SRC resolves to the real in-tree config =="
if [[ -f "$REAL_SRC" ]]; then
  # Unset SRC so the script's own default (SCRIPT_DIR-relative) is exercised.
  out=$(env -u SRC DEST_DIR="$TMP/real/user" bash "$SUT" 2>&1); rc=$?
  check "exits 0"                   [ "$rc" -eq 0 ]
  check "deployed the real config"  [ -f "$TMP/real/user/massabesic_datum_polygons.yaml" ]
  check "matches the git file"      cmp -s "$REAL_SRC" "$TMP/real/user/massabesic_datum_polygons.yaml"
else
  echo "  FAIL: real in-tree config missing at $REAL_SRC"; ((++FAIL))
fi

# --------------------------------------------------------------------------
echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
