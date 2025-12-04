from music21 import converter, stream, midi, metadata, instrument, clef, meter, note as m21_note
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo
import random
#######################################################################
#
#  
#
# This script takes a monophonic MIDI file generated 
# sonification pipeline and constructs a
# two-instrument duet (melody + harmony).
#
# Functionality:
#   - Remaps extreme pitches into an audible range using proportional
#     scaling (AUDIBLE_MIN–AUDIBLE_MAX),
#   - Snaps notes to the C major scale to preserve tonal clarity,
#   - Generates a harmony line by applying random intervals (-3, -5, -7)
#     to the melody notes,
#   - Assigns independent random rhythmic values (in ticks) to melody
#     and harmony from a small set of musical durations,
#   - Writes the result to a multi-track MIDI file.
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
#######################################################################


# Load the monophonic MIDI file (generated from interferogram)
input_midi = "harmonic.mid" #Use actual filename
midi_in = MidiFile(input_midi)

# Create a new multi-track MIDI file for two instruments
output_midi = MidiFile()

# Set the tempo (60 BPM)
tempo_bpm = 60
microsec_per_beat = bpm2tempo(tempo_bpm)
tempo_track = MidiTrack()
tempo_track.append(MetaMessage('set_tempo', tempo=microsec_per_beat, time=0))
output_midi.tracks.append(tempo_track)

# Create tracks for melody and harmony
tracks = {
    "melody": MidiTrack(),
    "harmony": MidiTrack()
}

# Define audible pitch range for instruments
AUDIBLE_MIN, AUDIBLE_MAX = 36, 84  # For example, from C2 to C6

# Assign MIDI channels
midi_channels = {"melody": 1, "harmony": 2}

# Define C Major scale (MIDI note numbers)
C_major_scale = [60, 62, 64, 65, 67, 69, 71, 72]

# Define possible note durations (in ticks)
note_durations = {
    'whole': 1920,  # 4 beats
    'half': 960,    # 2 beats
    'quarter': 480,  # 1 beat
    'eighth': 240,   # 1/2 beat
    'sixteenth': 120,  # 1/4 beat
}

# Function to proportionally remap extreme notes into the audible range
def remap_extreme_notes_proportional(note, min_note=AUDIBLE_MIN, max_note=AUDIBLE_MAX):
    note = max(0, min(127, note))  # Ensure within full MIDI range
    if note < min_note:
        # Scale up proportionally
        return min_note + ((note - min_note) * (max_note - min_note) // max(1, min_note))
    elif note > max_note:
        # Scale down proportionally
        return max_note - ((note - max_note) * (max_note - min_note) // max(1, (127 - max_note)))
    return note

# Function to snap any note to the nearest note in C Major.
def closest_scale_note(note):
    candidate_notes = [n for n in C_major_scale if abs(n - note) <= 4]
    return random.choice(candidate_notes) if candidate_notes else min(C_major_scale, key=lambda x: abs(x - note))

# Function to adjust velocity for extreme pitches
def adjust_velocity_for_extremes(note, velocity):
    if note > AUDIBLE_MAX or note < AUDIBLE_MIN:
        return max(30, velocity - 30)
    return velocity

# Process note: first remap to audible range, then snap to C Major, then clamp final note.
def process_note(note, velocity):
    # Remap into the audible range
    note = remap_extreme_notes_proportional(note)
    # Snap to the closest note in C Major (regardless of pitch)
    note = closest_scale_note(note)
    # Clamp the result to the audible range, in case snapping went out of bounds
    note = max(AUDIBLE_MIN, min(AUDIBLE_MAX, note))
    velocity = adjust_velocity_for_extremes(note, velocity)
    return note, velocity

# Extract melody from the input MIDI (only positive velocity note_on events)
melody = []
for track in midi_in.tracks:
    for msg in track:
        if msg.type == 'note_on' and msg.velocity > 0:
            melody.append((msg.note, msg.velocity))

# Generate harmony for each melody note by shifting with a random interval,
# then process it in the same way.
harmonies = {"harmony": []}
for note, velocity in melody:
    interval = random.choice([-3, -5, -7])  # Random harmonic interval
    shifted_note = note + interval
    # First remap the shifted note into the audible range
    shifted_note = remap_extreme_notes_proportional(shifted_note)
    # Then snap it to C Major
    harmony_note = closest_scale_note(shifted_note)
    # Clamp to ensure it is audible
    harmony_note = max(AUDIBLE_MIN, min(AUDIBLE_MAX, harmony_note))
    harmonies["harmony"].append(harmony_note)

# Assign processed melody and harmony notes to their respective tracks
for i, (mel_note, mel_vel) in enumerate(melody):
    mel_note, mel_vel = process_note(mel_note, mel_vel)
    # Randomly select a duration for the melody note
    mel_duration = random.choice(list(note_durations.values()))
    msg_on = Message('note_on', note=mel_note, velocity=mel_vel, time=0, channel=midi_channels["melody"])
    msg_off = Message('note_off', note=mel_note, velocity=mel_vel, time=mel_duration, channel=midi_channels["melody"])
    tracks["melody"].append(msg_on)
    tracks["melody"].append(msg_off)

    if i < len(harmonies["harmony"]):
        harm_note = harmonies["harmony"][i]
        # Randomly select a duration for the harmony note
        harm_duration = random.choice(list(note_durations.values()))
        msg_on = Message('note_on', note=harm_note, velocity=mel_vel, time=0, channel=midi_channels["harmony"])
        msg_off = Message('note_off', note=harm_note, velocity=mel_vel, time=harm_duration, channel=midi_channels["harmony"])
        tracks["harmony"].append(msg_on)
        tracks["harmony"].append(msg_off)

# Append both tracks to the output MIDI file
for trk in tracks.values():
    output_midi.tracks.append(trk)

# Save the new multi-instrument MIDI file
output_midi.save("two_instrument_output_fixed.mid")