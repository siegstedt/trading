import pandas as pd
import libs.TA as ta

df = pd.read_csv('binance/test_data.csv')

df["macd"] = ta.MACD(df)["MACD"]
df["signal"] = ta.MACD(df)["Signal"]
df["stoch"] = ta.stochOscltr(df)
df["adx"] = ta.adx(df, 20)
df["rsi"] = ta.rsi(df, 14)

print(df.head(50))
print(df['macd'].iloc[-1])
print(df['signal'].iloc[-1])
print(df['stoch'].iloc[-1])
print(df['rsi'].iloc[-1])
print(df['adx'].iloc[-1])
