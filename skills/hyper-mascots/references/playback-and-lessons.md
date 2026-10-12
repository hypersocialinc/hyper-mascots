# Playback states and transcript-backed lessons

Use this when integrating a guide or choosing between motion and speech clips.
It is a behavior contract to adapt to the requested UI, not a new player API.

## States and a single voice owner

- Idle: play the chosen loop(s), or show a still for reduced motion.
- Hover: show a hover loop only when not speaking; restore idle on leave.
- Speaking: show muted lip-sync video alongside the one active audio file.
- Transition: move the element in CSS while preserving its character/voice state.
  Internal body/prop motion belongs in video, not a fake CSS slide of the prop.
  Preserve the same silhouette outline across the cycle, including while flying
  over a differently colored object; the cover finish is the family reference.
- Muted: immediately stop voice; do not speak an extra “shh” unless requested.
- Hidden/offscreen: stop speech, cancel queued starts, pause idle/talk clips and
  timers, and remove invisible copies from hit-testing.

The product chooses replay policy. Specify whether a genuine return restarts,
resumes, or stays silent. Preserve mute preference forward and backward, and do
not retrigger an introduction on every scroll update. The optional HyperCoder
preset describes its chosen replay policy.

### Prevent overlapping lines

One controller owns the active line across tour, cover, and other sections.
Before starting another line, increment a generation/turn token, cancel start /
end / nudge / entrance timers, and pause/reset the outgoing audio and talk video.
Every asynchronous `play()` fulfillment/rejection, `playing`, `ended`, seek, and
fallback timeout checks the current token AND active line ID before changing
state. Stale callbacks must not restart an old line or clear the new state.
Treat an intentional pause’s `AbortError` as cancellation, not an audio failure.

Audio is the clock. Video is always muted; never play its embedded soundtrack as
well as the standalone recording. Keep the still/previous visible clip until the
new clip actually fires `playing`. On late video startup, seek to the current
active audio time when drift exceeds a small measured tolerance (the tour used
roughly 0.25–0.35 seconds). A delayed `playing` callback from another line cannot
seek or display over the active one. Use `ended` from the active audio and a
measured-duration fallback with the same token guard. Derive duration after voice
pitch/tempo treatment, not from an earlier raw recording.

Test rapid next/back, leaving during audio load, mute during `play()` startup,
returning to the section, hover while speaking, and offscreen idle suspension.
Keep these controls in the application’s player/controller. The optional
HyperCoder preset points to its implementation example; no app repo is required
by this skill.

## Lessons from a previous mascot project

These historical observations informed the workflow; model behavior can change.
The private transcript is not distributed. The record references below are an
internal chronology, not required inputs or assets for consumers.

| Evidence | Lesson retained |
|---|---|
| #5129–#6152 | Start with stills/loudness mouth states; add costly talking clips after the character/delivery is settled. Moving body clips and static mouth stills are different tiers. |
| #6152, #6889 | A loop uses the same source still as its first and last frame; separate idle, hover, and cover clips preserve their intended behaviors. |
| #6632 | “Fly fast” changed the silhouette by adding a green tail. Travel, lean, and stretch moved to CSS. |
| #6652, #6742, #6756 | Brightness cutout made body parts partly transparent. BiRefNet masks and a no-glow ink finish fixed the family’s presentation. |
| #7054 | Caption-off wording and unknown flags were ignored. Cropping/matting removed burned-in text; inspect actual results. |
| #8214–#8413 | H3 supplied speech but froze body motion; other video lip-sync attempts failed on the cartoon. A separate motion clip + H3 Max lip-sync speech + tracked face graft was the successful route (make the motion clip with H3 Max image-to-video). |
| 2026-10-10 | Kling 2.5 Turbo smeared thin orbit rings and scribbled a rings-appear transition; the owner rejected the clips. All motion now uses `minimax/h3-max/image-to-video` with a first frame (`image_url`) and a last frame (`end_image_url`); speech is ElevenLabs audio into H3 Max lip-sync. |
| 2026-10-10 | Naming a thing in order to forbid it draws it: "there are no rings around it" gave H3 Max a halo of rings. Describe only what IS in the shot ("only the blob and the map are in the picture"). |
| 2026-10-10 | Background removal is BiRefNet v2 on every frame in parallel, recomposed with FFmpeg, then HEVC-alpha for Safari and VP9-alpha for Chromium. The video endpoint is a fallback only. |
| 2026-10-10 | `genmedia --download <file>` does not overwrite: when the file exists it writes `<file>_1` and the old image stays in place. A regenerated still silently kept the old art until the sheet looked unchanged. Delete the target first, and look at the result before deriving anything from it. |
| 2026-10-10 | A prop can change during the working loop (a chart card flipping line, bars, pie) as long as the prompt names the starting picture as the last beat, so the loop closes. |
| 2026-10-11 | Faults a person found in clips already called fine: a walk drawn on twos, legs racing at 3× into a landing, a turn through a back view, a turn with eyes shut, a head that grows at the front view. Each is now looked for in every take before it is kept ([clip checks](clip-checks.md)); a check may refuse only once it finds its own known-bad clip. |
| #8353 | Grafting only the mouth made eyes and mouth disagree. Move the whole face ellipse together, then mask the final composite. |
| #7085, #7120, #7253 | Wait for the new video’s `playing` event before swapping; invisible duplicate characters must not catch hover/clicks. |
| #6922, #7997, #7151 | Audio/video drift was visible. Audio became the clock; stop when leaving the scene and restart deliberately on re-entry. |
| #6742, #6889 | The browser replayed stale media. Version approved replacement file names and explain suffix changes in provenance. |
| #7887, #7997 | Generated poses/clips differed in apparent size; the historical page used CSS scale corrections. Reusable exports now offer cut-time normalization against the same pose, with a separate manual factor. |

The original tour also used a `turn` cancellation token. The lower-section
`sectionTurn` extension was added in the later Codex session; its rapid navigation,
autoplay, and mute behavior was checked in browser tests. Do not attribute that
later implementation or unrun automatic diagnostics to the original transcript.

Opus sampled first/last and intermediate loop frames and found near-equal ends
with some large final-step snaps. Dropping a last frame can leave the same seam.
That evidence supports inspecting the motion around a loop boundary rather than
claiming that first/tail conditioning makes every loop seamless.
