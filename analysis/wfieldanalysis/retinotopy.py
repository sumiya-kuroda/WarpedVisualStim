"""
wfieldanalysis.retinotopy
--------------------------
FFT-based retinotopic mapping utilities and SVD reconstruction,
without requiring the wfield package.

Functions
---------
fft_movie         : FFT along time axis -> magnitude and phase per pixel
fft_get_phase     : extract phase from a raw FFT result
im_fftphase_hsv   : HSV colour image encoding FFT phase (for retinotopy maps)
reconstruct       : reconstruct full movie from SVD components (U, SVT)
"""

import numpy as np
from numpy.fft import fft
from scipy.ndimage import gaussian_filter
from scipy.sparse import issparse
import matplotlib.colors as mcolors
import pandas as pd

# ---------------------------------------------------------------------------
# FFT utilities
# ---------------------------------------------------------------------------

def fft_movie(movie, component=1, output_raw=False, axis=0):
    """Compute the FFT of a movie along the time axis.

    Parameters
    ----------
    movie : ndarray, shape (T, H, W)
        Imaging movie.
    component : int
        Which frequency component to extract (default 1 = stimulus frequency).
    output_raw : bool
        If True return the raw complex FFT component; otherwise return
        (magnitude, phase).

    Returns
    -------
    mag : ndarray, shape (H, W)
        Amplitude map: |FFT[component]| * 2 / T
    phase : ndarray, shape (H, W)
        Phase map in radians [0, 2*pi).

    Or, when output_raw is True:

    movief : ndarray, shape (H, W), complex
        Raw complex FFT at component.
    """
    movief = fft(movie, axis=axis)
    if output_raw:
        return movief   # full complex array, index [component] in the caller
    phase = -1.0 * np.angle(movief[component]) % (2 * np.pi)
    mag   = (np.abs(movief[component]) * 2.0) / len(movie)
    return mag, phase


def fft_get_phase(movief):
    """Return the phase [0, 2*pi) from a raw complex FFT array.

    Parameters
    ----------
    movief : ndarray, complex
        Output of fft_movie(..., output_raw=True).

    Returns
    -------
    phase : ndarray, float
    """
    return -1.0 * np.angle(movief) % (2 * np.pi)


# ---------------------------------------------------------------------------
# Visualisation
# ---------------------------------------------------------------------------

