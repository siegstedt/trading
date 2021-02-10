"""
main script for the trade bot app
"""

# custom modules
import libs.account as account
import libs.strategies as strategies

# ibapi modules
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order

# third party modules
import threading
import time
import pandas as pd
import numpy as np


class TradingApp(EWrapper, EClient):
    """Main class to establish connection retrieve ibapi functionality"""

    def __init__(self):
        """Initiate TradingApp by inheriting the Eclient class"""
        EClient.__init__(self, self)
        self.data = {}
        self.order_df = pd.DataFrame(
            columns=[
                "PermId",
                "ClientId",
                "OrderId",
                "Account",
                "Symbol",
                "SecType",
                "Exchange",
                "Action",
                "OrderType",
                "TotalQty",
                "CashQty",
                "LmtPrice",
                "AuxPrice",
                "Status",
            ]
        )
        self.pos_df = pd.DataFrame(
            columns=[
                "Account",
                "Symbol",
                "SecType",
                "Currency",
                "Position",
                "Avg cost",
            ]
        )
        self.acc_summary = pd.DataFrame(
            columns=["ReqId", "Account", "Tag", "Value", "Currency"]
        )
        self.pnl_summary = pd.DataFrame(
            columns=["ReqId", "DailyPnL", "UnrealizedPnL", "RealizedPnL"]
        )

    def error(self, reqId, errorCode, errorString):
        print(
            f"> app: Error with Request ID {reqId} with Error Code {errorCode}. {errorString}"
        )

    def contractDetails(self, reqId, contractDetails):
        print(f">>> app: Request ID: {reqId}, Contract: {contractDetails}")

    def historicalData(self, reqId, bar):
        if reqId not in self.data:
            self.data[reqId] = [
                {
                    "Date": bar.date,
                    "Open": bar.open,
                    "High": bar.high,
                    "Low": bar.low,
                    "Close": bar.close,
                    "Volume": bar.volume,
                }
            ]
        if reqId in self.data:
            self.data[reqId].append(
                {
                    "Date": bar.date,
                    "Open": bar.open,
                    "High": bar.high,
                    "Low": bar.low,
                    "Close": bar.close,
                    "Volume": bar.volume,
                }
            )
        # print(f" >> app: Data Request #{reqId}: Date {bar.date}, Open {bar.open}, High {bar.high}, Low {bar.low}, Close {bar.close}, Volume {bar.volume}.")

    def nextValidId(self, orderId):
        """get a new unique order id to avoid clashes across strategies and orders"""
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print(">>> app: Next valid order ID:", orderId)

    def openOrder(self, orderId, contract, order, orderState):
        """retrieve open orders into a dataframe"""
        super().openOrder(orderId, contract, order, orderState)
        dictionary = {
            "PermId": order.permId,
            "ClientId": order.clientId,
            "OrderId": orderId,
            "Account": order.account,
            "Symbol": contract.symbol,
            "SecType": contract.secType,
            "Exchange": contract.exchange,
            "Action": order.action,
            "OrderType": order.orderType,
            "TotalQty": order.totalQuantity,
            "CashQty": order.cashQty,
            "LmtPrice": order.lmtPrice,
            "AuxPrice": order.auxPrice,
            "Status": orderState.status,
        }
        self.order_df = self.order_df.append(dictionary, ignore_index=True)

    def position(self, account, contract, position, avgCost):
        """retrieve all current positions to a dataframe"""
        super().position(account, contract, position, avgCost)
        dictionary = {
            "Account": account,
            "Symbol": contract.symbol,
            "SecType": contract.secType,
            "Currency": contract.currency,
            "Position": position,
            "Avg cost": avgCost,
        }
        self.pos_df = self.pos_df.append(dictionary, ignore_index=True)

    def positionEnd(self):
        print(">>> app: Position data extracted.")

    def accountSummary(self, reqId, account, tag, value, currency):
        """retrieve an account summary to a dataframe"""
        super().accountSummary(reqId, account, tag, value, currency)
        dictionary = {
            "ReqId": reqId,
            "Account": account,
            "Tag": tag,
            "Value": value,
            "Currency": currency,
        }
        self.acc_summary = self.acc_summary.append(
            dictionary, ignore_index=True
        )

    def pnl(self, reqId, dailyPnL, unrealizedPnL, realizedPnL):
        """retrieve a profit and loss summary to a dataframe"""
        super().pnl(reqId, dailyPnL, unrealizedPnL, realizedPnL)
        dictionary = {
            "ReqId": reqId,
            "DailyPnL": dailyPnL,
            "UnrealizedPnL": unrealizedPnL,
            "RealizedPnL": realizedPnL,
        }
        self.pnl_summary = self.pnl_summary.append(
            dictionary, ignore_index=True
        )


