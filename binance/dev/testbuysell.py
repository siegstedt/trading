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

SYMBOL = "ETHEUR"
QUANTITY = 0.01
in_position = False

# define funcitons


def order(side, quantity, symbol, order_type):
    try:
        print(f" Sending {side} order. Symbol: {symbol}. Quantity: {quantity}.")
        order = client.create_order(
            symbol=symbol, side=side, type=order_type, quantity=quantity,
        )
    except Exception as e:
        print(e)
        return False, ""

    return True, order


def on_open(ws):
    print("Socket connection open.")


def on_close(ws):
    print("Socket connection closed.")


def on_message(ws, message):
    global in_position
    # prepare data from message stream
    json_message = json.loads(message)
    candle = json_message["k"]
    candle_closed = json_message["k"]["x"]
    # iterate through closed prices
    if candle_closed:
        print("TICK!")
        print(f" {candle['s']} closed at {candle['c']}. High {candle['h']}. Low {candle['l']}.")
        if in_position:
            print(" Sell!")
            # put binance sell order logic here
            order_succeeded, ordered = order(
                side=SIDE_SELL,
                quantity=QUANTITY,
                symbol=SYMBOL,
                order_type=ORDER_TYPE_MARKET,
            )
            if order_succeeded:
                print(" order was placed successfully")
                print(ordered)
                in_position = False
        else:
            print(" Buy!")
            # put binance buy order logic here
            order_succeeded, ordered = order(
                side=SIDE_BUY,
                quantity=QUANTITY,
                symbol=SYMBOL,
                order_type=ORDER_TYPE_MARKET,
            )
            if order_succeeded:
                print(" order was placed successfully")
                print(ordered)
                in_position = True


ws = websocket.WebSocketApp(
    SOCKET, on_open=on_open, on_close=on_close, on_message=on_message
)
ws.run_forever()
