from psychopy import visual, core, event
from rich.prompt import Prompt
from WarpedVisualStim.tools.FileTools import get_abspath

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

MOVIE_PATH = get_abspath('tools/zebranoise/zebranoise.mp4', pathlib=False)
print(f'Playing video: {MOVIE_PATH}')
BG_GRAY = [0.0, 0.0, 0.0]

MOVIE_SIZE = (640, 368)  
STEP_SEC = 1.0  

# Keys:
#   1-9   move movie
#   SPACE autoplay positions 1->9 (movie continues playing)
#   R     restart movie from beginning (keeps current position)
#   P     pause/resume
#   ESC   quit

# -------------------------
# WINDOW
# -------------------------
if setup == '2p313':
    win = visual.Window(size=[1920, 1080],
                            monitor="testMonitor",
                            fullscr=True,
                            screen=2,
                            color=BG_GRAY)

    win2 = visual.Window(size=[1920, 1080],
                            monitor="testMonitor",
                            fullscr=True,
                            screen=0,
                            color=BG_GRAY)
else:
    win = visual.Window(size=[1920, 1200],
                            monitor="testMonitor",
                            fullscr=True,
                            screen=1,
                            color=BG_GRAY)
    
screen_w, screen_h = win.size

# -------------------------
# GRID POSITIONS (reading order: 1 top-left ... 9 bottom-right)
# -------------------------
screen_w, screen_h = win.size
movie_w = MOVIE_SIZE[0]
movie_h = MOVIE_SIZE[1]

# Maximum allowed center positions so the movie stays fully on screen
x_edge = (screen_w - movie_w) / 2
y_edge = (screen_h - movie_h) / 2

# Clamp in case movie is >= screen size
x_edge = max(0, x_edge)
y_edge = max(0, y_edge)

xs = [-x_edge, 0, x_edge]
ys = [ y_edge, 0, -y_edge]   # top, middle, bottom

pos_map = {
    "1": (xs[0], ys[0]), "2": (xs[1], ys[0]), "3": (xs[2], ys[0]),
    "4": (xs[0], ys[1]), "5": (xs[1], ys[1]), "6": (xs[2], ys[1]),
    "7": (xs[0], ys[2]), "8": (xs[1], ys[2]), "9": (xs[2], ys[2]),
}

def movie_finished(m):
    if hasattr(m, "status") and str(m.status).endswith("FINISHED"):
        return True
    if hasattr(m, "isFinished") and m.isFinished:
        return True
    return False

# -------------------------
# MAKE MOVIE STIM
# -------------------------
def make_movie():
    m = visual.MovieStim3(win, filename=MOVIE_PATH, loop=False, noAudio=True)

    m.size = MOVIE_SIZE

    return m

movie = make_movie()
movie.pos = pos_map["5"]

# -------------------------
# CONTROL STATE
# -------------------------
paused = False
auto_play = False
auto_order = ["1","2","3","4","5","6","7","8","9"]
auto_idx = 0
next_switch_t = None
clock = core.Clock()

def restart_movie(keep_pos=True):
    """Recreate MovieStim3 to guarantee restart from t=0 across platforms."""
    global movie, paused, auto_play, auto_idx, next_switch_t
    cur_pos = movie.pos
    try:
        movie.stop()
    except Exception:
        pass
    movie = make_movie()
    if keep_pos:
        movie.pos = cur_pos
    paused = False
    auto_play = False
    auto_idx = 0
    next_switch_t = None

# -------------------------
# MAIN LOOP (runs until ESC)
# -------------------------
while True:
    keys = event.getKeys()

    if "escape" in keys:
        break

    # Move (1-9): immediate move, cancels autoplay
    for k in keys:
        if k in pos_map:
            movie.pos = pos_map[k]
            auto_play = False
            next_switch_t = None

    # Restart from beginning any time
    if "space" in keys:
        restart_movie(keep_pos=True)

    # Advance autoplay timing (movie keeps playing)
    if auto_play and next_switch_t is not None and (clock.getTime() >= next_switch_t):
        auto_idx += 1
        if auto_idx >= len(auto_order):
            auto_play = False
            next_switch_t = None
        else:
            movie.pos = pos_map[auto_order[auto_idx]]
            next_switch_t = clock.getTime() + STEP_SEC

    # Draw
    if not paused:
        movie.draw()
    win.flip()

    # If the movie ended, just sit on gray screen and allow restart/move/quit
    if movie_finished(movie):
        # Don’t break: user can press space to restart as many times as they want
        # Just keep flipping gray (no draw) until restart or quit.
        while True:
            keys2 = event.getKeys()
            if "escape" in keys2:
                keys = ["escape"]
                break
            for k in keys2:
                if k in pos_map:
                    movie.pos = pos_map[k]
                    auto_play = False
                    next_switch_t = None
            if "space" in keys2:
                restart_movie(keep_pos=True)
                break
            win.flip()  # gray only

        if "escape" in keys:
            break

# cleanup
try:
    movie.stop()
except Exception:
    pass
win.close()
core.quit()

# cemter pos offset
# +---+---+---+
# | 1 | 2 | 3 |
# +---+---+---+
# | 4 | 5 | 6 |
# +---+---+---+
# | 7 | 8 | 9 |
# +---+---+---+
