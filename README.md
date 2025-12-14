# Genomic-DNA-Sonification
## The Sonic Array of Rhythmic Alleles (SARA)
### Giving Voice to Genomic DNA Through FTIR Sonification

This repository contains the code for **SARA – The Sonic Array of Rhythmic Alleles**, a framework that converts **Fourier Transform Infrared (FTIR) spectra of genomic DNA** into structured **musical compositions**.

The pipeline implements:

- Reconstruction of **interferograms** from transmittance spectra (optional),
- Feature extraction from interferograms (peaks, spacing, widths, intensities),
- **Parameter-mapping sonification** of these features into:
  - pitch,
  - dynamics (loudness),
  - duration (rhythm),
  - spatialization (pan),
- Generation of **MIDI files** for listening, analysis, or performance,
- Quantitative **MIDI characterization**,
- Optional **trio arrangements** optimized for human listening (flute–viola–bassoon).

> If you use this code in research, teaching, or creative work, please cite the associated SARA manuscript.

---

## Dependencies

Tested with **Python 3.10+**.

Core packages:

- `numpy`  
- `pandas`  
- `matplotlib`  
- `seaborn`  
- `scipy`  
- `mido`  
- `midiutil`  
- `music21`  (for some arrangement scripts)

Install (for example):

```bash
pip install numpy pandas matplotlib seaborn scipy mido midiutil music21
```

---

## Workflow Overview

### 1. (Optional) Reconstruct interferogram from transmittance

**Script:** `IFFT_file.py`  

**Input:** CSV with **wavenumber (cm⁻¹)** and **normalized transmittance**.

The script:

- Sorts and interpolates the spectrum to a uniform wavenumber grid,  
- Converts to a simple “absorbance-like” spectrum (`1 − T`),  
- Mean-centers it to remove the DC component,  
- Applies an inverse FFT (IFFT) to approximate the interferogram,  
- Maps the result onto a symmetric OPD axis (e.g., −0.25 cm to +0.25 cm),  
- Saves: `interferogram_from_transmittance.csv`.

Usage: edit the `file_path` inside the script, then:

```bash
python IFFT_file.py
```

You can skip this step if you already have an interferogram in **OPD vs intensity** form.

---

### 2. Main sonification: interferogram → monophonic MIDI

**Script:** `SARA_IFG_to_MIDI.py`  

**Input:** CSV with **OPD (cm)** and **interferogram intensity**  
(e.g. `IFG.csv`).

**Preprocessing**

- Normalize intensities to [0, 1],  
- Smooth the interferogram using a Savitzky–Golay filter.

**Peak detection & feature extraction**

- Detect peaks in the smoothed interferogram,  
- Extract for each peak:
  - intensity,
  - spacing to the next peak (periodicity-like measure),
  - approximate width,
  - local intensity gradient.

**Mapping to musical parameters**

- **Pitch:**  
  - Peak spacing is converted into a frequency-like quantity,  
  - Frequencies are mapped to MIDI using a standard log formula,  
  - Pitches are smoothed and projected onto **C major**,  
  - Finally rescaled into the MIDI range [21, 108].

- **Dynamics (loudness):**  
  - Derived from normalized peak intensities,  
  - Smoothed with a short moving average,  
  - Slightly raised or lowered depending on the local intensity gradient to create gentle crescendos/decrescendos.

- **Duration:**  
  - Derived from peak widths using a simple nonlinear transform,  
  - Quantized and lightly modulated to introduce small rhythmic variations.

- **Pan (stereo position):**  
  - Mapped from normalized OPD position (0 → left, 1 → right).

- **Tempo:**  
  - Base tempo is **60 BPM**; a smoothly varying tempo curve can be computed but is not essential for basic use.

**MIDI generation**

- The script prompts for instrumentation:
  - `default` → single-instrument (piano-like) rendering,
  - `dynamic` → cycles through a small set of General MIDI instruments.
- Main output: **`harmonic_1.mid`**  
  (this is the primary monophonic SARA line analyzed in the manuscript).

**Figures produced (PDF, 300 dpi, transparent background)**

- `interferogram_with_peaks.pdf`  
- `decoded_midi_notes.pdf`  
- `mapped_parameters.pdf`  
- `timeline_parameters.pdf`  
- `heatmap_musical_parameters.pdf` (correlation of pitch, duration, dynamics, pan)

Usage (edit the CSV path at the top, then run):

```bash
python SARA_IFG_to_MIDI.py
```

---

### 3. MIDI characterization

**Script:** `MIDICharacterization.py`  

**Input:** a MIDI file (eg. `harmonic_1.mid`).

The script:

- Reads all note events,  
- Extracts:
  - pitches,
  - velocities (dynamics),
  - durations (in ticks),
  - basic timing information.

Generates:

- `pitch_distribution.pdf`  
  Histogram of MIDI pitches (used for pitch distribution analysis in the paper).

- `mapped_parameters.pdf`  
  Combined plot of pitch and dynamics vs note index.

- `dynamics_over_time.pdf`  
  Dynamics vs note index (expressive contour).

- `note_durations.pdf`  
  Distribution of note durations.

To analyze a different MIDI, edit:

```python
midi_file_path = "harmonic_1.mid"
```

and run:

```bash
python MIDICharacterization.py
```

---

### 4. Diatonic vs chromatic content (C-major analysis)

**Script:** `analyze_diatonic_fraction.py`  

**Input:** any MIDI file.

The script:

- Computes how many notes fall inside vs. outside **C major**,  
- Prints the fraction of **non-diatonic** notes and pitch-class counts.

Usage:

```bash
python analyze_diatonic_fraction.py harmonic_1.mid
```

This was used to verify the reported proportion of chromatic pitches in the manuscript.

---

### 5. Trio arrangements and merging (optional)

These scripts are **downstream arrangements** that take the monophonic SARA line (`harmonic_1.mid`) and re-voice it for a small ensemble. They do **not** change the underlying sonification mapping; they present it in a more idiomatic musical form.

#### a) Trio arrangement (flute–viola–bassoon)

**Script:** e.g. `trio_transformation.py`  

- Input: `harmonic_1.mid`.  
- Produces three monophonic parts:

  - **Flute**  
    - Main melodic line, snapped to C major, remapped to a higher register.

  - **Viola**  
    - Harmony line derived from intervals applied to the melody and remapped to a mid register.

  - **Bassoon**  
    - Low C3–G3 pedal / fifth pattern with softer dynamics, providing a harmonic foundation.

- Output example:

  - `Flute.mid`  
  - `Viola.mid`  
  - `Bassoon.mid`

#### b) Merge and pad into a synchronized trio

**Script:** e.g. `merge_trio_with_padding.py`  

**Input:**  
`Flute.mid`, `Viola.mid`, `Bassoon.mid`.

The script:

- Loads each part and normalizes `ticks_per_beat` if needed,  
- Preserves tempo / key meta from the first file,  
- Assigns each instrument to its own MIDI channel,  
- Pads shorter tracks so all three parts end together,  
- Ensures proper end-of-track markers.

**Output:**  
`Merged_Trio_FullPreservation_Padded.mid`  

This merged file is what you would typically import into a DAW or notation software for rendering and performance.
