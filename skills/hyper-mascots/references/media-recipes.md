# Mascot media recipes

Commands run from the installed skill folder; outputs belong in the application
workspace. Set an absolute output path when those folders differ. Models/schemas
are checked at execution time. No keys/tokens belong in manifests or output.

## Art and role variants

Inspect the full-resolution source, then upload the authorized reference with
`genmedia upload <source.png> --json`; the upload returns `cdn_url`.
The existing family was edited with `google/nano-banana-2.1/edit`.
`openai/gpt-image-2/edit` is another proven reference-editing candidate.

```sh
genmedia models --endpoint_id google/nano-banana-2.1/edit --json
genmedia schema google/nano-banana-2.1/edit --json
genmedia run google/nano-banana-2.1/edit \
  --image_urls '["<reference CDN URL>"]' \
  --prompt '<requested role change; preservation instructions>' \
  --download './output/source/<role>.{ext}' --json
```

Useful prompt shape: “Use this exact character family. Give the character
[one role prop and pose]. Preserve its face, silhouette, distinctive materials,
linework, palette, expression, and framing except for the requested change. Keep the prop large enough to read at the final card size.
Plain near-black background, no text or logos.” Do not ask for text-only recreation
of an existing mascot. Provider logos are separate SVG/text labels, not redrawn
by an image model.

For still cutouts, verify `fal-ai/birefnet/v2`, request a mask, download it with
GenMedia, and place the RGB still and grayscale mask in separate folders with
the same filename. Then use the existing matte tool:

```sh
"$MASCOT_PYTHON" scripts/matte.py \
  ./frames ./masks ./web outline all
```

Use the final argument `all` for stills and idle assets with detached props.
The default `captions` mode heuristically filters distant/bottom components for
lip-sync output and can remove legitimate props.

It writes transparent PNGs. Keep the approved RGB original and mask for reuse.
Use a separate outline/glow export instead of replacing the original. Inspect
long tools, books, phones, or other detached props: the matte tool filters distant
components, so a prop may need a better mask or a narrowly adjusted keep region.
Do not silently discard it.

## Idle, hover and state loops

Generate every motion clip with `minimax/h3-max/image-to-video` (H3 Max). Do not
use Kling, and do not use `minimax/h3-max-turbo/*` for a final asset: Turbo is the
draft tier and is visibly softer. The earlier pal and role loops were made with
`fal-ai/kling-video/v2.5-turbo/pro/image-to-video`; that recipe is retired
because it smeared thin lines such as orbit rings.

**A loop needs a first frame AND a last frame.** Pass the still as `image_url`
(first frame) and as `end_image_url` (last frame):

- a seamless loop (idle, hover, working): the SAME still URL for both;
- a transition (rings appear, a bubble pops in): the starting still as
  `image_url` and the ending still as `end_image_url`. Play it backwards with
  FFmpeg for the reverse transition instead of generating it twice.

Without `end_image_url` the clip drifts and will not loop. `genmedia schema`
returns null for this endpoint; these inputs were read on 2026-10-10 from
`https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=minimax/h3-max/image-to-video`.
Re-read that page if a field is refused:

| Input | Value |
|---|---|
| `image_url` | first frame |
| `end_image_url` | last frame |
| `prompt` | required |
| `prompt_expansion_mode` | required; `disabled` keeps the prompt as written, `balanced` is the default |
| `duration` | seconds, default 5; output can run about 0.7 s longer, so trim to the loop |
| `resolution` | `480P`, `768P` or `1080P`; use `1080P` |
| `seed` | optional; record the one used |

```sh
genmedia run minimax/h3-max/image-to-video \
  --image_url '<first-frame still CDN URL>' --end_image_url '<last-frame still CDN URL>' \
  --prompt '<loop prompt>' --prompt_expansion_mode disabled \
  --duration 5 --resolution 1080P --async --json
genmedia status minimax/h3-max/image-to-video \
  '<request ID>' --download './output/clips/' --json
```

Prompt shape that worked for the pals: one small action involving the role's own
prop, then "It stays centred and the same size and colours. Its mouth stays in a
small smile. Locked-off camera: no zoom, no push-in. Plain black background,
nothing else appears, no text. Seamless loop that ends exactly as it starts."
Say how the shot ends. One representative loop is enough to judge the family's
motion style before generating all roles.

The first/last constraint reduces seams; inspect the actual loop boundary. A
large turn, strong bounce, or added objects may change the silhouette or zoom
the character.

## A state set for an agent mascot

The set the HyperCoder owner settled on 2026-10-10, after rejecting quieter
versions. Each state is its own clip; the page swaps clips, it does not draw.

| State | Clip | First frame, last frame |
|---|---|---|
| Rest | calm bob and blink, no orbit rings | ring-free still, same still |
| Hover reaction | lights up, hops, rings whoosh in; play at about 1.8x so it lands in under 3 s | ring-free still, ringed still |
| Hover loop | bouncing, rings whirling; plays while the pointer stays | ringed still, same still |
| Rings leave | the hover reaction or a rings-in clip reversed with FFmpeg | (no generation) |
| Working | the role USES ITS PROP, visibly and at an energetic pace, rings spinning | working still, same still |
| Done, not seen | a speech bubble pops in and holds; no rings | ring-free still, bubble still |

