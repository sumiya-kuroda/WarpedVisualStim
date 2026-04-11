import os
import numpy as np
from pathlib import Path
from typing import Literal
import json
import pickle 
import scipy.io
import npimage

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

def save_frames_average(destination: Path, movie: np.array):
    """
    Save frames average to .npy, .tif, and .png files.

    Parameters
    ----------
    destination : Path
        Directory where frames_average.npy/tif/png will be saved.
    movie : np.array
        Movie array of shape (T, H, W).
    """
    out_path = destination / 'frames_average.npy'
    if not out_path.exists():
        frames_average = movie.mean(axis=0).astype(np.float32)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(out_path, frames_average)
        print('frames_average.npy saved!')

        npimage.save(frames_average, str(destination / 'frames_average.tif'), overwrite=True)
        print('frames_average.tif saved!')

        npimage.save(contrast_stretch_8bit(frames_average), str(destination / 'frames_average.png'), overwrite=True)
        print('frames_average.png saved!')
    else:
        print('Existing frames_average.npy found')
    return out_path

def save_frames_average_v1(destination: Path, dat_path: Path, dtype=np.float32):
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
                   suffix = '',
                   print_msg = False):
    top_level_path = Path(root) / top_level 
    if top_level == 'processed':
        return top_level_path
    
    # sub level
    sub_path = top_level_path / f"sub-{sub_id}"
    if top_level_path.exists():
        for folder in top_level_path.iterdir():
            if folder.is_dir() and f"sub-{sub_id}" in folder.name:
                sub_path = folder
                break
    
    # ses level
    base_path = sub_path / f"ses-{ses_id}{suffix}"
    if sub_path.exists():
        for folder in sub_path.iterdir():
            if folder.is_dir() and f"ses-{ses_id}" in folder.name:
                if print_msg:
                    print(f"Found folder: {folder}")
                base_path = folder
                break

    return base_path

def find_mapping_path(root, sub_id, ses_id):
    rawdata_path = find_base_path(root=root, top_level='rawdata', sub_id=sub_id, ses_id=ses_id, print_msg=True)
    if 'protocol-mapping' not in Path(rawdata_path).name:
        raise ValueError('This is not retinotopy mapping folder!')
    
    # extract the full suffix from rawdata (e.g. '_protocol-mapping') for derivatives
    rawdata_ses_suffix = Path(rawdata_path).name[len(f"ses-{ses_id}"):]
    derivative_path = find_base_path(root=root, top_level='derivatives', sub_id=sub_id, ses_id=ses_id,
                                     suffix=rawdata_ses_suffix, print_msg=False)
    derivative_path.mkdir(parents=True, exist_ok=True)
    return rawdata_path, derivative_path
    
def load_wf_tif(ses_raw_path, use_only_blue_channel=True, remove_prestim_frames=None, remove_final_dark_frames=5):
    frames_files = list((ses_raw_path / 'funcimg').glob('Frames_*.tif'))
    assert len(frames_files) == 1, 'There should be only one Frames_*.tif inside rawdata session path'
    if not frames_files:
        raise FileNotFoundError(f"No Frames_*.tif files found in {ses_raw_path}")
    
    raw_movie = npimage.load(frames_files[0])

    if remove_prestim_frames is not None:
        raw_movie = raw_movie[remove_prestim_frames:]
        print(f'Removed first {remove_prestim_frames} frames')

    if remove_final_dark_frames is not None:
        raw_movie = raw_movie[:-remove_final_dark_frames]
        print(f'Removed final {remove_final_dark_frames} frames')

    if use_only_blue_channel:
        print('Using only blue channel...')
        raw_movie = raw_movie[0::2]

    return raw_movie

def find_wf_data_v1(ses_raw_path):
    frames_files = list((ses_raw_path / 'funcimg').glob('Frames_*.dat'))
    assert len(frames_files) == 1, 'There should be only one Frames_*.dat inside rawdata session path'
    if not frames_files:
        raise FileNotFoundError(f"No Frames_*.dat files found in {ses_raw_path}")
    return frames_files[0]

def load_warpedvisualstim_config(ses_raw_path: Path):
    folder = ses_raw_path / 'behav'
    matches = list(folder.glob('*_settings.json'))
    if not matches:
        raise FileNotFoundError(f"No *_settings.json found in {folder}")
    if len(matches) > 1:
        raise ValueError(f"Multiple *_settings.json found: {matches}")
    with open(matches[0], 'r') as f:
        return json.load(f)
    
