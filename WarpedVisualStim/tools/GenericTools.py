import numpy as np
import queue
from WarpedVisualStim.DisplayStimulus import DisplaySequence
import os

def weighted_average(values, weights):
    if values.shape != weights.shape:
        raise ValueError('"values" and "weights" should have same shape.')

    if np.amin(weights) < 0.:
        raise ValueError('all weights should be no less than 0.')

    return np.sum((values * weights).flat) / np.sum(weights.flat)


def up_crossings(data, threshold=0):
    """
    find the index where the data up cross the threshold. return the indices of all up crossings (the onset data point
    that is greater than threshold, 1d-array). The input data should be 1d array.
    """
    if len(data.shape) != 1:
        raise ValueError('Input data should be 1-d array.')

    pos = data > threshold
    return (~pos[:-1] & pos[1:]).nonzero()[0] + 1


def down_crossings(data, threshold=0):
    """
    find the index where the data down cross the threshold. return the indices of all down crossings (the onset data
    point that is less than threshold, 1d-array). The input data should be 1d array.
    """
    if len(data.shape) != 1:
        raise ValueError('Input data should be 1-d array.')

    pos = data < threshold
    return (~pos[:-1] & pos[1:]).nonzero()[0] + 1


def all_crossings(data, threshold=0):
    """
    find the index where the data cross the threshold in either directions. return the indices of all crossings (the
    onset data point that is less or greater than threshold, 1d-array). The input data should be 1d array.
    """
    if len(data.shape) != 1:
        raise ValueError('Input data should be 1-d array.')

    pos_up = data > threshold
    pos_down = data < threshold
    return ((~pos_up[:-1] & pos_up[1:]) | (~pos_down[:-1] & pos_down[1:])).nonzero()[0] + 1

def make_nested_lst_of_tuples(nested_lst):
    nested_lst_of_tuples = [tuple(l) for l in nested_lst]
    return nested_lst_of_tuples

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')