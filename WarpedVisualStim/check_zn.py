from psychopy import visual, core, event
from WarpedVisualStim.tools.FileTools import get_abspath
from rich.prompt import Prompt

# -------------------------
# SETTINGS
# -------------------------
setup = Prompt.ask("Which setup are you using", default="2p313")
if '313' in setup:
    print('You are using 2p313 setup')
    setup = '2p313'
else:
    print('You are using wf370 setup')
    setup = 'wf370'

MOVIE_PATH = get_abspath("tools/zebranoise/zebranoise.mp4", pathlib=False)
print(f"Playing video: {MOVIE_PATH}")

BG_GRAY = [0, 0, 0]
MOVIE_SIZE = (640, 368)

# -------------------------
# WINDOW (WINDOWED, placed on Monitor 2)
# -------------------------
# IMPORTANT: Monitor placement depends on your Windows display layout.
# The safe way is to:
#   1) create a windowed window (fullscr=False)
#   2) move it to the correct monitor using winHandle.set_location(x, y)
#
# Common layouts:
# - 2 monitors side-by-side, each 1920 wide:
#     monitor 1: x=0..1919
#     monitor 2: x=1920..3839   -> set_location(1920, 0)
# - 3 monitors side-by-side, each 1920 wide:
#     monitor 3 starts at x=3840 -> set_location(3840, 0)

TARGET_MONITOR_LEFT_X = 1920  # <-- change to 3840 if your monitor 2 starts there

if setup == '2p313':
    win = visual.Window(
        size=[1920, 1080],
        monitor="testMonitor",
        fullscr=False,          # windowed (more stable)
        screen=0,               # doesn't reliably place window in windowed mode on Windows
        color=BG_GRAY,
        waitBlanking=False,
        allowGUI=False,
        gammaErrorPolicy="ignore",
    )
else:
    win = visual.Window(
        size=[1920, 1200],
        monitor="testMonitor",
        fullscr=False,          # windowed (more stable)
        screen=0,               # doesn't reliably place window in windowed mode on Windows
        color=BG_GRAY,
        waitBlanking=False,
        allowGUI=False,
        gammaErrorPolicy="ignore",
    )



# Move window onto Monitor 2 and bring to front
try:
    win.winHandle.set_location(TARGET_MONITOR_LEFT_X, 0)
    win.winHandle.activate()
except Exception:
    pass

# -------------------------
# GRID POSITIONS
# -------------------------
screen_w, screen_h = win.size
movie_w, movie_h = MOVIE_SIZE

x_edge = max(0, (screen_w - movie_w) / 2)
y_edge = max(0, (screen_h - movie_h) / 2)

xs = [-x_edge, 0, x_edge]
ys = [y_edge, 0, -y_edge]

pos_map = {
    "1": (xs[0], ys[0]), "2": (xs[1], ys[0]), "3": (xs[2], ys[0]),
    "4": (xs[0], ys[1]), "5": (xs[1], ys[1]), "6": (xs[2], ys[1]),
    "7": (xs[0], ys[2]), "8": (xs[1], ys[2]), "9": (xs[2], ys[2]),
}

# Accept number row + numpad variants
key_to_grid = {str(i): str(i) for i in range(1, 10)}
key_to_grid.update({f"num_{i}": str(i) for i in range(1, 10)})
key_to_grid.update({f"kp{i}": str(i) for i in range(1, 10)})

# -------------------------
# MOVIE (MovieStim3)
# -------------------------
movie = visual.MovieStim3(win, filename=MOVIE_PATH, loop=True, noAudio=True)
movie.size = MOVIE_SIZE
movie.pos = pos_map["5"]

# -------------------------
# MAIN LOOP
# -------------------------
fps_cap = 60.0
frame_clock = core.Clock()

print("Controls: press 1-9 to MOVE movie, ESC to quit.")
print("If keys don't respond, click the PsychoPy window once to focus it.")
print(f"Window moved to x={TARGET_MONITOR_LEFT_X}, y=0 (adjust TARGET_MONITOR_LEFT_X if wrong).")

while True:
    keys = event.getKeys()

    # Debug: print received keys
    if keys:
        print("keys:", keys)

    if "escape" in keys:
        break

    for k in keys:
        g = key_to_grid.get(k)
        if g is not None:
            print(f"Pressed {k} -> move to grid {g}")
            movie.pos = pos_map[g]

    movie.draw()
    win.flip()

    # gentle FPS cap
    dt = frame_clock.getTime()
    sleep_t = max(0, (1.0 / fps_cap) - dt)
    if sleep_t > 0:
        core.wait(sleep_t)
    frame_clock.reset()

# -------------------------
# CLEANUP
# -------------------------
try:
    movie.stop()
except Exception:
    pass

win.close()
core.quit()