- Rings mean "active". They appear on hover and while working, and are gone at
  rest and when done. Make a ring-free still by editing the approved still.
- Working: make a working still first (the prop in use, e.g. a marker with its
  tip on the map), then loop from it. Ask for marks that clear by the end so the
  loop closes. A big, clearly coloured prop moving fast was preferred; a small or
  slow one read as idle or was invisible at pill size.
- Hover must feel like a reaction, not a fade. A 5 s gentle transition was
  called lame; the fix was an excited clip, sped up, plus a CSS pop on entry.
- Measure before claiming a loop is calm or busy: mean frame-to-frame change at
  the real display size (28 px for a pill) settles it. Check each loop's
  last-to-first frame difference against its normal frame step, and each
  handoff between clips the same way.

## Voice and speaking clips

Choose the app’s voice. The ElevenLabs helper requires `MASCOT_VOICE` and uses
neutral pitch/tempo by default. `MASCOT_RATE_MULTIPLIER` and `MASCOT_TEMPO` can
apply a chosen character treatment. The HyperCoder preset records its Jessica
voice/pitch separately. ElevenLabs is the only speech
provider in this workflow.

```sh
MASCOT_VOICE='<chosen ElevenLabs voice>' \
  scripts/voice-line.sh ./output/voice/intro.mp3 \
  '[cheerful] Here are some people using the app.'
```

Verify `elevenlabs/tts/eleven-v4` before using the helper. Short section intros can
be about 3–5 seconds; a full tour explanation can be longer. Keep the established
voice and conversational phrasing, not a generic marketing paragraph.

Speech is always two steps: the voice line from ElevenLabs
(`scripts/voice-line.sh`, above), then `minimax/h3-max/lip-sync/image-to-video`
with that audio. Do not use another lip-sync model, and do not use H3 Max Turbo
with `target_audio_url` for speech: it only loosely follows the audio. The
lip-sync endpoint takes no prompt and no last frame; its inputs (read
2026-10-10 from the same OpenAPI page) are `image_url`, `audio_url`,
`resolution` (`480P`, `768P`, `1080P`, `2K`), `enable_transcription` and `seed`.
Audio must be at least five seconds: pad a shorter recording with silence for
generation, then trim the final clip to the spoken line. `enable_transcription
true` gave the tightest sync in another project but can write the spoken words
into empty parts of the frame; start with `false`, switch it on if sync is
loose, and inspect every take for burned-in text either way. Unsupported fields
may be silently ignored, so do not invent "no subtitles" API options.

```sh
ffmpeg -y -i ./output/voice/intro.mp3 -af apad -t 5.2 \
  ./output/voice/intro-lipsync.wav
genmedia run minimax/h3-max/lip-sync/image-to-video \
  --image_url '<approved source still CDN URL>' \
  --audio_url '<padded audio CDN URL>' --resolution 768P \
  --enable_transcription false --async --json
genmedia status minimax/h3-max/lip-sync/image-to-video \
  '<request ID>' --download './output/clips/' --json
```

Lip sync can freeze the body or fail on a moving cartoon. When the clip needs
role-specific motion as well as speech, generate motion and mouth footage from
the same still and use `scripts/mouth-graft.py`. Inspect that
script’s CLI and the worked car example in the optional HyperCoder preset; eye/mouth positions
are character-specific and must be measured. It pastes a tracked face onto a
moving body. Check multiple face crops for drift or cut-off features. The working
car sequence used 24fps 768 × 768 body/talk frames, then x264 CRF 16 for the
composite. Compute the BiRefNet mask from that FINAL composite, not either input;
otherwise the talking face and its alpha can disagree. Eye coordinates are
specific to each source; the recorded car example was `328,362 435,361 383,406`.
Record the measured coordinates and review tracking offsets for false locks.

## Transparent video export

For idle and state loops, set `MASCOT_KEEP=all` in the export invocation; for talking clips
use `captions` only when its prop-removal heuristic is appropriate.

Install `pillow numpy scipy` into a temporary or ignored virtual environment and
set `MASCOT_PYTHON` to that interpreter. `ffmpeg` is required; HEVC alpha encoding
uses macOS VideoToolbox. Masks come from `fal-ai/birefnet/v2` on every frame (the
default); see [transparent video](transparent-video.md).
The helper requests a BiRefNet mask video for the final raw MP4, then extracts
both streams with identical crop, padding, and 24fps. It preserves non-square crop
aspect ratio with letterboxing instead of squashing the character.

