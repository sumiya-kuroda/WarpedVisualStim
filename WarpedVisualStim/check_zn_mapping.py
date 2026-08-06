from psychopy import visual, event, core
from WarpedVisualStim.tools.FileTools import get_abspath

MOVIE = get_abspath("tools/zebranoise/zebra_mapping.mp4", pathlib=False)
print(f"Playing video: {MOVIE}")

win = visual.Window(fullscr=True, color=[0, 0, 0], units="pix", screen=2)
#                                        ^ gray: PsychoPy color range is -1..1,
#                                          so 0 = mid-gray (black=-1, white=+1)

mov = visual.MovieStim(
    win, MOVIE,
    size=win.size,        # upscale to fill 1920x1080
    noAudio=True,
    loop=False,
    interpolate=False,    # keep comb edges sharp through the 2x upscale
)

def gray_wait(duration):
    """Hold the gray background for `duration` seconds, still flipping each frame."""
    clk = core.Clock()
    while clk.getTime() < duration:
        win.flip()                       # window color is gray -> gray screen
        if event.getKeys(["escape"]):
            win.close(); core.quit()

# Gray until space
while True:
    win.flip()
    keys = event.getKeys(["space", "escape"])
    if "escape" in keys:
        win.close(); core.quit()
    if "space" in keys:
        break

mov.seek(0)
clk = core.Clock()
while clk.getTime() < mov.duration:
    mov.draw()
    win.flip()
    if event.getKeys(["escape"]):
        mov.stop(); win.close(); core.quit()
mov.stop()


win.close()
core.quit()