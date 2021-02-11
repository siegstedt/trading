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
    candle = json_message["k"]
    candle_closed = candle["x"]
    close = candle["c"]
    # iterate through closed prices
    if candle_closed:
        closes.append(float(close))
        # if enough data collected
        if len(closes) > RSI_PERIOD:
            df_close = pd.DataFrame(closes, columns=['Close'])
            print(df_close)
            rsi = ta.rsi(df_close, RSI_PERIOD)
            print(rsi)
            last_rsi = rsi[-1]
            print(f"current rsi: {last_rsi}")
            # trade strategy
            if last_rsi > RSI_OVERBOUGHT:
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
            if last_rsi < RSI_OVERSOLD:
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
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
SYMBOL = "ETH"
QUANTITY = 0.035

closes = []
in_position = False

ws = websocket.WebSocketApp(
    SOCKET,
    on_open=on_open,
    on_close=on_close,
    on_message=on_message
    )
ws.run_forever()
