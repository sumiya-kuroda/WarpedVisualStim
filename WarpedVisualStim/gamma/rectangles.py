from psychopy import visual, core, event


def show_three_rectangles():
    # Create window
    win = visual.Window(
        size=[800, 600],
        color=[0, 0, 0],   # background (black)
        units="pix",
        screen=2,
    )

    # Rectangle settings
    width = 200
    height = 300

    # Create rectangles
    rect_black = visual.Rect(
        win,
        width=width,
        height=height,
        fillColor=[-1, -1, -1],  # black
        pos=(-250, 0)
    )

    rect_gray = visual.Rect(
        win,
        width=width,
        height=height,
        fillColor=[0, 0, 0],     # gray
        pos=(0, 0)
    )

    rect_white = visual.Rect(
        win,
        width=width,
        height=height,
        fillColor=[1, 1, 1],     # white
        pos=(250, 0)
    )

    # Draw once
    rect_black.draw()
    rect_gray.draw()
    rect_white.draw()
    win.flip()

    # Wait for key press
    event.waitKeys()
    win.close()
    core.quit()


if __name__ == "__main__":
    show_three_rectangles()
