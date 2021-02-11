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


# define funcitons

def message_to_df(json_message):
    event_time = json_message["E"]
    candle = json_message["k"]
    candle_dict = {event_time: candle}
    df_candle = pd.DataFrame.from_dict(candle_dict, orient='index')
    df_candle.columns = col_names
    return df_candle


def order(side, quantity, symbol, order_type):
    try:
        print("sending order")
        order = client.create_order(
            symbol=symbol,
            side=side,
            type=order_type,
            quantity=quantity,
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
    # prepare data from message stream
    global closes
    json_message = json.loads(message)
    candle_closed = json_message["k"]["x"]
    # iterate through closed prices
    if candle_closed:
        tick += 1
        print(f"Clock: TICK! Run number {tick}.")
        # prepare data for trading
        df_candle = message_to_df(json_message)
        df = df.append(df_candle)
        df = df.tail(500)
        # if enough data collected
        if df.shape[0] > 14:
            # prepare technical analysis
            macd = ta.MACD(df)["MACD"]
            signal = ta.MACD(df)["Signal"]
            stoch = ta.stochOscltr(df)
            adx = ta.adx(df, 20)
            rsi = ta.rsi(df, RSI_PERIOD)
            print(f"current rsi: {rsi[-1]}")
            # sell strategy
            if (
                macd[-1] < signal[-1]
                and rsi[-1] > 50
                and rsi[-1] < rsi[-2]
                and adx[-1] > 20
                and adx[-1] < adx[-2]
                and stoch[-1] < stoch[-2]
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
            # buy strategy
            if (
                macd[-1] > signal[-1]
                and rsi[-1] < 60
                and rsi[-1] > rsi[-2]
                and adx[-1] > 20
                and adx[-1] > adx[-2]
                and stoch[-1] > stoch[-2]
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


# set some variables

SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
client = Client(config.API_KEY, config.API_SECRET, tld='com')

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
    "Close",
    "Low",
    "Volume",
    "Number",
    "Candel_closed",
    "Quote_volume",
    "Taker_buy_base_volume",
    "Taker_buy_quote_volume",
    ]
df = pd.DataFrame(columns=col_names)

in_position = False
tick = 0

ws = websocket.WebSocketApp(
    SOCKET,
    on_open=on_open,
    on_close=on_close,
    on_message=on_message
    )
ws.run_forever()
