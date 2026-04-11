import os
import numpy as np
from numpy.linalg import svd as _full_svd
from tqdm import tqdm
from pathlib import Path
from .io import load_dat

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_trial_baseline(idx, frames_average, onsets):
    """Return the baseline frame(s) that applies at frame index *idx*."""
    if frames_average.ndim <= 3:
        return frames_average
    if onsets is None:
        return frames_average[0]
    return frames_average[np.where(onsets <= idx)[0][-1]]


def _load_block(dat, start, length):
    """Load a contiguous block of frames from *dat* (array or memmap)."""
    if hasattr(dat, 'filename'):
        # memory-mapped: read from disk directly to avoid loading everything
        shape = dat.shape[1:]
        dt = dat.dtype
        framesize = int(np.prod(shape))
        with open(dat.filename, 'rb') as fd:
            fd.seek(start * framesize * dt.itemsize)
            buf = np.fromfile(fd, dtype=dt, count=framesize * length)
        return buf.reshape((-1, *shape), order='C').astype('float32')
    else:
        return dat[start:start + length].astype('float32')


def _make_overlapping_blocks(dims, blocksize=128, overlap=16):
    """Return a list of ``[(row_start, row_end), (col_start, col_end)]`` index pairs
    that tile *dims* = (H, W) with overlapping blocks."""
    w, h = dims
    blocks = []
    for a in range(0, w, blocksize - overlap):
        for b in range(0, h, blocksize - overlap):
            blocks.append([
                (a, int(np.clip(a + blocksize, 0, w))),
                (b, int(np.clip(b + blocksize, 0, h))),
            ])
    return blocks


def approximate_svd(dat, frames_average,
                    onsets=None,
                    k=200,
                    mask=None,
                    nframes_per_bin=15,
                    nbinned_frames=5000,
                    nframes_per_chunk=500,
                    divide_by_average=True):
    """Approximate SVD by estimating U from a binned movie then projecting onto it.

    Parameters
    ----------
    dat : array-like, shape (T, H, W)
        Raw imaging data.
    frames_average : ndarray, shape (H, W)
        Baseline used for mean-centring.
    onsets : array-like of int, optional
        Trial onset frame indices for per-trial baseline lookup.
    k : int
        Number of SVD components to retain (default 200).
    mask : ndarray of bool, shape (H, W), optional
        Pixels outside the mask are zeroed before decomposition.
    nframes_per_bin : int
        Frames averaged into each bin when estimating U (default 15).
    nbinned_frames : int
        Maximum number of bins used to estimate U (default 5000).
    nframes_per_chunk : int
        Frames loaded at once when projecting onto U (default 500).
    divide_by_average : bool
        If True compute (x - avg) / avg; otherwise compute x - avg.

    Returns
    -------
    U : ndarray, shape (H, W, k)
        Spatial components.
    SVT : ndarray, shape (k, T)
        Temporal components (S·VT).
    """
    from sklearn.preprocessing import normalize

    dims = dat.shape[1:]      # (H, W)
    nframes = dat.shape[0]
    npix = int(np.prod(dims)) # H * W

    # --- Step 1: bin the raw movie to estimate U ----------------------------
    if nbinned_frames < k:
        nframes_per_bin = int(np.clip(np.floor(nframes / k), 1, nframes_per_bin))

    nbinned_frames = int(min(nbinned_frames, np.floor(nframes / nframes_per_bin)))

    idx = np.arange(0, nbinned_frames * nframes_per_bin, nframes_per_bin, dtype='int')
    if idx[-1] != nbinned_frames * nframes_per_bin:
        idx = np.hstack([idx, nbinned_frames * nframes_per_bin - 1])

    binned = np.zeros([len(idx) - 1, npix], dtype='float32')

    for i in tqdm(range(len(idx) - 1), desc='Binning raw data'):
        blk = _load_block(dat, idx[i], idx[i + 1] - idx[i]).astype('float32')  # (chunk, H, W)
        avg = _get_trial_baseline(idx[i], frames_average, onsets).astype('float32')
        if divide_by_average:
            binned[i] = np.mean(
                (blk - avg) / (avg + np.float32(1e-10)),
                axis=0).ravel()
        else:
            binned[i] = np.mean(blk - avg, axis=0).ravel()

        if mask is not None:
            binned[i][~mask.ravel()] = 0.0

    # --- Step 2: SVD on the covariance of binned frames to get U ------------
    cov = np.dot(binned, binned.T) / npix
    cov = cov.astype('float32')

    u, s, v = _full_svd(cov)
    U = normalize(np.dot(u[:, :k].T, binned), norm='l2', axis=1)  # (k, npix)
    k = U.shape[0]  # may be smaller if variance is low

    # --- Step 3: project full data onto U to get SVT ------------------------
    idx = np.arange(0, nframes, nframes_per_chunk, dtype='int')
    if idx[-1] != nframes:
        idx = np.hstack([idx, nframes])

    SVT = np.zeros((k, nframes), dtype='float32')

    for i in tqdm(range(len(idx) - 1), desc='Computing SVT from raw data'):
        blk = _load_block(dat, idx[i], idx[i + 1] - idx[i]).astype('float32')  # (chunk, H, W)
        chunk_len = blk.shape[0]
        avg = _get_trial_baseline(idx[i], frames_average, onsets).astype('float32')
        blk -= avg
        if divide_by_average:
            blk /= avg + np.float32(1e-10)
        SVT[:, idx[i]:idx[i] + chunk_len] = np.dot(U, blk.reshape([chunk_len, npix]).T)  # (k, chunk)

    U = U.T.reshape([*dims, k])  # (H, W, k)
    return U, SVT


