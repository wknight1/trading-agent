
import os
import sys
newPath = os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))) + '/trading-gym'
sys.path.append(newPath)

from keras.models import Model
from keras.layers import LeakyReLU, Input, Dense, Conv3D, Conv1D, Dense, Flatten, MaxPooling1D, MaxPooling2D,MaxPooling3D,Concatenate
import numpy as np
import pickle
from rl.callbacks import FileLogger, ModelIntervalCheckpoint
from gym_core.ioutil import *  # file i/o to load stock csv files
import logging

"""
it will prevent process not to occupying 100% of gpu memory for the first time. 
Instead, it will use memory incrementally.
"""
# import tensorflow as tf
# from keras.backend.tensorflow_backend import set_session
# config = tf.ConfigProto()
# config.gpu_options.per_process_gpu_memory_fraction = 0.2
# set_session(tf.Session(config=config))

"""
build q newtork using cnn and dense layer
"""
def build_network():
    input_order = Input(shape=(10, 2, 120, 2), name="x1")
    input_tranx = Input(shape=(120, 11), name="x2")

    h_conv1d_2 = Conv1D(filters=16, kernel_size=3, activation='relu')(input_tranx)
    h_conv1d_4 = MaxPooling1D(pool_size=3, strides=None, padding='valid')(h_conv1d_2)
    h_conv1d_6 = Conv1D(filters=32, kernel_size=3, activation='relu')(h_conv1d_4)
    h_conv1d_8 = MaxPooling1D(pool_size=2, strides=None, padding='valid')(h_conv1d_6)

    h_conv3d_1_1 = Conv3D(filters=16, kernel_size=(2, 1, 5), activation='relu')(input_order)
    h_conv3d_1_2 = Conv3D(filters=16, kernel_size=(1, 2, 5), activation='relu')(input_order)

    h_conv3d_1_3 = MaxPooling3D(pool_size=(1, 1, 3))(h_conv3d_1_1)
    h_conv3d_1_4 = MaxPooling3D(pool_size=(1, 1, 3))(h_conv3d_1_2)

    h_conv3d_1_5 = Conv3D(filters=32, kernel_size=(1, 2, 5), activation='relu')(h_conv3d_1_3)
    h_conv3d_1_6 = Conv3D(filters=32, kernel_size=(2, 1, 5), activation='relu')(h_conv3d_1_4)

    h_conv3d_1_7 = MaxPooling3D(pool_size=(1, 1, 5))(h_conv3d_1_5)
    h_conv3d_1_8 = MaxPooling3D(pool_size=(1, 1, 5))(h_conv3d_1_6)
    o_conv3d_1 = Concatenate(axis=-1)([h_conv3d_1_7, h_conv3d_1_8])

    o_conv3d_1_1 = Flatten()(o_conv3d_1)

    i_concatenated_all_h_1 = Flatten()(h_conv1d_8)

    i_concatenated_all_h = Concatenate()([i_concatenated_all_h_1, o_conv3d_1_1])

    output = Dense(1, activation='linear')(i_concatenated_all_h)

    model = Model([input_order, input_tranx], output)

    return model


