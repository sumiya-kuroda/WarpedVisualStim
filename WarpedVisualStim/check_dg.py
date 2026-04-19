from psychopy import visual, core, event
from WarpedVisualStim.gamma.rectangles import get_gamma_grid, apply_gamma_correction
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

BG_GRAY = [0, 0, 0]
CONTRAST = 1.0
GRATING_SIZE = (368, 368)   # pixels; square so circular mask is round
SPATIAL_FREQ = 0.02         # cycles / pixel
TEMPORAL_FREQ = 4.0         # Hz

# 4 directions: (grating orientation in deg, phase sign)
# ori=0  → vertical bars, phase+ = rightward (0°)
# ori=90 → horizontal bars, phase+ = downward (270°)
DIRECTION_PARAMS = [
    (0.0,   +1, "0°   rightward"),
    (90.0,  -1, "90°  upward"),
    (0.0,   -1, "180° leftward"),
    (90.0,  +1, "270° downward"),
]
DIRECTION_DUR = 0.25        # seconds per direction (4 × 250 ms = 1 s/cycle)

# -------------------------
# WINDOW
# -------------------------
TARGET_MONITOR_LEFT_X = 1920

if setup == '2p313':
    win = visual.Window(
        size=[1920, 1080],
        monitor="testMonitor",
        fullscr=False,
        screen=0,
        color=BG_GRAY,
        waitBlanking=False,
        allowGUI=False,
        gammaErrorPolicy="ignore",
    )
else:
    win = visual.Window(
        size=[1920, 1200],
        monitor="testMonitor",
        fullscr=False,
        screen=0,
        color=BG_GRAY,
        waitBlanking=False,
        allowGUI=False,
        gammaErrorPolicy="ignore",
    )

try:
    win.winHandle.set_location(TARGET_MONITOR_LEFT_X, 0)
    win.winHandle.activate()
except Exception:
    pass

try:
    gamma_grid = get_gamma_grid("testMonitor")
except Exception as e:
    print(f"Warning: could not load gamma grid ({e}).")
    gamma_grid = None
print(f"Contrast set to: {CONTRAST:.2f}")

# -------------------------
# GRID POSITIONS
# -------------------------
screen_w, screen_h = win.size
grating_w, grating_h = GRATING_SIZE

x_edge = max(0, (screen_w - grating_w) / 2)
y_edge = max(0, (screen_h - grating_h) / 2)

xs = [-x_edge, 0, x_edge]
ys = [y_edge, 0, -y_edge]

pos_map = {
    "1": (xs[0], ys[0]), "2": (xs[1], ys[0]), "3": (xs[2], ys[0]),
    "4": (xs[0], ys[1]), "5": (xs[1], ys[1]), "6": (xs[2], ys[1]),
    "7": (xs[0], ys[2]), "8": (xs[1], ys[2]), "9": (xs[2], ys[2]),
}

key_to_grid = {str(i): str(i) for i in range(1, 10)}
key_to_grid.update({f"num_{i}": str(i) for i in range(1, 10)})
key_to_grid.update({f"kp{i}": str(i) for i in range(1, 10)})

# -------------------------
# GRATING STIMULUS
# -------------------------
dir_idx = 0
ori0, sign0, label0 = DIRECTION_PARAMS[dir_idx]

grating = visual.GratingStim(
    win,
    tex='sin',
    mask='circle',
    units='pix',
    size=GRATING_SIZE,
    sf=SPATIAL_FREQ,
    ori=ori0,
    contrast=CONTRAST,
    phase=0.0,
    pos=pos_map["5"],
)

# -------------------------
# MAIN LOOP
# -------------------------
fps_cap = 60.0
frame_clock = core.Clock()
dir_clock = core.Clock()

cycle_dur = len(DIRECTION_PARAMS) * DIRECTION_DUR
print(f"Directions: {len(DIRECTION_PARAMS)} × {DIRECTION_DUR*1000:.0f} ms = {cycle_dur*1000:.0f} ms/cycle, repeating.")
print(f"Starting direction: {label0}")
print("Controls: press 1-9 to MOVE grating, ESC to quit.")
print("If keys don't respond, click the PsychoPy window once to focus it.")

while True:
    keys = event.getKeys()

    if "escape" in keys:
        break

    for k in keys:
        g = key_to_grid.get(k)
        if g is not None:
            print(f"Pressed {k} -> move to grid {g}")
            grating.pos = pos_map[g]

    # advance direction when block time is up
    if dir_clock.getTime() >= DIRECTION_DUR:
        dir_idx = (dir_idx + 1) % len(DIRECTION_PARAMS)
        ori, sign, label = DIRECTION_PARAMS[dir_idx]
        grating.ori = ori
        grating.phase = 0.0
        dir_clock.reset()
        print(f"Direction: {label}")
    else:
        sign = DIRECTION_PARAMS[dir_idx][1]

    phase_step = sign * TEMPORAL_FREQ / fps_cap
    grating.phase += phase_step
    grating.draw()
    win.flip()

    dt = frame_clock.getTime()
    sleep_t = max(0, (1.0 / fps_cap) - dt)
    if sleep_t > 0:
        core.wait(sleep_t)
    frame_clock.reset()

# -------------------------
# CLEANUP
# -------------------------
win.close()
core.quit()
