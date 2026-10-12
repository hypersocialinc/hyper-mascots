# Checking a take before it is kept

Use this before a generated clip is kept, exported or wired into an app. It is a
list of faults that were each found by a person, one at a time, in clips already
called fine, and of what can be measured from the decoded frames to find them
sooner. The checks point a person at the worst frames. They never approve a clip:
someone still watches a whole loop at the display size.

If the project has its own clip gate (a command that reads a take and answers
pass, look or refuse), run it on every take and rank the takes by its score
before a person looks. If it has none, do the free checks below by hand or with a
short script; this skill does not bundle one.

## Free checks, from the decoded frames

Measure a step as the mean difference between one frame and the next inside the
figure's box, alpha included. The numbers are where one project's gate started;
tune them on your own rejected clips.

| Fault | What to measure | Where it started |
|---|---|---|
| Held drawings (motion on twos or worse, legs that freeze) | The share of steps under a quarter of the clip's big steps. A film's held frame is never the same bytes twice, so compare with the clip's own big steps, not a fixed number. | Look over 15% of steps, refuse over 30% in a walk |
| A tail that races into the next clip | When frames were sampled from a longer take, the take's frames per kept frame over the last steps against the rest. | Refuse when the last three steps run 2.5× or faster |
| Scale or head drift | Figure height and head height against the clip's OWN source still, after the same crop. | Height: look past 3%. Head's share of the height: look past 10% |
| Feet line | The lowest opaque row per frame against its usual place. | Look past 2% of the figure's height (a good walk read 1.4%) |
| Outline width | Ink width per frame against the family reference. | Look past 35% off the clip's usual width |
| A loop that snaps | The step from the last frame to the first against the usual step. | Look past twice the usual step |
| A cut between two clips | The step across the cut and the three frames either side against the usual step. | Look past one usual step |
| Colour under zero alpha | In a premultiplied export (HEVC with alpha), any colour where alpha is 0: the player adds it over the page as a pale wash. | Refuse past a handful of pixels (16) |

A facing turn defeats the head measure: the estimate moves 10 to 17% as the
character turns, so a head that grows at the front view is a question for a
person or a vision model.

## Vision checks, paid

For what numbers cannot see, put labelled frame sheets to a vision model with a
written rubric of named faults per kind of clip: legs frozen while travelling, a
limp, a foot that slides, eyes shut, a chin dropped, hands or feet smeared, a
detail flipped by a mirror, the character's fixed rules broken. Send small
overlapping groups of frames, keep the raw answer with a hash of the frames and
the questions, and state the price before the call like any other paid step.

Do not let a rubric line refuse a clip until it has found its own known-bad
example. In one measured run a vision model scored a known-bad frame 0.02 and a
good one 0.82.

## Calibrate on your own rejected clips

Keep each rejected clip (half size is enough) with one line saying what is wrong
in it, plus one good clip. Run every check over the set and record hits, misses
and false alarms. A check may refuse only when it finds its own known-bad clip
with no false alarm on the good one; until then it can only ask for a look. When
a person finds a fault the checks passed, add that clip to the set.

In the first project to do this, only held drawings and the racing tail earned
the right to refuse; every other check above could only ask for a look, and the
vision lines had not been calibrated.

## Report

Per clip: pass, look or refuse, with the frames behind each finding and a sheet
of the worst frames. Across takes: a ranking. Say which checks ran, which are
calibrated, and that a whole loop was or was not watched.
