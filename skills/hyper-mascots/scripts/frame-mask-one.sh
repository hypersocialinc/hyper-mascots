#!/bin/sh
# frame-mask-one.sh <frame.png> — one frame's BiRefNet v2 mask, written beside
# the frames as ../maskfull/<same name>. Called in parallel by frame-masks.sh.
# Three attempts; a frame with no mask fails the whole export.
set -e
FRAME=$1; DIR=$(cd "$(dirname "$FRAME")/.." && pwd); BASE=$(basename "$FRAME" .png)
PY=${MASCOT_PYTHON:-${ORBIE_PYTHON:-python3}}
JOB=$DIR/jobs/$BASE; mkdir -p "$JOB"
for attempt in 1 2 3; do
  if genmedia upload "$FRAME" --json > "$JOB/upload.json" 2> "$JOB/upload.err" \
     && URL=$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["cdn_url"])' "$JOB/upload.json") \
     && genmedia run fal-ai/birefnet/v2 --image_url "$URL" --output_mask true --download "$JOB/" --json > "$JOB/bn.json" 2> "$JOB/bn.err" \
     && MASK=$("$PY" -c '
import json,sys
d=json.load(open(sys.argv[1])); url=d["result"]["mask_image"]["url"]
print(next(x["path"] for x in d["downloaded_files"] if x["url"]==url))' "$JOB/bn.json") \
     && [ -s "$MASK" ]; then
    cp "$MASK" "$DIR/maskfull/$BASE.png"; exit 0
  fi
  sleep "$attempt"
done
echo "no mask for $BASE after 3 attempts; see $JOB" >&2
exit 1
