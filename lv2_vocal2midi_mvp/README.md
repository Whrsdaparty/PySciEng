# Vocal2MIDI LV2 MVP (Linux-first, Ardour-oriented)

This folder contains a **scaffold MVP** for a monophonic vocal-to-MIDI LV2 plugin wrapper with a Python bridge.

## What this MVP is

- LV2 plugin (C++) with the requested control ports.
- Audio passthrough + rolling capture buffer (last ~120 seconds).
- `Analyze` trigger launches offline-ish bridge logic.
- `Export MIDI` trigger supports reliable file export fallback.
- Python CLI bridge with a stable command-line contract that can later call your existing prototype.

> Design choice for v1: prioritize reliable MIDI file output and explicit parameters over deep host integration.

---

## Layout

- `src/plugin.cpp`: LV2 plugin implementation and bridge process launcher.
- `lv2/vocal2midi.lv2/*.ttl`: LV2 metadata.
- `scripts/vocal2midi_bridge.py`: CLI bridge (stdlib-only fallback implementation).
- `CMakeLists.txt`: Linux build scaffold.

---

## Prerequisites (Ubuntu)

Install these packages before trying anything:

```bash
sudo apt update
sudo apt install -y \
  build-essential \
  cmake \
  pkg-config \
  lv2-dev \
  lilv-utils \
  python3 \
  python3-venv \
  python3-pip \
  ripgrep
```

Notes:

- `lv2-dev` is required for building the plugin (`pkg-config lv2`).
- `lilv-utils` provides `lv2ls` (used for plugin discovery checks).
- `python3` is required because the MVP bridge is launched as `python3 scripts/vocal2midi_bridge.py`.

Optional but recommended:

```bash
sudo apt install -y ardour
```

---

## Build and install

### 1) Build bundle

```bash
cd /workspace/PySciEng/lv2_vocal2midi_mvp
cmake -S . -B build
cmake --build build -j
```

This produces:

- `build/vocal2midi.lv2/vocal2midi.so`
- `build/vocal2midi.lv2/manifest.ttl`
- `build/vocal2midi.lv2/vocal2midi.ttl`

### 2) Install for current user

```bash
mkdir -p ~/.lv2/vocal2midi.lv2
cp -a build/vocal2midi.lv2/* ~/.lv2/vocal2midi.lv2/
```

### 3) Verify plugin discovery

```bash
lv2ls | rg vocal2midi
```

Expected output includes:

```text
https://example.org/lv2/vocal2midi
```

---

## CLI bridge quick test (recommended first)

Before testing inside Ardour, validate bridge behavior directly.

### 1) Check CLI help

```bash
cd /workspace/PySciEng/lv2_vocal2midi_mvp
python3 scripts/vocal2midi_bridge.py --help
```

### 2) Prepare a mono WAV test input

If you do not have a vocal sample ready, generate a temporary mono tone WAV:

```bash
python3 - <<'PY'
import math, wave, struct
sr = 48000
seconds = 2
samples = [int(0.2 * 32767 * math.sin(2 * math.pi * 220 * t / sr)) for t in range(sr * seconds)]
with wave.open('/tmp/vocal2midi_test.wav', 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes(struct.pack('<' + 'h' * len(samples), *samples))
print('Wrote /tmp/vocal2midi_test.wav')
PY
```

### 3) Run bridge conversion

```bash
python3 scripts/vocal2midi_bridge.py \
  --input /tmp/vocal2midi_test.wav \
  --output /tmp/vocal2midi_test.mid \
  --quantize-grid 2 \
  --quantize-strength 0.85 \
  --min-note-ms 90 \
  --gap-merge-ms 45 \
  --vibrato-smoothing 0.6 \
  --min-confidence 0.5 \
  --octave-shift 0 \
  --start-offset-ms 0
```

### 4) Confirm output exists

```bash
ls -lh /tmp/vocal2midi_test.mid
```

If this file exists and is non-empty, the CLI path is working.

---

## Detailed testing guide

This section is a full end-to-end test checklist for the MVP.

## A) Static/sanity checks

Run these from repo root (`/workspace/PySciEng/lv2_vocal2midi_mvp`):

```bash
python3 -m py_compile scripts/vocal2midi_bridge.py
```

```bash
cmake -S . -B build
```

```bash
cmake --build build -j
```

Success criteria:

- Python compile check passes with no output.
- CMake configure finds `lv2` package.
- Shared object `build/vocal2midi.lv2/vocal2midi.so` exists.

## B) Bundle/install verification

```bash
mkdir -p ~/.lv2/vocal2midi.lv2
cp -a build/vocal2midi.lv2/* ~/.lv2/vocal2midi.lv2/
lv2ls | rg 'https://example.org/lv2/vocal2midi'
```

Success criteria:

- URI appears exactly once.
- `~/.lv2/vocal2midi.lv2/` contains `.so` + `.ttl` files.

## C) Ardour host smoke test

1. Launch Ardour and open/create a session.
2. Add **mono audio track** named `Vocal`.
3. Insert plugin `Vocal2MIDI MVP (Bridge)` on that track.
4. Confirm dry audio passes through unchanged (plugin is passthrough in MVP).

Success criteria:

