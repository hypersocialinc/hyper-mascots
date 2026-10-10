#!/bin/sh
# voice-line.sh <out.mp3> "<text, with [cheerful] / [playful] / [excited] tags>"
#
# ElevenLabs voice through GenMedia; choose MASCOT_VOICE for the family.
# Pitch/tempo are neutral by default; presets can set multiplier and tempo.
set -e
if [ "$#" -ne 2 ]; then
  echo 'usage: voice-line.sh <out.mp3> "<text>"' >&2
  exit 2
fi
OUT=$1; TEXT=$2
VOICE=${MASCOT_VOICE:-${ORBIE_VOICE:-}}
RATE=${MASCOT_RATE_MULTIPLIER:-1}
TEMPO=${MASCOT_TEMPO:-1}
if [ -z "$VOICE" ]; then echo 'Set MASCOT_VOICE to the chosen ElevenLabs voice' >&2; exit 2; fi
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
PY=${MASCOT_PYTHON:-${ORBIE_PYTHON:-python3}}
mkdir -p "$(dirname "$OUT")"
genmedia run elevenlabs/tts/eleven-v4 --text "$TEXT" --voice "$VOICE" --download "$TMP/" --json > "$TMP/r.json"
RAW=$("$PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); url=d["result"]["audio"]["url"]; print(next(x["path"] for x in d["downloaded_files"] if x["url"] == url))' "$TMP/r.json")
SR=$(ffprobe -v error -show_entries stream=sample_rate -of csv=p=0 "$RAW")
ffmpeg -v error -y -i "$RAW" -af "asetrate=$SR*$RATE,aresample=$SR,atempo=$TEMPO" -b:a 128k "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
