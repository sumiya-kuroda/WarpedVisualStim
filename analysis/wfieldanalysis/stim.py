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

def get_stim_onset_s(pd_analog: np.array, warpedvisualstim_config: dict,
                     ksstim_data:dict, digitizeThr: float=8):

    pd_analog2 = digitize_ai_signal(pd_analog, digitizeThr=digitizeThr)
    idx_rising = rising_edges(pd_analog2)
    idx_falling = falling_edges(pd_analog2)

    direction = ksstim_data['stimulation']['direction']

    return pd.DataFrame({
        'start': idx_rising / warpedvisualstim_config['ds_daqlogger_sample_rate'],
        'end': idx_falling / warpedvisualstim_config['ds_daqlogger_sample_rate'],
        'direction': direction
    })

def align_stim2wf(df_stim, pregap_dur):
    # when stim reaches pregapdur it send ttl to WF to start acquisition
    df = df_stim.copy()
    offset_sec = pregap_dur - df['start'].iloc[0]

    df['start'] = df['start'] + offset_sec
    df['end'] = df['end'] + offset_sec
    return df