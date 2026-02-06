## Zebranoise generation

We use a monitor with 1920 x 1080 and split this into 3x3 grid. Therefore, run the following code to generate noise
```sh
pip install zebranoise
```

```py
import zebranoise
zn = zebranoise.zebra_noise("zebranoise.mp4", xsize=640, ysize=360, tdur=5, fps=30, seed=0)
```

This will say `MAGEIO FFMPEG_WRITER WARNING: input image is not divisible by macro_block_size=16, resizing from (640, 360) to (640, 368) to ensure video compatibility with most codecs and players. To prevent resizing, make your input image divisible by the macro_block_size or set the macro_block_size to 1 (risking incompatibility).`

### Reference
https://github.com/mwshinn/zebra_noise