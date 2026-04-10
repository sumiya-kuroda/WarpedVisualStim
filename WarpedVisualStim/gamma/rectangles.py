from psychopy import visual, core, event, monitors
import numpy as np

def apply_gamma_correction(sequence, monitor_name='testMonitor'):
    mon = monitors.Monitor(monitor_name)
    print("Monitor: {}".format(monitor_name))
    print("Using calibration: {}".format(mon.currentCalib))

    gamma_grid = mon.getGammaGrid()

    if gamma_grid is None:
        print("Warning: no gamma calibration found, skipping correction.")
        return sequence

    gamma_mean = gamma_grid[0, 2]
    print("Gamma grid:\n  R={:.4f}, G={:.4f}, B={:.4f}, mean={:.4f}".format(
        gamma_grid[1, 2], gamma_grid[2, 2], gamma_grid[3, 2], gamma_mean))
    print("Applying inverse gamma correction: gamma={:.4f}".format(gamma_mean))

    seq_01 = np.clip((sequence.astype(np.float32) + 1.) / 2., 0., 1.)
    seq_corrected = np.power(seq_01, 1.0 / gamma_mean)
    return seq_corrected * 2. - 1.

def correct_color(color, monitor_name='testMonitor'):
    """Apply gamma correction to a single RGB color value in [-1, 1] range."""
    color_arr = np.array(color, dtype=np.float32)
    corrected = apply_gamma_correction(color_arr, monitor_name)
    return corrected.tolist()

def show_three_rectangles(monitor_name='testMonitor'):
    # Pre-correct colors before window creation
    black_corrected = correct_color([-1, -1, -1], monitor_name)
    gray_corrected  = correct_color([ 0,  0,  0], monitor_name)
    white_corrected = correct_color([ 1,  1,  1], monitor_name)

    print("Black: {} -> {}".format([-1,-1,-1], black_corrected))
    print("Gray:  {} -> {}".format([ 0, 0, 0], gray_corrected))
    print("White: {} -> {}".format([ 1, 1, 1], white_corrected))

    # Create window with gamma=1.0 to bypass GPU ramp
    win = visual.Window(
        size=[800, 600],
        color=[0, 0, 0],
        units="pix",
        screen=2,
        gamma=1.0,
        gammaErrorPolicy="ignore",
    )

    width = 200
    height = 300

    rect_black = visual.Rect(
        win,
        width=width,
        height=height,
        fillColor=black_corrected,
        pos=(-250, 0)
    )
    rect_gray = visual.Rect(
        win,
        width=width,
        height=height,
        fillColor=gray_corrected,
        pos=(0, 0)
    )
    rect_white = visual.Rect(
        win,
        width=width,
        height=height,
        fillColor=white_corrected,
        pos=(250, 0)
    )

    rect_black.draw()
    rect_gray.draw()
    rect_white.draw()
    win.flip()

    event.waitKeys()
    win.close()
    core.quit()

if __name__ == "__main__":
    show_three_rectangles(monitor_name='testMonitor')