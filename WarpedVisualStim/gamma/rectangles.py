from psychopy import visual, core, event, monitors
import numpy as np


def get_gamma_grid(monitor_name='testMonitor'):
    """Get full gamma grid from calibration."""
    mon = monitors.Monitor(monitor_name)
    print("Monitor: {}".format(monitor_name))
    print("Using calibration: {}".format(mon.currentCalib))
    gamma_grid = mon.getGammaGrid()
    if gamma_grid is None:
        raise ValueError("No gamma calibration found for '{}'".format(monitor_name))
    print("Gamma grid:")
    print("  R: lum=[{:.4f}, {:.4f}], gamma={:.4f}".format(
        gamma_grid[1, 0], gamma_grid[1, 1], gamma_grid[1, 2]))
    print("  G: lum=[{:.4f}, {:.4f}], gamma={:.4f}".format(
        gamma_grid[2, 0], gamma_grid[2, 1], gamma_grid[2, 2]))
    print("  B: lum=[{:.4f}, {:.4f}], gamma={:.4f}".format(
        gamma_grid[3, 0], gamma_grid[3, 1], gamma_grid[3, 2]))
    print("  mean: lum=[{:.4f}, {:.4f}], gamma={:.4f}".format(
        gamma_grid[0, 0], gamma_grid[0, 1], gamma_grid[0, 2]))
    return gamma_grid


def apply_gamma_correction(color, gamma_grid):
    """
    Apply inverse gamma correction to RGB color in [-1, 1].
    Uses row 0 gamma (white patch measurement) uniformly across channels.

    Parameters
    ----------
    color : list of 3 floats in [-1, 1]
    gamma_grid : ndarray from mon.getGammaGrid()

    Returns
    -------
    list of 3 floats in [-1, 1]
    """
    gamma = gamma_grid[0, 2]  # row 0 = white patch gamma
    color_arr = np.array(color, dtype=np.float32)
    c_01 = np.clip((color_arr + 1.) / 2., 0., 1.)
    c_corrected = np.power(c_01, 1.0 / gamma)
    return (c_corrected * 2. - 1.).tolist()


def luminance_to_psychopy(target_lum, gamma_grid):
    """
    Convert target total luminance (cd/m2) to normalized [-1, 1] value
    using row 0 (white patch measurement) from gamma grid.
    Does NOT apply gamma — pass result through apply_gamma_correction afterwards.

    Parameters
    ----------
    target_lum : float
        target luminance in cd/m2
    gamma_grid : ndarray from mon.getGammaGrid()

    Returns
    -------
    float in [-1, 1]
    """
    lum_min = gamma_grid[0, 0]  # white patch black level
    lum_max = gamma_grid[0, 1]  # white patch max luminance

    if target_lum < lum_min or target_lum > lum_max:
        raise ValueError("Target luminance {:.2f} cd/m2 outside monitor range "
                         "[{:.4f}, {:.4f}]".format(target_lum, lum_min, lum_max))

    lum_01 = (target_lum - lum_min) / (lum_max - lum_min)
    return float(np.clip(lum_01, 0., 1.) * 2. - 1.)


def show_three_rectangles(monitor_name='testMonitor', luminance=None):
    """
    Parameters
    ----------
    monitor_name : str
        PsychoPy monitor profile name
    luminance : tuple of (lum_black, lum_white) in cd/m2, optional
        e.g. (0., 20.) maps black=0, gray=10, white=20 cd/m2
        if None, uses full [-1, 1] range with gamma correction only
    """
    gamma_grid = get_gamma_grid(monitor_name)

    print("\n--- Luminance pipeline diagnostics ---")

    if luminance is not None:
        lum_target_min, lum_target_max = luminance
        lum_target_mid = (lum_target_min + lum_target_max) / 2.
        print("Target luminance: black={:.2f}, gray={:.2f}, white={:.2f} cd/m2".format(
            lum_target_min, lum_target_mid, lum_target_max))

        # step 1: convert target cd/m2 to [-1,1] using white measurement (row 0)
        print("\nBefore gamma correction (normalized [-1,1]):")
        black_val = luminance_to_psychopy(lum_target_min, gamma_grid)
        gray_val  = luminance_to_psychopy(lum_target_mid,  gamma_grid)
        white_val = luminance_to_psychopy(lum_target_max, gamma_grid)
        print("  black_val: {}".format(black_val))
        print("  gray_val:  {}".format(gray_val))
        print("  white_val: {}".format(white_val))

        # step 2: apply per-channel inverse gamma
        black_corrected = apply_gamma_correction([black_val] * 3, gamma_grid)
        gray_corrected  = apply_gamma_correction([gray_val]  * 3, gamma_grid)
        white_corrected = apply_gamma_correction([white_val] * 3, gamma_grid)
    else:
        black_corrected = apply_gamma_correction([-1., -1., -1.], gamma_grid)
        gray_corrected  = apply_gamma_correction([ 0.,  0.,  0.], gamma_grid)
        white_corrected = apply_gamma_correction([ 1.,  1.,  1.], gamma_grid)

    print("\nAfter gamma correction (sent to PsychoPy):")
    print("  black_corrected: {}".format(black_corrected))
    print("  gray_corrected:  {}".format(gray_corrected))
    print("  white_corrected: {}".format(white_corrected))

    win = visual.Window(
        size=[800, 600],
        color=gray_corrected,
        units="pix",
        screen=2,
        gamma=1.0,
        gammaErrorPolicy="ignore",
    )

    width = 200
    height = 300

    rect_black = visual.Rect(win, width=width, height=height,
                             fillColor=black_corrected, pos=(-250, 0))
    rect_gray  = visual.Rect(win, width=width, height=height,
                             fillColor=gray_corrected,  pos=(0, 0))
    rect_white = visual.Rect(win, width=width, height=height,
                             fillColor=white_corrected, pos=(250, 0))

    print("\nActual fillColor set on rects (as seen by PsychoPy):")
    print("  rect_black.fillColor: {}".format(rect_black.fillColor))
    print("  rect_gray.fillColor:  {}".format(rect_gray.fillColor))
    print("  rect_white.fillColor: {}".format(rect_white.fillColor))
    print("--------------------------------------\n")

    rect_black.draw()
    rect_gray.draw()
    rect_white.draw()
    win.flip()

    while True:
        rect_black.draw()
        rect_gray.draw()
        rect_white.draw()
        win.flip()
        keys = event.getKeys(keyList=['q', 'escape', 'space', 'return'])
        if keys:
            print("Key pressed: {}".format(keys[0]))
            break

    win.close()
    core.quit()


if __name__ == "__main__":
    show_three_rectangles(monitor_name='testMonitor',
                          luminance=(0.16, 17.))