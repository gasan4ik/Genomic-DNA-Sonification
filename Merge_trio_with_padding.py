from mido import MidiFile, MidiTrack, Message, MetaMessage

# This script merges three part files (Flute*.mid, Viola*.mid, Bassoon*.mid)
# into a single trio MIDI. It normalizes ticks_per_beat, preserves global tempo
# from the first file, assigns each part to its own MIDI channel, and pads
# shorter tracks so all three parts end at the same global time.
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

# Load MIDI files (Replace with actual filenames)
midi_files = ["Flute.mid", "Viola.mid", "Bassoon.mid"]

# Check if all files have the same ticks_per_beat
tpb_values = [MidiFile(file).ticks_per_beat for file in midi_files]
if len(set(tpb_values)) == 1:
    STANDARD_TPB = tpb_values[0]
else:
    STANDARD_TPB = 480

# Create a new merged MIDI file with standard TPB
merged_midi = MidiFile(ticks_per_beat=STANDARD_TPB)

# Create a master tempo & metadata track
tempo_track = MidiTrack()
merged_midi.tracks.append(tempo_track)

instrument_tracks = {}
track_end_times = []  # Track lengths to align them later

for i, file in enumerate(midi_files):
    midi = MidiFile(file)
    time_scale = STANDARD_TPB / midi.ticks_per_beat if midi.ticks_per_beat != STANDARD_TPB else 1.0

    track = MidiTrack()
    instrument_tracks[file] = track

    abs_time = 0  # Track the absolute time in ticks
    for original_track in midi.tracks:
        for msg in original_track:
            if msg.is_meta:
                if msg.type in ["set_tempo", "time_signature", "key_signature"] and i == 0:
                    tempo_track.append(msg)
                elif msg.type in ["track_name", "marker", "cue_point"]:
                    track.append(msg)
                continue

            if msg.type.startswith("control_change"):
                abs_time += int(msg.time * time_scale)
                track.append(msg.copy(time=int(msg.time * time_scale)))

            elif msg.type == "program_change":
                abs_time += int(msg.time * time_scale)
                track.append(msg.copy(time=int(msg.time * time_scale)))

            elif msg.type in ["note_on", "note_off"]:
                abs_time += int(msg.time * time_scale)
                new_msg = msg.copy(time=int(msg.time * time_scale))
                new_msg.channel = i
                track.append(new_msg)

    # Store the final time of this track
    track_end_times.append(abs_time)

    # Append the processed track to the merged MIDI file
    merged_midi.tracks.append(track)

# Pad shorter tracks to match the longest one
max_end_time = max(track_end_times)
for i, (file, track) in enumerate(instrument_tracks.items()):
    pad_time = max_end_time - track_end_times[i]
    if pad_time > 0:
        # Padding with an empty delay before end_of_track
        track.append(Message('note_off', note=0, velocity=0, time=pad_time, channel=i))

    # Ensure end_of_track message is present
    if not any(msg.type == 'end_of_track' for msg in track):
        track.append(MetaMessage('end_of_track'))

merged_midi.save("Merged_Trio_FullPreservation_Padded.mid")
print("Successfully merged and padded three MIDI tracks!")
