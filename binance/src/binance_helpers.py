"""
binance helper scripts
"""

import requests                    # for "get" request to API
import json                        # parse json into a list
import pandas as pd                # working with data frames
import datetime as dt              # working with dates


def get_historical_bars(symbol, interval, start_time, end_time, limit="1000"):
    """
    Get historical bars for a ticker from Binance
    
    Args:
        symbol (str): Binance symbol
        interval (str): Interval for historical data, e.g. '1h' for hourly bars
        start_time (datetime object): Start time of history
        end_time (datetime object): End time of history
        limit (str): Limit of number of lines for data request, defaulted to 1000
    
    Returns:
        df: pandas DataFrame object
        
    Example:
        >>> get_historical_bars('ETHEUR', '1h', dt.datetime(2020, 1, 1), dt.datetime(2020, 2, 1))
        
    """

    # define the binance url from data is requested
    url = "https://api.binance.com/api/v3/klines"
    
    # setting request params
    req_params = {'symbol': symbol,
                  'interval': interval,
                  'startTime': str(int(start_time.timestamp() * 1000)),
                  'endTime' : str(int(end_time.timestamp() * 1000)),
                  'limit' : str(limit)}
 
    # load request into a dataframe
    df = pd.DataFrame(json.loads(requests.get(url, params = req_params).text))
    if (len(df.index) == 0):
        return None     
    
    # transfrom dataframe
    df = df.iloc[:, 0:6]  # extract 
    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume'] 
    df.open = df.open.astype("float")
    df.high = df.high.astype("float")
    df.low = df.low.astype("float")
    df.close = df.close.astype("float")
    df.volume = df.volume.astype("float")
    df.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in df.datetime]
 
    return df


def get_all_tickers(markets=None):
    """
    Get all tickers from Binance
    
    Args:
        - markets (list): list object with markets, e.g. ['USDT','EUR']
    Returns:
        - pandas DataFrame object
    Example:
        >>> get_all_tickers(markets=['USDT','EUR'])
    """

    # load raw data from api
    url = "https://api.binance.com/api/v3/ticker/price"
    response = json.loads(requests.get(url).text)
    if not markets is None:
        # filter response for selected markets
        response = [
            i 
            for market in markets
            for i in response if market in i['symbol']
        ]
    
    # read response into a dataframe
    df = pd.DataFrame(response)
    if (len(df.index) == 0):
        return None   
    
    return df

