"""
Print a PsychoPy monitor's gamma calibration.

Usage: python gamma/check.py [--monitor testMonitor] [--calib 2026_11_21]
Without --calib the most recent calibration is shown (same as the experiments).
"""
import argparse

import numpy as np
from WarpedVisualStim.tools.GammaTools import load_gamma_calibration

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--monitor', default='testMonitor')
parser.add_argument('--calib', default=None)
args = parser.parse_args()

mon, calib_name, gamma_grid = load_gamma_calibration(args.monitor, args.calib)

if gamma_grid is not None:
    np.set_printoptions(precision=4, suppress=True)
    print("\nFull gamma grid:")
    print(gamma_grid)
    print("Row labels: 0=mean, 1=R, 2=G, 3=B")
    print("Col labels: 0=lum_min, 1=lum_max, 2=gamma, 3=a, 4=b, 5=k")

    print("\nlum_min : {:.4f} cd/m2".format(gamma_grid[0, 0]))
    print("lum_max : {:.4f} cd/m2".format(gamma_grid[0, 1]))
    print("gamma R : {:.4f}".format(gamma_grid[1, 2]))
    print("gamma G : {:.4f}".format(gamma_grid[2, 2]))
    print("gamma B : {:.4f}".format(gamma_grid[3, 2]))
    print("gamma mean (row 0, used for correction): {:.4f}".format(gamma_grid[0, 2]))

    levels, lums = mon.getLevelsPre(), mon.getLumsPre()
    if levels is not None and lums is not None:
        print("\nMeasured luminance (cd/m2) per DAC level:")
        print("  level: {}".format(list(np.asarray(levels).astype(int))))
        print("  lum  : {}".format(np.round(np.asarray(lums)[0], 2).tolist()))
