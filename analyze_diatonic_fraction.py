#!/usr/bin/env python3
#######################################################################
#
#  Description:
#      Utility script to analyze the pitch content of a MIDI file with
#      respect to the C major scale. It counts how many notes are
#      diatonic (C, D, E, F, G, A, B in any octave) versus
#      non-diatonic, and reports both the absolute counts and the
#      fraction of non-diatonic pitches. The script also prints a
#      simple histogram of pitch classes (MIDI % 12).
#
#  Usage:
#      python analyze_diatonic_fraction.py <midi_file>
#
#  Author: Hasan Babazada, Ph.D.
#  Date:   02/20/2025
#  Email:  gasan4ik@hotmail.com
#
#  SPDX-License-Identifier: MIT
# #
# # This program is released under the MIT License.
# # See the LICENSE file in the repository root for the full text.
#
#######################################################################

from mido import MidiFile
import sys
from collections import Counter

# C major pitch classes in 12-TET (MIDI % 12)
C_MAJOR_PITCH_CLASSES = {0, 2, 4, 5, 7, 9, 11}  # C, D, E, F, G, A, B

def is_c_major(midi_note: int) -> bool:
    """Return True if the MIDI note belongs to C major (by pitch class)."""
    return (midi_note % 12) in C_MAJOR_PITCH_CLASSES

def analyze_midi(path: str):
    midi = MidiFile(path)
    notes = []

    # Collect all note_on events with velocity > 0 from all tracks
    for track in midi.tracks:
        for msg in track:
            if msg.type == "note_on" and msg.velocity > 0:
                notes.append(msg.note)

    if not notes:
        print(f"No note_on events with velocity > 0 found in {path}.")
        return

    total_notes = len(notes)
    diatonic_notes = sum(1 for n in notes if is_c_major(n))
    non_diatonic_notes = total_notes - diatonic_notes

    percent_non_diatonic = 100.0 * non_diatonic_notes / total_notes

    # Optional: show histogram of pitch classes
    pcs = [n % 12 for n in notes]
    pc_counts = Counter(pcs)

    print(f"File: {path}")
    print(f"Total notes:           {total_notes}")
    print(f"Diatonic (C major):    {diatonic_notes}")
    print(f"Non-diatonic:          {non_diatonic_notes}")
    print(f"Non-diatonic fraction: {percent_non_diatonic:.2f} %")
    print("\nPitch-class counts (MIDI % 12):")
    for pc in sorted(pc_counts.keys()):
        print(f"  PC {pc:2d}: {pc_counts[pc]}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_diatonic_fraction.py <midi_file>")
        sys.exit(1)

    midi_path = sys.argv[1]
    analyze_midi(midi_path)
