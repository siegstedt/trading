"""
Module to provide various tools for technical analysis and trading strategies
"""
import numpy as np


def MACD(DF, a=12, b=26, c=9):
    """function to calculate MACD
       typical values a(fast moving average) = 12;
                      b(slow moving average) =26;
                      c(signal line ma window) =9"""
    df = DF.copy()
    df["MA_Fast"] = df["Close"].ewm(span=a, min_periods=a).mean()
    df["MA_Slow"] = df["Close"].ewm(span=b, min_periods=b).mean()
    df["MACD"] = df["MA_Fast"] - df["MA_Slow"]
    df["Signal"] = df["MACD"].ewm(span=c, min_periods=c).mean()
    df.dropna(inplace=True)
    return df


def bollBnd(DF, n=20):
    "function to calculate Bollinger Band"
    df = DF.copy()
    # df["MA"] = df['close'].rolling(n).mean()
    df["MA"] = df["Close"].ewm(span=n, min_periods=n).mean()
    df["BB_up"] = df["MA"] + 2 * df["Close"].rolling(n).std(
        ddof=0
    )  # ddof=0 is required as we take std dev of population and not sample
    df["BB_dn"] = df["MA"] - 2 * df["Close"].rolling(n).std(
        ddof=0
    )  # ddof=0 is required as we take std dev of population and not sample
    df["BB_width"] = df["BB_up"] - df["BB_dn"]
    df.dropna(inplace=True)
    return df


def atr(DF, n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df["H-L"] = abs(df["High"] - df["Low"])
    df["H-PC"] = abs(df["High"] - df["Close"].shift(1))
    df["L-PC"] = abs(df["Low"] - df["Close"].shift(1))
    df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1, skipna=False)
    # df['ATR'] = df['TR'].rolling(n).mean()
    df["ATR"] = df["TR"].ewm(com=n, min_periods=n).mean()
    return df["ATR"]


def rsi(DF, n=20):
    "function to calculate RSI"
    df = DF.copy()
    df["delta"] = df["Close"] - df["Close"].shift(1)
    df["gain"] = np.where(df["delta"] >= 0, df["delta"], 0)
    df["loss"] = np.where(df["delta"] < 0, abs(df["delta"]), 0)
    avg_gain = []
    avg_loss = []
    gain = df["gain"].tolist()
    loss = df["loss"].tolist()
    for i in range(len(df)):
        if i < n:
            avg_gain.append(np.NaN)
            avg_loss.append(np.NaN)
        elif i == n:
            avg_gain.append(df["gain"].rolling(n).mean()[n])
            avg_loss.append(df["loss"].rolling(n).mean()[n])
        elif i > n:
            avg_gain.append(((n - 1) * avg_gain[i - 1] + gain[i]) / n)
            avg_loss.append(((n - 1) * avg_loss[i - 1] + loss[i]) / n)
    df["avg_gain"] = np.array(avg_gain)
    df["avg_loss"] = np.array(avg_loss)
    df["RS"] = df["avg_gain"] / df["avg_loss"]
    df["RSI"] = 100 - (100 / (1 + df["RS"]))
    return df["RSI"]


def adx(DF, n=20):
    "function to calculate ADX"
    df2 = DF.copy()
    df2["H-L"] = abs(df2["High"] - df2["Low"])
    df2["H-PC"] = abs(df2["High"] - df2["Close"].shift(1))
    df2["L-PC"] = abs(df2["Low"] - df2["Close"].shift(1))
    df2["TR"] = df2[["H-L", "H-PC", "L-PC"]].max(axis=1, skipna=False)
    df2["+DM"] = np.where(
        (df2["High"] - df2["High"].shift(1)) > (df2["Low"].shift(1) - df2["Low"]),
        df2["High"] - df2["High"].shift(1),
        0,
    )
    df2["+DM"] = np.where(df2["+DM"] < 0, 0, df2["+DM"])
    df2["-DM"] = np.where(
        (df2["Low"].shift(1) - df2["Low"]) > (df2["High"] - df2["High"].shift(1)),
        df2["Low"].shift(1) - df2["Low"],
        0,
    )
    df2["-DM"] = np.where(df2["-DM"] < 0, 0, df2["-DM"])

    df2["+DMMA"] = df2["+DM"].ewm(span=n, min_periods=n).mean()
    df2["-DMMA"] = df2["-DM"].ewm(span=n, min_periods=n).mean()
    df2["TRMA"] = df2["TR"].ewm(span=n, min_periods=n).mean()

    df2["+DI"] = 100 * (df2["+DMMA"] / df2["TRMA"])
    df2["-DI"] = 100 * (df2["-DMMA"] / df2["TRMA"])
    df2["DX"] = 100 * (abs(df2["+DI"] - df2["-DI"]) / (df2["+DI"] + df2["-DI"]))

    df2["ADX"] = df2["DX"].ewm(span=n, min_periods=n).mean()

    return df2["ADX"]


def stochOscltr(DF, a=20, b=3):
    """function to calculate Stochastics
       a = lookback period
       b = moving average window for %D"""
    df = DF.copy()
    df["C-L"] = df["Close"] - df["Low"].rolling(a).min()
    df["H-L"] = df["High"].rolling(a).max() - df["Low"].rolling(a).min()
    df["%K"] = df["C-L"] / df["H-L"] * 100
    df["%D"] = df["%K"].ewm(span=b, min_periods=b).mean()
    return df[["%K", "%D"]]
