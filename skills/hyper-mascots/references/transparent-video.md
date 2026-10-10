# Transparent browser video with local tools

Keep approved RGB video and its BiRefNet mask as sources. For motion plus speech,
mask the FINAL face-grafted composite, not either input clip. This is what keeps
color and alpha aligned as the character moves.

## Frame pipeline

1. Generate/download a mask with GenMedia’s verified BiRefNet video endpoint.
2. Extract RGB and mask frames with the same crop, padding and frame rate.
3. Use `scripts/matte.py` to keep body/eyes/props opaque and apply the selected
   per-frame outline. `all` keeps detached props; `captions` is a heuristic that
   can discard distant/bottom components and needs review.
4. Recombine the RGBA PNGs into the browser formats below. Audio is separate;
   silent character videos must not add a second voice track.

The included `scripts/alpha-clip.sh` handles the sequence, hash-checked mask cache,
optional fixed scale, exports and provenance JSON. Run from the installed skill
folder, with outputs in the app workspace:

```sh
MASCOT_PYTHON=/path/to/venv/bin/python MASCOT_KEEP=all \
  sh scripts/alpha-clip.sh planner ./clips/planner.mp4 ./web 320
```

macOS defaults to WebM and MOV. Other platforms default to WebM. Use
`MASCOT_FORMATS=webm` or `MASCOT_FORMATS=webm,mov` explicitly when useful.
MOV-with-alpha requires the macOS VideoToolbox encoder; requesting it on another
platform fails before generation instead of silently producing an opaque video.
Use `MASCOT_MASK=<local-mask.mp4>` for an offline rerender. Source timing and
extracted frame names must match; also inspect RGB/mask alignment visually.

## Chrome and Firefox: VP9 alpha WebM

Given RGBA PNG frames named `f_0001.png` onward:

```sh
ffmpeg -y -framerate 24 -i cut/f_%04d.png \
  -c:v libvpx-vp9 -pix_fmt yuva420p -auto-alt-ref 0 \
  -deadline good -cpu-used 4 -threads 2 -b:v 0 -crf 34 -an mascot.webm
```

Use `realtime`/cpu-used 8 only when speed matters and inspect the output. Do not
replace alpha with a black fill to accelerate encoding.

## Safari: HEVC alpha MOV (macOS)

```sh
ffmpeg -y -framerate 24 -i cut/f_%04d.png \
  -c:v hevc_videotoolbox -alpha_quality 0.75 -q:v 55 \
  -tag:v hvc1 -pix_fmt bgra -an mascot.mov
```

HEVC-with-alpha is an Apple-supported overlay format; the encoder’s alpha-quality
setting is essential. Ordinary HEVC or H.264 without an alpha layer is not an
interchangeable transparent export. See [Apple’s HEVC-alpha guide](https://developer.apple.com/documentation/avfoundation/using-hevc-video-with-alpha)
and [FFmpeg’s VideoToolbox alpha implementation](https://ffmpeg.org/pipermail/ffmpeg-devel/2021-February/276736.html).

## Playback and fallbacks

```html
<video muted playsinline loop poster="mascot.png">
  <source src="mascot.mov" type="video/quicktime">
  <source src="mascot.webm" type="video/webm">
</video>
```

This two-source order is the tested Safari/WebM pattern from the original app.
Test it in the actual deployment browsers and server: `.mov` and `.webm` need
correct media MIME types, and some artifact hosts do not serve MOV. A poster
PNG/WebP is the static/reduced-motion fallback. If the host cannot serve MOV,
use a compatible host or an explicit static fallback for Safari; do not claim an
unsupported transparent format will work. An H.264 MP4 preview can be flattened
onto a chosen background for sharing, but then it is intentionally opaque.

Verify alpha in a decoded WebM frame with libvpx (native VP9 decoding may omit it):

```sh
ffmpeg -y -c:v libvpx-vp9 -i mascot.webm -frames:v 1 alpha-check.png
ffprobe -v error -show_entries stream=codec_name,width,height -of json mascot.mov
```

`ffprobe` may report HEVC’s base color pixel format without exposing auxiliary
alpha; that alone does not prove transparency. Play the MOV in Safari over the
actual colored surface. Check dark facial regions remain solid, the edge is
consistent across the cycle, and no matte halo or clipped prop appears.

Offline helper checks use synthetic local clips and a GenMedia stub:

```sh
python scripts/smoke-test.py
```

The smoke suite verifies WebM everywhere and additionally HEVC on macOS. Install
Pillow, NumPy and SciPy into the interpreter that runs it. It never needs Fal
credentials or generation credits.
