"""
wfieldanalysis.hemodynamic
---------------------------
Hemodynamic correction for dual-channel widefield data (470 nm / 405 nm),
without requiring the wfield package.

The correction regresses the violet (405 nm) channel out of the blue (470 nm)
channel on a per-pixel basis in the SVD-compressed domain.

Functions
---------
hemodynamic_correction : correct SVT_470 using SVT_405 as a regressor
"""

import numpy as np
from tqdm import tqdm
from scipy.signal import butter, filtfilt
from joblib import Parallel, delayed


# ---------------------------------------------------------------------------
# Internal filters
# ---------------------------------------------------------------------------

def _highpass(X, w=0.1, fs=30.):
    """2nd-order Butterworth highpass filter applied along the last axis."""
    b, a = butter(2, w / (fs / 2.), btype='highpass')
    return filtfilt(b, a, X, padlen=50)


def _lowpass(X, w=14., fs=30.):
    """2nd-order Butterworth lowpass filter applied along the last axis."""
    b, a = butter(2, w / (fs / 2.), btype='lowpass')
    return filtfilt(b, a, X, padlen=50)


# ---------------------------------------------------------------------------
# Internal coefficient estimation
# ---------------------------------------------------------------------------

def _find_coeffs(U_chunk, SVTa, SVTb):
    """Regression coefficient r = sum(Ua * Ub) / sum(Ub^2) per pixel chunk."""
    a = np.dot(U_chunk, SVTa)
    b = np.dot(U_chunk, SVTb)
    eps = 1e-10
    return (np.nansum(a * b, axis=1) /
            (np.nansum(b * b, axis=1) + eps))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def hemodynamic_correction(U, SVT_470, SVT_405,
                           fs=30.,
                           freq_lowpass=14.,
                           freq_highpass=0.1,
                           nchunks=1024,
                           run_parallel=True):
    """Correct the blue-channel SVT for haemodynamic artefacts using violet.

    Regresses the (filtered) violet channel (405 nm, SVT_405) out of the
    blue channel (470 nm, SVT_470) on a per-pixel basis.  Operates entirely
    in the SVD-compressed domain — equivalent to ``wfield.hemodynamic_correction``.

    Parameters
    ----------
    U : ndarray, shape (H, W, k) or (H*W, k)
        Spatial components from SVD.
    SVT_470 : ndarray, shape (k, T)
        Temporal components for the blue (signal) channel.
    SVT_405 : ndarray, shape (k, T)
        Temporal components for the violet (reference) channel.
    fs : float
        Frame rate in Hz (default 30).
    freq_lowpass : float or None
        Low-pass cut-off applied to the violet channel before regression
        (default 14 Hz).  Pass None to skip.
    freq_highpass : float or None
        High-pass cut-off applied to both channels before regression
        (default 0.1 Hz).  Pass None to skip.
    nchunks : int
        Number of pixel chunks for parallelisation (default 1024).
    run_parallel : bool
        Run chunk-wise regression in parallel with joblib (default True).

    Returns
    -------
    SVTcorr : ndarray, shape (k, T), float32
        Haemodynamically corrected temporal components (zero-mean).
    rcoeffs : ndarray, shape (H, W) or (H*W,), float32
        Per-pixel regression coefficients.
    T_matrix : ndarray, shape (k, k), float32
        Regression transform matrix (U^+ @ diag(r) @ U).
    """
    dims = U.shape
    U_flat = U.reshape([-1, dims[-1]])   # (H*W, k)
    npix = U_flat.shape[0]

    SVTa = SVT_470.copy().astype('float64')
    SVTb = SVT_405.copy().astype('float64')

    # --- filter ---
    if freq_highpass is not None:
        SVTa = _highpass(SVTa, w=freq_highpass, fs=fs)
        SVTb = _highpass(SVTb, w=freq_highpass, fs=fs)
    if freq_lowpass is not None:
        if freq_lowpass < fs / 2:
            SVTb = _lowpass(SVTb, w=freq_lowpass, fs=fs)
        else:
            print('Skipping lowpass on the violet channel.')

    # --- zero-mean ---
    SVTa = (SVTa.T - np.nanmean(SVTa, axis=1)).T.astype('float32')
    SVTb = (SVTb.T - np.nanmean(SVTb, axis=1)).T.astype('float32')

    # --- per-pixel regression coefficients ---
    idx = np.array_split(np.arange(npix), nchunks)

    if run_parallel:
        results = Parallel(n_jobs=-1)(
            delayed(_find_coeffs)(U_flat[ind, :], SVTa, SVTb)
            for ind in idx)
        rcoeffs = np.hstack(results).astype('float32')
    else:
        rcoeffs = np.zeros(npix, dtype='float32')
        for ind in tqdm(idx, desc='Hemodynamic correction'):
            rcoeffs[ind] = _find_coeffs(U_flat[ind, :], SVTa, SVTb)

    rcoeffs[np.isnan(rcoeffs)] = 1e-10

    # --- regression transform and correction ---
    T_matrix = np.dot(np.linalg.pinv(U_flat), (U_flat.T * rcoeffs).T)
    SVTcorr = SVTa - np.dot(T_matrix, SVTb)
    SVTcorr = (SVTcorr.T - np.nanmean(SVTcorr, axis=1)).T.astype('float32')

    return (SVTcorr,
            rcoeffs.reshape(dims[:2]).astype('float32'),
            T_matrix.astype('float32'))