def svd_blockwise(dat, frames_average,
                  k=200, block_k=20,
                  blocksize=120, overlap=8,
                  divide_by_average=True,
                  random_state=42):
    """Memory-efficient block-wise randomised SVD.

    Splits the spatial dimensions into overlapping blocks, runs a randomised
    SVD on each block (all time points, few pixels), then merges by running a
    second SVD on the concatenated temporal components.

    Equivalent to ``wfield.svd_blockwise`` (Musall / Stringer et al. 2019).

    Parameters
    ----------
    dat : array-like, shape (T, C, H, W)
        Raw imaging data.
    frames_average : ndarray, shape (C, H, W)
        Baseline subtracted before decomposition.
    k : int
        Final number of components (default 200).
    block_k : int
        Components extracted per spatial block (default 20).
    blocksize : int
        Spatial block size in pixels (default 120).
    overlap : int
        Overlap between adjacent blocks (default 8).
    divide_by_average : bool
        If True compute ``(x - avg) / avg`` before SVD (default True).
    random_state : int
        Seed for the randomised SVD (default 42).

    Returns
    -------
    U : ndarray, shape (H*W, k)
        Spatial components.
    SVT : ndarray, shape (k, T*C)
        Temporal components.
    S : ndarray, shape (k,)
        Singular values.
    """
    from sklearn.utils.extmath import randomized_svd
    from sklearn.preprocessing import normalize

    nframes, nchannels, w, h = dat.shape
    n = nframes * nchannels

    blocks = _make_overlapping_blocks((w, h), blocksize=blocksize, overlap=overlap)
    nblocks = len(blocks)

    block_U   = np.full((nblocks, blocksize, blocksize, block_k), np.nan, dtype=np.float32)
    block_SVT = np.zeros((nblocks, block_k, n), dtype=np.float32)

    for iblock, (ir, ic) in tqdm(enumerate(blocks), total=nblocks,
                                  desc='Block-wise SVD'):
        arr = np.array(dat[:, :, ir[0]:ir[1], ic[0]:ic[1]], dtype='float32')
        arr -= frames_average[:, ir[0]:ir[1], ic[0]:ic[1]]
        if divide_by_average:
            arr /= frames_average[:, ir[0]:ir[1], ic[0]:ic[1]] + np.float32(1e-10)
        bw, bh = arr.shape[-2:]
        arr = arr.reshape([-1, bw * bh])
        u, s, vt = randomized_svd(arr.T,
                                   n_components=block_k,
                                   n_iter=5,
                                   power_iteration_normalizer='LQ',
                                   random_state=random_state)
        block_U[iblock, :bw, :bh, :] = u.reshape([bw, bh, -1])
        block_SVT[iblock] = np.dot(np.diag(s), vt)

    U, SVT, S = _complete_svd_from_blocks(block_U, block_SVT, blocks, k, (w, h))
    return U, SVT, S


# ---------------------------------------------------------------------------
# Private helpers for svd_blockwise
# ---------------------------------------------------------------------------

def _assemble_blockwise_spatial(block_U, blocks, dims):
    w, h = dims
    U = np.zeros([block_U.shape[0], block_U.shape[-1], w, h], dtype='float32')
    weights = np.zeros((w, h), dtype='float32')
    for iblock, (ir, ic) in enumerate(blocks):
        lw = ir[1] - ir[0]
        lh = ic[1] - ic[0]
        U[iblock, :, ir[0]:ir[1], ic[0]:ic[1]] = \
            block_U[iblock, :lw, :lh, :].transpose(-1, 0, 1)
        weights[ir[0]:ir[1], ic[0]:ic[1]] += 1
    U = (U / weights).reshape((block_U.shape[0] * block_U.shape[-1], -1))
    return U.T


def _complete_svd_from_blocks(block_U, block_SVT, blocks, k, dims,
                               n_iter=15, random_state=42):
    from sklearn.utils.extmath import randomized_svd
    u, s, vt = randomized_svd(
        block_SVT.reshape([np.prod(block_SVT.shape[:2]), -1]),
        n_components=k,
        n_iter=n_iter,
        power_iteration_normalizer='QR',
        random_state=random_state)
    S = s
    SVT = np.dot(np.diag(S), vt)
    U = np.dot(_assemble_blockwise_spatial(block_U, blocks, dims), u)
    return U, SVT, S

def run_svd(destination: Path, movie: np.array, frames_average: np.array, method='approximate'):
    U_path = destination /'U.npy'
    SVT_path = destination /'SVT.npy'
    if not U_path.exists():
        if method == 'approximate':
            U,SVT = approximate_svd(movie, frames_average)
        else:
            raise NotImplementedError
        
        np.save(U_path,U)
        np.save(SVT_path,SVT)
        print('SVD results saved!')
    else:
        print('Existing SVD results found')
    return U_path, SVT_path