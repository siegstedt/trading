"""
run a lstm prediction model on market price data
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM
from tensorflow.keras.layers import Dropout
from math import sqrt

def load_data(platform, ticker, start_time, end_time, interval):
    """
    load data from ressources

    Args:
        - platform
        - ticker
        - start_time
        - end_time
        - interval
    Returns:
        - pd.Dataframe object with datetime as index
    """
    # set up file path
    filedir = os.path.join('/home/siegstedt/projects/trading',platform, 'data')
    filename = ticker + '_' + start_time + '_' + end_time + '_' + interval + '.csv'
    filepath = os.path.join(filedir, filename)
    # read in the data
    data = pd.read_csv(filepath, index_col=0, header=0).drop(columns=["datetime"])
    data.index.name = "datetime"
    # reorder columns for having closed price accessible at the end of the data frame
    data = data[['close','open','high','low','volume']]

    return data


def scale_data(data_in, cat_cols=[]):
    """
    transform data set into float data objects

    Args:
        - df: pd.DataFrame object with datetime as index
        - cat_cols: categorical columns as list of column names
    Returns:
        - scaled dataset
    """    

    # get values
    values = data_in.values

    # categorical columns transformation
    if cat_cols != []:
        cols = data_in.columns.to_list()
        cat_cols_i = []
        for i, col in enumerate(cols):
            # retrieve cat_cols
            for j in cat_cols:
                if col == j:
                    cat_cols_i.append(i)

        # integer encode direction
        encoder = LabelEncoder()

        for i in cat_cols_i:
            values[:,i] = encoder.fit_transform(values[:,i])

    # ensure that all values are floats
    values = values.astype('float64')
    # normalize features
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(values)
    
    return scaled


def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
    """
    convert series to supervised learning

    Args:
        - data:
        - n_in:
        - n_out:
        - dropnan:
    Return:
        - 
    """
    n_vars = 1 if type(data) is list else data.shape[1]
    df = pd.DataFrame(data)
    cols, names = list(), list()
    # input sequence (t-n, ... t-1)
    for i in range(n_in, 0, -1):
        cols.append(df.shift(i))
        names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
    # forecast sequence (t, t+1, ... t+n)
    for i in range(0, n_out):
        cols.append(df.shift(-i))
        if i == 0:
            names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
        else:
            names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
    # put it all together
    agg = pd.concat(cols, axis=1)
    agg.columns = names
    # drop rows with NaN values
    if dropnan:
        agg.dropna(inplace=True)
    return agg


def design_model(train_X):
    # design network
    model = Sequential()
    # first layer
    model.add(LSTM(units = 50, return_sequences = True, input_shape=(train_X.shape[1], train_X.shape[2])))
    model.add(Dropout(0.2))

    # second layer
    model.add(LSTM(units = 50, return_sequences = True))
    model.add(Dropout(0.2))

    # third layer
    model.add(LSTM(units = 50, return_sequences = True))
    model.add(Dropout(0.2))

    # last layer
    model.add(LSTM(units = 50))
    model.add(Dropout(0.2))

    # dense down the net
    model.add(Dense(1))

    # compile loss
    model.compile(loss='mean_squared_error', optimizer='adam')

    return model


def main():
    # read the training data    
    data_input = load_data('binance', 'etheur', '2020-01', '2021-02', '1h')
    #print(data_input.head())

    # scale input data
    # ensure that all values are floats
    values = data_input.values
    values = values.astype('float64')
    # normalize features
    scaler = MinMaxScaler(feature_range=(0, 1))
    data_scaled = scaler.fit_transform(values)

    # transform data frame as supervised learning
    n_hours = 1
    n_features = 5
    data_reframed = series_to_supervised(data_scaled, n_hours, 1)
    print(f"Reframed data shape: {data_reframed.shape}")

    # prepare training data
    ## split into train and test sets
    values = data_reframed.values
    n_train_hours = data_reframed.shape[0] - 3 * 24
    train = values[:n_train_hours, :]
    test = values[n_train_hours:, :]

    ## split into input and outputs
    n_obs = max(1,n_hours) * n_features
    train_X, train_y = train[:, :n_obs], train[:, -n_features]
    test_X, test_y = test[:, :n_obs], test[:, -n_features]
    print(train_X.shape, len(train_X), train_y.shape)

    ## reshape input to be 3D [samples, timesteps, features]
    timesteps = max(1,n_hours)
    train_X = train_X.reshape((train_X.shape[0], timesteps, n_features))
    test_X = test_X.reshape((test_X.shape[0], timesteps, n_features))
    print(train_X.shape, train_y.shape, test_X.shape, test_y.shape)

    # design network
    model = design_model(train_X)

    # fit model
    model.fit(
        train_X, 
        train_y, 
        epochs=50,
        batch_size=72,
        verbose=2,
        shuffle=False
    )

    # store model

    #
    #
    # einschub
    #
    #

    # make a prediction
    yhat = model.predict(test_X)
    test_X = test_X.reshape((test_X.shape[0], max(1,n_hours)*n_features))

    # invert scaling for forecast
    n_inverted = n_features - 1
    inv_yhat = np.concatenate((yhat, test_X[:, -n_inverted:]), axis=1)
    inv_yhat = scaler.inverse_transform(inv_yhat)
    inv_yhat = inv_yhat[:,0]
    # invert scaling for actual
    test_y = test_y.reshape((len(test_y), 1))
    inv_y = np.concatenate((test_y, test_X[:, -n_inverted:]), axis=1)
    inv_y = scaler.inverse_transform(inv_y)
    inv_y = inv_y[:,0]

    # calculate RMSE
    rmse = sqrt(mean_squared_error(inv_y, inv_yhat))
    print('Test RMSE: %.3f' % rmse)


    # inspect the time series
    past = {
        "real": data_input.close.iloc[:n_train_hours].tail(50).to_list(),
        "pred": [np.nan for i in range(50)]
    }
    predicted = {
        "real": inv_y,
        "pred": inv_yhat,
    }

    check = pd.concat(
        [
            pd.DataFrame(past),
            pd.DataFrame(predicted)
        ]
    ).reset_index(drop=True)

    check["rel_diff_%"] = (check.pred - check.real) / check.real * 100
    print(check.iloc[49:60,:])

    #
    #
    # einschub ende
    #
    #

    # read data for prediction

    # transform data

    # load model

    # run prediction

if __name__ == '__main__':
    main()