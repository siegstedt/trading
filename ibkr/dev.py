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
        # delete all old entries from self.pos_df
        self.pos_df = pd.DataFrame(columns=self.pos_df.columns)

        # append new entries into self.pos_df
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


def compileRuntime(hours, minutes):
    run_time = (60 * 60 * hours) + (60 * minutes)
    timeout = time.time() + (run_time)
    return timeout


def terminateLoop(iteration, starttime_loop, minutes):
    print(f"> Reached end of iteration #{iteration}.")
    sleep_time = 60 * minutes - ((time.time() - starttime_loop) % 60.0 * minutes)
    print(
        f"> Residual sleep time till next iteration: {str(int(sleep_time))} seconds."
    )
    time.sleep(sleep_time)


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


def updateStopLoss(iteration, positions, orders):
    # Iterate through tickers we are currently invested in
    positions = positions[positions["Position"] > 0]
    curr_tickers = np.unique(positions.Symbol.to_numpy())
    for counter, ticker in enumerate(curr_tickers):
        counter = iteration * 1000000 + 1000 + counter
        print(f">>> {ticker}: Starting passthrough for ticker {ticker}, request {counter}")

        # pull historical data
        contract = getContract(
            symbol=ticker, secType="STK", currency="USD", exchange="ISLAND",
        )
        getHistData(
            req_num=counter,
            contract=contract,
            duration="2 W",
            candle_size="15 mins",
        )
        time.sleep(5)

        # prepare a data frame
        data_trading = app.data
        print(f">>> {ticker}: Retrieved {len(data_trading[counter])} lines.")
        df = pd.DataFrame.from_dict(data_trading[counter]).drop_duplicates()
        df.set_index("Date", inplace=True)
        df["atr"] = strategies.atr(df, 60)

        # if there are no orders yet placed
        if orders[orders["Symbol"] == ticker].empty:
            print(f">>> {ticker}: No placed orders for ticker {ticker}.")
            # place a stop loss order
            old_quantity = (
                positions[positions["Symbol"] == ticker]["Position"]
                .sort_values(ascending=True)
                .values[-1]
            )
            order_id = app.nextValidOrderId
            time.sleep(2)
            contract = getContract(
                symbol=ticker,
                secType="STK",
                currency="USD",
                exchange="ISLAND",
            )
            app.placeOrder(
                order_id + 1,
                contract,
                stopOrder(
                    "SELL",
                    old_quantity,
                    round(df["Close"][-1] - df["atr"][-1], 1),
                ),
            )
            time.sleep(2)
            continue

        # If current marvet value over total expenses
        last_closing_price = df["Close"][-1]
        bot_price = positions[(positions["Symbol"] == ticker)]["Avg cost"].sort_values(ascending=True).values[-1]
        hold_positions = positions[(positions["Symbol"] == ticker)]["Position"].sort_values(ascending=True).values[-1]
        current_value = float(last_closing_price) * float(hold_positions)
        total_expenses = float(bot_price) * float(hold_positions) + 2
        if current_value > total_expenses:
            # cancel older buy orders
            ord_id = (
                orders[orders["Symbol"] == ticker]["OrderId"]
                .drop_duplicates()
                .sort_values(ascending=True)
                .values[-1]
            )
            old_quantity = (
                positions[positions["Symbol"] == ticker]["Position"]
                .sort_values(ascending=True)
                .values[-1]
            )
            app.cancelOrder(ord_id)
            app.reqIds(-1)
            time.sleep(2)
            # place a new stop loss order
            order_id = app.nextValidOrderId
            contract = getContract(
                symbol=ticker,
                secType="STK",
                currency="USD",
                exchange="ISLAND",
            )
            app.placeOrder(
                order_id,
                contract,
                stopOrder(
                    "SELL",
                    old_quantity,
                    round(df["Close"][-1] - df["atr"][-1], 1),
                ),
            )
            time.sleep(2)
        else:
            print(f">>> {ticker}: No changes to current orders.")


