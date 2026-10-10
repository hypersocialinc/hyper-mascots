#!/bin/sh
# alpha-clip.sh <name> <src.mp4> <out_dir> [size]
#
# Turn a generated clip (on black, 1:1) into transparent web video:
#   <out_dir>/<name>.webm  VP9 with alpha   (Chrome, Firefox)
#   <out_dir>/<name>.mov   HEVC with alpha  (Safari; needs macOS to encode)
#
# The character's mask comes from BiRefNet v2 (fal-ai/birefnet/v2/video, a
# fraction of a cent per clip), so the body is solid on every frame.
# MASCOT_STYLE=outline (default) or glow (for an explicitly dark finish).
# MASCOT_KEEP=all for idles; captions (default) for lip-sync output.
# MASCOT_FORMATS=webm,mov on macOS; webm by default elsewhere.
# Still images use matte.py directly with an image mask.
#
# The generic crop preserves the full frame. Choose a family crop when
# removing burned captions or fitting wider props.
set -e
if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  echo 'usage: alpha-clip.sh <name> <clip.mp4> <out_dir> [size]' >&2
  exit 2
fi
HERE=$(cd "$(dirname "$0")" && pwd)
NAME=$1; SRC=$2; OUT=$3; SIZE=${4:-320}
PY=${MASCOT_PYTHON:-${ORBIE_PYTHON:-python3}}; STYLE=${MASCOT_STYLE:-${ORBIE_STYLE:-outline}}
KEEP=${MASCOT_KEEP:-${ORBIE_KEEP:-captions}}
SPEED=${MASCOT_ENCODE_SPEED:-${ORBIE_ENCODE_SPEED:-quality}}
CROP=${MASCOT_CROP:-${ORBIE_CROP:-crop=iw:ih:0:0}}
MASK_OVERRIDE=${MASCOT_MASK:-${ORBIE_MASK:-}}
REFRESH=${MASCOT_REFRESH_MASK:-${ORBIE_REFRESH_MASK:-0}}
FORMATS=${MASCOT_FORMATS:-}
if [ -z "$FORMATS" ]; then
  if [ "$(uname -s)" = Darwin ]; then FORMATS=webm,mov; else FORMATS=webm; fi
fi
case "$FORMATS" in webm|mov|webm,mov|mov,webm) ;; *) echo 'MASCOT_FORMATS must be webm, mov, or webm,mov' >&2; exit 2 ;; esac
case "$FORMATS" in *mov*) if [ "$(uname -s)" != Darwin ]; then echo 'HEVC alpha MOV requires macOS VideoToolbox; select MASCOT_FORMATS=webm here' >&2; exit 2; fi ;; esac
WORK=$(mktemp -d)
cleanup() {
  status=$?
  if [ "$status" -eq 0 ]; then rm -rf "$WORK";
  else echo "alpha export failed; diagnostics retained in $WORK" >&2; fi
}
trap cleanup EXIT
mkdir -p "$WORK/raw" "$WORK/mask" "$WORK/cut" "$OUT"
CACHE=${MASCOT_CACHE_DIR:-${ORBIE_CACHE_DIR:-$(dirname "$SRC")/.mascot-mask-cache}}
mkdir -p "$CACHE"
DIGEST=$("$PY" -c 'import hashlib,sys; h=hashlib.sha256(); f=open(sys.argv[1],"rb"); [h.update(b) for b in iter(lambda:f.read(1024*1024),b"")]; print(h.hexdigest())' "$SRC")
CACHED_MASK=$CACHE/$DIGEST.mp4
if [ -n "$MASK_OVERRIDE" ]; then
  MASK=$MASK_OVERRIDE
  MASK_ORIGIN=override
  RESPONSE=
