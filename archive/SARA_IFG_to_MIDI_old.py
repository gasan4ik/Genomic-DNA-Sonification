#######################################################################
#
# 
# This script implements the core sonification pipeline for
# converting an interferogram of genomic DNA into a monophonic MIDI
# composition.
# ----------------------------------------------------------
# no pitch smoothing, no C-major quantization,
# no duration quantization, dynamics without moving-average smoothing
# ----------------------------------------------------------
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
#######################################################################

import pandas as pd
import numpy as np
from scipy.signal import find_peaks, savgol_filter
from midiutil import MIDIFile
import matplotlib.pyplot as plt


# Load interferogram data with x-axis in OPD
file_path = '/Users/hmb/Desktop/DNA music/OPD corrected IFG baseline corrected.csv'  # Replace with your file path
data = pd.read_csv(file_path)

# Extract x (OPD) and y (Intensity) values
x_opd = data.iloc[:, 0].values  # X-axis: Optical Path Difference (cm)
y_intensity = data.iloc[:, 1].values  # Y-axis: Intensity

# Step 1: Preprocess the Interferogram
# Normalize intensity values between 0 and 1
y_normalized = (y_intensity - np.min(y_intensity)) / (np.max(y_intensity) - np.min(y_intensity))

# Smooth the interferogram using Savitzky-Golay filter
y_smoothed = savgol_filter(y_normalized, window_length=11, polyorder=3)

# Step 2: Extract Key Features
# Identify peaks in the smoothed interferogram with dynamic threshold and distance adjustments
peak_height_threshold = 0.1
peak_distance = 10
peaks, _ = find_peaks(y_smoothed, height=peak_height_threshold, distance=peak_distance)

# Extract peak intensities, distances, widths, and gradient information
peak_intensities = y_smoothed[peaks]
peak_distances = np.diff(x_opd[peaks])
peak_widths = np.diff(peak_distances, prepend=0)
peak_gradients = np.gradient(y_smoothed)[peaks]  # Intensity gradient at peaks

# ---------------------------------------
# Visualization: Smoothed interferogram with detected peaks
# ---------------------------------------
plt.figure(figsize=(10, 5))
plt.plot(x_opd, y_smoothed, label="Smoothed interferogram", linewidth=1.5)
plt.scatter(x_opd[peaks], y_smoothed[peaks], color="red", marker="x", label="Detected peaks")
plt.xlabel("Optical Path Difference (cm)")
plt.ylabel("Normalized Intensity (a.u.)")
plt.title("Smoothed Interferogram with Detected Peaks")
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend()
plt.savefig(
    "interferogram_with_peaks.pdf",
    format="pdf",
    dpi=300,
    transparent=True,
    bbox_inches="tight"
)
plt.close()

# Step 3: Map Features to Musical Parameters
scaling_factor = 2  # Adjusted scaling factor for frequency mapping
frequencies = scaling_factor / peak_distances

# Ensure frequencies are within the human auditory range
frequencies = np.clip(frequencies, 20, 20000)

# Map frequency to MIDI pitches (chromatic)
base_pitch = 69
pitches = 12 * np.log2(frequencies / 440) + base_pitch
pitches = np.clip(pitches, 21, 108)

# Dynamic range compression of pitches into MIDI range (same as sonic 5)
pitches = (pitches - np.min(pitches)) / (np.max(pitches) - np.min(pitches)) * 87 + 21

# Map peak intensities to dynamics (velocity)
scaling_dynamic = 1.2  # Scale factor for dynamics
dynamics = np.clip((peak_intensities * 127 * scaling_dynamic).astype(int), 0, 127)

# Add crescendos/decrescendos based on peak trends (no smoothing, as in sonic 5)
trends = np.gradient(peak_intensities)
trend_dynamics = np.where(trends > 0, dynamics + 10, dynamics - 10)
dynamics = np.clip(trend_dynamics, 0, 127)

# Map peak widths to note durations using logarithmic scaling
durations = np.log1p(peak_widths)
durations = np.clip(durations, 0.5, 2)

# Introduce rhythmic complexity (polyrhythms/syncopation)
syncopation_factor = 0.1
syncopated_durations = durations + (np.sin(np.arange(len(durations))) * syncopation_factor)

# Map spatialization based on peak positions (computed but not used in MIDI, as in sonic 5)
pan_values = (x_opd[peaks] - np.min(x_opd[peaks])) / (np.max(x_opd[peaks]) - np.min(x_opd[peaks]))

# Step 4: Tempo
tempo = 60  # Set a slower tempo (60 BPM)

