#######################################################################
#
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
#       * Pitch: derived from inter-peak distances and then
#         snapped to a C major scale,
#       * Dynamics (velocity): derived from peak intensities with
#         smoothed trend-based shaping,
#       * Duration: derived from peak width using log scaling and
#         mild syncopation,
#       * Pan: derived from OPD position and used for spatialization,
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
...
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
file_path = '/Users/hmb/Desktop/DNA music/Leonardo/src/data/OPD corrected IFG baseline corrected.csv'  # Replace with your file path
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
...
peaks, properties = find_peaks(
    y_smoothed,
    height=np.mean(y_smoothed) + 0.1 * np.std(y_smoothed),
    distance=5
)

# Extract peak positions (OPD), intensities, and distances between peaks
peak_positions = x_opd[peaks]
peak_intensities = y_smoothed[peaks]

# Compute inter-peak distances, widths, and gradients
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
plt.tight_layout()
# Save as high-resolution PDF for the manuscript
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
...
# Example harmonic mapping (placeholder)
# In practice, you would map to nearest C-major pitch class:
#   C, D, E, F, G, A, B  -> MIDI classes {0, 2, 4, 5, 7, 9, 11}
pitches_harmonic = pitches_smooth  # Replace with actual scale-snapping logic

# Map peak intensities to dynamics (MIDI velocities)
alpha = 1.0
dynamics_raw = alpha * peak_intensities * 127
dynamics_raw = np.clip(dynamics_raw, 0, 127)

# Smooth dynamics with a short moving average
window_size = 5
kernel = np.ones(window_size) / window_size
dynamics_smooth = np.convolve(dynamics_raw, kernel, mode="same")

# Adjust dynamics based on local intensity gradient:
#   positive gradient -> slightly louder, negative -> slightly softer
gradient_sign = np.sign(peak_gradients)
dynamics = dynamics_smooth + 10 * gradient_sign
dynamics = np.clip(dynamics, 0, 127)

# Map peak widths / distances to durations (in beats)
widths = np.abs(peak_widths) + 1e-6  # avoid log(0)
durations = np.log(1 + widths)
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
    note_names = ['C', 'C#', 'D', 'D#', 'E',
                  'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    decoded_notes = []
    for midi_value in midi_pitches:
        midi_int = int(round(midi_value))
        name = note_names[midi_int % 12]
        octave = (midi_int // 12) - 1
        decoded_notes.append(f"{name}{octave}")
    return decoded_notes

decoded_notes = midi_to_note_name(pitches)

# Step 5: Generate MIDI File
midi = MIDIFile(1)  # Single track
track = 0
time = 0
channel = 0

# Ask the user for their choice of instrumentation
choice = input("Choose instrumentation type (default/dynamic): ").strip().lower()
use_dynamic_instrumentation = (choice == "dynamic")

# Add tempo to the MIDI track
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
n_notes = min(len(peaks), len(pitches), len(dynamics), len(syncopated_durations), len(pan_values))
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
        # Map normalized pan value [0, 1] to MIDI pan controller [0, 127]
        pan_cc = int(np.clip(pan_values[i] * 127, 0, 127))
        midi.addControllerEvent(track, channel, time, 10, pan_cc)
        midi.addNote(track, channel, pitch, time, duration, velocity)
        time += duration
else:
    print("Using default piano instrumentation...")
    midi.addProgramChange(track, channel, time, default_instrument)
    for i in range(n_notes):
        pitch = int(pitches[i])
        velocity = int(dynamics[i])
        duration = float(syncopated_durations[i])
        pan_cc = int(np.clip(pan_values[i] * 127, 0, 127))
        midi.addControllerEvent(track, channel, time, 10, pan_cc)
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
plt.plot(range(len(decoded_notes)), durations, label='Note Durations (beats)', marker='o')
plt.plot(range(len(decoded_notes)), dynamics, label='Dynamics (Velocity)', marker='x')
plt.title('Note Durations and Dynamics Over Time')
plt.xlabel('Note Index')
plt.ylabel('Beats / Velocity')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.savefig('durations_dynamics_timeline.pdf', format='pdf', dpi=300, transparent=True, bbox_inches='tight')
plt.close()

# Step 7: DataFrame and Correlation Heatmap
df_params = pd.DataFrame({
    "Pitch": pitches,
    "Duration": durations,
    "Dynamics": dynamics,
    "Pan": pan_values
})

# Compute correlation matrix
corr_matrix = df_params.corr()

# Visualize correlation heatmap
plt.figure(figsize=(8, 6))
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
