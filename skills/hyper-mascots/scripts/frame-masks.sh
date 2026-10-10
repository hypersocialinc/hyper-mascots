#!/bin/sh
# frame-masks.sh <clip.mp4> <mask.mp4> <work_dir>
#
# The mask for a clip, made the way the transparent Hype clips were made: every
# frame goes to BiRefNet v2 (the IMAGE model, fal-ai/birefnet/v2) on its own, many
# at once, and FFmpeg puts the mask frames back together as a video in the
# source's frame order. The image model judges each frame at full resolution, so
# thin parts (orbit rings, a pencil tip) survive where the video endpoint drops them.
# MASCOT_MASK_JOBS (default 8) is how many frames run at once.
set -e
SRC=$1; OUT=$2; WORK=$3
HERE=$(cd "$(dirname "$0")" && pwd)
JOBS=${MASCOT_MASK_JOBS:-8}
mkdir -p "$WORK/src" "$WORK/maskfull" "$WORK/jobs"
ffmpeg -v error -y -i "$SRC" -vf fps=24 "$WORK/src/f_%04d.png"
N=$(ls "$WORK/src" | wc -l | tr -d ' ')
ls "$WORK/src"/f_*.png | xargs -n 1 -P "$JOBS" sh "$HERE/frame-mask-one.sh"
M=$(ls "$WORK/maskfull" | wc -l | tr -d ' ')
if [ "$N" != "$M" ]; then echo "frame masks incomplete: $M of $N" >&2; exit 1; fi
ffmpeg -v error -y -framerate 24 -i "$WORK/maskfull/f_%04d.png" -c:v libx264 -crf 10 -pix_fmt yuv420p -an "$OUT"
echo "$N" > "$WORK/mask-frames.txt"
