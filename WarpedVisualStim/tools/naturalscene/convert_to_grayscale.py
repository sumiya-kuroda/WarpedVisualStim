"""
Convert a color (RGB/RGBA) images_original.tif stack to grayscale so it can
be used with WarpedVisualStim's Monitor.warp_images(), which only accepts
2D (single image) or 3D (frame x height x width) arrays.

Grayscale conversion uses a flat mean across the R/G/B channels.
Always writes to a new file -- never overwrites the input.

Usage:
    python convert_to_grayscale.py path\to\images_original.tif
    # writes path\to\images_original_gray.tif

    # optional: specify output path explicitly
    python convert_to_grayscale.py path\to\images_original.tif -o path\to\output.tif
"""

import argparse
import os
import sys

import numpy as np
import tifffile as tf


def convert_to_grayscale(imgs: np.ndarray) -> np.ndarray:
    if imgs.ndim in (2, 3):
        print(f"Input already has shape {imgs.shape} (2D or 3D) -- no conversion needed.")
        return imgs

    if imgs.ndim != 4:
        raise ValueError(
            f"Unexpected array shape {imgs.shape} (ndim={imgs.ndim}). "
            "Expected 4D (frame x height x width x channel)."
        )

    n_channels = imgs.shape[-1]
    if n_channels not in (3, 4):
        raise ValueError(
            f"Last axis has {n_channels} entries; expected 3 (RGB) or 4 (RGBA)."
        )

    gray = imgs[..., :3].mean(axis=-1)
    return gray.astype(imgs.dtype)


def default_output_path(input_path: str) -> str:
    root, ext = os.path.splitext(input_path)
    return f"{root}_gray{ext}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="path to images_original.tif")
    parser.add_argument(
        "-o", "--output", default=None,
        help="output path (default: <input>_gray.tif, in the same folder)"
    )
    args = parser.parse_args()

    output_path = args.output or default_output_path(args.input)
    if os.path.abspath(output_path) == os.path.abspath(args.input):
        print("Error: output path must be different from the input path.")
        sys.exit(1)

    print(f"Reading: {args.input}")
    imgs = tf.imread(args.input)
    print(f"Input shape: {imgs.shape}, dtype: {imgs.dtype}")

    try:
        imgs_gray = convert_to_grayscale(imgs)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Writing grayscale stack to: {output_path}")
    print(f"Output shape: {imgs_gray.shape}, dtype: {imgs_gray.dtype}")
    tf.imwrite(output_path, imgs_gray)
    print("Done.")


if __name__ == "__main__":
    main()