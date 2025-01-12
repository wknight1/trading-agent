import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-training", "--training", help="turn on training mode", action="store_true")
parser.add_argument("-import-gym", "--import-gym",help="import trading gym", action="store_true")
parser.add_argument("-gym-dir", "--gym-dir", type=str, help="import trading gym")

args = parser.parse_args()

if args.import_gym:
    import sys
    sys.path.insert(0, args.gym_dir)

import config
from gym_core import ioutil  # file i/o to load stock csv files
from collections import deque
import pandas as pd
import datetime
import numpy as np
import pickle
import os

training_mode = config.BSA_PARAMS['TRAINING_MODE']
if args.training:
    training_mode = True
else:
    training_mode = False

_csv_dir  = None
_save_dir = None

os.environ["CUDA_VISIBLE_DEVICES"] = str(config.BSA_PARAMS['P_TRAINING_GPU'])
_len_observation = int(config.BSA_PARAMS['P_OBSERVATION_LEN'])


if training_mode:
    _csv_dir = config.BSA_PARAMS['CSV_DIR_FOR_CREATING_PICKLE_TRAINING']
    _save_dir = config.BSA_PARAMS['PICKLE_DIR_FOR_TRAINING']
else:
    _csv_dir = config.BSA_PARAMS['CSV_DIR_FOR_CREATING_PICKLE_TEST']
    _save_dir = config.BSA_PARAMS['PICKLE_DIR_FOR_TEST']


"""
previously,  I gave secs as 120. but like iljoo said, it needs to be 120.

in other agents, it can changes but you don't have to read every time seconds periods changes
just read maximum periods of data and reuse it   
"""
def prepare_datasets(load_csv_dir, is_spare_dataset=False, interval=120, len_observation=60, len_sequence_secs=120, save_dir=''):
    """
    main coordinate fucntion to create pickle
    :param load_csv_dir : a directory where csv files to be read exist
    :param is_spare_dataset: if true, it uses not prepare_dataset function, but prepares_spare_dataset function.
    :param interval: same as prepare_sparse_dataset
    :param len_observation: only used if is_spare_dataset is true
    :param len_sequence_secs: same as prepare_sparse_dataset
    :param save_dir: root directory where pickle will save
    :return:
    """
    # l = ioutil.load_data_from_directory('0', max_n_episode=1) # episode type
    l = ioutil.load_data_from_directory(load_csv_dir, '0')  # episode type
    for li in l:
        if is_spare_dataset:
            try:
                prepare_sparse_dataset(li, 120, _len_observation, save_dir)
            except Exception as e:
                print(str(e))
        else:
            prepare_dataset(li, 1, len_sequence_secs)


def prepare_sparse_dataset(d, interval=120, len_observation=_len_observation, save_dir=''):
    """
    original version
    loading data from ticker 20180403, yyyymmdd 003350 is started.
    executed time :  1538.569629558868 -> 25.6 minutes!! ( each episode would be 100 mb)

    This function is to get more sparse data set. It is created to make loading time from pickle into memory fast
    :param d:  same as prepare_dataset
    :param interval: same as prepare_dataset, 120 seconds. it is also for performance
    :param len_observation: Instead of 120 seconds, taking 60 seconds is just for performance
    :param save_dir: root directory where pickle will save
    :return: same as prepare_dataset
    """
    current_date = d['meta']['date']
    current_ticker = d['meta']['ticker']

    c_start = datetime.datetime(int(current_date[0:4]), int(current_date[4:6]),
                                int(current_date[6:8]), 9, 5)  # 9hr 5min 0sec, start time
    c_end = datetime.datetime(int(current_date[0:4]), int(current_date[4:6]),
                              int(current_date[6:8]), 15, 20)  # 15hr 20min 0sec, finish time
    c_rng_ts = pd.date_range(start=c_start, end=c_end,
                                    freq='S')  # range between c_start and c_end saving each seconds' data

    max_idx = len(c_rng_ts) - 1

    x_2d = []  # orderbook
    x_1d = []  # transactions
    y_1d = []  # width

    for i, s in enumerate(c_rng_ts):

        if i % interval != 0:
            continue

        d_x2d = deque(maxlen=_len_observation)
        d_x1d = deque(maxlen=_len_observation)

        if c_rng_ts[max_idx] < s + len_observation or i >= max_idx:
            break
        elif s - _len_observation < c_rng_ts[0]:
            continue
        else:
            # first_quote = d['quote'].loc[s]
            # first_order = d['order'].loc[s]
            width = 0
            threshold = 0.33

            # assemble observation for len_observation
            for i in reversed(range(len_observation)):
                d_x2d.append(d['order'].loc[s-i])
                d_x1d.append(d['quote'].loc[s-i])

            # calculate width
            for j in range(len_observation):
                if j == 0:
                    # price_at_signal is the price when the current stock received signal
                    price_at_signal = d['quote'].loc[c_rng_ts[i+j]]['Price(last executed)']
                else:
                    price = d['quote'].loc[c_rng_ts[i+j]]['Price(last executed)']
                    gap = price - price_at_signal - threshold
                    width += gap
            x_2d.append(np.array(d_x2d))
            x_1d.append(np.array(d_x1d))
            y_1d.append(width)

    pickle_name = save_dir + os.path.sep + current_date + '_' + current_ticker + '.pickle'
    print('{} file is created.'.format(pickle_name))
    f = open(pickle_name, 'wb')
    pickle.dump([x_2d, x_1d, y_1d], f)
    f.close()


