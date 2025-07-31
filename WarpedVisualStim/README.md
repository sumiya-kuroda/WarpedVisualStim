## WarpedVisualStim - Getting Started
WarpedVisaulStim experiments have two independent components: (A) displaying visual stimuli and (B) recording photodiode signals (via NIDAQ), which need to be conducted at the same time.

### A. Visual stimuli
You choose what stimulus to show by selectively running
```sh
python STIMULUS_TYPE.py
```
and configure its pattern by editing the json file under `protocols/`. Their filenames should start with the name of imaging modality you are using: e.g. `2p` or `wf`.

As of July 2025, available stimuli are
- `main.py`: RF mapping
- `checkerboard.py`: RF mapping
- `dgrating.py`: drifting grating (both non-inversed and inversed)

### B. Photodiode recording
On a separate conda window, run
```sh
python daqlogger.py
```

### Postprocessing
Run
```sh
python postprocess.py
```

It will output stats like below
```
Total number of frames      : 40995.
Total length of display     : 148.10938 second.
Expected length of display  : 683.25000 second.
Mean of frame intervals     : 3.61 ms.
S.D. of frame intervals     : 8.56 ms.
Shortest frame: 0.00 ms, index: 0.
Longest frame : 46.88 ms, index: 1996.
Number of frames longer than 0.020 second: 2500;   6.10%
Number of frames longer than 0.033 second: 3;   0.01%
Number of frames longer than 0.050 second: 0;   0.00%
Number of frames longer than 0.100 second: 0;   0.00%

Analyzing photodiode onsets in a sequential manner ...
000_LocallySparseNoiseRetinotopicMapping     : number of photodiode_onset: 2709

Total number of expected photodiode onsets: 2709
Postprocess completed!
```

Edit `protocols/postprocess_setting.json` for your environments.

### How to analyze Photodiode recording
- `main.py`'s photodiode becomes high during all stimulus presentation.
- `checkerboard.py`'s photodiode becomes high at the onset of each square presentation, and becomes low afterwards.