def websocket_con():
    """Run connection to the web socket.
    Note: We export the app.run() function here so that we can call it in
          a separate thread.
    """
    # execute the app
    app.run()
    # close the app upon event trigger
    event.wait()
    if event.is_set():
        app.close()


def getContract(symbol, secType, currency, exchange):
    """retrieve contract data"""
    contract = Contract()
    contract.symbol = symbol
    contract.secType = secType
    contract.currency = currency
    contract.exchange = exchange
    return contract


def getHistData(req_num, contract, duration, candle_size):
    """extracts historical data"""
    app.reqHistoricalData(
        reqId=req_num,
        contract=contract,
        endDateTime="",
        durationStr=duration,
        barSizeSetting=candle_size,
        whatToShow="ADJUSTED_LAST",
        useRTH=1,
        formatDate=1,
        keepUpToDate=0,
        chartOptions=[],
    )


def storeData(tradeapp_obj, symbols):
    """store the requested tickers data in a pandas data frame"""
    df_data = {}
    for counter, symbol in enumerate(symbols):
        df_data[symbol] = pd.DataFrame(tradeapp_obj.data[counter])
        df_data[symbol].set_index("Date", inplace=True)
    return df_data


def runDataRetrieval():
    # retrieve historical data for a given data set of tickers
    tickers_data = {
        "INTC": {"index": 0, "currency": "USD", "exchange": "ISLAND"},
        "BARC": {"index": 1, "currency": "GBP", "exchange": "LSE"},
        "INFY": {"index": 2, "currency": "INR", "exchange": "NSE"},
    }
    # prepare time tracking feature
    start_time = time.time()
    time_out = start_time + 60 * 5  # setting a 5 minutes time out
    # iteratively execute the retrieval process
    while time.time() < time_out:
        # retrieve historical data for each ticker
        for ticker in tickers:
            contract = getContract(
                symbol=ticker,
                secType="STK",
                currency=tickers_data[ticker]["currency"],
                exchange=tickers_data[ticker]["exchange"],
            )
            getHistData(
                reqNum=tickers_data[ticker]["index"],
                contract=contract,
                duration="3 M",
                candle_size="30 mins",
            )
            # some latency to make sure that all historical data was extracted
            time.sleep(5)
        # store the historical data in a data frame
        df = storeData(app, tickers)
        # calculate how much time to pass untill the next iteration may start
        # wait for the remainder of 30 seconds and then start again
        time.sleep(30 - ((time.time() - start_time) % 30))


def limitOrder(direction, quantity, lmt_price):
    order = Order()
    order.action = direction
    order.orderType = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice = lmt_price
    print(f">>> app: Placed {direction} limit order for {quantity} stocks at {lmt_price}.")
    return order


def marketOrder(direction, quantity):
    order = Order()
    order.action = direction
    order.orderType = "MKT"
    order.totalQuantity = quantity
    print(f">>> app: Placed {direction} market order for {quantity} stocks at market price.")
    return order


def stopOrder(direction, quantity, st_price):
    order = Order()
    order.action = direction
    order.orderType = "STP"
    order.totalQuantity = quantity
    order.auxPrice = st_price
    print(f">>> app: Placed {direction} stop order for {quantity} stocks at {st_price}.")
    return order


def trailStopOrder(direction, quantity, st_price, tr_step=1):
    order = Order()
    order.action = direction
    order.orderType = "TRAIL"
    order.totalQuantity = quantity
    order.auxPrice = tr_step
    order.trailStopPrice = st_price
    print(f">>> app: Placed {direction} trail stop order for {quantity} stocks at {st_price} stop price and {tr_step} trail stop.")
    return order


###############################################################################

# create an event object for asynchronous execution
event = threading.Event()

# define app as connection to ibapi client through the wrapper
app = TradingApp()
app.connect("127.0.0.1", 7497, clientId=1)  # paper
# app.connect("127.0.0.1", 7496, clientId=1)  # live

# start the connection on a separate deamon thread
con_thread = threading.Thread(target=websocket_con)
con_thread.start()
# some latency to ensure that the connection was established as you move on
time.sleep(1)

print("Interactive Brokers Trade Bot is up and running.")

#
# 1. CHECK ACCOUNT
#


