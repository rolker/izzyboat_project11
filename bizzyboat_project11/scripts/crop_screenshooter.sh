#!/usr/bin/env bash
# Crop a region out of an operator screenshooter time-lapse and burn the real
# per-frame wall-clock timestamp (from the sidecar CSV) onto each frame, so
# frames trace back to bag data. UTC is shown (matches ROS message epoch) plus
# EDT in parens (matches local-time bag dir names like operator_...T14.21.16).
#
# Usage:  crop_screenshooter.sh <YYYY-MM-DD> [region]
#   region = a named preset (default: middle) or a raw ffmpeg crop "w:h:x:y".
#
# Presets (tuned to the 3840x5760 3-monitor stack; re-check per deployment if
# the operator monitor layout changes):
#   middle      annunciator + CAMP/chart + camera grid + segmentation + the
#               bottom sidescan waterfall (terminals flank it). 3840:2250:0:2000
#   top-middle  the above PLUS the top screen above it.            3840:4250:0:0
#
# Source (from ccomjhc_project11/scripts/screenshooter.bash):
#   ~/data/logs/operator/<date>/screenshots/operator_<date>.{mp4,csv}
#   CSV cols: frame_index,timestamp(YYYY-MM-DDTHH-MM-SS, UTC),filename
#   Output video is 2 fps -> each frame == 0.5 s of timeline.
set -euo pipefail

DATE="${1:?usage: crop_screenshooter.sh <YYYY-MM-DD> [region]}"
REGION="${2:-middle}"
FPS=2
UTC_OFFSET_HOURS=-4   # EDT (June). Use -5 for EST outside DST.

# --- resolve region preset -> ffmpeg crop w:h:x:y ---
case "$REGION" in
  middle)                            CROP="3840:2250:0:2000" ;;
  top-middle|middle-top|top+middle)  CROP="3840:4250:0:0" ;;
  *:*:*:*)                           CROP="$REGION" ;;   # raw w:h:x:y override
  *) echo "unknown region '$REGION' (use: middle | top-middle | w:h:x:y)" >&2; exit 1 ;;
esac
TAG="$(echo "$REGION" | tr ':+' '__')"

SRCDIR="$HOME/data/logs/operator/$DATE/screenshots"
MP4="$SRCDIR/operator_$DATE.mp4"
CSV="$SRCDIR/operator_$DATE.csv"
OUTDIR="$HOME/data/logs/analysis/${DATE}_screenshooter_crop"
ASS="$OUTDIR/operator_${DATE}_${TAG}_timestamps.ass"
OUT="$OUTDIR/operator_${DATE}_${TAG}_ts.mp4"

[[ -f "$MP4" ]] || { echo "missing video: $MP4" >&2; exit 1; }
[[ -f "$CSV" ]] || { echo "missing CSV:   $CSV" >&2; exit 1; }
mkdir -p "$OUTDIR"

# --- ASS subtitle from CSV (explicit PlayRes -> predictable font size) ---
python3 - "$CSV" "$ASS" "$FPS" "$UTC_OFFSET_HOURS" "$CROP" <<'PY'
import csv, sys, datetime
csvpath, asspath, fps, off, crop = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
w, h = crop.split(":")[0], crop.split(":")[1]
frame_s = 1.0 / fps
def ass_t(t):
    cs = int(round(t * 100)); hh, cs = divmod(cs, 360000); mm, cs = divmod(cs, 6000); ss, cs = divmod(cs, 100)
    return f"{hh:d}:{mm:02d}:{ss:02d}.{cs:02d}"
rows = list(csv.DictReader(open(csvpath)))
# Alignment 1 = bottom-left (clear of the annunciator panel in the top-left).
hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ts,DejaVu Sans Mono,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,3,0,0,1,30,30,25,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
with open(asspath, "w") as f:
    f.write(hdr)
    for i, row in enumerate(rows):
        dt = datetime.datetime.strptime(row["timestamp"], "%Y-%m-%dT%H-%M-%S")
        loc = dt + datetime.timedelta(hours=off)
        text = f"{dt:%Y-%m-%d %H:%M:%S} UTC ({loc:%H:%M:%S} EDT)"
        f.write(f"Dialogue: 0,{ass_t(i*frame_s)},{ass_t((i+1)*frame_s)},ts,,0,0,0,,{text}\n")
print(f"wrote {len(rows)} ASS events -> {asspath}")
PY

# --- crop + burn timestamp + re-encode ---
ffmpeg -hide_banner -loglevel warning -stats -i "$MP4" \
  -vf "crop=${CROP},subtitles='${ASS}'" \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p -r "$FPS" \
  "$OUT" -y

echo "==> region=$REGION crop=$CROP"
echo "==> $OUT"
ls -la "$OUT"
