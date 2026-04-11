import numpy as np
import pandas as pd

def digitize_ai_signal(ai_signal, digitizeThr=0.9):
    ai_signal_digitized = np.array(ai_signal)

    ai_signal_digitized[ai_signal < digitizeThr] = 0.
    ai_signal_digitized[ai_signal >= digitizeThr] = 1.

    return ai_signal_digitized

def rising_edges(x):
    x = np.asarray(x)
    return np.where((x[:-1] == 0) & (x[1:] == 1))[0] + 1

def falling_edges(x):
    x = np.asarray(x)
    return np.where((x[:-1] == 1) & (x[1:] == 0))[0] + 1

def getKSAllDirFrame(frame_analog: np.array, pd_analog: np.array, 
                     digitizeThr_frame: float=3, digitizeThr_pd: float=8,
                     add_direction_default: bool=False):
    frame_digital = digitize_ai_signal(frame_analog, digitizeThr=digitizeThr_frame)
    pd_digital = digitize_ai_signal(pd_analog, digitizeThr=digitizeThr_pd)

    t_frame = rising_edges(frame_digital)
    t_pd_start = rising_edges(pd_digital)
    t_pd_end = falling_edges(pd_digital)

    rows = []
    for start, end in zip(t_pd_start, t_pd_end):
        mask = (t_frame >= start) & (t_frame <= end)
        frames_in_pulse = np.where(mask)[0]
        if len(frames_in_pulse) > 0:
            rows.append({
                'start_frame': frames_in_pulse[0],
                'end_frame':   frames_in_pulse[-1],
            })
    print(f'Found sweeps: {len(rows)}')

    df = pd.DataFrame(rows)

    if add_direction_default:
        directions = ['B2U', 'U2B', 'L2R', 'R2L']
        df['direction'] = [directions[i % len(directions)] for i in range(len(df))]

    return df

def align_analog_to_stim_onset(analog_rec: dict, digitizeThr: float = 3) -> dict:
    """
    Align all analog channels to the first rising edge of ch2.
    
    Parameters
    ----------
    analog_rec : dict
        Output of load_analog_data, with keys ch0, ch1, ch2, ch3, sample_rate, timestamps_ms.
    digitizeThr : float
        Threshold for digitizing ch2 (default 0.9 V).
    
    Returns
    -------
    dict with same keys, all channels trimmed to start from ch2 onset.
    """
    ch2_dig = digitize_ai_signal(analog_rec['ch2'], digitizeThr=digitizeThr)
    edges = rising_edges(ch2_dig)
    
    if len(edges) == 0:
        raise ValueError('No rising edge found in ch2 — check digitizeThr')
    
    onset_idx = edges[0]
    
    return {
        'frame': analog_rec['ch0'][onset_idx:],
        'pd': analog_rec['ch3'][onset_idx:],
    }