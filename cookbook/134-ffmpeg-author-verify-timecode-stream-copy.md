# Author + verify an arbitrary start timecode on a lossless `-c copy` trim (and a synthetic burned-in-TC test clip)

**Tags:** ffmpeg -timecode, -c copy trim, tmcd stream tag, ffprobe stream_tags, -ss before -i, nb_read_packets duration, FCP conform, drawtext timecode

**Source:** Penumbra — `docs/spikes/fcp-consolidate-roundtrip/run_spike.sh` (2026-06-25 FCP-consolidate gating spike). Sibling of [[07-timecode-typography]] (TC *display*) and [[15-native-video-analysis]]. Underpins any "trim a sub-range losslessly and round-trip it into an NLE by timecode" feature.

## The problem
You stream-copy (`-c copy`, no re-encode) a sub-range out of a long clip and want an NLE (Final Cut, Resolve, Premiere) to **conform the edit by timecode** — i.e. the NLE relinks by the *file's embedded `tmcd` track*, NOT by any sidecar/XML value. So the trimmed file must carry a **correct, authored start timecode**, and you must be able to **prove it landed**. Three non-obvious traps make this fail silently.

## The recipe

**1 — Trim losslessly + author an arbitrary start TC. `-ss` goes BEFORE `-i`** (input-seek → snaps to the preceding keyframe, which a clean `-c copy` requires; output-seek after `-i` would need a decode and garble the head):
```bash
ffmpeg -y -ss "$START_SEC" -i src.mov -t "$DUR_SEC" \
  -map 0:v -c copy -timecode "01:00:09:00" -avoid_negative_ts make_zero trim.mov
```

**2 — Verify the TC actually wrote — read the `tmcd` STREAM tag, NOT the format tag.** This is the trap that wastes an afternoon: the format-level tag is empty even on a *successful* write, so a verifier checking it reports a false failure on every working file.
```bash
# ✅ CORRECT — timecode lives on the tmcd DATA stream's tag
ffprobe -v error -select_streams d -show_entries stream_tags=timecode -of csv=p=0 trim.mov
#   → 01:00:09:00
# ❌ WRONG — almost always empty even when the write succeeded
ffprobe -v error -show_entries format_tags=timecode trim.mov     # → [FORMAT][/FORMAT]
```

**3 — Find the preceding keyframe to snap to, with no decode** (packet flags; `K` = keyframe):
```bash
ffprobe -v error -select_streams v:0 -show_entries packet=pts_time,flags -of csv=p=0 src.mov \
  | awk -F, -v fps=25 -v tgt="$TARGET_FRAME" '$2 ~ /K/ {f=int($1*fps+0.5); if (f<=tgt && f>b) b=f} END{print b}'
```

**4 — Declare any downstream duration from the PROBED file, never the predicted length.** `-c copy` includes the whole trailing GOP, so you ask for 8.0 s and get 8.16 s. Hand the NLE the *predicted* 8.0 s and FCP throws "no shared media range" (a duration-metadata mismatch). Probe the real frame count:
```bash
ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of csv=p=0 trim.mov
```

## Bonus: a synthetic burned-in-TC test clip (validate NLE conform with no real footage)
`testsrc2` + `drawtext`'s `timecode=` option paints a *running* timecode into the pixels, so an NLE-import test becomes a purely visual pass/fail (does the clip's first frame read the editorial in-point or the file start?). Control the GOP so keyframe positions are deterministic, and embed a matching `tmcd`:
```bash
ffmpeg -y -f lavfi -i "testsrc2=size=1280x720:rate=25:duration=60" \
  -vf "drawtext=fontfile=/System/Library/Fonts/Supplemental/Courier New Bold.ttf:\
timecode='01\:00\:00\:00':rate=25:fontcolor=white:fontsize=54:x=40:y=40:box=1:boxcolor=black@0.7" \
  -c:v libx264 -pix_fmt yuv420p -g 25 -keyint_min 25 -x264-params "scenecut=0:open-gop=0" \
  -timecode "01:00:00:00" src.mov
```
(Burned-in TC and embedded `tmcd` are authored to agree, so the pixels are a human-readable oracle for what the `tmcd` claims.)

## Gotchas (each cost real time)
- **`tmcd` stream tag, not format tag** (trap #2) — wire your verifier to `-select_streams d -show_entries stream_tags=timecode`.
- **`-ss` before `-i`** for `-c copy` — input-seek keyframe-snaps; after-`-i` decodes/garbles.
- **Probe duration, don't predict** — the trailing GOP makes copy longer than requested.
- **MOV, not MP4** — MOV's `tmcd` is the format Apple/NLE conform reads; MP4 timecode is private/non-standard.
- **Integer-frame math** if you also emit FCPXML/EDL — derive times from frame counts, never `float_seconds × fps`, or the NLE rejects "not on an edit frame boundary."
- **Why it matters:** the NLE conforms relink off the *file's* `tmcd` + duration + audio-channel count, not off your XML's `asset.start` — the file writer is the load-bearing part. (See Penumbra `docs/specs/fcp-consolidate.md`; the read side mirrors Penumbra's `SourceTimecodeReader` AVFoundation `tmcd` reader.)

## Best for
Lossless sub-range extraction (camera-original H.264/HEVC/ProRes) that must round-trip into an NLE by source timecode — and headless, footage-free validation of timecode-conform via a burned-in synthetic clip.
