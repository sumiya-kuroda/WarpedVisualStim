# WarpedVisualStim package
  
by Jun Zhuang
&copy; 2019 Allen Institute
email: junz&lt;AT&gt;alleninstitute&lt;DOT&gt;org
  
The WarpedVisualStim package is a self-contained module
for display spherically corrected visual stimuli on a flat
screen in visual physiology experiments. It is a wrapper of 
the "[psychopy](https://www.psychopy.org/)" package.
  
The visual stimuli generation and display is implemented in the modules
`MonitorSetup.py`, `StimulusRoutines.py` and `DisplayStimulus.py`.
These modules allow you to display flashing circle, sparse noise,
locally sparse noise, drifting grading circle, static grading circle
and others with spherical correction. The method for spherical
correction is the same as Marshel et al. 2011 (2). These stimulus
routines are highly customizable and designed to give the user
significant flexibility and control in creative experimental design.
  
It can also interact with a National Instrument equipment to receive 
trigger and emit timing signals.
  
Please check the '\examples\visual_stimulation' folder for
example script `example_stimulation.py` of visual stimulation.

### Contributors:
* Jun Zhuang @zhuangj
* John Yearseley @yearsj
* Derric Williams @derricw

### Level of support
We are planning on occasional updating this tool with no fixed schedule. Community involvement is encouraged through both issues and pull requests.

#### Language:

1. python 3.8


#### Install:
```sh
cd <package_path>
conda env create -f environment.yml # use 3.8.10 for latest psychopy
PYTHONIOENCODING=utf8 conda activate warpedvisualstim # (Windows) https://stackoverflow.com/questions/59974715/conda-unicodeencodeerror-charmap-codec-cant-encode-character-u2580-in-po
source activate warpedvisualstim # (Mac or Linux)
python setup.py install
# pip install psychopy==2023.1.0
# pip install pytest
```


#### Dependencies:
1. pytest
2. numpy
3. scipy
4. matplotlib
5. h5py
6. pillow
7. psychopy
8. pyglet
9. OpenCV
10. scikit-image
11. tifffile
12. PyDAQmx
13. configobj
14. sphinx, version 1.6.3 or later (just for documentation)
15. numpydoc, version 0.7.0 (just for documentation)

for detailed installation instructions see the
install page in documentation (`doc` branch).

#### Issues:

1. Most image analysis parameters are defined as number of pixels, not microns.
2. Works in windows, but not fully tested on Mac and Linux.
3. You can delete conda env with `conda remove --name warpedvisualstim --all`.