#!/usr/bin/env python3
"""Print CSS keyframes that move Orbie's four mouth frames in time with a voice line.

  mouth-keyframes.py <line.mp3> <name>

Reads the recording's loudness ten times a second and picks a mouth for each
reading: closed (0) in silence, "eh" (1) when quiet, "eh"/"oh" (1/3)
alternating at medium level, "ah" (2) when loud. Output: one @keyframes per
frame (opacity 0/1, to be used with `step-end`) and the line's duration.
Needs ffmpeg and ffprobe on PATH.
"""
import math, struct, subprocess, sys

src, name = sys.argv[1], sys.argv[2]
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
n = len(raw) // 2
pcm = struct.unpack("<%dh" % n, raw)
hop = 800
env = [math.sqrt(sum(x * x for x in pcm[i:i + hop]) / hop) for i in range(0, n - hop, hop)]
top = max(env)
env = [min(1, (e / top) ** 0.6) for e in env]
frames = [0 if e < 0.14 else 1 if e < 0.42 else (3 if i % 2 else 1) if e < 0.72 else 2 for i, e in enumerate(env)]
frames[-1] = 0
last = len(frames) - 1
for f in range(4):
    stops, prev = [], None
    for i, x in enumerate(frames):
        on = 1 if x == f else 0
        if on != prev:
            stops.append("%.2f%%{opacity:%d}" % (i * 100 / last, on))
            prev = on
    if not stops[-1].startswith("100.00%"):
        stops.append("100%%{opacity:%d}" % (1 if f == 0 else 0))
    print("@keyframes orbie-%s-%d{%s}" % (name, f, "".join(stops)))
print("/* duration: %.2fs */" % dur)
