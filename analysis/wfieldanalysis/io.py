import os
import numpy as np
from pathlib import Path
from typing import Literal


def _parse_binary_fname(fname, lastidx=None, dtype='uint16', shape=None, sep='_'):
    """Extract dtype and (NCHANNELS, H, W) shape from a wfield-convention filename.

    The filename stem is split on ``sep``; the dtype token is the last
    non-numeric token that is a valid numpy dtype, and the three integers
    immediately before it are (NCHANNELS, H, W).
    """
    fn = os.path.splitext(os.path.basename(fname))[0]
    fnsplit = fn.split(sep)
    fnum = None

    if lastidx is None:
        lastidx = -1
        idx = np.where([not f.isnumeric() for f in fnsplit])[0]
        for i in idx[::-1]:
            try:
                dtype = np.dtype(fnsplit[i])
                lastidx = i
                break
            except TypeError:
                pass

    if dtype is None:
        dtype = np.dtype(fnsplit[lastidx])

    before = [f for f in fnsplit[:lastidx] if f.isdigit()]
    after  = [f for f in fnsplit[lastidx:] if f.isdigit()]

    if shape is None:
        shape = [int(t) for t in before[-3:]]
    if len(after) > 0:
        fnum = [int(t) for t in after]

    return dtype, shape, fnum


def load_dat(filename, nframes=None, offset=0, shape=None, dtype='uint16'):
    """Load frames from a wfield binary `.dat` file into a numpy array.

    Parameters
    ----------
    filename : str
        Path to the `.dat` file.  Shape and dtype are inferred from the
        filename if not provided explicitly.
    nframes : int, optional
        Number of frames to read.  Reads the whole file when ``None``.
    offset : int
        Frame index to start reading from (default 0).
    shape : sequence of int, optional
        ``(NCHANNELS, H, W)`` — inferred from filename when ``None``.
    dtype : str or numpy dtype
        Pixel dtype (default ``'uint16'``).

    Returns
    -------
    numpy.ndarray
        Array of shape ``(nframes, NCHANNELS, H, W)``.
    """
    if not os.path.isfile(filename):
        raise OSError(f'File not found: {filename}')

    if shape is None or dtype is None:
        dtype, shape, _ = _parse_binary_fname(filename, shape=shape, dtype=dtype)

    dt = np.dtype(dtype)
    framesize = int(np.prod(shape))

    if nframes is None:
        nframes = int(os.path.getsize(filename) / (framesize * dt.itemsize))

    with open(filename, 'rb') as fd:
        fd.seek(int(offset) * framesize * dt.itemsize)
        buf = np.fromfile(fd, dtype=dt, count=framesize * nframes)

    return buf.reshape((-1, *shape), order='C')


def mmap_dat(filename, mode='r', nframes=None, shape=None, dtype='uint16'):
    """Open a wfield binary `.dat` file as a memory-mapped array.

    Useful when the data is too large to load into RAM at once.

    Parameters
    ----------
    filename : str
        Path to the `.dat` file.
    mode : {'r', 'r+', 'c'}
        Memory-map access mode (default ``'r'`` — read-only).
    nframes : int, optional
        Number of frames.  Inferred from file size when ``None``.
    shape : sequence of int, optional
        ``(NCHANNELS, H, W)`` — inferred from filename when ``None``.
    dtype : str or numpy dtype
        Pixel dtype (default ``'uint16'``).

    Returns
    -------
    numpy.memmap
        Memory-mapped array of shape ``(nframes, NCHANNELS, H, W)``.
    """
    if not os.path.isfile(filename):
        raise OSError(f'File not found: {filename}')

    if shape is None or dtype is None:
        dtype, shape, _ = _parse_binary_fname(filename, shape=shape, dtype=dtype)

    dt = np.dtype(dtype)

    if nframes is None:
        nframes = int(os.path.getsize(filename) / (np.prod(shape) * dt.itemsize))

    return np.memmap(filename, mode=mode, dtype=dt,
                     shape=(int(nframes), *shape))

def save_frames_average(destination: Path, dat_path: Path, dtype=np.float32):
    """
    Save frames average to a .npy file.

    Parameters
    ----------
    destination : Path
        Directory where frames_average.npy will be saved.
    dat_path : str, optional
        Path to a .dat binary file to compute the average from.
    dtype : np.dtype, optional
        Cast dtype before saving (default: np.float32).
    """
    out_path = destination /'frames_average.npy'
    if not out_path.exists():
        dat = mmap_dat(str(dat_path))
        frames_average = dat.mean(axis=0)
        
        out_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(out_path, frames_average.astype(dtype))
        print('frames_average.npy is saved!')
    else:
        print('Existing frames_average.npy found')
    return out_path

def find_base_path(root = '',
                   top_level: Literal["rawdata", "derivatives", "processed"] = "processed",
                   sub_id = '001',
                   ses_id = '001',
                   print_msg = False):
    top_level_path = Path(root) / top_level 
    if top_level == 'processed':
        return top_level_path
    
    # sub level
    sub_path = None
    for folder in top_level_path.iterdir():
        if folder.is_dir() and f"sub-{sub_id}" in folder.name:
            sub_path = folder
            break
    
    if sub_path is None:
        sub_path = top_level_path / f"sub-{sub_id}"

    # ses level
    base_path = None
    for folder in sub_path.iterdir():
        if folder.is_dir() and f"ses-{ses_id}" in folder.name:
            if print_msg:
                print(f"Found folder: {folder}")
            base_path = folder
            break
    
    if base_path is None:
        base_path = sub_path / f"ses-{ses_id}"

    return base_path

def find_mapping_path(root, sub_id, ses_id):
    rawdata_path = find_base_path(root = root, top_level = 'rawdata', sub_id = sub_id, ses_id = ses_id, print_msg=True)
    derivative_path = find_base_path(root = root, top_level = 'derivatives', sub_id = sub_id, ses_id = ses_id, print_msg=False)
    if 'protocol-mapping' in Path(rawdata_path).name:
        derivative_path.mkdir(parents=True, exist_ok=True)
        return rawdata_path, derivative_path
    else:
        raise ValueError('This is not retinotopy mapping folder!')
    
def find_wf_data(ses_raw_path):
    frames_files = list((ses_raw_path / 'funcimg').glob('Frames_*.dat'))
    assert len(frames_files) == 1, 'There should be only one Frames_*.dat inside rawdata session path'
    if not frames_files:
        raise FileNotFoundError(f"No Frames_*.dat files found in {ses_raw_path}")
    return frames_files[0]