"""
Helpers for loading PsychoPy monitor gamma calibrations.

Every place that applies gamma correction should load the calibration through
`load_gamma_calibration`, so the calibration in use is always printed and can
be chosen explicitly (default: the most recent one).
"""
import time

import numpy as np
from psychopy import monitors


def _calib_date(calib):
    """Return the calibration date as seconds since epoch (or -inf)."""
    date = calib.get('calibDate')
    if isinstance(date, time.struct_time):
        return time.mktime(date)
    try:
        return float(date)
    except (TypeError, ValueError):
        return float('-inf')


def load_gamma_calibration(monitor_name, calib_name=None, verbose=True):
    """
    Load a gamma calibration from a PsychoPy monitor profile.

    Parameters
    ----------
    monitor_name : str
        PsychoPy monitor profile name (as in Monitor Center).
    calib_name : str, optional
        name of the calibration to use. If None, the most recent calibration
        (by calibration date) is used.
    verbose : bool
        print which calibration is used and its gamma values.

    Returns
    -------
    mon : psychopy.monitors.Monitor
        monitor with the chosen calibration set as current.
    calib_name : str or None
        name of the calibration used (None if the monitor has none).
    gamma_grid : ndarray or None
        4x6 gamma grid (rows: lum, R, G, B; cols: min, max, gamma, a, b, k).
    """
    mon = monitors.Monitor(monitor_name, verbose=False)

    if len(mon.calibNames) == 0:
        if verbose:
            print("Gamma: monitor '{}' has no calibrations.".format(monitor_name))
        return mon, None, None

    if calib_name is None:
        calib_name = max(mon.calibNames, key=lambda n: _calib_date(mon.calibs[n]))
        how = "most recent"
    elif calib_name in mon.calibNames:
        how = "selected"
    else:
        raise ValueError("Gamma calibration '{}' not found for monitor '{}'. "
                         "Available: {}".format(calib_name, monitor_name,
                                                mon.calibNames))
    mon.setCurrent(calib_name)
    gamma_grid = mon.getGammaGrid()

    if verbose:
        date = _calib_date(mon.currentCalib)
        date_str = (time.strftime('%Y-%m-%d %H:%M', time.localtime(date))
                    if date != float('-inf') else 'unknown')
        print("Gamma: monitor '{}', calibration '{}' ({}, date {})".format(
            monitor_name, calib_name, how, date_str))
        print("       available calibrations: {}".format(mon.calibNames))
        if gamma_grid is None:
            print("       no gamma grid in this calibration.")
        else:
            print("       gamma lum={:.4f} R={:.4f} G={:.4f} B={:.4f}, "
                  "luminance {:.3f}-{:.3f} cd/m2, fit formula (linearizeMethod)={}".format(
                      gamma_grid[0, 2], gamma_grid[1, 2], gamma_grid[2, 2],
                      gamma_grid[3, 2], gamma_grid[0, 0], gamma_grid[0, 1],
                      mon.getLinearizeMethod()))

    return mon, calib_name, gamma_grid


def stim_to_display(values, gamma_grid, luminance=None, verbose=True):
    """
    Convert stimulus values in [-1, 1] to the display values to send to
    PsychoPy (gamma=1.0), so that they appear at the intended luminance.

    1. if `luminance` is given, -1/+1 are remapped to the target luminance
       (black, white) in cd/m2, relative to the monitor's measured range
       (gamma_grid[0, 0:2]); 0 becomes their mean.
    2. inverse gamma correction with gamma_grid[0, 2] (simple power law).

    Parameters
    ----------
    values : array-like
        stimulus values in [-1, 1] (any shape, NaN allowed).
    gamma_grid : ndarray
        gamma grid from `load_gamma_calibration`.
    luminance : list/tuple of two floats, optional
        target (black, white) luminance in cd/m2. If None, -1/+1 map to the
        monitor's full measured range.
    verbose : bool
        print the luminance remap and gamma used.

    Returns
    -------
    ndarray (float32) of display values in [-1, 1], same shape as `values`.
    """
    # row 0 = mean/luminance, row 1=R, 2=G, 3=B; col 0/1 = min/max lum, col 2 = gamma
    lum_min, lum_max, gamma = gamma_grid[0, 0], gamma_grid[0, 1], gamma_grid[0, 2]

    vals_01 = (np.asarray(values, dtype=np.float32) + 1.) / 2.

    if luminance is not None:
        target_min, target_max = luminance
        if verbose:
            print("Luminance remap: black={:.2f}, gray={:.2f}, white={:.2f} cd/m2 "
                  "(monitor range {:.2f}-{:.2f} cd/m2)".format(
                      target_min, (target_min + target_max) / 2., target_max,
                      lum_min, lum_max))
            if target_min < lum_min or target_max > lum_max:
                print("Warning: target luminance outside the monitor range, "
                      "values will be clipped.")
        vals_lum = target_min + vals_01 * (target_max - target_min)   # cd/m2
        vals_01 = (vals_lum - lum_min) / (lum_max - lum_min)          # fraction of monitor range

    if verbose:
        print("Applying inverse gamma correction: gamma={:.4f}".format(gamma))

    vals_01 = np.clip(vals_01, 0., 1.)
    return np.power(vals_01, 1.0 / gamma) * 2. - 1.


def display_to_luminance(display_values, gamma_grid):
    """Predicted luminance (cd/m2) of display values in [-1, 1], from the
    calibration fit. Useful to check what a photometer should read."""
    lum_min, lum_max, gamma = gamma_grid[0, 0], gamma_grid[0, 1], gamma_grid[0, 2]
    vals_01 = np.clip((np.asarray(display_values, dtype=np.float32) + 1.) / 2., 0., 1.)
    return lum_min + (lum_max - lum_min) * np.power(vals_01, gamma)
