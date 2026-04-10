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
from numpy.fft import fft as _fft
from scipy.ndimage import gaussian_filter
from scipy.sparse import issparse
import matplotlib.colors as mcolors


# ---------------------------------------------------------------------------
# FFT utilities
# ---------------------------------------------------------------------------

def fft_movie(movie, component=1, output_raw=False):
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
    movief = _fft(movie, axis=0)
    if output_raw:
        return movief[component]
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
