#######################################################################
#
# SARA_IFG_to_MIDI.py
#
# This script implements the core sonification pipeline for
# converting an interferogram of genomic DNA into a monophonic MIDI
# composition.
#
# Functionality:
#   - Loads interferogram data (OPD vs intensity) from a CSV file,
#   - Normalizes and smooths the interferogram (Savitzky–Golay filter),
#   - Detects peaks and extracts key features:
#       * peak positions (OPD),
#       * peak intensities,
#       * inter-peak distances,
#       * peak widths and gradients,
#   - Maps these features to musical parameters:
#       * Pitch: derived from inter-peak distances, mapped via
#         an inverse-distance relation and snapped to a C major scale,
#       * Dynamics (velocity): derived from peak intensities with
#         smoothed trend-based shaping,
#       * Duration: derived from peak width using log scaling and
#         mild syncopation,
#       * Pan: derived from OPD position and used as an analytic
#         spatial parameter (included in the correlation analysis
#         but not rendered as stereo panning in this script),
#   - Generates the primary MIDI file with optional
#     dynamic instrumentation,
#   - Produces high-resolution figures for analysis:
#       * Smoothed interferogram with detected peaks,
#       * Decoded MIDI note plot,
#       * Mapped musical parameters (pitch + dynamics),
#       * Timeline of durations and dynamics,
#       * Correlation heatmap of pitch, duration, dynamics, and pan.
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
import seaborn as sns
from scipy.interpolate import interp1d

# Load interferogram data with x-axis in OPD
file_path = 'PATH to interferogram .csv file'  # Replace with your file path
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
plt.scatter(x_opd[peaks], y_smoothed[peaks], color="red", marker="o", label="Detected peaks")
plt.xlabel("Optical Path Difference (cm)")
plt.ylabel("Normalized Intensity (a.u.)")
plt.title("Smoothed Interferogram with Detected Peaks")
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend()

# Save as high-resolution PDF
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

# Smooth the pitches for gradual transitions
pitches_smooth = savgol_filter(pitches, window_length=7, polyorder=2)

# Map smoothed pitches to a harmonic scale (C major)
scale = [60, 62, 64, 65, 67, 69, 71]  # C Major scale
pitches_harmonic = [scale[int(p % len(scale))] for p in pitches_smooth]

# Map peak intensities to dynamics (velocity) with scaling for smoother variations
scaling_dynamic = 1.2  # Scale factor for dynamics
dynamics = np.clip((peak_intensities * 127 * scaling_dynamic).astype(int), 0, 127)

# Smooth dynamics using a moving average
window_size = 5
dynamics_smooth = np.convolve(dynamics, np.ones(window_size) / window_size, mode='same')

# Add crescendos/decrescendos based on peak trends
trends = np.gradient(peak_intensities)
trend_dynamics = np.where(trends > 0, dynamics_smooth + 10, dynamics_smooth - 10)
dynamics = np.clip(trend_dynamics, 0, 127)

# Map peak widths to note durations using logarithmic scaling
durations = np.log1p(peak_widths)
durations = np.clip(durations, 0.5, 2)

# Quantize durations to the nearest 0.5 (e.g., eighth notes)
quantized_durations = np.round(durations * 2) / 2

# Introduce rhythmic complexity (polyrhythms/syncopation)
syncopation_factor = 0.1
syncopated_durations = quantized_durations + (np.sin(np.arange(len(quantized_durations))) * syncopation_factor)

# Map spatialization based on peak positions
pan_values = (x_opd[peaks] - np.min(x_opd[peaks])) / (np.max(x_opd[peaks]) - np.min(x_opd[peaks]))

# Dynamic range compression of pitches into full MIDI range
pitches = (pitches_harmonic - np.min(pitches_harmonic)) / (np.max(pitches_harmonic) - np.min(pitches_harmonic)) * 87 + 21

# Step 4: Adjust Tempo and Dynamics
tempo = 60  # Set a slower tempo (60 BPM)

