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

SOCKET = "wss://stream.binance.com:9443/ws/etheur@kline_1m"
client = Client(config.API_KEY, config.API_SECRET, tld="com")
SYMBOL = "ETHEUR"
QUANTITY = 0.066
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
in_position = False
bot_price = 0
bot_qty = 0
bot_commission = 0

tick = 0
candle_dict = {}

# define funcitons


def order(side, quantity, symbol, order_type):
    try:
        print(f"> Sending {side} order. Symbol: {symbol}. Quantity: {quantity}.")
        order = client.create_order(
            symbol=symbol, side=side, type=order_type, quantity=quantity,
        )
    except Exception as e:
        print(e)
        return False, ""

    return True, order


def on_open(ws):
    print("Binance socket connection open.")


def on_close(ws):
    print("Socket connection closed.")


def on_message(ws, message):
    # call some of the global variables
    global in_position
    global bot_price
    global bot_qty
    global bot_commission
    global tick
    global candle_dict
    # prepare data from message stream
    json_message = json.loads(message)
    event_time = json_message["E"]
    candle = json_message["k"]
    candle_closed = json_message["k"]["x"]
    # iterate through closed prices
    if candle_closed:
        tick += 1
        print(f"TICK! Run number: {tick}.")
        if in_position:
            print(f"> We hold {QUANTITY} coins of {SYMBOL}.")
        else:
            print(f"> We don't own any {SYMBOL} yet. Let's see if we can buy.")
        print(f"> {candle['s']} closed at {candle['c']}. High {candle['h']}. Low {candle['l']}.")
        if bot_price > 0:
            print(f"> {candle['s']} was initially bought at {bot_price}.")
        # prepare dataframe for trading
        candle_dict[event_time] = candle
        df_candle = pd.DataFrame.from_dict(candle_dict, orient="index")
        df_candle.columns = col_names
        df_candle = df_candle.astype({"Open": "float64", "Close": "float64", "High": "float64", "Low": "float64"})
        df_candle = df_candle.tail(100)
        print(f"> Prepared dataframe with {df_candle.shape[0]} rows and {df_candle.shape[1]} cols for analysis.")
        # prepare technical analysis
        df_candle["macd"] = ta.MACD(df_candle, 9, 26, 6)["MACD"]
        df_candle["signal"] = ta.MACD(df_candle, 9, 26, 6)["Signal"]
        df_candle["stoch"] = ta.stochOscltr(df_candle, 9)
        df_candle["adx"] = ta.adx(df_candle, 20)
        print("> Technical analysis done. Values:")
        print(f"> MACD: {df_candle['macd'].iloc[-1]}. Signal: {df_candle['signal'].iloc[-1]}. Stoch: {df_candle['stoch'].iloc[-1]}. ADX: {df_candle['adx'].iloc[-1]}.")
        # sell strategy
        technically_bad = (df_candle["macd"].iloc[-1] < df_candle["signal"].iloc[-1]
        #and df_candle["adx"].iloc[-1] > 20
        #and df_candle["adx"].iloc[-1] < df_candle["adx"].iloc[-2]
        and df_candle["stoch"].iloc[-1] > 50
        and df_candle["stoch"].iloc[-1] < df_candle["stoch"].iloc[-2]
        )
        on_the_money = (df_candle['Low'].iloc[-1] > bot_price*1.01)
        if technically_bad or on_the_money:
            if in_position:
                print("> Sell!")
                # put binance sell order logic here
                order_succeeded, ordered = order(
                    side=SIDE_SELL,
                    quantity=QUANTITY,
                    symbol=SYMBOL,
                    order_type=ORDER_TYPE_MARKET,
                )
                if order_succeeded:
                    print("> Order was placed successfully")
                    in_position = False
            else:
                print("> Good time to sell. But we don't own any.")
        else:
            print("> No sell signal.")
        # buy strategy
        if (
            df_candle["macd"].iloc[-1] > df_candle["signal"].iloc[-1]
            and df_candle["adx"].iloc[-1] > 15
            and df_candle["adx"].iloc[-1] > df_candle["adx"].iloc[-2]
            and df_candle["stoch"].iloc[-1] < 90
            and df_candle["stoch"].iloc[-1] > df_candle["stoch"].iloc[-2]
        ):
            if in_position:
                print("> It is oversold. but you already own.")
            else:
                print("> Buy!")
                # put binance buy order logic here
                order_succeeded, ordered = order(
                    side=SIDE_BUY,
                    quantity=QUANTITY,
                    symbol=SYMBOL,
                    order_type=ORDER_TYPE_MARKET,
                )
                if order_succeeded:
                    print("> Order was placed successfully")
                    # turn the switch for position
                    in_position = True
                    # save order data
                    bot_price = float(ordered['fills'][0]['price'])
                    bot_qty = float(ordered['fills'][0]['qty'])
                    bot_commission = float(ordered['fills'][0]['commission'])
                    bot_total = bot_price * bot_qty + bot_commission
        else:
            print("> No buy signal.")
        print("> Cycle end.")


ws = websocket.WebSocketApp(
    SOCKET, on_open=on_open, on_close=on_close, on_message=on_message
)
ws.run_forever()