# Function to decode MIDI pitches into note names
def midi_to_note_name(midi_pitches):
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    notes = []
    for pitch in midi_pitches:
        note = note_names[int(pitch) % 12]  # Get the note within an octave
        octave = int(pitch) // 12 - 1       # Calculate the octave number
        notes.append(f"{note}{octave}")
    return notes

# Decode the generated pitches (before any length trimming)
decoded_notes = midi_to_note_name(pitches)
print("Generated Notes:", decoded_notes)

# Visualize the decoded notes
plt.figure(figsize=(12, 6))
plt.bar(range(len(decoded_notes)), pitches, color='skyblue', label='MIDI Pitch')
plt.xticks(range(len(decoded_notes)), decoded_notes, rotation=45, ha='right')
plt.xlabel('Note Index')
plt.ylabel('MIDI Pitch')
plt.title('Decoded MIDI Notes')
plt.legend()
plt.grid()
plt.savefig('decoded_midi_notes.pdf', format='pdf', dpi=300, transparent=True, bbox_inches='tight')
plt.close()

# Step 5: Generate MIDI File
midi = MIDIFile(1)  # Single track
track = 0
time = 0
channel = 0

# Ask the user for their choice of instrumentation
choice = input("Choose instrumentation type (default/dynamic): ").strip().lower()
use_dynamic_instrumentation = (choice == "dynamic")

midi.addTrackName(track, time, "Interferogram Symphony")
midi.addTempo(track, time, tempo)

# Assign instruments (default: Acoustic Grand Piano)
default_instrument = 0  # Acoustic Grand Piano
dynamic_instruments = [
    0,  # Acoustic Grand Piano
    40,  # Violin
    42,  # Cello
    46,  # Harp
    56,  # Trumpet
    73   # Flute
]

# Ensure all parameters are the same length for MIDI writing
n_notes = min(len(peaks), len(pitches), len(dynamics), len(syncopated_durations))
peaks = peaks[:n_notes]
pitches = pitches[:n_notes]
dynamics = dynamics[:n_notes]
syncopated_durations = syncopated_durations[:n_notes]

if use_dynamic_instrumentation:
    print("Using dynamic instrumentation...")
    for i in range(n_notes):
        instrument_index = i % len(dynamic_instruments)  # Cycle through instruments
        midi.addProgramChange(track, channel, time, dynamic_instruments[instrument_index])
        pitch = int(pitches[i])
        velocity = int(dynamics[i])
        duration = float(syncopated_durations[i])
        midi.addNote(track, channel, pitch, time, duration, velocity)
        time += duration
else:
    print("Using default piano instrumentation...")
    midi.addProgramChange(track, channel, time, default_instrument)
    for i in range(n_notes):
        pitch = int(pitches[i])
        velocity = int(dynamics[i])
        duration = float(syncopated_durations[i])
        midi.addNote(track, channel, pitch, time, duration, velocity)
        time += duration

# Save the MIDI file (same name as in sonic 5 dyn enhanced.py)
midi_file_path = "Interferogram_Symphony_Enhanced.mid"
with open(midi_file_path, "wb") as midi_file:
    midi.writeFile(midi_file)

print(f"MIDI file saved at: {midi_file_path}")

# Step 6: Visualize Mapped Parameters (pitch + dynamics vs index)
plt.figure(figsize=(12, 6))
plt.bar(range(len(pitches)), pitches, color='blue', alpha=0.6, label='MIDI Pitches')
plt.plot(dynamics, color='red', marker='o', label='Dynamics (Velocity)')
plt.title('Mapped Musical Parameters')
plt.xlabel('Peak Index')
plt.ylabel('MIDI Pitch / Dynamics')
plt.legend()
plt.grid()
plt.savefig('mapped_parameters.pdf', format='pdf', dpi=300, transparent=True, bbox_inches='tight')
plt.close()

# Additional Data Visualization: Timeline (durations + dynamics vs index)
# Use the original durations & dynamics length (matches decoded_notes at this point)
plt.figure(figsize=(12, 6))
plt.plot(range(len(decoded_notes)), durations, label='Durations', marker='o')
plt.plot(range(len(decoded_notes)), dynamics[:len(decoded_notes)], label='Dynamics', marker='s')
plt.title('Timeline of Musical Parameters')
plt.xlabel('Note Index')
plt.ylabel('Parameter Value')
plt.legend()
plt.grid()
plt.savefig('timeline_parameters.pdf', format='pdf', dpi=300, transparent=True, bbox_inches='tight')
plt.close()
