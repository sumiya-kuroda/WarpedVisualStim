from psychopy import monitors
import numpy as np

mon_name = 'testMonitor'  # change this to your monitor name

mon = monitors.Monitor(mon_name)
print("Monitor: {}".format(mon_name))
print("All calibrations: {}".format(list(mon.calibs.keys())))
print("Current calibration: {}".format(mon.currentCalib))

gamma_grid = mon.getGammaGrid()
print("\nFull gamma grid:")
print(gamma_grid)
print("\nRow labels: 0=mean, 1=R, 2=G, 3=B")
print("Col labels: 0=lum_min, 1=lum_max, 2=gamma, 3=a, 4=b, 5=c, 6=lum_0")

if gamma_grid is not None:
    print("\nlum_min : {:.4f} cd/m2".format(gamma_grid[0, 0]))
    print("lum_max : {:.4f} cd/m2".format(gamma_grid[0, 1]))
    print("gamma R : {:.4f}".format(gamma_grid[1, 2]))
    print("gamma G : {:.4f}".format(gamma_grid[2, 2]))
    print("gamma B : {:.4f}".format(gamma_grid[3, 2]))
    print("gamma mean (row 0): {:.4f}".format(gamma_grid[0, 2]))