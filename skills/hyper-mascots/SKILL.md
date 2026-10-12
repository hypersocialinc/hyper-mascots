---
name: hyper-mascots
description: Create reference-consistent application mascots, role variants, idle and speaking animations, and transparent browser assets through the GenMedia CLI. Use for app mascots and guides; ordinary testimonial portraits are outside this workflow.
---

# Hyper Mascots

A portable GenMedia workflow skill for application mascots. Keep a character’s
identity, style, apparent size, and contrast consistent across still, idle, hover,
speaking, and transition states. GenMedia handles model discovery, generation,
uploads, queues, pricing, and downloads; the included local scripts prepare masks,
normalize frames, and export browser assets. This is a skill extension, not an
unimplemented `genmedia mascots` CLI command.

## Start with the application’s character

Use the app’s approved reference, visual style, palette, voice, destination
surfaces, and display size. Do not impose Hype’s appearance or voice on another
app. Establish a neutral base before role siblings; derive each role directly
from it instead of chaining edits. Generate and inspect one representative asset
before expanding a batch. Choose the needed tier: still for small cards, idle /
hover motion when useful, speaking for a readable guide, motion plus face graft
only when necessary.

For HyperCoder/Hype specifically, read [the optional preset](references/presets/hypercoder.md).
It contains project-specific settings but no copyrighted character artwork.

Read only the references relevant to the task:
- [Media recipes](references/media-recipes.md): art, role variants, idle loops,
  voice, and motion-plus-face-graft workflows.
- [Transparent browser video](references/transparent-video.md): local FFmpeg,
  BiRefNet masks, HEVC alpha MOV for Safari, VP9 alpha WebM for Chrome/Firefox,
  static fallbacks, and format verification.
- [Playback and lessons](references/playback-and-lessons.md): state transitions,
  one voice owner, cancellation tokens, and preventing mixed or stale lines.
- [Checking a take](references/clip-checks.md): the faults to look for in every
  generated clip before it is kept, what to measure, and how to calibrate.

## Execute through GenMedia

Use `genmedia models`, `schema`, `pricing`, `upload`, `run`, and `status` rather
than a second provider implementation. Load the core GenMedia skill when it is
installed; otherwise use `genmedia --help` plus these recipes. Respect an explicitly
chosen provider/model; these helpers target Fal-hosted GenMedia endpoints.
Verify candidate IDs and inspect schemas before custom inputs. If schema returns
null inputs/outputs, use the official API page or `genmedia docs`; do not guess
fields or use an unknown-flag request as a supposedly free probe. Parse `--json`,
save media with `--download`, and queue long jobs with `--async`.

## Preserve the family and finish

Preserve the approved reference’s face, silhouette, palette, materials, linework,
and unrelated details while making the requested change. Keep raw sources and
successful prompts. Condition idle loops with the same first and last still,
small motion, and a locked camera. Use CSS for element travel/lean/stretch; video
supplies internal body, expression and prop motion.

Motion clips come from `minimax/h3-max/image-to-video`, always with a first
frame (`image_url`) and a last frame (`end_image_url`): the same still for a
loop, two stills for a transition. Speech is an ElevenLabs voice line fed to
`minimax/h3-max/lip-sync/image-to-video`. Do not use Kling or H3 Max Turbo for a
final asset. Write prompts as what is in the shot, never as what is absent.

Remove backgrounds with BiRefNet v2 on EVERY FRAME in parallel and recompose
with FFmpeg (`scripts/alpha-clip.sh` does this by default), then the included
`scripts/matte.py`; never a brightness-only cutout, and not the one-call video
mask for a final asset. Preserve dark facial/body regions, orbit details, and detached props.
Match a clip with its OWN source pose/props after the same crop; silhouette area
is not semantic body alignment across unlike roles. Record fixed reference and
manual scale separately; do not normalize every frame and erase intended motion.

Choose a consistent per-frame edge treatment against every surface and object
crossed during the cycle. An ink outline can provide contrast; configure its color
and width for the app and keep apparent width consistent between states. Generate
it from the final silhouette, rather than a fuzzy glow or only a box shadow.
Glow requires an explicitly dark presentation. Do not add a halo, disc, or speech
bubble unless requested. Check the cycle at the actual display scale.

## Deliver reproducible assets

Reuse existing upload/generation authorization and report batch cost estimates,
including discarded variants. Explain a blocked upload and obtain permission for
that asset; never substitute a different result and claim it is the requested one.
Keep raw art/clips, successful prompt/model/request provenance and export records
in the app’s chosen source/output folders, within the caller’s workspace.

The helpers live inside this skill; paths are relative to the installed skill
folder. Use `MASCOT_*` settings for another app; `ORBIE_*` aliases preserve legacy
HyperCoder integrations. Dependencies: GenMedia, FFmpeg/FFprobe, Python with
Pillow/NumPy/SciPy. HEVC-with-alpha encoding additionally uses macOS VideoToolbox;
WebM can be prepared on other supported FFmpeg platforms.

Check every take before it is kept (held drawings, a racing tail, scale against
its own still, the loop's wrap, colour under zero alpha), with the project's clip
gate when it has one; a passing score does not replace watching it move.
Inspect representative frames and loop boundaries on the destination surfaces;
verify alpha, props, size, browser playback, reduced motion, and audio ownership.
Say whether the voice was heard and a complete loop watched; a contact sheet does
not verify either. Package raw sources separately when exact offline recreation
is required; this skill does not bundle any app’s proprietary mascot assets.
