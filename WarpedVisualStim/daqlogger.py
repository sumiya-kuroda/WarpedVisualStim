import os
from os.path import expanduser
from WarpedVisualStim.tools.daqmx_recorder import DAQLogger
from WarpedVisualStim.tools.FileTools import load_dumped_taskinfo
from WarpedVisualStim.tools.GenericTools import clear_screen
from WarpedVisualStim.tools import OperationError
import pyfiglet 

input('Press return to launch daqlogger')
print('Launching daqlogger...')
task_protocol = load_dumped_taskinfo()
if task_protocol["ds_use_daqlogger"]:
    daqlogger = DAQLogger(dev_name=task_protocol["ds_sync_pulse_NI_dev"],
                            ai_channels=task_protocol["ds_daqlogger_ai_channels"],
                            ci_channels = task_protocol["ds_daqlogger_ci_channels"][0],
                            sample_rate = task_protocol["ds_daqlogger_sample_rate"],
                            sample_size = task_protocol["ds_daqlogger_sample_size"], 
                            osc_ip = task_protocol["ds_daqlogger_osc_ip"],
                            osc_port = task_protocol["ds_daqlogger_osc_port"],
                            osc_address_ai = task_protocol["ds_daqlogger_osc_address_ai"],
                            osc_address_ci = task_protocol["ds_daqlogger_osc_address_ci"],
                            save_file_location_ai = os.path.join(expanduser("~"), '.daqlogger_temp_ai.bin'),
                            save_file_location_ci = os.path.join(expanduser("~"), '.daqlogger_temp_ci.bin'))
else:
    raise OperationError('Task protocol says no daqlogger is needed')

daqlogger.start_acquisition()
print(pyfiglet.figlet_format('Recording NIDAQ!',font='doom'))

input('Press return to stop the recording')

clear_screen()
daqlogger.stop_acquisition()
daqlogger.close_tasks()
print('daqlogger has shut down!')