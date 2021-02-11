import pandas as pd


# function

def message_to_df(json_message):
    event_time = json_message["E"]
    candle = json_message["k"]
    candle_dict = {event_time: candle}  
    df_candle = pd.DataFrame.from_dict(candle_dict, orient='index')
    df_candle.columns = col_names
    return df_candle

# global

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

# program

for i in range(5):
    json_message = {"E":123456789, "k": {"t": 123400000,"T": 123460000,"s": "BNBBTC", "i": "1m", "f": 100, "L": 200, "o": "0.0010", "c": "0.0020", "h": "0.0025", "l": "0.0015", "v": "1000", "n": 100, "x": False, "q": "1.0000", "V": "500", "Q": "0.500", "B": "123456"}}
    df_candle = message_to_df(json_message)
    df = df.append(df_candle)
    print(df.shape)