import numpy as np
from pathlib import Path
from .IO.nidaq_DAQLogger import AnalogInput, AngularEncoder
from pythonosc.udp_client import SimpleUDPClient

class DAQLogger():
    # Inspired from
    # https://github.com/SWC-Advanced-Microscopy/SimplePyScanner
    # - Rob Campbell
    # Output: binary file with the data formatted as np.float64

    def __init__(self, dev_name:str = 'Dev2', ai_channels:list = [], 
                 voltage_range:float = 5, ci_channels = 'ctr0', 
                 sample_rate = 9000, sample_size = 1000, 
                 save_file_location_ai:str = '',
                 save_file_location_ci:str = '',
                 use_osc = True, osc_ip = "127.0.0.1", osc_port = "8888",
                 osc_address_ai = [], osc_address_ci = [],
                 autoconnect=True):
        self.task_AIs = None
        self.task_CIs = None
        self.dev_name = dev_name
        self.ai_channels = ai_channels
        self.voltage_range = voltage_range
        self.ci_channels = ci_channels
        self.sample_rate = sample_rate
        self.sample_size = sample_size
        self.source_clock_ai = '' # This uses /ai/SampleClock
        self.source_clock_ci = '/{}/PFI0'.format(self.dev_name)

        self.use_osc = use_osc
        self.osc_ip = osc_ip
        self.osc_port = osc_port
        self.osc_address_ai = osc_address_ai
        self.osc_address_ci = osc_address_ci

        self.save_file_location_ai = Path(save_file_location_ai)
        self.save_file_location_ci = Path(save_file_location_ci)
        if save_file_location_ai != '':
            self.outFile_ai = open(self.save_file_location_ai, 'wb')
        if save_file_location_ci != '':
            self.outFile_ci = open(self.save_file_location_ci, 'wb')

        if autoconnect:
            if self.use_osc:
                self.set_up_osc()
                self.set_up_tasks('osc_buffer')
            else:
                self.set_up_tasks('read_buffer')              

    def set_up_osc(self):
        self.client = SimpleUDPClient(self.osc_ip, int(self.osc_port))  # Create and assign client

    def set_up_tasks(self, task_callback='save_buffer'):
        self.task_callback = task_callback

        if len(self.ai_channels) >0:
            ai_channels_full = ['{}/{}'.format(self.dev_name, aiX) for aiX in self.ai_channels]
            self.task_AIs = AnalogInput(ai_channels_full, 
                                         min_value=-1*self.voltage_range, max_value=self.voltage_range)
            self.task_AIs.set_datastream(self.sample_rate,
                                          self.source_clock_ai,
                                          self.source_clock_ci,
                                          self.sample_size,
                                          task_callback=task_callback,
                                          outfile=self.outFile_ai)
            if self.use_osc:
                self.task_AIs.client = self.client
                self.task_AIs.osc_address = self.osc_address_ai

        if self.ci_channels != '':
            if len(self.ai_channels) == 0:
                raise NotImplementedError('DAQLogger cannot record events when only counter inputs are set!')
            else:
                pass
            self.task_CIs = AngularEncoder('{}/{}'.format(self.dev_name, self.ci_channels))
            self.task_CIs.set_datastream(self.sample_rate,
                                          self.source_clock_ci,
                                          self.sample_size,
                                          task_callback=task_callback,
                                          outfile=self.outFile_ci)
            if self.use_osc:
                self.task_CIs.client = self.client
                self.task_CIs.osc_address = self.osc_address_ci

    def send_oscmsg(self, address, msg):
        self.client.send_message(address, msg) 

    def start_acquisition(self):
        print('Stating the task!')
        if self.task_AIs is not None:
            self.task_AIs.start()
            self._print_task_status('start', 'AI')
        if self.task_CIs is not None:
            self.task_CIs.start()
            self._print_task_status('start', 'CI')

    def stop_acquisition(self):
        print('Stopping the task...')
        if self.task_AIs is not None:
            self.task_AIs.stop()
            self._print_task_status('stop', 'AI')
        if self.task_CIs is not None:
            self.task_CIs.stop()
            self._print_task_status('stop', 'CI')

    def close_tasks(self):
        print('Closing the task...')
        if self.task_AIs is not None:
            self.task_AIs.close()
        if self.task_CIs is not None:
            self.task_CIs.close()
    
    def _print_task_status(self, status, channel):
        if status == 'start':
            print('Acquisition started for {}'.format(channel))
            if self.task_callback=='save_buffer' or self.task_callback=='osc_buffer':
                if "AI" in channel or "ai" in channel:
                    print('Saving data in {}'.format(str(self.save_file_location_ai)))
                elif "CI" in channel or "ci" in channel:
                    print('Saving data in {}'.format(str(self.save_file_location_ci)))
                else:
                    pass
        elif status == 'stop':
            print('Acquisition stopped for {}'.format(channel))
        elif status == 'close':
            pass