elif [ "$REFRESH" != 1 ] && [ -s "$CACHED_MASK" ] && "$PY" - "$CACHED_MASK" "$CACHE/$DIGEST.json" "$DIGEST" <<'PYCACHE'
import hashlib,json,sys
try:
    mask,response,digest=sys.argv[1:];record=json.load(open(response))
    actual=hashlib.sha256(open(mask,"rb").read()).hexdigest()
    assert record["source_sha256"]==digest and record["mask_sha256"]==actual
except (OSError,ValueError,KeyError,AssertionError):sys.exit(1)
PYCACHE
then
  MASK=$CACHED_MASK
  MASK_ORIGIN=cache
  RESPONSE=$CACHE/$DIGEST.json
else
  genmedia upload "$SRC" --json > "$WORK/upload.json"
  URL=$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["cdn_url"])' "$WORK/upload.json")
  genmedia run fal-ai/birefnet/v2/video --video_url "$URL" --output_mask true --download "$WORK/" --json > "$WORK/bn.json"
  MASK=$("$PY" - "$WORK/bn.json" <<'PYJSON'
import json,sys
path=sys.argv[1]
try:
    d=json.load(open(path)); url=d["result"]["mask_video"]["url"]
    print(next(x["path"] for x in d["downloaded_files"] if x["url"] == url))
except (ValueError,KeyError,TypeError,StopIteration) as error:
    raise SystemExit(f"Expected result.mask_video.url and matching downloaded_files in {path}: {error}")
PYJSON
)
  cp "$MASK" "$CACHED_MASK.tmp.$$"
  mv "$CACHED_MASK.tmp.$$" "$CACHED_MASK"
  "$PY" - "$WORK/bn.json" "$CACHED_MASK" "$DIGEST" "$CACHE/$DIGEST.json.tmp.$$" <<'PYRECORD'
import hashlib,json,sys
response,mask,digest,out=sys.argv[1:];data=json.load(open(response))
record={"source_sha256":digest,"mask_sha256":hashlib.sha256(open(mask,"rb").read()).hexdigest(),
        "request_id":data.get("request_id"),"endpoint":"fal-ai/birefnet/v2/video"}
with open(out,"w") as file:json.dump(record,file,indent=2)
PYRECORD
  mv "$CACHE/$DIGEST.json.tmp.$$" "$CACHE/$DIGEST.json"
  MASK=$CACHED_MASK
  MASK_ORIGIN=fetched
  RESPONSE=$CACHE/$DIGEST.json
fi
if [ ! -s "$MASK" ]; then echo "Missing mask video: $MASK" >&2; exit 2; fi
"$PY" - "$SRC" "$MASK" <<'PYALIGN'
import json,subprocess,sys
from fractions import Fraction

