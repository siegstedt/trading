"""
binance trade bot
"""
# binance modules
from binance.client import Client
from binance.enums import *

# open source modules
import websocket
import json
import pandas as pd

# custom libraries
import config
import libs.TA as ta

# set some variables

SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
client = Client(config.API_KEY, config.API_SECRET, tld="com")
RSI_PERIOD = 14
SYMBOL = "ETHUSD"
QUANTITY = 0.02
col_names = [
    "Start_time",
    "Close_time",
    "Symbol",
    "Interval",
    "First_trade",
    "Last_trade",
    "Open",
    "Close",
    "High",
    "Low",
    "Volume",
    "Number",
    "Candel_closed",
    "Quote_volume",
    "Taker_buy_base_volume",
    "Taker_buy_quote_volume",
    "Ignore",
]
df = pd.DataFrame(columns=col_names)
in_position = False
tick = 0


# define funcitons


def message_to_df(json_message):
    event_time = json_message["E"]
    candle = json_message["k"]
    candle_dict = {event_time: candle}
    df_candle = pd.DataFrame.from_dict(candle_dict, orient="index")
    df_candle.columns = col_names
    return df_candle


def order(side, quantity, symbol, order_type):
    try:
        print("sending order")
        order = client.create_order(
            symbol=symbol, side=side, type=order_type, quantity=quantity,
        )
        print(order)
    except Exception as e:
        return False

    return True


def on_open(ws):
    print("Socket connection open.")


def on_close(ws):
    print("Socket connection closed.")


def on_message(ws, message):
    # call some of the global variables
    global df
    global in_position
    global tick
    # prepare data from message stream
    json_message = json.loads(message)
    candle_closed = json_message["k"]["x"]
    # iterate through closed prices
    if candle_closed:
        tick += 1
        print(f"TICK! Run number: {tick}.")
        # prepare data for trading
        df_candle = message_to_df(json_message)
        df = df.append(df_candle)
        df = df.tail(500)
        print(f"Loaded {df.shape[0]} rows and {df.shape[1]} cols.")
        print(df.columns)
        # if enough data collected
        if df.shape[0] > 1:
            print("1 - i am reaching this line")
            df.to_csv('binance/test_data_1.csv')
            # prepare technical analysis
            df["macd"] = ta.MACD(df)["MACD"]
            #
            print("2 - i am reaching this line")
            print(df['macd'].iloc[-1])
            #
            df["signal"] = ta.MACD(df)["Signal"]
            #
            print("3 - i am reaching this line")
            print(df['signal'].iloc[-1])
            #
            df["stoch"] = ta.stochOscltr(df)
            #
            print("4 - i am reaching this line")
            print(f"stoch :{df['stoch'].iloc[-1]}")
            #
            #df["adx"] = ta.adx(df, 20)
            #
            #print("5 - i am reaching this line")
            #print(df['adx'].iloc[-1])
            #
            df["rsi"] = ta.rsi(df, 14)
            #
            print("6 - i am reaching this line")
            print(df['rsi'].iloc[-1])
            #
            df.to_csv('binance/test_data_2.csv')
            # sell strategy
            if (
                df["macd"].iloc[-1] < df["signal"].iloc[-1]
                and df["rsi"].iloc[-1] > 50
                and df["rsi"].iloc[-1] < df["rsi"].iloc[-2]
                and df["adx"].iloc[-1] > 20
                and df["adx"].iloc[-1] < df["adx"].iloc[-2]
                and df["stoch"].iloc[-1] < df["stoch"].iloc[-2]
            ):
                if in_position:
                    print("sell!")
                    # put binance sell order logic here
                    order_succeeded = order(
                        side=SIDE_SELL,
                        quantity=QUANTITY,
                        symbol=SYMBOL,
                        order_type=ORDER_TYPE_MARKET,
                    )
                    if order_succeeded:
                        in_position = False
                else:
                    print("overbougth but we don't own any")
            else:
                print("no sell signal")
            # buy strategy
            if (
                df["macd"].iloc[-1] > df["signal"].iloc[-1]
                and df["rsi"].iloc[-1] < 60
                and df["rsi"].iloc[-1] > df["rsi"].iloc[-2]
                and df["adx"].iloc[-1] > 20
                and df["adx"].iloc[-1] > df["adx"].iloc[-2]
                and df["stoch"].iloc[-1] > df["stoch"].iloc[-2]
            ):
                if in_position:
                    print("it is oversold. but you already own")
                else:
                    print("buy!")
                    # put binance buy order logic here
                    order_succeeded = order(
                        side=SIDE_BUY,
                        quantity=QUANTITY,
                        symbol=SYMBOL,
                        order_type=ORDER_TYPE_MARKET,
                    )
                    if order_succeeded:
                        in_position = True
            else:
                print("no buy signal")


ws = websocket.WebSocketApp(
    SOCKET, on_open=on_open, on_close=on_close, on_message=on_message
)
ws.run_forever()