def stockScreener(iteration, positions, num_basis=250, num_extract=20, new_day=False):
    # retrieve a complete list of all nasdaq tickers
    nasdaq_complete = pd.read_csv("ibkr/data/nasdaq_screener_1612425832719.csv")
    # select the 250 largest by market cap
    nasdaq_complete = nasdaq_complete.nlargest(num_basis, "Market Cap")
    # save list of nasdaq tickers
    tickers_nasdaq = nasdaq_complete["Symbol"].to_numpy()

    # retrieve historical data for selected nasdaq tickers
    print(f">>> Start data extraction for {len(tickers_nasdaq)} tickers.")
    process_start = time.time()
    # create a dictionary
    ticker_nasdaq_dict = {}
    for counter, ticker in enumerate(tickers_nasdaq):
        counter = iteration * 1000000 + 2000 + counter
        # prepare a dict with counter and ticker
        ticker_nasdaq_dict[counter] = ticker
        # get contract details
        contract = getContract(
            symbol=ticker, secType="STK", currency="USD", exchange="ISLAND",
        )
        # get historic data
        if new_day:
            getHistData(
                req_num=counter,
                contract=contract,
                duration="1 D",
                candle_size="1 day",
            )            
        else:
            getHistData(
                req_num=counter,
                contract=contract,
                duration="900 S",
                candle_size="15 mins",
            )
        # make the loop sleep for a bit to allow multiple API calls
        time.sleep(3)
    process_time = time.time() - process_start
    print(f">>> Extraction took {process_time} Secs, or {process_time/60} Mins.")

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
    print(f">>> Retrieved historical data for {len(tickers_scrnd)} tickers.")
    print(f">>> Loaded a dataframe of {df_scrnd.shape[1]} rows and {df_scrnd.shape[0]} columns.")
    df_scrnd.to_csv("ibkr/data/screened_data.csv")

    # filter for the n biggest winners
    df_scrnd = df_scrnd[df_scrnd["rel_change"] > 0.1]

    # sort according to volume and get the n best tickers
    df_scrnd = df_scrnd.sort_values("Volume", ascending=False)
    tickers_scrnd = df_scrnd["ticker"].dropna().unique()[:num_extract]

    # report status
    print(f"> Selected {len(tickers_scrnd)} for further technical analysis.")
    print(f"> Tickers: {', '.join(tickers_scrnd)}.")

    return tickers_scrnd