def probe(path):
    d=json.loads(subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=avg_frame_rate,nb_frames,duration:format=duration","-of","json",path]))
    stream=d["streams"][0]
    rate=float(Fraction(stream.get("avg_frame_rate","24/1")))
    duration=float(stream.get("duration",d["format"].get("duration",0)))
    return duration,rate,stream.get("nb_frames")
a,b=probe(sys.argv[1]),probe(sys.argv[2])
if abs(a[0]-b[0])>max(1/max(a[1],1),1/max(b[1],1),.03)*1.5:
    raise SystemExit(f"Source/mask durations differ ({a[0]:.3f}s vs {b[0]:.3f}s); supply the matching mask")
if a[2] and b[2] and a[2]!=b[2]:
    print(f"WARNING: source/mask frame counts differ ({a[2]} vs {b[2]}); review timing before accepting export",file=sys.stderr)
PYALIGN
# MASCOT_CROP overrides the crop for a wider subject (a group of characters).
VF="$CROP,fps=24,scale=$SIZE:$SIZE:force_original_aspect_ratio=decrease,pad=$SIZE:$SIZE:(ow-iw)/2:(oh-ih)/2:color=black"
ffmpeg -v error -y -i "$SRC" -vf "$VF" "$WORK/raw/f_%04d.png"
ffmpeg -v error -y -i "$MASK" -vf "$VF" "$WORK/mask/f_%04d.png"
# Normalize against the same pose/props, or apply an explicitly measured scale.
REFERENCE_SOURCE=${MASCOT_REFERENCE_MASK:-${ORBIE_REFERENCE_MASK:-}}
REFERENCE=$REFERENCE_SOURCE
SCALE=${MASCOT_SCALE:-${ORBIE_SCALE:-}}
if [ -n "$REFERENCE" ]; then
  ffmpeg -v error -y -i "$REFERENCE" -vf "$VF" -frames:v 1 "$WORK/reference.png"
  REFERENCE=$WORK/reference.png
fi
if [ -n "$REFERENCE" ] || [ -n "$SCALE" ]; then
  "$PY" "$HERE/normalize-frames.py" "$WORK/raw" "$WORK/mask" "${REFERENCE:--}" "${SCALE:-auto}" "$KEEP" > "$WORK/normalization.json"
else
  echo '{"scale":1,"reference_scale":1,"manual_scale":1,"max_clipped_mask_pixels":0}' > "$WORK/normalization.json"
fi
"$PY" "$HERE/matte.py" "$WORK/raw" "$WORK/mask" "$WORK/cut" "$STYLE" "$KEEP" > "$WORK/matte.json"
case "$SPEED" in
  quality) DEADLINE=good; CPU_USED=4 ;;
  fast) DEADLINE=realtime; CPU_USED=8 ;;
  *) echo 'MASCOT_ENCODE_SPEED must be quality or fast' >&2; exit 2 ;;
esac
case "$FORMATS" in
  *webm*) ffmpeg -v error -y -framerate 24 -i "$WORK/cut/f_%04d.png" -c:v libvpx-vp9 -pix_fmt yuva420p -auto-alt-ref 0 -deadline "$DEADLINE" -cpu-used "$CPU_USED" -threads 2 -b:v 0 -crf 34 -an "$OUT/$NAME.webm" ;;
esac
case "$FORMATS" in
  *mov*) ffmpeg -v error -y -framerate 24 -i "$WORK/cut/f_%04d.png" -c:v hevc_videotoolbox -alpha_quality 0.75 -q:v 55 -tag:v hvc1 -pix_fmt bgra -an "$OUT/$NAME.mov" ;;
esac
"$PY" - "$SRC" "$MASK" "$OUT" "$NAME" "$SIZE" "$STYLE" "$KEEP" "$SPEED" "$DIGEST" "$RESPONSE" "$CROP" "$WORK/normalization.json" "$REFERENCE_SOURCE" "$MASK_ORIGIN" "$WORK/matte.json" "$FORMATS" <<'PYMANIFEST'
import hashlib,json,os,sys
source,mask,out,name,size,style,keep,speed,digest,response,crop,normalization,reference,origin,matte_stats,formats=sys.argv[1:]
request_id=json.load(open(response)).get("request_id") if response and os.path.isfile(response) else None
data={"version":1,"source":os.path.relpath(source,out),"source_sha256":digest,
      "mask":os.path.relpath(mask,out),"mask_endpoint":"fal-ai/birefnet/v2/video",
      "mask_request_id":request_id,"mask_origin":origin,
      "mask_sha256":hashlib.sha256(open(mask,"rb").read()).hexdigest(),"crop":crop,"size":int(size),"fps":24,
      "finish":style,"keep_mode":keep,"encoding":speed,"ink":os.environ.get("MASCOT_INK","#0B0B0F"),"formats":formats.split(","),"matte":json.load(open(matte_stats)),
      "normalization":json.load(open(normalization)),
      "reference_mask":os.path.relpath(reference,out) if reference else None,
      "reference_mask_sha256":hashlib.sha256(open(reference,"rb").read()).hexdigest() if reference else None}
with open(os.path.join(out,name+".json"),"w") as file: json.dump(data,file,indent=2); file.write("\n")
PYMANIFEST
echo "Exported $FORMATS; settings: $OUT/$NAME.json"