def check_account(portfolio_size):

    print("> We start checking the account")

    # get current positions
    pos_df = account.getCurrentPositions(app)
    pos_df = pos_df[pos_df.Position != 0].drop_duplicates()
    tickers_curr = np.unique(pos_df.Symbol.to_numpy())
    print(
        f"> Currently holding {len(tickers_curr)} positions: {', '.join(tickers_curr)}."
    )

    # get account summary
    acc_df = account.getAccountSummary(app)
    current_balance = acc_df[
        (acc_df.Currency == "EUR") & (acc_df.Tag == "CashBalance")
    ]["Value"].values[0]
    print(f"> Currently {current_balance} Euro to spend on our cash balance.")

    # allocate budget for trade
    if float(current_balance) < 50:
        # only allow for trades if there is sufficient budget
        print(f"! You only have {current_balance} Euro available cash.")
        print("! That's not enough to make a trade. Top up.")
        trade_budget = 0
    else:
        # distribute available cash evenly across portfolio size
        # but not more then 2000 per thread
        trade_budget = min(
            float(current_balance) / (portfolio_size - len(tickers_curr)), 2000
        )
        print(f"> Available trade budget set to {trade_budget} Euro.")

    return tickers_curr, float(trade_budget)


#
# 2. SCREEN NASDAQ
#


def stock_screener(num_basis=250, num_extract=20):
    print("Start screening for potential trade candidates.")

    # retrieve a complete list of all nasdaq tickers
    nasdaq_complete = pd.read_csv("ibkr/data/nasdaq_screener_1612425832719.csv")
    # select the 250 largest by market cap
    nasdaq_complete = nasdaq_complete.nlargest(num_basis, "Market Cap")
    # save list of nasdaq tickers
    tickers_nasdaq = nasdaq_complete.Symbol.to_numpy()
    print(
        f"> Loaded {len(tickers_nasdaq)} strongest tickers from the NASDAQ exchange."
    )

    # retrieve historical data for selected nasdaq tickers
    ticker_nasdaq_dict = {}
    for counter, ticker in enumerate(tickers_nasdaq):
        # prepare a dict with counter and ticker
        ticker_nasdaq_dict[counter] = ticker
        # get contract details
        contract = getContract(
            symbol=ticker, secType="STK", currency="USD", exchange="ISLAND",
        )
        # get historic data
        getHistData(
            req_num=counter,
            contract=contract,
            duration="3600 S",
            candle_size="1 hour",
        )
        # make the loop sleep for a bit to allow multiple API calls
        time.sleep(2.5)

    # prepare screened data
    data_screened = app.data
    df_scrnd = pd.DataFrame()
    for row in data_screened:
        df_load = pd.DataFrame.from_dict(data_screened[row])
        df_load["counter"] = row
        df_load["ticker"] = df_load["counter"].map(ticker_nasdaq_dict)
        df_load.set_index("Date", inplace=True)
        df_load = df_load.drop_duplicates()
        df_load["rel_change"] = ((df_load.Close / df_load.Open) - 1) * 100
        df_scrnd = df_scrnd.append(df_load)

    # report status
    tickers_scrnd = df_scrnd["ticker"].dropna().unique()
    print(f"> Retrieved historical data for {len(tickers_scrnd)} tickers.")

    # filter for the 50 most traded stocks
    df_scrnd = df_scrnd.nlargest(num_extract * 3, "Volume")

    # filter for the 20 biggest winners and losers
    df_scrnd = df_scrnd.sort_values("rel_change")
    df_scrnd = pd.concat(
        [
            df_scrnd.head(int(num_extract / 2)),
            df_scrnd.tail(int(num_extract / 2)),
        ]
    )
    tickers_scrnd = df_scrnd["ticker"].dropna().unique()

    # report status
    print(f"> Selected {len(tickers_scrnd)} for further technical analysis.")
    print(f"> Tickers: {', '.join(tickers_scrnd)}.")

    return tickers_scrnd


#
# 3. DEPLOY STRATEGY
#


