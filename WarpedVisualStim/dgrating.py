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

# ================ Load protocol and Enter session information ==================================
expInfo = {
    'User ID': 'skuroda',
    'Mouse ID': '',
    'Identifier': datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
    'Protocol': search_protcol("./protocols"),
    'Saving location': [str(expanduser("~")), 'D:/SuKu_RawData'],
    'Plot map': True,
    'Inverse Gratings': False
}
dlg = gui.DlgFromDict(dictionary=expInfo, title='WarpedVisualStim MFH', screen=0, sortKeys=False) # show dialog and wait for OK or Cancel
if dlg.OK == False:
    print('user cancelled')
    core.quit()  # user pressed cancel

task_protocol = load_protocol('./protocols/{}.json'.format(expInfo['Protocol']))

# ================ Initialize the monitor object ==================================
mon = Monitor(resolution=task_protocol["mon_resolution"], dis=task_protocol["mon_dis"], mon_width_cm=task_protocol["mon_width_cm"],
              mon_height_cm=task_protocol["mon_height_cm"], C2T_cm=task_protocol["mon_height_cm"] /2, C2A_cm=task_protocol["mon_width_cm"] /2,
              visual_field='left',
              center_coordinates=(0., 45.),
              downsample_rate=task_protocol["mon_downsample_rate"])
if expInfo['Plot map']:
    mon.plot_map()
    plt.show()
else:
    pass
# =================================================================================

# ================ Initialize the indicator object ================================
ind = Indicator(mon, width_cm=task_protocol["ind_width_cm"], height_cm=task_protocol["ind_height_cm"],
                position=task_protocol["ind_position"], is_sync=True, freq=task_protocol["ind_freq"])
# =================================================================================

# ========================== DriftingGratingCircle =====================================
dgc = stim.DriftingGratingMultipleCircle(monitor=mon, indicator=ind, background=task_protocol["background"],
                                 coordinate=task_protocol["coordinate"], center_list=make_nested_lst_of_tuples(task_protocol["dgmc_center_list"]), sf_list=task_protocol["dgmc_sf_list"],
                                 tf_list=task_protocol["dgmc_tf_list"], dire_list=task_protocol["dgmc_direction_list"], con_list=task_protocol["dgmc_contrast_list"], radius_list=task_protocol["dgmc_radius_list"],
                                 block_dur=task_protocol["dgmc_block_dur"], midgap_dur=task_protocol["dgmc_midgap_dur"], is_smooth_edge=task_protocol["dgmc_is_smooth_edge"], iteration=task_protocol["dgmc_iteration"], pregap_dur=task_protocol["dgmc_pregap_dur"],
                                 postgap_dur=task_protocol["dgmc_postgap_dur"], is_blank_block=task_protocol["dgmc_is_blank_block"], is_random_start_phase=task_protocol["dgmc_is_random_start_phase"],
                                 inverse=expInfo['Inverse Gratings'])

# =================================================================================

# ================ Initialize the DisplaySequence object ==========================
ds = DisplaySequence(log_dir=expInfo['Saving location'], backupdir=None, identifier=expInfo['Identifier'], display_iter=task_protocol["ds_display_iter"],
                     mouse_id=expInfo['Mouse ID'], user_id=expInfo['User ID'],
                     psychopy_mon=task_protocol["ds_stimulus_mon"],display_screen=task_protocol["ds_stimulus_screen"],
                     psychopy_nonused_mon=task_protocol["ds_nonused_mon"], nonused_screen=task_protocol["ds_nonused_screen"],
                     is_by_index=True,is_interpolate=task_protocol["ds_is_interpolate"],is_triggered=task_protocol["ds_is_triggered"],
                     trigger_event=task_protocol["ds_trigger_event"], trigger_NI_dev=task_protocol["ds_trigger_NI_dev"],
                     trigger_NI_port=task_protocol["ds_trigger_NI_port"], trigger_NI_line=task_protocol["ds_trigger_NI_line"],
                     is_sync_pulse=task_protocol["ds_is_sync_pulse"], sync_pulse_NI_dev=task_protocol["ds_sync_pulse_NI_dev"],
                     sync_pulse_NI_port=task_protocol["ds_sync_pulse_NI_port"],
                     sync_pulse_NI_line=task_protocol["ds_sync_pulse_NI_line"],
                     is_save_sequence=task_protocol["ds_is_save_sequence"],
                     initial_background_color=task_protocol["ds_initial_background_color"],
                     color_weights=task_protocol["ds_color_weights"])
# =================================================================================

# =========================== display and daq logger ==============================
ds.set_stim(dgc)
if task_protocol["ds_use_daqlogger"]:
    dump_taskinfo('./protocols/{}.json'.format(expInfo['Protocol']))
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
print('Plotting stats')
plt.show()
