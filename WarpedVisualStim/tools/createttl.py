import numpy as np
from pathlib import Path
from .IO.nidaq import DigitalOutput
import time
import threading

class TTLGenerator():
    def __init__(self, dev_name:str = 'Dev2', port:int = 0, line:int = 0):
        self.syncPulseTask = DigitalOutput(dev_name, port, line)
        self.syncPulseTask.StartTask()
        self._stop_event = threading.Event()
        self.runTTLCycle()

    def makeHIGH(self):
        _ = self.syncPulseTask.write(np.array([1]).astype(np.uint8))

    def makeLOW(self):
        _ = self.syncPulseTask.write(np.array([0]).astype(np.uint8))

    def runTTLCycle(self, frequency=60, rec_time_s=10000):
        print(f'starting camera TTL | {frequency} Hz | {rec_time_s} s')
        on_time = 0.01
        off_time = 1/frequency - on_time
        num_cycles = rec_time_s * frequency

        self._stop_event.clear()

        def _run():
            for n in range(num_cycles):
                if self._stop_event.is_set():
                    break
                self.makeHIGH()
                time.sleep(on_time)
                self.makeLOW()
                time.sleep(off_time)
            self.makeLOW()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()

    def close(self):
        self.stop()
        self.syncPulseTask.StopTask()