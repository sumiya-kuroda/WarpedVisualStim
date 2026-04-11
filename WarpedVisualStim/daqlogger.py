import os
from os.path import expanduser
from WarpedVisualStim.tools.daqmx_recorder import DAQLogger
from WarpedVisualStim.tools.createttl import TTLGenerator
from WarpedVisualStim.tools.FileTools import load_dumped_taskinfo
from WarpedVisualStim.tools.GenericTools import clear_screen
from WarpedVisualStim.tools import OperationError
import pyfiglet 

input('Press return to launch daqlogger')
print('Launching daqlogger...')
task_protocol = load_dumped_taskinfo()
if task_protocol["ds_use_daqlogger"]:
    record_ai = len(task_protocol["ds_daqlogger_ai_channels"]) > 0
    record_ci = len(task_protocol["ds_daqlogger_ci_channels"]) > 0

    daqlogger = DAQLogger(dev_name=task_protocol["ds_sync_pulse_NI_dev"],
                            ai_channels=task_protocol["ds_daqlogger_ai_channels"] if record_ai else [],
                            ci_channels = task_protocol["ds_daqlogger_ci_channels"][0] if record_ci else '',
                            sample_rate = task_protocol["ds_daqlogger_sample_rate"],
                            sample_size = task_protocol["ds_daqlogger_sample_size"], 
                            osc_ip = task_protocol["ds_daqlogger_osc_ip"],
                            osc_port = task_protocol["ds_daqlogger_osc_port"],
                            osc_address_ai = task_protocol["ds_daqlogger_osc_address_ai"] if record_ai else '',
                            osc_address_ci = task_protocol["ds_daqlogger_osc_address_ci"] if record_ci else '',
                            save_file_location_ai = os.path.join(expanduser("~"), '.daqlogger_temp_ai.bin'),
                            save_file_location_ci = os.path.join(expanduser("~"), '.daqlogger_temp_ci.bin'))
else:
    raise OperationError('Task protocol says no daqlogger is needed')

if task_protocol["ds_use_camera_pulse"]:
    camerattl = TTLGenerator(task_protocol["ds_camera_pulse_NI_dev"], task_protocol["ds_camera_pulse_NI_port"], task_protocol["ds_camera_pulse_NI_line"])

daqlogger.start_acquisition()
if task_protocol["ds_use_camera_pulse"]:
    camerattl.runTTLCycle(frequency=task_protocol["ds_camera_pulse_freq"])
print(pyfiglet.figlet_format('Recording NIDAQ!',font='doom'))

input('Press return to stop the recording')

clear_screen()
if task_protocol["ds_use_camera_pulse"]:
    camerattl.close()
daqlogger.stop_acquisition()
daqlogger.close_tasks()
print('daqlogger has shut down!')