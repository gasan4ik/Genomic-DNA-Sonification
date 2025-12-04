from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo
import random


# This script maps the monophonic output to flute–viola–bassoon
# without explicit dynamic hierarchy or fixed random seed, producing a more
# exploratory, less strictly reproducible arrangement.
# Extreme pitches are remapped into an audible band using logarithmic scaling,
# then snapped to the C major scale. Both voices
# share a similar register, with velocities adjusted to soften remapped
# extremes, producing a psychoacoustically smoother but still data-driven sound.
#
#
#
# Author: Hasan Babazada, Ph.D.
# Date: 02/20/2025
# Email: gasan4ik@hotmail.com
#
# Copyright (c) 2025 Hasan Babazada
# SPDX-License-Identifier: MIT
#
# This program is released under the MIT License.
# See the LICENSE file in the repository root for the full text.
########################################################################

INPUT_MIDI = "harmonic.mid" # Use actual filename
OUTPUT_MIDI = "trio_output_baseline.mid"

TEMPO_BPM = 60
TPB = 480  # ticks per beat

# Instrument ranges (MIDI note numbers)
FLUTE_RANGE = (60, 96)      # roughly C4–C7+
VIOLA_RANGE = (48, 72)      # C3–C6
BASSOON_RANGE = (48, 55)    # C3–G3 (you said you like C3/G3 region)

# C major scale (pitch classes)
C_MAJOR_PCS = [0, 2, 4, 5, 7, 9, 11]


def remap_to_range(note: int, min_note: int, max_note: int) -> int:
    """
    Push note into [min_note, max_note] by octave wrapping.
    Guarantees: min_note <= result <= max_note.
    """
    if min_note > max_note:
        raise ValueError("min_note must be <= max_note")

    while note < min_note:
        note += 12
    while note > max_note:
        note -= 12
    return note


def snap_to_c_major(note: int) -> int:
    """
    Snap any MIDI note to the nearest note in C major,
    keeping the octave as close as possible.
    """
    octave = note // 12
    pc = note % 12

    # Find closest pitch class in C major
    best_pc = None
    best_dist = 999
    for target_pc in C_MAJOR_PCS:
        dist = abs(target_pc - pc)
        if dist < best_dist:
            best_dist = dist
            best_pc = target_pc

    return octave * 12 + best_pc


def process_melody_note(note: int, velocity: int) -> tuple[int, int]:
    """
    Apply range remap + C major snap for the flute.
    """
    note = remap_to_range(note, FLUTE_RANGE[0], FLUTE_RANGE[1])
    note = snap_to_c_major(note)
    return note, velocity


def generate_viola_harmony(note: int) -> int:
    """
    Generate a harmony note for the viola by applying an interval
    (typically -3, -5, or -7 semitones), then remap and snap.
    """
    interval = random.choice([-3, -5, -7])
    harm_note = note + interval
    harm_note = remap_to_range(harm_note, VIOLA_RANGE[0], VIOLA_RANGE[1])
    harm_note = snap_to_c_major(harm_note)
    return harm_note


def generate_bassoon_note(index: int) -> int:
    """
    Simple C3–G3 pedal / fifth pattern:
    even notes -> C3 (48), odd notes -> G3 (55).
    """
    c3 = 48
    g3 = 55
    note = c3 if index % 2 == 0 else g3
    return remap_to_range(note, BASSOON_RANGE[0], BASSOON_RANGE[1])


# ---------- PROCESSING ----------

# Load input monophonic MIDI
midi_in = MidiFile(INPUT_MIDI)

# Extract raw melody (ignore timing, just grab note_on with velocity > 0)
melody = []
for track in midi_in.tracks:
    for msg in track:
        if msg.type == "note_on" and msg.velocity > 0:
            melody.append((msg.note, msg.velocity))

print(f"Found {len(melody)} melody notes")

# Create output MIDI
midi_out = MidiFile(ticks_per_beat=TPB)

# Tempo track
tempo_track = MidiTrack()
tempo_msg = MetaMessage('set_tempo', tempo=bpm2tempo(TEMPO_BPM), time=0)
tempo_track.append(tempo_msg)
midi_out.tracks.append(tempo_track)

# Create instrument tracks
flute_track = MidiTrack()
viola_track = MidiTrack()
bassoon_track = MidiTrack()

# Channel assignments
FLUTE_CH = 0
VIOLA_CH = 1
BASSOON_CH = 2

# Fixed durations (you can tweak)
FLUTE_DUR = TPB        # 1 beat
VIOLA_DUR = TPB * 2    # 2 beats
BASSOON_DUR = TPB * 4  # 4 beats (slower, more sustained)

# Build tracks
for i, (raw_note, raw_vel) in enumerate(melody):
    # --- Flute (melody) ---
    flute_note, flute_vel = process_melody_note(raw_note, raw_vel)
    flute_track.append(Message('note_on', note=flute_note, velocity=flute_vel,
                               time=0, channel=FLUTE_CH))
    flute_track.append(Message('note_off', note=flute_note, velocity=flute_vel,
                               time=FLUTE_DUR, channel=FLUTE_CH))

    # --- Viola (harmony) ---
    viola_note = generate_viola_harmony(raw_note)
    viola_vel = raw_vel  # you can also scale this if you want it softer
    viola_track.append(Message('note_on', note=viola_note, velocity=viola_vel,
                               time=0, channel=VIOLA_CH))
    viola_track.append(Message('note_off', note=viola_note, velocity=viola_vel,
                               time=VIOLA_DUR, channel=VIOLA_CH))

    # --- Bassoon (low pattern) ---
    bassoon_note = generate_bassoon_note(i)
    # Slightly softer to keep in background
    bassoon_vel = max(30, int(raw_vel * 0.6))
    bassoon_track.append(Message('note_on', note=bassoon_note, velocity=bassoon_vel,
                                 time=0, channel=BASSOON_CH))
    bassoon_track.append(Message('note_off', note=bassoon_note, velocity=bassoon_vel,
                                 time=BASSOON_DUR, channel=BASSOON_CH))

# Add tracks to MIDI
midi_out.tracks.append(flute_track)
midi_out.tracks.append(viola_track)
midi_out.tracks.append(bassoon_track)

# Save
midi_out.save(OUTPUT_MIDI)
print(f"Saved trio MIDI to: {OUTPUT_MIDI}")
