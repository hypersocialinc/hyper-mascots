# Hyper Mascots

An open agent skill for creating consistent app mascots with the GenMedia CLI:
reference edits, role variants, idle/hover loops, speaking clips, transparent
exports, outlines, and playback without overlapping voice lines.

## Install

```sh
npx skills add hypersocialinc/hyper-mascots --skill hyper-mascots
```

For specific agents:

```sh
npx skills add hypersocialinc/hyper-mascots --skill hyper-mascots -a claude-code -a codex
```

Then ask your agent to use `$hyper-mascots` with your own character reference,
brand palette, voice and app surfaces. Hype/HyperCoder settings are an optional
preset; no app artwork, recordings, customer photos or private transcripts are
included. This skill uses GenMedia; it does not add a native `genmedia mascots`
command and is not yet published in the separate GenMedia skill registry.

## Local tools

Install the [GenMedia CLI](https://github.com/fal-ai-community/genmedia-cli) and
FFmpeg/FFprobe. In the installed skill folder, prepare Python dependencies:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install pillow numpy scipy
```

Generation uses your configured Fal account; check live model schemas and pricing
before a batch. Local smoke tests mock GenMedia and use no credentials or credits.

The included helpers preserve dark body/eye regions with BiRefNet masks, retain
props when selected, add per-frame outlines, cache masks for local rerenders, and
write source/mask/export provenance. They produce VP9 alpha WebM for Chrome and
Firefox and HEVC alpha MOV for Safari using macOS VideoToolbox. Other platforms
can export WebM; HEVC-alpha encoding requires macOS. See the included
[transparent-video recipe](skills/hyper-mascots/references/transparent-video.md).

## Verify offline

```sh
python skills/hyper-mascots/scripts/smoke-test.py
```

Test actual browser playback too, including hidden states, rapid scene changes,
reduced motion, mute/re-entry behavior and Safari alpha. Decoded-frame checks do
not replace watching a full loop or hearing the recording.

## License

MIT. Third-party models, generated media, app brands and input artwork keep their
own terms; this repository licenses the skill instructions and helper code.
