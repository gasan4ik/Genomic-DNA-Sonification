#######################################################################
#
#  IFFT_file.py
#
# This script demonstrates reconstruction of an
# interferogram from a transmittance spectrum using an inverse
# Fourier transform (IFFT).
#
# The transmittance spectrum is:
#   - loaded from a CSV file (wavenumber vs. normalized transmittance),
#   - interpolated to a uniform wavenumber grid,
#   - converted to an "absorbance-like" spectrum (1 - T),
#   - mean-centered to remove the DC component,
#   - transformed using IFFT to produce an interferogram-like signal.
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

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from numpy.fft import ifft, fftshift

# ----------------------------------------------------------------------
# Configuration (adjust as needed)
# ----------------------------------------------------------------------

# Path to input CSV file
# Expected format by default:
#   column 0: wavenumber (cm^-1)
#   column 1: normalized transmittance (arbitrary units)
INPUT_CSV_PATH = "PATH to csv file"  # <-- set this to your file

# Column indices (0-based)
WAVENUMBER_COL = 0
TRANSMITTANCE_COL = 1

# OPD range (cm) for the reconstructed interferogram
OPD_MIN = -0.25
OPD_MAX = 0.25

# Zoom range (cm) for the interferogram plot
ZOOM_MIN = -0.25
ZOOM_MAX = 0.25

# Output CSV for the reconstructed interferogram
OUTPUT_CSV_PATH = "interferogram_from_transmittance.csv"

def main():
  
    # 1. Load transmittance spectrum
   
    data = pd.read_csv(INPUT_CSV_PATH)

    # Extract wavenumber (cm^-1) and transmittance values
    wavenumber = data.iloc[:, WAVENUMBER_COL].values
    transmittance = data.iloc[:, TRANSMITTANCE_COL].values

    # Sort by wavenumber in ascending order (in case the file is descending)
    sort_idx = np.argsort(wavenumber)
    wavenumber_sorted = wavenumber[sort_idx]
    transmittance_sorted = transmittance[sort_idx]

   
    # 2. Interpolate to a uniform wavenumber grid
    
    num_points = len(wavenumber_sorted)
    uniform_wavenumber = np.linspace(
        wavenumber_sorted.min(),
        wavenumber_sorted.max(),
        num_points
    )
    uniform_transmittance = np.interp(
        uniform_wavenumber,
        wavenumber_sorted,
        transmittance_sorted
    )

    
    # 3. Preprocess spectrum for IFFT
    
    # Scale T to ~0–1, convert to 1 - T, remove DC
    T_scaled = uniform_transmittance / np.max(uniform_transmittance)
    spectrum_for_ifft = 1.0 - T_scaled
    spectrum_for_ifft = spectrum_for_ifft - spectrum_for_ifft.mean()  # DC removal

   
    # 4. Inverse Fourier transform to get approximate interferogram
    
    interferogram_raw = ifft(spectrum_for_ifft)
    interferogram = np.real(fftshift(interferogram_raw))  # center main lobe

    
    # 5. Construct OPD axis
   
    opd = np.linspace(OPD_MIN, OPD_MAX, num_points)  # Optical Path Difference (cm)

    
    # 6. Plot the transmittance spectrum
    
    plt.figure(figsize=(10, 5))
    # Plot in standard FTIR style: high wavenumber on the left
    plt.plot(uniform_wavenumber[::-1], T_scaled[::-1], label="Transmittance (scaled)")
    plt.gca().invert_xaxis()
    plt.xlabel("Wavenumber (cm⁻¹)")
    plt.ylabel("Transmittance (a.u.)")
    plt.title("Normalized Transmittance Spectrum")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()

    
    # 7. Plot the approximate interferogram (zoomed around center)
    
    plt.figure(figsize=(10, 5))
    plt.plot(opd, interferogram, label="Approximate Interferogram")
    plt.xlabel("Optical Path Difference (cm)")
    plt.ylabel("Intensity (a.u.)")
    plt.title("Approximate Interferogram from IFFT of Transmittance")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()

    # Zoom in around the center if necessary
    plt.xlim(ZOOM_MIN, ZOOM_MAX)

    plt.tight_layout()
    plt.show()

   
    # 8. Save interferogram to CSV
    
    output_data = pd.DataFrame({
        "OPD (cm)": opd,
        "Interferogram Intensity": interferogram
    })
    output_data.to_csv(OUTPUT_CSV_PATH, index=False)

    print(f"Interferogram saved to: {OUTPUT_CSV_PATH}")


if __name__ == "__main__":
    main()