def im_fftphase_hsv(mov, component=1, blur=0,
                    vperc=98, sperc=90, return_hsv=False):
    """Create an HSV-encoded colour image of the FFT phase map.

    Hue encodes phase (retinotopic position), saturation and value encode
    response amplitude.  Equivalent to wfield.im_fftphase_hsv.

    Parameters
    ----------
    mov : ndarray, shape (T, H, W), or list [magnitude, phase]
        Raw movie, or pre-computed [mag, phase] from fft_movie.
    component : int
        Stimulus frequency component (default 1).
    blur : float
        Gaussian sigma applied to each frame before FFT (default 0 = off).
    vperc : float
        Percentile used to normalise the value (brightness) channel (default 98).
    sperc : float
        Percentile used to normalise the saturation channel (default 90).
    return_hsv : bool
        If True return a float32 HSV array in [0, 1] instead of an RGB
        uint8 image.

    Returns
    -------
    rgb : ndarray, shape (H, W, 3), uint8
        RGB colour image (suitable for plt.imshow).

    Or, when return_hsv is True:

    hsv : ndarray, shape (H, W, 3), float32
        HSV array with values in [0, 1].
    """
    if blur != 0:
        mov = np.stack([gaussian_filter(frame, sigma=blur) for frame in mov])

    if isinstance(mov, list):
        mag, H = mov
    else:
        mag, H = fft_movie(mov, component=component)

    H = H / (2 * np.pi)           # hue: [0, 1]

    V = mag.copy()
    V /= np.percentile(mag, vperc)

    S = mag ** 0.3
    S /= np.percentile(S, sperc)

    hsv = np.clip(np.stack([H, S, V], axis=2).astype(np.float32), 0, 1)

    if return_hsv:
        return hsv

    # Convert HSV -> RGB using matplotlib (no cv2 needed)
    rgb = mcolors.hsv_to_rgb(hsv)
    return (rgb * 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# SVD reconstruction
# ---------------------------------------------------------------------------

def reconstruct(u, svt, dims=None):
    """Reconstruct a movie from SVD spatial (U) and temporal (SVT) components.

    Works with both dense and sparse U matrices.

    Parameters
    ----------
    u : ndarray, shape (H*W, k) or sparse matrix
        Spatial components. If U is shaped (H, W, k) from approximate_svd,
        reshape first: U.reshape(-1, U.shape[-1]).
    svt : ndarray, shape (k, T)
        Temporal components.
    dims : tuple of int (H, W), optional
        Required when u is a sparse matrix.

    Returns
    -------
    movie : ndarray, shape (T, H, W)
        Reconstructed movie.

    Examples
    --------
    >>> U_flat = U.reshape(-1, U.shape[-1])   # (H*W, k)
    >>> movie  = reconstruct(U_flat, SVT)      # (T, H, W)
    """
    if issparse(u):
        if dims is None:
            raise ValueError('Provide dims=(H, W) when u is a sparse matrix.')
    else:
        if dims is None:
            dims = u.shape[:2]

    return (u @ svt).reshape((*dims, -1)).transpose(-1, 0, 1).squeeze()





def compute_dff(movie: np.ndarray, df_stim: pd.DataFrame, n_baseline_frames: int = 5) -> np.ndarray:
    """
    Compute dF/F using per-trial baseline from the n frames preceding each trial onset.

    Parameters
    ----------
    movie : np.ndarray, shape (T, H, W)
        Raw fluorescence movie.
    df_stim : pd.DataFrame
        Columns: start_frame, end_frame, direction.
    n_baseline_frames : int
        Number of frames before each trial start to use as baseline (default 5).

    Returns
    -------
    dff : np.ndarray, shape (T, H, W)
        dF/F movie, same shape as input.
    """
    movie = movie.astype(np.float32)
    dff = np.full_like(movie, np.nan)

    starts = df_stim['start_frame'].values
    ends   = df_stim['end_frame'].values

    for i, (start, end) in enumerate(zip(starts, ends)):
        # baseline: n frames before trial start
        baseline_start = max(0, start - n_baseline_frames)
        baseline = movie[baseline_start:start].mean(axis=0)  # (H, W)
        baseline = np.where(baseline == 0, 1e-10, baseline)  # avoid division by zero

        dff[start:end] = (movie[start:end] - baseline) / baseline

    return dff


def remap_range(x: np.ndarray, out_min: float, out_max: float) -> np.ndarray:
    """Linearly remap array from its own [min, max] to [out_min, out_max]."""
    x_min, x_max = x.min(), x.max()
    return (x - x_min) / (x_max - x_min) * (out_max - out_min) + out_min


def compute_phase_maps(dff: np.ndarray, df_stim: pd.DataFrame,
                       azimuth_range: tuple = (0, 90),
                       elevation_range: tuple = (-30, 30),
                       smooth_sigma: float = 2.0):
    """
    Compute retinotopic phase maps and visual field sign map from dF/F movie.

    Parameters
    ----------
    dff : np.ndarray, shape (T, H, W)
        dF/F movie.
    df_stim : pd.DataFrame
        Columns: start_frame, end_frame, direction (B2U, U2B, L2R, R2L).
    azimuth_range : tuple
        (min, max) horizontal visual angle in degrees e.g. (0, 90).
    elevation_range : tuple
        (min, max) vertical visual angle in degrees e.g. (-30, 30).
    smooth_sigma : float
        Gaussian smoothing sigma for phase/VFS maps.

    Returns
    -------
    dict with keys: azimuth, elevation, vfs, magnitude
    """
    directions = ['B2U', 'U2B', 'L2R', 'R2L']

    # --- Step 1: FFT at stimulus frequency per direction ---
    fft_maps = {}
    for direction in directions:
        trials = df_stim[df_stim['direction'] == direction]
        trial_ffts = []
        for _, row in trials.iterrows():
            snippet = dff[row['start_frame']:row['end_frame']].astype(np.float32)
            f = np.fft.fft(snippet, axis=0)
            trial_ffts.append(f[1])
        fft_maps[direction] = np.mean(trial_ffts, axis=0)

    # --- Step 2: combine opposite directions to cancel hemodynamic delay ---
    a1 = np.mod(-np.angle(fft_maps['B2U']), 2 * np.pi)
    a2 = np.mod(-np.angle(fft_maps['U2B']), 2 * np.pi)
    elevation = remap_range((a1 - a2) / 2, *elevation_range)

    a1 = np.mod(-np.angle(fft_maps['L2R']), 2 * np.pi)
    a2 = np.mod(-np.angle(fft_maps['R2L']), 2 * np.pi)
    azimuth = remap_range((a1 - a2) / 2, *azimuth_range)

    # --- Step 3: magnitude ---
    magnitude = np.sqrt(
        np.abs(fft_maps['B2U'] * fft_maps['U2B']) +
        np.abs(fft_maps['L2R'] * fft_maps['R2L'])
    )
    magnitude = (magnitude - magnitude.min()) / (magnitude.max() - magnitude.min())

    # --- Step 4: smooth ---
    elevation_smooth = gaussian_filter(elevation, sigma=smooth_sigma)
    azimuth_smooth   = gaussian_filter(azimuth,   sigma=smooth_sigma)

    # --- Step 5: visual field sign map ---
    dhdx, dhdy = np.gradient(azimuth_smooth)
    dvdx, dvdy = np.gradient(elevation_smooth)

    graddir_hor  = np.arctan2(dhdy, dhdx)
    graddir_vert = np.arctan2(dvdy, dvdx)

    vdiff = np.exp(1j * graddir_hor) * np.exp(-1j * graddir_vert)
    vfs = np.sin(np.angle(vdiff))
    vfs = gaussian_filter(vfs, sigma=smooth_sigma)

    return {
        'azimuth':   azimuth_smooth,
        'elevation': elevation_smooth,
        'vfs':       vfs,
        'magnitude': magnitude,
    }