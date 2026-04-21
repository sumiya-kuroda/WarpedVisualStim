import matplotlib.pyplot as plt
import numpy as np
import WarpedVisualStim.StimulusRoutines as stim
from WarpedVisualStim.MonitorSetup import Monitor, Indicator
from WarpedVisualStim.DisplayStimulus import DisplaySequence
from WarpedVisualStim.tools.FileTools import load_protocol, search_protcol
from psychopy import gui, core
from datetime import datetime, timezone
from os.path import expanduser
import matplotlib.pyplot as plt
import WarpedVisualStim.StimulusRoutines as stim
from WarpedVisualStim.MonitorSetup import Monitor, Indicator
from WarpedVisualStim.DisplayStimulus import DisplaySequence
from WarpedVisualStim.tools.FileTools import load_protocol, search_protcol, save_session_setting, dump_taskinfo, clear_daqlogger_temp
from WarpedVisualStim.tools.GenericTools import make_nested_lst_of_tuples
from psychopy import gui, core
from datetime import datetime, timezone
from os.path import expanduser, split
from rich.prompt import Prompt
import os
from pathlib import Path

# ================ Load protocol and Enter session information ==================================
expInfo = {
    'User ID': 'skuroda',
    'Mouse ID': '',
    'Identifier': datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
    'Protocol': search_protcol("./protocols"),
    'Saving location': [str(expanduser("~")), 'D:/SuKu_RawData'],
    'Luminance (cd/m2)': 8.0,
    'Duration (s)': 1800.0,
}
dlg = gui.DlgFromDict(dictionary=expInfo, title='Gray Screen', screen=0, sortKeys=False)
if dlg.OK == False:
    print('user cancelled')
    core.quit()

task_protocol = load_protocol('./protocols/{}.json'.format(expInfo['Protocol']))

# ================ Initialize the monitor object ==================================
mon = Monitor(resolution=task_protocol["mon_resolution"],
              dis=task_protocol["mon_dis"],
              mon_width_cm=task_protocol["mon_width_cm"],
              mon_height_cm=task_protocol["mon_height_cm"],
              C2T_cm=task_protocol["mon_height_cm"] / 2,
              C2A_cm=task_protocol["mon_width_cm"] / 2,
              visual_field='left',
              center_coordinates=(0., 45.),
              downsample_rate=task_protocol["mon_downsample_rate"],
              name=task_protocol["ds_stimulus_mon"])

ind = Indicator(mon,
                width_cm=task_protocol["ind_width_cm"],
                height_cm=task_protocol["ind_height_cm"],
                position=task_protocol["ind_position"],
                is_sync=True,
                freq=task_protocol["ind_freq"])
# =================================================================================

# ================ Compute target gray value in [-1, 1] ===========================
target_lum = float(expInfo['Luminance (cd/m2)'])
if mon.luminance_range is not None:
    lum_min, lum_max = mon.luminance_range
    lum_01   = (target_lum - lum_min) / (lum_max - lum_min)
    gray_val = float(np.clip(lum_01, 0., 1.) * 2. - 1.)
    print("Target: {:.2f} cd/m2 -> [-1,1] value (before gamma): {:.4f}".format(target_lum, gray_val))
else:
    gray_val = 0.0
    print("No luminance range found, using mid-gray (0.0)")
# =================================================================================

# ================ Display gray screen using UniformContrast ======================
uc = stim.UniformContrast(monitor=mon,
                           indicator=ind,
                           duration=float(expInfo['Duration (s)']),
                           color=gray_val,
                           pregap_dur=0.,
                           postgap_dur=0.,
                           background=gray_val)

ds = DisplaySequence(log_dir=expInfo['Saving location'],
                     identifier=expInfo['Identifier'],
                     mouse_id=expInfo['Mouse ID'],
                     user_id=expInfo['User ID'],
                     psychopy_mon=task_protocol["ds_stimulus_mon"],
                     psychopy_nonused_mon=task_protocol["ds_nonused_mon"],
                     nonused_screen=task_protocol["ds_nonused_screen"],
                     display_screen=task_protocol["ds_stimulus_screen"],
                     initial_background_color=gray_val,
                     color_weights=task_protocol["ds_color_weights"],
                     is_triggered=False,
                     is_sync_pulse=False,
                     is_by_index=True,
                     is_save_sequence=False)


ds.set_stim(uc)
if task_protocol["ds_use_daqlogger"]:
    dump_taskinfo('./protocols/{}.json'.format(expInfo['Protocol']))
    Prompt.ask('Run [bold magenta]avi_recorder.bonsai[/bold magenta] to start recording cameras. Press return to continue when ready')
    Prompt.ask('Run [bold magenta]python daqlogger.py[/bold magenta] to start recording NIDAQ. Press return to continue when ready')
else:
      pass

Prompt.ask('Start [bold magenta]Grab[/bold magenta] on ScanImage. Press return to continue when ready')
saved_file, _ = ds.trigger_display()

input('please stop daqlogger now. Press return to continue when ready')
if task_protocol["ds_use_daqlogger"]:
    if not 'test' in expInfo['Mouse ID']:
        clear_daqlogger_temp(ds.directory, split(saved_file)[1].split('.')[0])
    else:
        print('Due to test session, DAQ Logger was not used')
save_session_setting(task_protocol, expInfo, 
                     split(saved_file)[0], 
                     split(saved_file)[1].split('.')[0] + '_settings.json')

# =================================================================================