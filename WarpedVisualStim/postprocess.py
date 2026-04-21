# This script postoricess data and upload it to ceph
from pathlib import Path
from psychopy import gui, core
from WarpedVisualStim.tools.FileTools import load_protocol, saveFile, get_protocol_tag
from WarpedVisualStim.tools.PlottingTools import plot_nidaq_channels
from WarpedVisualStim.DisplayLogAnalysis import DisplayLogAnalyzer
from os.path import expanduser, split
import shutil
import numpy as np

# ================ Load protocol and Enter session information ==================================
postprocess_settings = load_protocol('./protocols/postprocess_settings.json')
 
if postprocess_settings['format'] == 'neuroblueprint':
    postprocessInfo = {
        'Upload data to server?': True,
        'SubjectID': 'SK001',
        'SessionID': '1',
        'Datatype': ['behav', 'funcimg', 'ephys'],
        'Local data location': [str(expanduser("~")), 'D:/SuKu_RawData'],
    }
 
    dlg = gui.DlgFromDict(dictionary=postprocessInfo, title='WarpedVisualStim MFH Postprocessing', screen=0, sortKeys=False)
    if dlg.OK == False:
        print('user cancelled')
        core.quit()
 
    filesToOpen = gui.fileOpenDlg(tryFilePath=postprocessInfo['Local data location'], tryFileName='', prompt='Select log file to open', allowed='*.pkl')
    if filesToOpen is None:
        print('user cancelled')
        core.quit()
    if len(filesToOpen) >= 2:
        print('Select only one file')
        core.quit()
 
    local_log_path = split(filesToOpen[0])[0]
    local_log_fname = split(filesToOpen[0])[1].split('.')[0]
 
    sub_dir_name = 'sub-' + postprocessInfo['SubjectID']
    ses_date = local_log_fname.split('_')[0][-8:]
    protocol_tag = get_protocol_tag(local_log_fname)
    ses_dir_name = 'ses-' + postprocessInfo['SessionID'] + '_protocol-' + protocol_tag + '_date-' + ses_date
    if postprocessInfo["Upload data to server?"]:
        server_behav_backup_location = Path(postprocess_settings['path_to_server']) / 'rawdata' / sub_dir_name / ses_dir_name / postprocessInfo['Datatype']
        server_behav_backup_location.mkdir(parents=True, exist_ok=True)
        server_funcimg_backup_location = Path(postprocess_settings['path_to_server']) / 'rawdata' / sub_dir_name / ses_dir_name / 'funcimg'
        server_funcimg_backup_location.mkdir(parents=True, exist_ok=True)
        print(server_behav_backup_location)
 
        shutil.copy2(local_log_path + '/' + local_log_fname + '.pkl', str(server_behav_backup_location))
        shutil.copy2(local_log_path + '/' + local_log_fname + '_settings.json', str(server_behav_backup_location))
 
    session_settings = load_protocol(local_log_path + '/' + local_log_fname + '_settings.json')
 
    if session_settings["ds_use_daqlogger"]:
        print('Converting nidaq recording')
 
        # ---- Analog input channels ----
        if len(session_settings["ds_daqlogger_ai_channels"]) >= 1:
            if postprocessInfo["Upload data to server?"]:
                shutil.copy2(local_log_path + '/' + local_log_fname + '_ai.bin', str(server_behav_backup_location))
 
            nidaq_ai = np.fromfile(local_log_path + '/' + local_log_fname + '_ai.bin', dtype=np.float64)
            nidaq_ai_data = nidaq_ai.reshape((-1, len(session_settings["ds_daqlogger_ai_channels"]))).T
 
            ai_channel_data = []
            ai_channel_names = []
            for i, aix in enumerate(session_settings["ds_daqlogger_ai_channels"]):
                print(aix)
                np.save(local_log_path + '/' + local_log_fname + '_' + aix + '.npy', nidaq_ai_data[i, :])
                if postprocessInfo["Upload data to server?"]:
                    np.save(str(server_behav_backup_location) + '/' + local_log_fname + '_' + aix + '.npy', nidaq_ai_data[i, :])
                ai_channel_data.append(nidaq_ai_data[i, :])
                ai_channel_names.append(aix)
 
            plot_nidaq_channels(
                ai_channel_data,
                ai_channel_names,
                channel_type='AI',
                log_fname=local_log_fname,
            )
 
        # ---- Counter input channels ----
        if len(session_settings["ds_daqlogger_ci_channels"]) >= 1:
            if postprocessInfo["Upload data to server?"]:
                shutil.copy2(local_log_path + '/' + local_log_fname + '_ci.bin', str(server_behav_backup_location))
 
            nidaq_ci = np.fromfile(local_log_path + '/' + local_log_fname + '_ci.bin', dtype=np.float64)
            nidaq_ci_data = nidaq_ci.reshape((-1, len(session_settings["ds_daqlogger_ci_channels"]))).T
 
            ci_channel_data = []
            ci_channel_names = []
            for i, cix in enumerate(session_settings["ds_daqlogger_ci_channels"]):
                print(cix)
                np.save(local_log_path + '/' + local_log_fname + '_' + cix + '.npy', nidaq_ci_data[i, :])
                if postprocessInfo["Upload data to server?"]:
                    np.save(str(server_behav_backup_location) + '/' + local_log_fname + '_' + cix + '.npy', nidaq_ci_data[i, :])
                ci_channel_data.append(nidaq_ci_data[i, :])
                ci_channel_names.append(cix)
 
            plot_nidaq_channels(
                ci_channel_data,
                ci_channel_names,
                channel_type='CI',
                log_fname=local_log_fname,
            )
 
        else:
            print('No nidaq recording found')
 
    if not 'KSstimAllDir' in local_log_fname:
        print('Loading {}'.format(local_log_path + '/' + local_log_fname + '.pkl'))
        dla = DisplayLogAnalyzer(local_log_path + '/' + local_log_fname + '.pkl')
        stim_dict = dla.get_stim_dict()
        pd_onsets_seq = dla.analyze_photodiode_onsets_sequential(stim_dict, pd_thr=-0.5)
        pd_onsets_combined = dla.analyze_photodiode_onsets_combined(pd_onsets_seq)
        saveFile(local_log_path + '/' + local_log_fname + '_pd_onsets_combined.pkl', pd_onsets_combined)
        if postprocessInfo["Upload data to server?"]:
            saveFile(str(server_behav_backup_location) + '/' + local_log_fname + '_pd_onsets_combined.pkl', pd_onsets_combined)
 
    if 'StaticImages' in local_log_fname:
        if postprocessInfo["Upload data to server?"]:
            path_to_images = Path('./tools/naturalscene').glob('*.h5')
            for image in path_to_images:
                shutil.copy2(str(image), str(server_behav_backup_location))
            print('Copied all the natural image HDF5 files')
 
else:
    raise NotImplementedError
 
print('Postprocess completed!')