def trading_strategy(ticker_list, trade_budget, portfolio_size):
    print("> Running the trading strategy")

    # call account and orders data
    ord_df = account.getOpenOrders(app)

    # start iterating
    for counter, ticker in enumerate(ticker_list):
        counter = counter + 1000000
        print(f">>> {ticker}: Starting passthrough for ticker {ticker}, request {counter}")

        # check account
        pos_df = account.getCurrentPositions(app)
        pos_df = pos_df[pos_df.Position != 0].drop_duplicates()
        curr_tickers = np.unique(pos_df.Symbol.to_numpy())
        # We can start a trade for portfolio_size - len(curr_tickers)
        if len(curr_tickers) >= portfolio_size:
            continue

        # pull historical data
        contract = getContract(
            symbol=ticker, secType="STK", currency="USD", exchange="ISLAND",
        )
        getHistData(
            req_num=(counter),
            contract=contract,
            duration="1 W",
            candle_size="5 mins",
        )
        time.sleep(5)

        # prepare a data frame
        data_trading = app.data
        print(
            f">>> {ticker}: Retrieved a total of {len(data_trading[counter])} lines for ticker {ticker}, request {counter}."
        )
        df = pd.DataFrame.from_dict(data_trading[counter]).drop_duplicates()
        df.set_index("Date", inplace=True)

        # calculate signals
        df["stoch"] = strategies.stochOscltr(df)
        df["macd"] = strategies.MACD(df)["MACD"]
        df["signal"] = strategies.MACD(df)["Signal"]
        df["atr"] = strategies.atr(df, 60)
        df.dropna(inplace=True)

        # calculate number of stocks for available budget
        curr_price = df["Close"][-1]
        quantity = min(int(float(trade_budget) / float(curr_price)),500)
        if quantity == 0:
            print(f">>> {ticker}: At the current stock price {curr_price} USD, you cannot buy a single {ticker} share.")
            continue
        else:
            print(f">>> {ticker}: For the budget of {trade_budget} and at the current price of {curr_price} USD, {quantity} stocks can be purchased.")

        # start iterating
        # if no positions in our account
        if len(curr_tickers) == 0:
            if (
                df["macd"][-1] > df["signal"][-1]
                and df["stoch"][-1] > 30
                and df["stoch"][-1] > df["stoch"][-2]
            ):
                app.reqIds(-1)
                time.sleep(2)
                order_id = app.nextValidOrderId
                contract = getContract(
                    symbol=ticker,
                    secType="STK",
                    currency="USD",
                    exchange="ISLAND",
                )
                # place a buy order
                app.placeOrder(order_id, contract, marketOrder("BUY", quantity))
                # place a stop loss order
                app.placeOrder(
                    order_id + 1,
                    contract,
                    stopOrder(
                        "SELL",
                        quantity,
                        round(df["Close"][-1] - df["atr"][-1], 1),
                    ),
                )
            else:
                print(f">>> {ticker}: No orders proceeded for {ticker}.")
        # if there are positions in our account and ticker is none of those
        elif len(curr_tickers) != 0 and ticker not in curr_tickers:
            if (
                df["macd"][-1] > df["signal"][-1]
                and df["stoch"][-1] > 30
                and df["stoch"][-1] > df["stoch"][-2]
            ):
                app.reqIds(-1)
                time.sleep(2)
                order_id = app.nextValidOrderId
                contract = getContract(
                    symbol=ticker,
                    secType="STK",
                    currency="USD",
                    exchange="ISLAND",
                )
                # place a buy order
                app.placeOrder(order_id, contract, marketOrder("BUY", quantity))
                # place a stop loss order
                app.placeOrder(
                    order_id + 1,
                    contract,
                    stopOrder(
                        "SELL",
                        quantity,
                        round(df["Close"][-1] - df["atr"][-1], 1),
                    ),
                )
            else:
                print(f">>> {ticker}: No orders proceeded for {ticker}.")
        # if the ticker is in our possesion
        elif len(curr_tickers) != 0 and ticker in curr_tickers:
            # if value of that position == 0, then we can think of buying
            if (
                pos_df[pos_df["Symbol"] == ticker]["Position"]
                .sort_values(ascending=True)
                .values[-1]
                == 0
            ):
                if (
                    df["macd"][-1] > df["signal"][-1]
                    and df["stoch"][-1] > 30
                    and df["stoch"][-1] > df["stoch"][-2]
                ):
                    app.reqIds(-1)
                    time.sleep(2)
                    order_id = app.nextValidOrderId
                    contract = getContract(
                        symbol=ticker,
                        secType="STK",
                        currency="USD",
                        exchange="ISLAND",
                    )
                    # place a buy order
                    app.placeOrder(
                        order_id, contract, marketOrder("BUY", quantity)
                    )
                    # place a stop loss order
                    app.placeOrder(
                        order_id + 1,
                        contract,
                        stopOrder(
                            "SELL",
                            quantity,
                            round(df["Close"][-1] - df["atr"][-1], 1),
                        ),
                    )
                else:
                    print(f">>> {ticker}: No orders proceeded for {ticker}.")
            # else if there is value in the position
            elif (
                pos_df[pos_df["Symbol"] == ticker]["Position"]
                .sort_values(ascending=True)
                .values[-1]
                > 0
            ):
                # check for older orders
                if ord_df[ord_df["Symbol"] == ticker].empty:
                    print(f">>> {ticker}: No placed orders for ticker {ticker}.")
                else:
                    ord_id = (
                        ord_df[ord_df["Symbol"] == ticker]["OrderId"]
                        .sort_values(ascending=True)
                        .values[-1]
                    )
                    old_quantity = (
                        pos_df[pos_df["Symbol"] == ticker]["Position"]
                        .sort_values(ascending=True)
                        .values[-1]
                    )
                    # cancel older buy orders
                    app.cancelOrder(ord_id)
                    app.reqIds(-1)
                    time.sleep(2)
                    order_id = app.nextValidOrderId
                    contract = getContract(
                        symbol=ticker,
                        secType="STK",
                        currency="USD",
                        exchange="ISLAND",
                    )
                    # place a stop loss order
                    app.placeOrder(
                        order_id + 1,
                        contract,
                        stopOrder(
                            "SELL",
                            old_quantity,
                            round(df["Close"][-1] - df["atr"][-1], 1),
                        ),
                    )
            else:
                print(f">>> {ticker}: No orders proceeded for {ticker}.")
        # if no orders were proceeded for the ticker
        else:
            print(f">>> {ticker}: No orders proceeded for {ticker}.")


