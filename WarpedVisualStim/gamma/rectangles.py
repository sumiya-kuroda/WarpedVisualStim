"""
Show black / gray / white rectangles exactly as the experiments show them
(stimulus values -1 / 0 / 1 -> luminance remap -> inverse gamma), so you can
check them with a photometer (e.g. ColorCAL).

Usage (from the WarpedVisualStim package folder):
    python gamma/rectangles.py                       # wf-370_skuroda protocol
    python gamma/rectangles.py --protocol wf-370_test
    python gamma/rectangles.py --calib 2026_11_21    # pick a calibration
Monitor, screen, "mon_luminance" and "gamma_calib" are read from the protocol.
"""
import argparse

import numpy as np
from psychopy import visual, core, event

from WarpedVisualStim.tools.FileTools import load_protocol, get_abspath
from WarpedVisualStim.tools.GammaTools import (load_gamma_calibration,
                                               stim_to_display,
                                               display_to_luminance)


def get_gamma_grid(monitor_name='testMonitor', calib_name=None):
    """Get gamma grid from calibration (most recent one if calib_name is None)."""
    _, _, gamma_grid = load_gamma_calibration(monitor_name, calib_name)
    if gamma_grid is None:
        raise ValueError("No gamma calibration found for '{}'".format(monitor_name))
    return gamma_grid


def apply_gamma_correction(color, gamma_grid, luminance=None):
    """
    Convert an RGB color in [-1, 1] to display values (luminance remap if
    `luminance` is given, then inverse gamma). Same conversion as
    DisplaySequence. Returns a list of floats in [-1, 1].
    """
    return stim_to_display(color, gamma_grid, luminance, verbose=False).tolist()


def show_three_rectangles(monitor_name='testMonitor', luminance=None,
                          calib_name=None, screen=1):
    """
    Parameters
    ----------
    monitor_name : str
        PsychoPy monitor profile name
    luminance : list/tuple of (lum_black, lum_white) in cd/m2, optional
        target luminance, as "mon_luminance" in the protocol. e.g. (0.24, 100.)
        shows black=0.24, gray=50.12, white=100 cd/m2. If None, -1/0/1 use the
        monitor's full measured range.
    calib_name : str, optional
        calibration to use; most recent one if None
    screen : int
        stimulus screen number
    """
    gamma_grid = get_gamma_grid(monitor_name, calib_name)

    stim_values = np.array([-1., 0., 1.])                       # black, gray, white
    display_values = stim_to_display(stim_values, gamma_grid, luminance)
    expected_lum = display_to_luminance(display_values, gamma_grid)

    print("\n--- Rectangles (left to right) ---")
    for name, s, d, L in zip(['black', 'gray', 'white'], stim_values,
                             display_values, expected_lum):
        print("  {:5s}: stimulus {:+.0f} -> display value {:+.4f} -> expected {:.2f} cd/m2".format(
            name, s, d, L))
    print("Measure each rectangle with the photometer and compare.")
    print("Press q / escape / space / return to quit.\n")

    black, gray, white = [[float(d)] * 3 for d in display_values]

    win = visual.Window(
        size=[800, 600],
        color=gray,
        units="pix",
        screen=screen,
        gamma=1.0,
        gammaErrorPolicy="ignore",
    )

    width = 200
    height = 300

    rects = [visual.Rect(win, width=width, height=height, fillColor=black, pos=(-250, 0)),
             visual.Rect(win, width=width, height=height, fillColor=gray, pos=(0, 0)),
             visual.Rect(win, width=width, height=height, fillColor=white, pos=(250, 0))]

    while True:
        for r in rects:
            r.draw()
        win.flip()
        keys = event.getKeys(keyList=['q', 'escape', 'space', 'return'])
        if keys:
            print("Key pressed: {}".format(keys[0]))
            break

    win.close()
    core.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--protocol', default='wf-370_skuroda',
                        help="protocol name in protocols/ (without .json)")
    parser.add_argument('--calib', default=None,
                        help="gamma calibration name (default: protocol's "
                             "'gamma_calib', else the most recent)")
    args = parser.parse_args()

    protocol = load_protocol(get_abspath('protocols/{}.json'.format(args.protocol),
                                         pathlib=False))
    print("Protocol: {}".format(args.protocol))
    show_three_rectangles(monitor_name=protocol["ds_stimulus_mon"],
                          luminance=protocol["mon_luminance"],
                          calib_name=args.calib or protocol.get("gamma_calib"),
                          screen=protocol["ds_stimulus_screen"])