def load_warpedvisualstim_data(ses_raw_path: Path):
    folder = ses_raw_path / 'behav'
    matches = list(folder.glob('*complete.pkl'))
    if not matches:
        raise FileNotFoundError(f"No *complete.pkl found in {folder}")
    if len(matches) > 1:
        raise ValueError(f"Multiple *complete.pkl found: {matches}")
    with open(matches[0], 'rb') as f:
        return pickle.load(f)
    
def load_photodiode_data(ses_raw_path: Path, channel: str='ai2'):
    folder = ses_raw_path / 'behav'
    matches = list(folder.glob(f'*{channel}.npy'))
    if not matches:
        raise FileNotFoundError(f"No *{channel}.npy found in {folder}")
    if len(matches) > 1:
        raise ValueError(f"Multiple *{channel}.npy found: {matches}")
    return np.load(matches[0])

def read_frame_times(mat_path: Path) -> dict:
    """
    Read a frameTimes .mat file (MATLAB v5 format)
    """
    mat = scipy.io.loadmat(str(mat_path))

    return {
        "frame_times":    mat["frameTimes"].ravel().astype(np.float64),
        "removed_frames": int(mat["removedFrames"].ravel()[0]),
        "pre_stim":       int(mat["preStim"].ravel()[0]),
        "post_stim":      int(mat["postStim"].ravel()[0]),
        "img_size":       mat["imgSize"].ravel().astype(np.uint16),
    }

def load_wf_data(ses_raw_path):
    frames_files = list((ses_raw_path / 'funcimg').glob('frameTimes_*.mat'))
    assert len(frames_files) == 1, 'There should be only one frameTimes_*.mat inside rawdata session path'
    if not frames_files:
        raise FileNotFoundError(f"No frameTimes_*.mat files found in {ses_raw_path}")
    return read_frame_times(frames_files[0])

HEADER_DTYPE  = np.dtype("<f8")   # float64 LE
RECORD_DTYPE  = np.dtype("<u2")   # uint16 LE
HEADER_FLOATS = 4
RECORD_WORDS  = 5                 # uint16 words per sample
ADC_MAX_RAW   = 4095.0
ADC_VREF      = 5.0               # volts


def load_analog_data(ses_raw_path: Path):
    frames_files = list((ses_raw_path / 'funcimg').glob('Analog_*.dat'))
    assert len(frames_files) == 1, 'There should be only one Analog_*.dat inside rawdata session path'
    if not frames_files:
        raise FileNotFoundError(f"No Analog_*.dat files found in {ses_raw_path}")
    return read_analog_dat(frames_files[0])

def read_analog_dat(path: Path) -> dict:
    path = Path(path)
    raw = path.read_bytes()

    header = np.frombuffer(raw[:HEADER_FLOATS * 8], dtype=HEADER_DTYPE)
    sample_rate = float(header[2]) * 1_000.0   # kHz -> Hz

    body  = raw[HEADER_FLOATS * 8:]
    n_rec = len(body) // (RECORD_WORDS * 2)
    recs  = np.frombuffer(body[: n_rec * RECORD_WORDS * 2],
                          dtype=RECORD_DTYPE).reshape(n_rec, RECORD_WORDS)

    def to_volts(raw_u16: np.ndarray) -> np.ndarray:
        return (raw_u16.astype(np.float32) / ADC_MAX_RAW * ADC_VREF)

    return {
        "sample_rate":    sample_rate,
        "timestamps_ms":  recs[:, 0],
        "ch0":            to_volts(recs[:, 1]),
        "ch1":            to_volts(recs[:, 2]),
        "ch2":            to_volts(recs[:, 3]),
        "ch3":            to_volts(recs[:, 4]),
    }

def contrast_stretch_8bit(img: np.array, pmin: float = 1, pmax: float = 99) -> np.array:
    """Contrast-stretch a 2D array to uint8 using percentile clipping."""
    vmin, vmax = np.percentile(img, (pmin, pmax))
    img_8bit = np.clip((img - vmin) / (vmax - vmin), 0, 1)
    return (img_8bit * 255).astype(np.uint8)

def save_borders_overlay(destination: Path, img: np.ndarray):
    import tifffile
    tifffile.imwrite(str(destination / 'borders_overlay.tif'), img)
    print('borders_overlay.tif saved!')

    npimage.save(img, str(destination / 'borders_overlay.png'), overwrite=True)
    print('borders_overlay.png saved!')