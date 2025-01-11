from __future__ import division, print_function
from functools import partial

import nidaqmx as daq
from nidaqmx.constants import AcquisitionType, EncoderType, EncoderZIndexPhase, AngleUnits, \
    AcquisitionType, Signal, TerminalConfiguration
import numpy as np
from nidaqmx.stream_readers import AnalogMultiChannelReader, CounterReader

from pythonosc.udp_client import SimpleUDPClient
# Adapted from exisitng works by Masahiro Nakano, Sandra Reinert in Mrsic-FLogel lab.
# This script uses nidaqmx instead of pydaqmx


class AnalogInput:

    def __init__(self, chan:list, min_value:float, max_value:float, threshold=None):
        self.data = []

        self.chan = chan
        self.min_value = min_value
        self.max_value = max_value
        self.threshold = threshold
        self.reader = None
        self.task = daq.Task()
        for aiX in self.chan:
            self.task.ai_channels.add_ai_voltage_chan(aiX,
                                                        min_val=self.min_value, 
                                                        max_val=self.max_value,
                                                        terminal_config=TerminalConfiguration.RSE)

    def set_datastream(self, sample_rate:int, source:str, clock_output:str='/Dev1/PFI0', sample_size:int=1000,
                       task_callback='save_buffer', outfile=None):
        # Configure the sampling rate and the number of samples
        task_callback = dict(read_buffer=self._read_buffer, 
                             save_buffer=self._save_buffer, 
                             osc_buffer=self._osc_buffer)[task_callback]
        self.outfile = outfile
        self.data_written = 0
        
        self.task.timing.cfg_samp_clk_timing(sample_rate,
                                    source= source,
                                    samps_per_chan=sample_size,
                                    sample_mode=AcquisitionType.CONTINUOUS)
        
        # Export the AI/SampleClock to PFI0 (default)
        self.task.export_signals.export_signal(Signal.SAMPLE_CLOCK, clock_output)

        self.reader = AnalogMultiChannelReader(self.task.in_stream)
        self.task.in_stream.input_buf_size = sample_size * 10
        task_callback_selected = partial(task_callback, 
                                          n_channels=len(self.chan), n_samples=sample_size)
        self.task.register_every_n_samples_acquired_into_buffer_event(sample_size, task_callback_selected)
    
    def read_float(self):
        # deprecated
        value_box = daq.float64()
        self.task.ReadAnalogScalarF64(0, daq.byref(value_box), None)
        value = value_box.value
        if self.threshold is not None:
            value = value > self.threshold
        return value

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, value:SimpleUDPClient):
        self._client = value

    @property
    def osc_address(self):
        return self._osc_address

    @osc_address.setter
    def osc_address(self, value:list):
        self._osc_address = value

    # Callback functions
    def _read_buffer(self, taskHandle, eventType, samples, callbackData, 
                     n_channels:int, n_samples:int):
        buffer = np.zeros((n_channels, n_samples), dtype=np.float64)
        try:
            self.reader.read_many_sample(buffer, n_samples, timeout=0) 
            # timeout = constants.WAIT_INFINITELY
            data = buffer.T.astype(np.float64)
            self.data.append(data)
        except daq.DaqError:
            self.stop()
            raise

        return 0 # always stop at 0 (reqiored DAQmx)

    def _save_buffer(self, taskHandle, eventType, samples, callbackData, 
                     n_channels:int, n_samples:int):
        buffer = np.zeros((n_channels, n_samples), dtype=np.float64)
        try:
            self.reader.read_many_sample(buffer, n_samples, timeout=0) 
            # timeout = constants.WAIT_INFINITELY
            data = buffer.T.astype(np.float64)
            self.data.append(data)

            self.outfile.write(data.tostring())
            self.data_written += n_samples
        except daq.DaqError:
            self.stop()
            raise

        return 0 # always stop at 0 (reqiored DAQmx)

    def _osc_buffer(self, taskHandle, eventType, samples, callbackData, 
                     n_channels:int, n_samples:int):
        if self._client is None:
            raise ValueError('Set OSC client first!')
        buffer = np.zeros((n_channels, n_samples), dtype=np.float64)
        try:
            self.reader.read_many_sample(buffer, n_samples, timeout=0) 
            # timeout = constants.WAIT_INFINITELY
            data = buffer.T.astype(np.float64)
            self.data.append(data)

            self.outfile.write(data.tostring())
            self.data_written += n_samples

            for i, b in enumerate(buffer.tolist()):
                self._client.send_message(self.osc_address[i], b)
        except daq.DaqError:
            self.stop()
            raise

        return 0 # always stop at 0 (reqiored DAQmx)

    def start(self):
        self.task.start()

    def stop(self):
        self.task.stop()

    def close(self):
        if self.task is not None:
            self.task.close()
            self.task = None
            self.data = []
            self.data_written = 0