# Smooth tempo variations using interpolation
tempo_variations = 60 + (np.gradient(peaks) * 10) + (np.gradient(peak_intensities) * 5)
tempo_variations = np.clip(tempo_variations, 40, 120)  # Clamp tempo to a reasonable range
tempo_x = np.linspace(0, len(tempo_variations) - 1, num=len(tempo_variations))
tempo_interp = interp1d(tempo_x, tempo_variations, kind='cubic')
tempo_smooth = tempo_interp(tempo_x)

# Ensure all arrays have the same length for plotting / MIDI writing
min_length = min(len(pitches), len(dynamics), len(syncopated_durations), len(pan_values), len(tempo_smooth), len(durations))
pitches = pitches[:min_length]
dynamics = dynamics[:min_length]
syncopated_durations = syncopated_durations[:min_length]
pan_values = pan_values[:min_length]
tempo_smooth = tempo_smooth[:min_length]
durations = durations[:min_length]  # keep durations aligned for plotting

# Function to decode MIDI pitches into note names
def midi_to_note_name(midi_pitches):
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    notes = []
    for pitch in midi_pitches:
        note = note_names[int(pitch) % 12]  # Get the note within an octave
        octave = int(pitch) // 12 - 1       # Calculate the octave number
        notes.append(f"{note}{octave}")
    return notes

# Decode the generated pitches
decoded_notes = midi_to_note_name(pitches)
print("Generated Notes:", decoded_notes)

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
    0,   # Acoustic Grand Piano
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

# Save the MIDI file
midi_file_path = "harmonic_1.mid"
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
plt.figure(figsize=(12, 6))
plt.plot(range(len(decoded_notes)), durations, label='Durations', marker='o')
plt.plot(range(len(decoded_notes)), dynamics, label='Dynamics', marker='s')
plt.title('Timeline of Musical Parameters')
plt.xlabel('Note Index')
plt.ylabel('Parameter Value')
plt.legend()
plt.grid()
plt.savefig('timeline_parameters.pdf', format='pdf', dpi=300, transparent=True, bbox_inches='tight')
plt.close()

# ---- Correlation Heatmap of Musical Parameters (Pitch, Duration, Dynamics, Pan) ----
# For correlation, use:
#   - pitches_harmonic     (before final rescaling)
#   - syncopated_durations (final rhythmic values used in the piece)
#   - dynamics_smooth      (before trend-based +/-10)
#   - pan_values

min_length_corr = min(
    len(pitches_harmonic),
    len(syncopated_durations),
    len(dynamics_smooth),
    len(pan_values)
)

pitch_corr = np.array(pitches_harmonic[:min_length_corr])
dur_corr = np.array(syncopated_durations[:min_length_corr])
dyn_corr = np.array(dynamics_smooth[:min_length_corr])
pan_corr = np.array(pan_values[:min_length_corr])

heatmap_df = pd.DataFrame({
    "Pitch": pitch_corr,
    "Duration": dur_corr,
    "Dynamics": dyn_corr,
    "Pan": pan_corr
})

# Optional sanity check: make sure we actually have variance
print("Std devs (Pitch, Duration, Dynamics, Pan):",
      pitch_corr.std(), dur_corr.std(), dyn_corr.std(), pan_corr.std())

corr_matrix = heatmap_df.corr()
print("Correlation matrix (Pitch, Duration, Dynamics, Pan):")
print(corr_matrix.round(2))

plt.figure(figsize=(6, 5))
sns.heatmap(
    corr_matrix,
    annot=True,
    vmin=-1,
    vmax=1,
    cmap="coolwarm",
    square=True,
    cbar=True,
    xticklabels=corr_matrix.columns,
    yticklabels=corr_matrix.columns
)
plt.title("Correlation Matrix of Musical Parameters")
plt.tight_layout()
plt.savefig('heatmap_musical_parameters.pdf', format='pdf', dpi=300, transparent=True, bbox_inches='tight')
plt.close()