- No crash on plugin insert.
- Audio still audible on track playback.

## D) Analyze trigger test

1. Put a short vocal clip on the `Vocal` track (or record one).
2. Play transport so audio flows through plugin.
3. Pulse `Analyze` control from 0 -> 1 -> 0.
4. In shell, inspect output directory:

```bash
ls -ltr /tmp/vocal2midi/
```

Success criteria:

- New `capture_<timestamp>.wav` appears.
- New `capture_<timestamp>.mid` appears shortly after.

## E) Export MIDI trigger test

1. Ensure at least one successful Analyze run has occurred.
2. Pulse `Export MIDI` control from 0 -> 1 -> 0.
3. Re-check output directory:

```bash
ls -ltr /tmp/vocal2midi/
```

Success criteria:

- Another `.mid` file is created as export copy/fallback.

## F) Parameter behavior tests

Test each parameter by changing one variable at a time and re-running Analyze.

### Suggested matrix

- Quantize grid: `Off`, `1/16`, `1/32`
- Quantize strength: `0.0`, `0.5`, `1.0`
- Min note length: `40`, `120`, `300` ms
- Gap merge: `10`, `60`, `150` ms
- Vibrato smoothing: `0.0`, `0.5`, `1.0`
- Min confidence: `0.2`, `0.6`, `0.9`
- Octave shift: `-1`, `0`, `+1`
- Start offset: `-100`, `0`, `+100` ms

Success criteria:

- Output MIDI file changes in plausible direction (timing/pitch/length).
- No plugin/host instability when moving parameters.

## G) Stability/repeatability test

1. Trigger Analyze repeatedly (20+ times) while transport runs.
2. Trigger Export repeatedly (20+ times).
3. Alternate Analyze/Export quickly.

Success criteria:

- Ardour remains stable.
- No deadlock/hang from background work.
- `/tmp/vocal2midi` accumulates timestamped files.

## H) Ardour import fallback test

1. Use `Session > Import` in Ardour.
2. Import generated `/tmp/vocal2midi/*.mid`.
3. Place imported MIDI on a MIDI/instrument track.
4. Verify timing alignment and audible playback.

Success criteria:

- MIDI imports successfully.
- Region starts where expected and plays.

---

## Parameter map (v1)

- `--quantize-grid`: `0=Off, 1=1/4, 2=1/8, 3=1/16, 4=1/32`
- `--quantize-strength`: `0..1`
- `--min-note-ms`: milliseconds
- `--gap-merge-ms`: milliseconds
- `--vibrato-smoothing`: `0..1`
- `--min-confidence`: `0..1`
- `--octave-shift`: integer octave offset
- `--start-offset-ms`: milliseconds

---

## Ardour workflow notes (MVP)

1. Insert plugin on a mono vocal track.
2. Route/record vocals as usual.
3. Press `Analyze` control (toggle pulse).
4. Plugin writes capture WAV in `/tmp/vocal2midi/` and calls bridge.
5. MIDI file appears in `/tmp/vocal2midi/*.mid`.
6. Import resulting MIDI file into Ardour manually (`Session > Import`).

This avoids dependence on direct in-place MIDI region creation APIs in early versions.

---

## Stable bridge contract for future native engine

Current LV2 plugin launches:

```bash
python3 scripts/vocal2midi_bridge.py \
  --input <wav_path> \
  --output <midi_path> \
  --quantize-grid <int> \
  --quantize-strength <float> \
  --min-note-ms <float> \
  --gap-merge-ms <float> \
  --vibrato-smoothing <float> \
  --min-confidence <float> \
  --octave-shift <int> \
  --start-offset-ms <float>
```

You can swap internals of `vocal2midi_bridge.py` to call existing Python prototype now, and later replace launcher with native C++ engine while preserving parameter semantics.

---

## TODOs for replacing bridge with native C++ engine

1. Replace `std::system(...)` with LV2 Worker extension for safe non-RT background execution.
2. Move capture buffering to lock-free ring buffer.
3. Implement robust monophonic pitch tracking (YIN/pYIN or CREPE-like model).
4. Add note segmentation using `min_note_ms`, `gap_merge_ms`, `vibrato_smoothing`, `min_confidence`.
5. Replace file-based handoff with in-memory event pipeline.
6. Emit LV2 MIDI events directly when host supports capture/export workflow.
7. Keep file-export path as deterministic fallback.
8. Add explicit output directory / basename controls (likely atom/path ports or state extension).
9. Add automated regression corpus (wav->mid expected note tests).

---

## Troubleshooting

### `Package 'lv2', required by 'virtual:world', not found`

Install LV2 development package:

```bash
sudo apt install -y lv2-dev
```

### Plugin does not appear in Ardour

- Verify files under `~/.lv2/vocal2midi.lv2/`.
- Re-run `lv2ls | rg vocal2midi`.
- Restart Ardour after install/copy.

### No MIDI file generated after Analyze

- Ensure audio is actually flowing through plugin before trigger.
- Ensure trigger is a pulse (0->1->0), not constantly held.
- Check `/tmp/vocal2midi/` permissions and content.

### Bridge script fails

Run it directly with the same arguments shown in logs/README to isolate Python/runtime issues.