def dayTrader(iteration, ticker_list, trade_budget, positions, portfolio_size):
    # prepare list of current positions
    positions = positions[positions["Position"] != 0]
    curr_tickers = np.unique(positions.Symbol.to_numpy())

    # iterate over submitted list tickers
    for counter, ticker in enumerate((t for t in ticker_list if t not in curr_tickers)):
        counter = iteration * 1000000 + 3000 + counter
        print(f">>> {ticker}: Starting passthrough for ticker {ticker}, request {counter}")

        # skip if portfolio size was reached
        if len(curr_tickers) == portfolio_size:
            continue

        # pull historical data
        contract = getContract(
            symbol=ticker, secType="STK", currency="USD", exchange="ISLAND",
        )
        getHistData(
            req_num=(counter),
            contract=contract,
            duration="2 W",
            candle_size="15 mins",
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
        df["adx"]= strategies.adx(df, 20)
        df["atr"] = strategies.atr(df, 60)
        df.dropna(inplace=True)

        # calculate number of stocks for available budget
        curr_price = df["Close"][-1]
        quantity = min(int(float(trade_budget) / float(curr_price)), 500)
        if quantity == 0:
            print(f">>> {ticker}: At the current stock price {curr_price} USD, you cannot buy a single {ticker} share.")
            continue
        else:
            print(f">>> {ticker}: For the budget of {trade_budget} and at the current price of {curr_price} USD, {quantity} stocks can be purchased.")

        # place orders according to conditions
        if (
            df["macd"][-1] > df["signal"][-1] 
            and df["stoch"][-1] > 20
            and df["stoch"][-1] < 80
            and df["stoch"][-1] > df["stoch"][-2] > df["stoch"][-3]
            and df["adx"][-1] > 20
            and df["adx"][-1] > df["adx"][-2] > df["adx"][-3]
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
            # append ticker to list of current tickers
            curr_tickers = np.append(curr_tickers, ticker)
        else:
            print(f">>> {ticker}: Criteria not met. No orders placed.")


def liquifyAll():
    # cancelling open orders
    app.reqGlobalCancel()

    # closing off open positions
    order_id = app.nextValidOrderId
    positions = account.getCurrentPositions(app)

    for ticker in positions["Symbol"]:
        quantity = positions[positions["Symbol"] == ticker]["Position"].values[0]
        contract = getContract(
            symbol=ticker,
            secType="STK",
            currency="USD",
            exchange="ISLAND",
        )
        app.placeOrder(order_id, contract, marketOrder("SELL", quantity))
        order_id += 1


##############################################################################


# global variables
portfolio_size = 20
max_per_trade = 2000

# create an event object for asynchronous execution
event = threading.Event()

# define app as connection to ibapi client through the wrapper
app = TradingApp()
app.connect("127.0.0.1", 7497, clientId=1)  # paper
# app.connect("127.0.0.1", 7496, clientId=1)  # live

# start the connection on a separate deamon thread
con_thread = threading.Thread(target=websocket_con)
con_thread.start()
time.sleep(1)
print("Interactive Brokers Trade Bot is up and running.")

# here I could take like 30 mins to generate an initial list of
# companies that are worth being checked over the day

# start while loop
timeout = compileRuntime(hours=6, minutes=0)
mins_per_loop = 15
iteration = 0
while time.time() <= timeout:
    # break while loop if past 3:30 PM US Eastern time

    # start
    iteration += 1
    starttime_loop = time.time()
    time_string = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
    print(f"> {time_string} - Starting loop #{str(iteration)}.")

    # prepare variables for the loop
    curr_tickers = account.getCurrentPositionsList(app)
    positions = account.getCurrentPositions(app)

    # run through current positions for updating stop loss
    if len(curr_tickers) > 0:
        orders = account.getOpenOrders(app)
        print(f">> Update stop loss orders in loop # {iteration}")
        updateStopLoss(iteration=iteration, positions=positions, orders=orders)

    # if portfolio is filled, set sleeping time and continue
    if portfolio_size == len(curr_tickers):
        terminateLoop(iteration=iteration, starttime_loop=starttime_loop, minutes=mins_per_loop)
        continue

    # allocate trade budget
    curr_balance = account.getAccountBalance(app)
    open_slots = account.calculateOpenTradeSlots(
        portfolio_size=portfolio_size, num_of_curr_pos=len(curr_tickers)
    )
    trade_budget = account.allocateTradeBudget(
        curr_balance, open_slots, max_per_trade=max_per_trade
    )

    # move ahead only if there is sufficient tarde budget
    print(f"> Available budget per trade is at {str(trade_budget)}.")
    trade_budget = 10000
    if trade_budget < 50:
        print("! Account not sufficiently funded. Inject more capital.")
        terminateLoop(iteration=iteration, starttime_loop=starttime_loop, minutes=mins_per_loop)
        continue

    # screen for stocks
    if (len(curr_tickers) == 0) and (iteration == 1):
        print("FIRST RUN OF THE DAY")
        # screen stocks of past day
        screened_tickers = stockScreener(iteration, positions, 200, 40, True)
    else:
        print("N-TH RUN OF THE DAY")
        # screen stocks of past 15 minutes
        screened_tickers = stockScreener(iteration, positions, 200, 40)

    print(f">> Trading process to start with {len(screened_tickers)} tickers:")
    print(f">> {', '.join(screened_tickers)}")

    # deploy trading strategy on selected stocks
    print(f">> Start day trading for loop # {iteration}")
    dayTrader(
        iteration=iteration,
        ticker_list=screened_tickers,
        trade_budget=trade_budget,
        positions=positions,
        portfolio_size=portfolio_size,
    )

    # set a maximum time per while loop
    terminateLoop(iteration=iteration, starttime_loop=starttime_loop, minutes=mins_per_loop)

# liquify all positions and cancel all orders
liquifyAll()

# close the connection upon event triger
event.set()
