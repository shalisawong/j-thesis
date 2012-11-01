from __future__ import division # float division by default
import math

def correlate_circuits(entry_circ,exit_circ):
    # the first cell recorded at the entry is from the circuit creation at
    # the middle router, so we ignore it.
    entry_begin = entry_circ.cells_in[1][0]
    entry_end   = entry_circ.cells_in[-1][0]
    entry_count = len(entry_circ.cells_in)-1

    exit_begin = exit_circ.cells_in[0][0]
    exit_end   = exit_circ.cells_in[-1][0]
    exit_count = len(exit_circ.cells_in)

    total_count = entry_count + exit_count
    start_diff = abs(exit_begin-entry_begin)
    count_diff = abs(exit_count-entry_count)

    # Correlation formula:
    #  20000 - start_diff   total_count - count_diff
    #  ------------------ * ------------------------
    #        20000                 total_count

    # times are in ms, so 20000ms is 20 seconds
    time_part = (20000 - start_diff) / 20000
    count_part = (total_count - count_diff) / total_count

    return time_part * count_part