class AngularEncoder:

    def __init__(self, chan, pulses_per_rev=1024, error_value=None,
                 encoder_type=EncoderType.X_4, units=AngleUnits.DEGREES):
        # units=AngleUnits.TICKS
        self.data = []

        self.chan = chan
        self.error_value = error_value
        self.reader = None
        self.task = daq.Task()
        self.task.ci_channels.add_ci_ang_encoder_chan(chan,
                                                 "",
                                                 encoder_type,
                                                 False, 0,
                                                 EncoderZIndexPhase.AHIGH_BHIGH,
                                                 units,
                                                 pulses_per_rev, 0.0, "")

    def set_datastream(self, sample_rate:int, source:str, sample_size:int,
                       task_callback='save_buffer', outfile=None):
        # Configure the sampling rate and the number of samples
        task_callback = dict(read_buffer=self._read_buffer, 
                             save_buffer=self._save_buffer, 
                             osc_buffer=self._osc_buffer)[task_callback]
        self.outfile = outfile
        self.data_written = 0
        self.task.timing.cfg_samp_clk_timing(sample_rate,
                                              source=source,
                                              samps_per_chan=sample_size,
                                              sample_mode=AcquisitionType.CONTINUOUS)
        # https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z000000kEddSAE&l=en-GB

        self.reader = CounterReader(self.task.in_stream)
        self.task.in_stream.input_buf_size = sample_size * 2
        task_callback_selected = partial(task_callback, 
                                          n_samples=sample_size)
        self.task.register_every_n_samples_acquired_into_buffer_event(sample_size, task_callback_selected)

    def read_float(self):
        # deprecated
        value_box = daq.float64()
        self.task.ReadCounterScalarF64(0, daq.byref(value_box), None)
        return value_box.value if value_box.value < self.error_value else 0

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @property
    def osc_address(self):
        return self._osc_address

    @osc_address.setter
    def osc_address(self, value:list):
        self._osc_address = value

    # Callback functions
    def _read_buffer(self, taskHandle, eventType, samples, callbackData, 
                     n_samples:int):
        buffer = np.zeros(n_samples, dtype=np.float64)
        try:
            self.reader.read_many_sample_double(buffer, n_samples, timeout=0) 
            # timeout = constants.WAIT_INFINITELY
            data = buffer.T.astype(np.float64)
            self.data.append(data)
        except daq.DaqError:
            self.stop()
            raise

        return 0 # always stop at 0 (reqiored DAQmx)

    def _save_buffer(self, taskHandle, eventType, samples, callbackData, 
                     n_samples:int):
        buffer = np.zeros(n_samples, dtype=np.float64)
        try:
            self.reader.read_many_sample_double(buffer, n_samples, timeout=0) 
            # timeout = constants.WAIT_INFINITELY
            data = buffer.T.astype(np.float64)
            self.data.append(data)

            self.outfile.write(data.tostring())
            self.data_written += n_samples
        except daq.DaqError:
            self.stop()
            raise

        return 0 # always stop at 0 (reqiored DAQmx)

    def _osc_buffer(self, taskHandle, eventType, samples, callbackData, 
                     n_samples:int):
        if self._client is None:
            raise ValueError('Set OSC client first!')
        buffer = np.zeros(n_samples, dtype=np.float64)
        try:
            self.reader.read_many_sample_double(buffer, n_samples, timeout=0) 
            # timeout = constants.WAIT_INFINITELY
            data = buffer.T.astype(np.float64)
            self.data.append(data)

            self.outfile.write(data.tostring())
            self.data_written += n_samples

            self._client.send_message(self.osc_address[0], buffer) 
        except daq.DaqError:
            self.stop()
            raise

        return 0 # always stop at 0 (reqiored DAQmx)
    
    def start(self):
        self.task.start()

    def stop(self):
        self.task.stop()

    def close(self):
        if self.task is not None:
            self.task.close()
            self.task = None
            self.data = []
            self.data_written = 0