"""
build q newtork using cnn and dense layer
"""
def build_network_for_sparsed():

    input_order = Input(shape=(10, 2, 60, 2), name="x1")
    input_tranx = Input(shape=(60, 11), name="x2")
    input_elapedtime = Input(shape=(max_len,), name="x3")
    input_lefttime = Input(shape=(max_len,), name="x4")

    h_conv1d_2 = Conv1D(filters=16, kernel_size=3)(input_tranx)
    h_conv1d_2 = LeakyReLU(alpha=0.3)(h_conv1d_2)

    h_conv1d_4 = MaxPooling1D(pool_size=3, strides=None, padding='valid')(h_conv1d_2)

    h_conv1d_6 = Conv1D(filters=32, kernel_size=3)(h_conv1d_4)
    h_conv1d_6 = LeakyReLU(alpha=0.3)(h_conv1d_6)

    h_conv1d_8 = MaxPooling1D(pool_size=2, strides=None, padding='valid')(h_conv1d_6)

    h_conv3d_1_1 = Conv3D(filters=16, kernel_size=(2, 1, 5))(input_order)
    h_conv3d_1_1 = LeakyReLU(alpha=0.3)(h_conv3d_1_1)

    h_conv3d_1_2 = Conv3D(filters=16, kernel_size=(1, 2, 5))(input_order)
    h_conv3d_1_2 = LeakyReLU(alpha=0.3)(h_conv3d_1_2)

    h_conv3d_1_3 = MaxPooling3D(pool_size=(1, 1, 3))(h_conv3d_1_1)
    h_conv3d_1_4 = MaxPooling3D(pool_size=(1, 1, 3))(h_conv3d_1_2)

    h_conv3d_1_5 = Conv3D(filters=32, kernel_size=(1, 2, 5))(h_conv3d_1_3)
    h_conv3d_1_5 = LeakyReLU(alpha=0.3)(h_conv3d_1_5)

    h_conv3d_1_6 = Conv3D(filters=32, kernel_size=(2, 1, 5))(h_conv3d_1_4)
    h_conv3d_1_6 = LeakyReLU(alpha=0.3)(h_conv3d_1_6)

    h_conv3d_1_7 = MaxPooling3D(pool_size=(1, 1, 5))(h_conv3d_1_5)
    h_conv3d_1_8 = MaxPooling3D(pool_size=(1, 1, 5))(h_conv3d_1_6)
    o_conv3d_1 = Concatenate(axis=-1)([h_conv3d_1_7, h_conv3d_1_8])

    o_conv3d_1_1 = Flatten()(o_conv3d_1)

    i_concatenated_all_h_1 = Flatten()(h_conv1d_8)

    i_concatenated_all_h = Concatenate()([i_concatenated_all_h_1, o_conv3d_1_1, input_elapedtime, input_lefttime])

    hidden_out = Dense(100)(i_concatenated_all_h)
    hidden_out = LeakyReLU(alpha=0.3)(hidden_out)

    output = Dense(1, activation='linear')(hidden_out)

    model = Model([input_order, input_tranx, input_elapedtime, input_lefttime], output)

    return model

def get_sample_data(count):

    start = 0
    ld_x1 = []
    ld_x2 = []
    ld_y = []
    d1 = []

    # x1_dimension_info = (10, 2, 120, 2)  # 60 --> 120 (@ilzoo)
    # x2_dimension_info = (120, 11)
    # y1_dimension_info = (120,)

    for i in range(count):
        d1_2 = np.arange(start, start + 2 * 10 * 120 * 2).reshape([10, 2, 120, 2])
        start += 2 * 10 * 120
        d2 = np.arange(start, start+11*120).reshape([120, 11])
        start += 11 * 120
        ld_x1.append(d1_2)

        # ld_x1.append([d1_1, d1_2])
        ld_x2.append(d2)

    for j in range(count):
        d1 = np.arange(start, start + 1)
        ld_y.append(d1)

    return np.asarray(ld_x1), np.asarray(ld_x2), np.asarray(ld_y)




def get_real_data_sparsed(ticker='001470', date='20180420', train_data_rows=None, save_dir=''):
    """
    Get sparsed data for supervised learning
    :param ticker: ticker number to read
    :param date: date yyyymmdd to read
    :param train_data_rows: data rows to read for training, default None : read all rows
    :param save_dir: default ''
    :return: training data x1, x2, y1 for supervised learning model
    """
    current_ticker = ticker
    current_date = date

    x1_dimension_info = (10, 2, 60, 2)  # 60 --> 120 (@iljoo)
    x2_dimension_info = (60, 11)
    x3_dimension_info = (max_len,)
    x4_dimension_info = (max_len,)
    # y1_dimension_info = (120,)

    pickle_name = save_dir + os.path.sep + current_ticker + '_' + current_date + '.pickle'
    f = open(pickle_name, 'rb')
    d = pickle.load(f)  # d[data_type][second] : mapobject!!
    f.close()

    total_rows = len(d[0])

    if train_data_rows is None:
        train_data_rows = len(d[0])

    x1 = np.zeros([10, 2, 60, 2])
    x2 = np.zeros([60, 11])
    x3 = np.zeros([max_len,])
    x4 = np.zeros([max_len,])
    y1 = np.zeros([120])

    d_x1 = []
    d_x2 = []
    d_x3 = []
    d_x4 = []
    d_y1 = []

    for idx in range(train_data_rows):
        for row in range(x1_dimension_info[0]):  # 10 : row
            for column in range(x1_dimension_info[1]):  # 2 : column
                for second in range(x1_dimension_info[2]):  # 60: seconds
                    for channel in range(x1_dimension_info[3]):  # 2 : channel
                        x1[row][column][second][channel] = d[0][idx][second][channel*20+column*10]
        d_x1.append(x1)

        for second in range(x2_dimension_info[0]):  # 120 : seconds
            for feature in range(x2_dimension_info[1]):  # 11 : features
                x2[second, feature] = d[1][idx][second][feature]
        d_x2.append(x2)

        binary_second = seconds_to_binary_array(d[2][idx], max_len)
        for feature in range(x3_dimension_info[0]):  # max_len :features
            x3[feature] = binary_second[feature]
        d_x3.append(x3)

        binary_second = seconds_to_binary_array(d[3][idx], max_len)
        for feature in range(x4_dimension_info[0]):  # max_len :features
            x4[feature] = binary_second[feature]
        d_x4.append(x4)


        # for second in range(y1_dimension_info[0]): # 60 : seconds
        d_y1.append(d[4][idx])

    return np.asarray(d_x1), np.asarray(d_x2), np.asarray(d_x3), np.asarray(d_x4), np.asarray(d_y1)