Masks are cached by raw-source SHA-256 beside the source in `.mascot-mask-cache/`
(ignored by Git), independently of the export folder. An explicit `MASCOT_MASK`
rerenders locally without GenMedia; `MASCOT_CACHE_DIR` overrides the cache location.
`MASCOT_REFRESH_MASK=1` explicitly refreshes it. Cache hashes are checked and writes
are atomic. A timing check and exact extracted frame-name matching catch duration /
count mismatch, but do not prove a caller-supplied mask’s spatial alignment.
Inspect aligned first/middle/last RGB/mask samples. Archive approved masks as
source files deliberately if a fresh checkout must rerender exactly offline.

```sh
MASCOT_PYTHON=/path/to/venv/bin/python MASCOT_STYLE=outline MASCOT_KEEP=all \
  scripts/alpha-clip.sh \
  role-planner-ink ./output/clips/planner.mp4 ./output/web 240
```

The default export is a 320px square canvas and a full-frame crop. Choose the
frame/crop for this app; the HyperCoder preset records its 240/320px sizes and
caption-removal crop. Cropping can remove burned text but must preserve props.
Set `MASCOT_CROP` when a prop or group needs different framing. Apply exactly the
same crop and frame rate to raw video and mask. If the shape changes size between
clips, fix the crop against the approved asset’s visible bounds before changing
CSS. Outline adds ink around the final per-frame silhouette, including orbit rings
and retained props. It must be part of every state’s asset, not only the cover
still or a drop shadow behind the video element. Keep the same ink color and
apparent width across idle/hover/talk clips; normalize crop/scale before matting
so the edge does not thicken or thin when a clip changes. Test it over the actual
overlapped object (headline card, app window, illustration), including mid-flight.
Glow keeps soft transparency only for an explicitly dark presentation; cropping
or outlining an unremoved glow previously produced a fuzzy halo.

Quality encoding is the default (`good`, cpu-used 4, two threads).
Use `MASCOT_ENCODE_SPEED=fast` (`realtime`, cpu-used 8) only when encoding is slow,
then inspect the small-scale result. Preserve `yuva420p`; do not turn
alpha into an opaque black rectangle to speed it up.

## Integration and checks

```html
<video muted playsinline loop poster="role.png">
  <source src="role.mov" type="video/quicktime">
  <source src="role.webm" type="video/webm">
</video>
```

The existing two-source order is part of the site’s browser compatibility
contract. Keep the still/previous clip visible until the next video actually
plays, synchronize muted speaking footage to the separate audio, and pause
hidden/offscreen idles. Respect reduced motion with a still. Sound is opt-in;
share mute state across surfaces and stop outgoing audio before starting another.
For section navigation, reverse the same travel path when going back, and replay
an intro on a real section re-entry without triggering on every scroll event.

Keep motion effects (travel, sparkles, hover lift) in the application layer.
The optional HyperCoder preset points to its original example when working in
that project. Do not copy mockup global timers as production visibility policy.

### Scale and provenance

Use `MASCOT_REFERENCE_MASK=<source-still-mask.png>` to normalize a clip against its
OWN source pose/props under the same crop/padding. The fixed reference scale is
`sqrt(reference_foreground_area / frame0_foreground_area)`, measured after the
selected keep filter; differences within 3% area are left alone to avoid blur.
This is a silhouette-area estimate, not semantic body measurement across roles.
`MASCOT_SCALE=<manual factor>` multiplies the reference scale for a per-pose visual
correction. Both factors are recorded separately, along with frame area ratios,
centroid offset, clipping/edge warnings, mask origin/hash and frame count. A
varying area warns about drift; it does not rescale every frame or remove intended
squash/stretch. The tool records centroid offset but does not automatically move
faces or props. Inspect the resulting framing at the intended display size.

Every video export writes `<name>.json` beside the served `.mov` and `.webm` with
local source paths/hashes, mask provenance, crop, finish, keep mode, encoding, and
normalization. It contains no credentials. Keep a family generation manifest
beside raw sources as well; the export record cannot invent the generation prompt:

```json
{
  "version": 1,
  "family": "agent-roles",
  "reference": "source/neutral-pal.png",
  "assets": [{
    "name": "planner",
    "source": "source/planner.png",
    "kind": "idle",
    "generation": {
      "endpoint": "minimax/h3-max/image-to-video",
      "prompt": "Exact successful prompt recorded after generation",
      "request_id": "Provider request ID recorded after generation"
    },
    "raw_clip": "clips/planner.mp4",
    "export_record": "web/planner-ink.json"
  }]
}
```

Use a versioned output name when replacing an approved recording/clip if the
browser would cache the old file; record why it changed (voice, crop, face graft,
finish), not just a suffix. Avoid a generated schema-discovery request to find
unsupported fields. Loop-tail equality is not proof of a seam: compare the final
step with ordinary frame-to-frame motion; do not automatically drop the last
frame. A short end blend or calmer regeneration may be needed.

Verify representative beginning/middle/end frames and first/last loop frames on
the destination surfaces. Dark eyes/body parts must stay opaque,
props and rings must survive, and foreground size must match idle/speaking stills.
Use actual browser playback for autoplay/mute/navigation behavior. Report whether
you heard the voice and watched a complete loop; a contact sheet alone does not
verify audio quality or a seamless loop.
