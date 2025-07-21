# This script postoricess data and upload it to ceph
from pathlib import Path
from psychopy import gui, core
from WarpedVisualStim.tools.FileTools import load_protocol, saveFile
from WarpedVisualStim.DisplayLogAnalysis import DisplayLogAnalyzer
from os.path import expanduser, split
import shutil
import json
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

    dlg = gui.DlgFromDict(dictionary=postprocessInfo, title='WarpedVisualStim MFH Postprocessing', screen=0, sortKeys=False) # show dialog and wait for OK or Cancel
    if dlg.OK == False:
        print('user cancelled')
        core.quit()  # user pressed cancel

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
    print(ses_date)
    ses_dir_name = 'ses-' + postprocessInfo['SessionID'] + '_date-' + ses_date 

    if postprocessInfo["Upload data to server?"]:
        server_behav_backup_location = Path(postprocess_settings['path_to_server']) / 'rawdata' / sub_dir_name / ses_dir_name / postprocessInfo['Datatype']
        server_behav_backup_location.mkdir(parents=True, exist_ok=True)
        server_funcimg_backup_location = Path(postprocess_settings['path_to_server']) / 'rawdata' / sub_dir_name / ses_dir_name / 'funcimg'
        server_funcimg_backup_location.mkdir(parents=True, exist_ok=True)

        # Copy all logs to server
        shutil.copy2(local_log_path + '/' + local_log_fname + '.pkl', str(server_behav_backup_location))
        shutil.copy2(local_log_path + '/' + local_log_fname + '_settings.json', str(server_behav_backup_location))

    # Copy and Read NIDAQ recording binary files and convert them into npy files (if they exist).
    session_settings = load_protocol(local_log_path + '/' + local_log_fname + '_settings.json')
    if session_settings["ds_use_daqlogger"]:
        print('Converting nidaq recording')
        if len(session_settings["ds_daqlogger_ai_channels"]) >= 1:
            if postprocessInfo["Upload data to server?"]:
                shutil.copy2(local_log_path + '/' + local_log_fname + '_ai.bin', str(server_behav_backup_location))
            nidaq_ai = np.fromfile(local_log_path + '/' + local_log_fname + '_ai.bin', dtype=np.float64) # Needs to be float64!
            nidaq_ai_data = nidaq_ai.reshape((len(session_settings["ds_daqlogger_ai_channels"]), -1))
            for i, aix in enumerate(session_settings["ds_daqlogger_ai_channels"]):
                print(aix)
                np.save(local_log_path + '/' + local_log_fname + '_' + aix + '.npy', nidaq_ai_data[i,:])
                if postprocessInfo["Upload data to server?"]:
                    np.save(str(server_behav_backup_location) + '/' + local_log_fname + '_' + aix + '.npy', nidaq_ai_data[i,:])

        if len(session_settings["ds_daqlogger_ci_channels"]) >= 1:
            if postprocessInfo["Upload data to server?"]:
                shutil.copy2(local_log_path + '/' + local_log_fname + '_ci.bin', str(server_behav_backup_location))
            nidaq_ci = np.fromfile(local_log_path + '/' + local_log_fname + '_ci.bin', dtype=np.float64) # Needs to be float64!
            nidaq_ci_data = nidaq_ai.reshape((len(session_settings["ds_daqlogger_ci_channels"]), -1))
            for i, cix in enumerate(session_settings["ds_daqlogger_ci_channels"]):
                print(cix)
                np.save(local_log_path + '/' + local_log_fname + '_' + cix + '.npy', nidaq_ci_data[i,:])
                if postprocessInfo["Upload data to server?"]:
                    np.save(str(server_behav_backup_location) + '/' + local_log_fname + '_' + cix + '.npy', nidaq_ci_data[i,:])
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

else:
    raise NotImplementedError

print('Postprocess completed!')