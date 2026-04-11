from psychopy import prefs
import os, glob

mon_name = "testMonitor"

mon_dir = os.path.join(prefs.paths["userPrefsDir"], "monitors")
print("Monitor calib dir:", mon_dir)

candidates = glob.glob(os.path.join(mon_dir, f"{mon_name}*.calib"))
print("Candidates:", candidates)
