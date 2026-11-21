"""Launch PsychoPy Monitor Center with gammaErrorPolicy='warn', so gamma
calibration works with extended multi-monitor desktops on Windows 10/11
(Monitor Center otherwise crashes with 'GetDeviceGammaRamp failed')."""
from psychopy import visual

_orig_init = visual.Window.__init__


def _init(self, *args, **kwargs):
    kwargs.setdefault("gammaErrorPolicy", "warn")
    _orig_init(self, *args, **kwargs)


visual.Window.__init__ = _init

from psychopy.monitors.MonitorCenter import MonitorCenter

if __name__ == "__main__":
    app = MonitorCenter(0)
    app.MainLoop()