#
# DEPLOY
#

# global variables
portfolio_size = 20

# run program for a given duration of time
starttime = time.time()
timeout = time.time() + 60 * 60 * 1

# start while loop
iteration = 0
while time.time() <= timeout:
    # start
    iteration += 1
    time_string = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
    print(f"> {time_string} - Starting a new loop. Iteration number {str(iteration)}.")

    # check account
    curr_tickers, trade_budget = check_account(portfolio_size=portfolio_size)

    # move ahead if we hold less than 5 positions
    if len(curr_tickers) < portfolio_size:
        print(f"> We can start a trade for {portfolio_size - len(curr_tickers)} position.")

    else:
        print("> We are already running on full thruttle. Wait for a sell.")
        print(f"> Reached end of iteration #{iteration}.")
        sleep_time = 60 * 5 - ((time.time() - starttime) % 60.0 * 5)   
        print(f"> Residual sleep time till next iteration: {str(int(sleep_time))} seconds.")
        time.sleep(sleep_time)
        continue

    # move ahead only if there is sufficient tarde budget
    trade_budget = 10000
    if trade_budget < 50:
        print("> Account not sufficiently funded. Inject more capital.")
        # set a maximum time per while loop: 5 minutes
        print(f"> Reached end of iteration #{iteration}.")
        sleep_time = 60 * 5 - ((time.time() - starttime) % 60.0 * 5)   
        print(f"> Residual sleep time till next iteration: {str(int(sleep_time))} seconds.")
        time.sleep(sleep_time)
        continue

    # screen for stocks
    # screened_tickers = stock_screener(num_basis=250, num_extract=20)
    screened_tickers = [
        "AAPL","MSFT","AMZN","GOOG","GOOGL","TSLA","FB","BABA","TSM",
        "V","JNJ","JPM","WMT","NVDA","MA","UNH","DIS","PG","HD","PYPL",
        "BAC","NFLX","PDD","INTC","CMCSA","ADBE","ASML","VZ","NKE","CRM",
        "ABT","KO","TM","T","NVS","XOM","TMO","MRK","PFE","CSCO","PEP",
        "AVGO","ABBV","LLY","QCOM","ORCL","CVX","BHP","DHR","NVO","ACN",
        "AMGN","TXN","CHTR","GILD","FISV","BKNG","INTU","ADP","CME",
        "TMUS","MU","TJX","INTU","F",
    ]

    # deploy trading strategy on selected stocks
    # trading_strategy(ticker_list=screened_tickers, trade_budget=1000)
    trading_strategy(ticker_list=screened_tickers, trade_budget=trade_budget, portfolio_size=portfolio_size)

    # set a maximum time per while loop: 5 minutes
    print(f"> Reached end of iteration #{iteration}.")
    sleep_time = 60 * 5 - ((time.time() - starttime) % 60.0 * 5)   
    print(f"> Residual sleep time till next iteration: {str(int(sleep_time))} seconds.")
    time.sleep(sleep_time)
    

# close the connection upon event triger
event.set()
