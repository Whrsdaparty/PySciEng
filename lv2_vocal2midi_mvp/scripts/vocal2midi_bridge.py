#!/usr/bin/env python3
"""CLI bridge for vocal-to-MIDI MVP.

This script intentionally keeps dependencies minimal (stdlib only) so it can run
in constrained Linux environments.
"""

from __future__ import annotations

import argparse
import math
import shutil
import struct
import wave
from dataclasses import dataclass
from pathlib import Path


GRID_TO_BEAT = {
    0: None,      # Off
    1: 1.0,       # 1/4
    2: 0.5,       # 1/8
    3: 0.25,      # 1/16
    4: 0.125,     # 1/32
}


@dataclass
class BridgeConfig:
    quantize_grid: int
    quantize_strength: float
    min_note_ms: float
    gap_merge_ms: float
    vibrato_smoothing: float
    min_confidence: float
    octave_shift: int
    start_offset_ms: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline vocal-to-MIDI bridge MVP")
    parser.add_argument("--input", required=True, help="Input mono WAV path")
    parser.add_argument("--output", required=True, help="Output MIDI path")
    parser.add_argument("--copy-from", help="Copy existing MIDI file to --output and exit")
    parser.add_argument("--quantize-grid", type=int, default=0)
    parser.add_argument("--quantize-strength", type=float, default=1.0)
    parser.add_argument("--min-note-ms", type=float, default=80.0)
    parser.add_argument("--gap-merge-ms", type=float, default=40.0)
    parser.add_argument("--vibrato-smoothing", type=float, default=0.5)
    parser.add_argument("--min-confidence", type=float, default=0.4)
    parser.add_argument("--octave-shift", type=int, default=0)
    parser.add_argument("--start-offset-ms", type=float, default=0.0)
    return parser.parse_args()


def read_wav_mono(path: Path) -> tuple[list[float], int]:
    with wave.open(str(path), "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        framerate = wav_file.getframerate()
        n_frames = wav_file.getnframes()
        raw = wav_file.readframes(n_frames)

    if sample_width != 2:
        raise ValueError("Only 16-bit PCM WAV is supported in MVP bridge")

    fmt = "<" + "h" * (len(raw) // 2)
    ints = struct.unpack(fmt, raw)

    if channels == 1:
        mono = [x / 32768.0 for x in ints]
    else:
        mono = []
        for i in range(0, len(ints), channels):
            mono.append(sum(ints[i : i + channels]) / (channels * 32768.0))

    return mono, framerate


def estimate_frequency(samples: list[float], sr: int) -> tuple[float, float]:
    if not samples:
        return 0.0, 0.0

    rms = math.sqrt(sum(s * s for s in samples) / len(samples))
    if rms < 0.01:
        return 0.0, rms

    crossings = 0
    for i in range(1, len(samples)):
        if samples[i - 1] <= 0 < samples[i] or samples[i - 1] >= 0 > samples[i]:
            crossings += 1

    duration_s = len(samples) / sr
    freq = (crossings / 2.0) / duration_s if duration_s > 0 else 0.0
    return freq, min(1.0, rms * 4.0)


def freq_to_midi_note(freq: float) -> int:
    if freq <= 0:
        return 60
    note = 69 + 12 * math.log2(freq / 440.0)
    return max(0, min(127, int(round(note))))


def quantize_beats(beats: float, cfg: BridgeConfig) -> float:
    grid = GRID_TO_BEAT.get(cfg.quantize_grid)
    if grid is None:
        return beats
    snapped = round(beats / grid) * grid
    return beats + (snapped - beats) * max(0.0, min(1.0, cfg.quantize_strength))


def vlq(value: int) -> bytes:
    buffer = value & 0x7F
    out = bytearray()
    while value > 0x7F:
        value >>= 7
        buffer <<= 8
        buffer |= ((value & 0x7F) | 0x80)
    while True:
        out.append(buffer & 0xFF)
        if buffer & 0x80:
            buffer >>= 8
        else:
            break
    return bytes(out)


def build_single_note_midi(note: int, velocity: int, start_beats: float, dur_beats: float) -> bytes:
    ppq = 480
    start_ticks = max(0, int(round(start_beats * ppq)))
    dur_ticks = max(1, int(round(dur_beats * ppq)))

    track = bytearray()
    track.extend(vlq(0))
    track.extend(bytes([0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20]))  # 120 bpm
    track.extend(vlq(start_ticks))
    track.extend(bytes([0x90, note, velocity]))
    track.extend(vlq(dur_ticks))
    track.extend(bytes([0x80, note, 0]))
    track.extend(vlq(0))
    track.extend(bytes([0xFF, 0x2F, 0x00]))

    header = bytearray(b"MThd")
    header.extend(struct.pack(">IHHH", 6, 0, 1, ppq))

    chunk = bytearray(b"MTrk")
    chunk.extend(struct.pack(">I", len(track)))
    chunk.extend(track)

    return bytes(header + chunk)


def transcribe_to_midi(input_wav: Path, output_midi: Path, cfg: BridgeConfig) -> None:
    samples, sr = read_wav_mono(input_wav)
    freq, confidence = estimate_frequency(samples, sr)

    if confidence < cfg.min_confidence:
        note = 60
        velocity = 1
    else:
        note = freq_to_midi_note(freq) + (cfg.octave_shift * 12)
        note = max(0, min(127, note))
        velocity = int(40 + confidence * 80)

    start_beats = max(0.0, cfg.start_offset_ms / 500.0)  # 120 bpm -> 500ms per beat
    note_beats = max(cfg.min_note_ms / 500.0, len(samples) / sr / 0.5)
    note_beats = quantize_beats(note_beats, cfg)

    midi_data = build_single_note_midi(note, velocity, start_beats, note_beats)
    output_midi.parent.mkdir(parents=True, exist_ok=True)
    output_midi.write_bytes(midi_data)


def main() -> int:
    args = parse_args()
    output = Path(args.output)

    if args.copy_from:
        shutil.copyfile(args.copy_from, output)
        return 0

    cfg = BridgeConfig(
        quantize_grid=args.quantize_grid,
        quantize_strength=args.quantize_strength,
        min_note_ms=args.min_note_ms,
        gap_merge_ms=args.gap_merge_ms,
        vibrato_smoothing=args.vibrato_smoothing,
        min_confidence=args.min_confidence,
        octave_shift=args.octave_shift,
        start_offset_ms=args.start_offset_ms,
    )

    transcribe_to_midi(Path(args.input), output, cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
