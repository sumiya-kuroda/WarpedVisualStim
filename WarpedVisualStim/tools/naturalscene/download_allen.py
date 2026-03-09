from allensdk.core.brain_observatory_cache import BrainObservatoryCache
import tifffile
from pathlib import Path
import numpy as np
from skimage.transform import resize

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

print('Downsampling with factor 5...')

target_h = 1080 // 5  # 216
target_w = 1920 // 5  # 384

downsampled = resize(
    scenes.astype(np.float32),
    (scenes.shape[0], target_h, target_w),
    order=3,                # bicubic interpolation
    anti_aliasing=True,
    preserve_range=True
)

print("Downsampled shape:", downsampled.shape)
# (118, 216, 384)

# ------------------------------------------------
# Save as single TIFF stack
# ------------------------------------------------

tifffile.imwrite(
    "natural_scenes_allen_downsampled.tiff",
    downsampled.astype(np.float32)
)