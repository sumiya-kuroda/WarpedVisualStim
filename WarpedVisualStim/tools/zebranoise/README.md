## Zebranoise generation

We use a monitor with 1920 x 1080 and split this into 3x3 grid. Therefore, run the following code to generate noise
```sh
pip install zebranoise
```

```py
import zebranoise
zn = zebranoise.zebra_noise("zebranoise.mp4", xsize=640, ysize=360, tdur=5, fps=30, seed=0)

## For reference video
zn = zebranoise.zebra_noise("./reference.mp4", xsize=1920, ysize=1080, tdur=300, fps=30, seed=0)
```

# quick mapping of visual responsive neurons
pip install git+https://github.com/mwshinn/zebra_noise.git

```py
import zebranoise
zebranoise.zebra_noise(
    "zebra_mapping.mp4",
    xsize=960, ysize=540, tdur=60*7,
    fps=30, seed=0, filters=[("comb", 0.125), "photodiode_bscope"]
)
```

This will say `MAGEIO FFMPEG_WRITER WARNING: input image is not divisible by macro_block_size=16, resizing from (640, 360) to (640, 368) to ensure video compatibility with most codecs and players. To prevent resizing, make your input image divisible by the macro_block_size or set the macro_block_size to 1 (risking incompatibility).`

### Reference
https://github.com/mwshinn/zebra_noise