def get_real_data(ticker='001470', date='20180420', train_data_rows=None, save_dir=''):
    """
    Get data for supervised learning
    :param ticker: ticker number to read
    :param date: date yyyymmdd to read
    :param train_data_rows: data rows to read for training, default None : read all rows
    :param save_dir: default ''
    :return: training data x1, x2, y1 for supervised learning model
    """
    current_ticker = ticker
    current_date = date

    x1_dimension_info = (10, 2, 120, 2)  # 60 --> 120 (@iljoo)
    x2_dimension_info = (120, 11)
    # y1_dimension_info = (120,)

    pickle_name = save_dir + os.path.sep + current_ticker + '_' + current_date + '.pickle'
    f = open(pickle_name, 'rb')
    d = pickle.load(f)  # d[data_type][second] : mapobject!!
    f.close()

    total_rows = len(d[0])

    if train_data_rows is None:
        train_data_rows = len(d[0])

    x1 = np.zeros([10, 2, 120, 2])
    x2 = np.zeros([120, 11])
    y1 = np.zeros([120])

    d_x1 = []
    d_x2 = []
    d_y1 = []

    for idx_second in range(train_data_rows):

        if idx_second + 120 > total_rows:
            break

        for row in range(x1_dimension_info[0]):  # 10 : row
            for column in range(x1_dimension_info[1]):  # 2 : column
                for second in range(x1_dimension_info[2]):  # 120 : seconds
                    for channel in range(x1_dimension_info[3]):  # 2 : channel
                        key = ''
                        if channel == 1:
                            key = 'Buy'
                        else:
                            key = 'Sell'
                        if column == 0:
                            value = 'Hoga'
                        else:
                            value = 'Order'

                        x1[row][column][second][channel] = d[0][idx_second+second][key+value+str(row+1)]
        d_x1.append(x1)

        for second in range(x2_dimension_info[0]):  # 120 : seconds
            for feature in range(x2_dimension_info[1]):  # 11 : features
                x2[second, feature] = d[1][idx_second+second][feature]
        d_x2.append(x2)

        # for second in range(y1_dimension_info[0]): # 60 : seconds
        d_y1.append(d[2][idx_second])

    return np.asarray(d_x1), np.asarray(d_x2), np.asarray(d_y1)

# def train_using_fake_data():
#     train_per_each_episode('','',True)


def train_using_real_data(d, save_dir=''):

    model = build_network()
    model.compile(optimizer='adam', loss='mse', metrics=['accuracy'])
    model.compile(optimizer='adam', loss='mse', metrics=['accuracy'])
    model.summary()

    l = load_ticker_yyyymmdd_list_from_directory(d)

    t_x1, t_x2, t_y1 = [], [], []

    for (ti, da) in l:
        print('loading data from ticker {}, yyyymmdd {} is started.'.format(ti, da))
        x1, x2, y1 = load_data(ti, da, use_fake_data=False, save_dir=save_dir)
        t_x1.append(x1)
        t_x2.append(x2)
        t_y1.append(y1)
        print('loading data from ticker {}, yyyymmdd {} is finished.'.format(ti, da))

    print('total x1 : {}, total x2 : {}, total y1 : {}'.format(len(t_x1), len(t_x2), len(t_y1)))

    # {steps} --> this file will be saved whenever it runs every steps as much as {step}
    checkpoint_weights_filename = 'bsa_' + 'fill_params_information_in_here' + '_weights_{step}.h5f'

    # TODO: here we can add hyperparameters information like below!!
    log_filename = 'bsa_{}_log.json'.format('fill_params_information_in_here')
    checkpoint_interval = 50

    callbacks = [ModelIntervalCheckpoint(checkpoint_weights_filename, interval=checkpoint_interval)]
    callbacks += [FileLogger(log_filename, interval=100)]

    print('start to train.')
    model.fit({'x1': t_x1, 'x2': t_x2}, t_y1, epochs=30, verbose=2, batch_size=64, callbacks=callbacks)
    model.save_weights('final_weight.h5f')

