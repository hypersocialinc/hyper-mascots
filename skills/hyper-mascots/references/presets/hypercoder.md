# HyperCoder preset (optional)

Use only for HyperCoder’s established Hype/Orbie and Claude/Codex pal family.
This preset contains settings and lessons, not artwork, voice recordings, or
private conversation transcripts. Other apps use their own references/settings.

- Palette: yellow #FFDA1B, pink #FF3EA5, mint #19E08B, blue, near-black #0B0B0F.
- Hype style: fluffy halftone blob, glossy eyes, blush, orbit rings, ink outline.
- Voice: ElevenLabs v4 Jessica, rate multiplier 1.22, tempo 0.86.
- Finish: outline. Use the same edge treatment throughout idle/hover/talk/travel.
- Crop: `crop=iw*0.729:ih*0.729:iw*0.12:ih*0.1276` for normal solo clips.
- Sizes: pals 240px, Hype 320px. The wider car composite used crop 0.86 and 360px;
  inspect the actual prop and record a custom crop instead of reusing that blindly.
- Replay: sound carries forward; a genuine section return restarts its intro;
  mute survives navigation. No speech bubble in the current section guide.

```sh
export MASCOT_VOICE=Jessica
export MASCOT_RATE_MULTIPLIER=1.22
export MASCOT_TEMPO=0.86
export MASCOT_STYLE=outline
export MASCOT_INK='#0B0B0F'
export MASCOT_CROP='crop=iw*0.729:ih*0.729:iw*0.12:ih*0.1276'
```

When working in the HyperCoder checkout, originals remain under
`docs/design/orbie/source/`, raw clips under `clips/`, and built assets under
`web/`. Its README and `docs/design/site-redesign/Main.dc.html` document the
family and application integration. These optional project files are not a
portable skill dependency. Derive new roles from one approved neutral pal base;
existing pal drawings have a phone that otherwise repeatedly hides the face.

The moving car workflow measured eye/mouth anchors at `328,362 435,361 383,406`
on 768px frames. They are source-specific, not defaults for another character.
