# Genomic-DNA-Sonification
# The Sonic Array of Rhythmic Alleles (SARA)
### Giving Voice to Genomic DNA Through FTIR Sonification

This repository contains the analysis and sonification pipeline for **SARA – The Sonic Array of Rhythmic Alleles**, a framework that converts **FTIR spectra of genomic DNA** into structured **musical compositions**.

The code implements:

- Reconstruction of **interferograms** from transmittance spectra,
- Feature extraction from interferograms (peaks, distances, widths, intensities),
- **Parameter-mapping sonification** from spectral features to:
  - pitch,
  - dynamics (loudness),
  - duration (rhythm),
  - spatialization (pan),
- Generation of **MIDI files** suitable for analysis and performance,
- Quantitative **MIDI characterization**,
- Optional **harmonic arrangements** (duet and trio) optimized for human listening.

**If you use this code in research, teaching, or creative work, please cite the associated SARA manuscript.**
---
Dependencies

Tested with Python 3.10+.

Core packages:

numpy

pandas

matplotlib

seaborn

scipy

mido

midiutil

music21 (for some harmony experiments)

Install (for example):

pip install numpy pandas matplotlib seaborn scipy mido midiutil music21

Workflow Overview
1. (Optional) Reconstruct interferogram from transmittance

Script: IFFT_file.py

Input: CSV file with wavenumber (cm⁻¹) and normalized transmittance.

Steps:

Sorts and interpolates the spectrum to a uniform wavenumber grid,

Converts to an “absorbance-like” spectrum (1 - T),

Mean-centers to remove the DC component,

Uses inverse FFT (IFFT) to approximate the interferogram,

Maps the result onto a symmetric OPD axis (e.g., -0.25 cm to +0.25 cm),

Saves: interferogram_from_transmittance.csv.

Usage (edit the file path inside the script):

file_path = "data_examples/transmittance_example.csv"


Run:

python IFFT_file.py


You can skip this step if you already have an interferogram in OPD vs intensity form.

2. Main sonification: interferogram → monophonic MIDI

Script: SARA_IFG_to_MIDI.py

Input: CSV with OPD (cm) and interferogram intensity (e.g., OPD corrected IFG baseline corrected.csv).

Steps:

Preprocessing

Normalize intensity to [0, 1],

Smooth with a Savitzky–Golay filter.

Peak detection & feature extraction

Detect peaks along OPD,

Extract:

peak intensities,

inter-peak distances (periodicity),

approximate widths,

intensity gradients at peaks.

Mapping to musical parameters

Pitch:

Frequencies ∝ 1 / (inter-peak distance),

Mapped to MIDI using 12 * log2(f / 440) + 69,

Smoothed and snapped to C major,

Compressed into the MIDI range [21, 108].

Dynamics:

Derived from normalized peak intensities,

Smoothed and shaped with trend-based crescendos/decrescendos.

Duration:

Derived from peak widths using log(1 + width),

Quantized and lightly modulated for syncopation.

Pan:

Derived from normalized OPD position (0 → left, 1 → right).

Tempo

Base tempo = 60 BPM, with optional smooth variations (not required for basic use).

MIDI generation

Prompts for instrumentation:

default → single-instrument piano-like rendering,

dynamic → cycles through several General MIDI instruments.

Output: harmonic_1.mid

Output figures (PDFs, high-resolution, transparent background):

interferogram_with_peaks.pdf

decoded_midi_notes.pdf

mapped_parameters.pdf

timeline_parameters.pdf

heatmap_musical_parameters.pdf (correlation matrix of pitch, duration, dynamics, pan)

Usage (edit the CSV path at the top, then run):

python SARA_IFG_to_MIDI.py

3. Alternate mapping variant (v2) 

Script: SARA_IFG_to_MIDI_v2.py (name may differ slightly in your repo)

Same core logic as SARA_IFG_to_MIDI.py, but:

Uses slightly different mapping or smoothing choices.

Outputs a different main MIDI file, e.g.:

4. MIDI characterization

Script: MIDICharacterization.py

Input: a MIDI file (e.g. harmonic_1.mid).

Extracts:

pitches,

velocities (dynamics),

durations (in ticks),

index-based timing.

Produces:

pitch_distribution.pdf
Histogram of MIDI pitches – corresponds to pitch distribution analyses in the manuscript.

mapped_parameters.pdf
Combined plot of pitch and dynamics over note index.

dynamics_over_time.pdf
Dynamics vs note index, showing the expressive contour.

note_durations.pdf
Duration distribution across notes.

You can switch the input MIDI at the top:

midi_file_path = "midi_examples/harmonic_1.mid"


Run:

python MIDICharacterization.py

5. Trio arrangement and merging (optional)

If you include trio scripts, they follow a pattern like:

a) Trio arrangement script

Script: e.g. trio_arrangement_trio_script.py

Input: harmonic_1.mid.

Creates three parts (e.g., flute, viola, bassoon):

Flute:

Main melodic line, snapped to C major and remapped into a higher range.

Viola:

Harmonic line built via intervals (e.g., -3, -5, -7) and remapped into mid range.

Bassoon:

Pedal / fifth-based low pattern (e.g., alternating C3 and G3), softer dynamics.

Output: three separate MIDIs:

Flute.mid

Viola.mid

Bassoon.mid

b) Merge and pad into a synchronized trio

Script: merge_trio_with_padding.py (or similar)

Input:

Flute.mid, Viola.mid, Bassoon.mid.

Steps:

Loads each file,

Normalizes ticks_per_beat if needed,

Preserves tempo and key meta from the first file,

Assigns each instrument to its own MIDI channel,

Aligns and pads tracks so they end together,

Ensures proper end-of-track markers.

Output:

Merged_Trio_FullPreservation_Padded.mid (or similar name)

This is the version you’d typically export to audio (DAW / notation software).