def prepare_dataset(d, interval=1, len_sequence_of_secs=120):
    """
    :param d
        the variable having pickle file data in memory
    :param interval
        a period between previous observation and current observation,
        if it bring data moving 1 second forward, data size is so huge.
    :param len_sequence_of_secs:
        each observation length
    :return:
        nothing, it end up saving list of pickle files as you configured
    """
    current_date = d['meta']['date']
    current_ticker = d['meta']['ticker']

    d_price = deque(maxlen=len_sequence_of_secs)

    c_start = datetime.datetime(int(current_date[0:4]), int(current_date[4:6]),
                                int(current_date[6:8]), 9, 5)  # 9hr 5min 0sec, start time
    c_end = datetime.datetime(int(current_date[0:4]), int(current_date[4:6]),
                              int(current_date[6:8]), 15, 20)  # 15hr 20min 0sec, finish time
    c_rng_ts = pd.date_range(start=c_start, end=c_end,
                                    freq='S')  # range between c_start and c_end saving each seconds' data

    x_2d = []  # orderbook
    x_1d = []  # transactions
    y_1d = []  # width

    max_idx = len(c_rng_ts) - 1

    for i, s in enumerate(c_rng_ts):

        if i % interval != 0:
            continue

        if c_rng_ts[max_idx] < c_rng_ts[i] + len_sequence_of_secs or i >= max_idx:
            break
        elif s - len_sequence_of_secs < c_rng_ts[0]:
            continue
        else:
            first_quote = d['quote'].loc[s]
            first_order = d['order'].loc[s]
            width = 0
            threshold = 0.33

            # calculate width
            for j in range(len_sequence_of_secs):
                if j == 0:
                    # price_at_signal is the price when the current stock received signal
                    price_at_signal = d['quote'].loc[c_rng_ts[i+j]]['Price(last executed)']
                else:
                    price = d['quote'].loc[c_rng_ts[i+j]]['Price(last executed)']
                    gap = price - price_at_signal - threshold
                    width += gap

            x_2d.append(first_order)
            x_1d.append(first_quote)
            y_1d.append(width)

    pickle_name = current_date + '_' + current_ticker + '.pickle'
    f = open(pickle_name, 'wb')
    pickle.dump([x_2d, x_1d, y_1d], f)
    print('{} file is created.'.format(pickle_name))
    f.close()


if _csv_dir == '' or _csv_dir is None:
    _csv_dir = 'sparse_3'

if _save_dir == '' or _save_dir is None:
    _csv_dir = 'pickle_dir'

if not os.path.isdir(_save_dir):
    os.makedirs(_save_dir)

prepare_datasets(load_csv_dir=_csv_dir, is_spare_dataset=True, save_dir=_save_dir)