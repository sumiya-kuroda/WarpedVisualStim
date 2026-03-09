from allensdk.core.brain_observatory_cache import BrainObservatoryCache
import tifffile
from pathlib import Path
import numpy as np

# ------------------------------------------------
# Download natural scenes stimulus
# ------------------------------------------------

boc = BrainObservatoryCache(manifest_file="manifest.json")

# find an experiment that used natural scenes
exps = boc.get_ophys_experiments(stimuli=["natural_scenes"])

# load experiment data
ds = boc.get_ophys_experiment_data(exps[0]["id"])

# get the image stack
scenes = ds.get_stimulus_template("natural_scenes")

print("Scenes shape:", scenes.shape)
# typically (118, height, width)

# ------------------------------------------------
# Save as single TIFF stack
# ------------------------------------------------

tifffile.imwrite(
    "natural_scenes_allen.tiff",
    scenes.astype(np.float32)
)

print("Saved: natural_scenes_allen.tiff")