def train_using_real_data_sparsed(d, save_dir=''):

    model = build_network_for_sparsed()
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    # model.compile(optimizer='adam', loss='mse', metrics=['accuracy'])
    # model.summary()

    l = load_ticker_yyyymmdd_list_from_directory(d)

    t_x1, t_x2, t_x3, t_x4, t_y1 = [],[],[],[],[]

    for (ti, da) in l:
        print('loading data from ticker {}, yyyymmdd {} is started.'.format(ti, da))
        x1, x2, x3, x4, y1 = load_data_sparsed(ti, da, use_fake_data=False, save_dir=save_dir)
        t_x1.append(x1)
        t_x2.append(x2)
        t_x3.append(x3)
        t_x4.append(x4)
        t_y1.append(y1)
        print('loading data from ticker {}, yyyymmdd {} is finished.'.format(ti, da))
    t_x1 = np.concatenate(t_x1)
    t_x2 = np.concatenate(t_x2)
    t_x3 = np.concatenate(t_x3)
    t_x4 = np.concatenate(t_x4)

    t_y1 = np.concatenate(t_y1)

    print('total x1 : {}, total x2 : {}, total x3 : {}, total x4 : {}, total y1 : {}'.format(len(t_x1), len(t_x2), len(t_x3), len(t_x4), len(t_y1)))
    # np.append(t_x1,values=(36,8,10,2,60))

    # {steps} --> this file will be saved whenever it runs every steps as much as {step}
    checkpoint_weights_filename = 'ssa_' + 'fill_params_information_in_here' + '_weights_{step}.h5f'

    # TODO: here we can add hyperparameters information like below!!
    log_filename = 'ssa_{}_log.json'.format('fill_params_information_in_here')
    checkpoint_interval = 50

    callbacks = [ModelIntervalCheckpoint(checkpoint_weights_filename, interval=checkpoint_interval)]
    callbacks += [FileLogger(log_filename, interval=100)]

    print('start to train.')
    model.fit({'x1': t_x1, 'x2': t_x2, 'x3': t_x3, 'x4': t_x4}, t_y1, epochs=70, verbose=2, batch_size=10, callbacks=callbacks)
    model.save_weights('final_weight.h5f')
    model.save('final_model.h5')




def load_data(t, d, use_fake_data=False, save_dir =''):
    if use_fake_data:
        x1, x2, y = get_sample_data(10)
    else:
        current_date = d
        current_ticker = t
        #if you give second as None, it will read every seconds in file.
        # x1, x2, y = get_real_data(current_ticker, current_date, train_data_rows=130)
        x1, x2, y = get_real_data(current_ticker, current_date, save_dir=save_dir)
    return x1, x2, y



def load_data_sparsed(t, d, use_fake_data=False, save_dir =''):
    if use_fake_data:
        x1, x2, x3, x4, y = get_sample_data(10)
    else:
        current_date = d
        current_ticker = t
        #if you give second as None, it will read every seconds in file.
        # x1, x2, y = get_real_data(current_ticker, current_date, train_data_rows=130)
        x1, x2, x3, x4, y = get_real_data_sparsed(current_ticker, current_date, save_dir=save_dir)
    return x1, x2, x3, x4, y

dat = np.arange(1, 13) / 2.0
def discretize(data, bins):
    split = np.array_split(np.sort(data), bins)
    cutoffs = [x[-1] for x in split]
    cutoffs = cutoffs[:-1]
    discrete = np.digitize(data, cutoffs, right=True)
    return discrete, cutoffs
def get_maxlen_of_binary_array(max_seconds):
    return len(np.binary_repr(max_seconds))
def seconds_to_binary_array(seconds, max_len):
    return np.binary_repr(seconds).zfill(max_len)

d  = os.path.abspath(os.path.dirname(__file__)) + "/sparse/train"
max_len = get_maxlen_of_binary_array(120)
train_using_real_data_sparsed(d, 'sparse/train')


