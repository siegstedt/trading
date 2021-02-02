"""
main script for the trade bot app
"""

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
import threading
import time
import pandas as pd


class TradingApp(EWrapper, EClient):
    """Main class to establish connection retrieve ibapi functionality"""

    def __init__(self):
        """Initiate TradingApp by inheriting the Eclient class"""
        EClient.__init__(self, self)
        self.data = {}
        self.order_df = pd.DataFrame(columns=['PermId', 'ClientId', 'OrderId',
                                              'Account', 'Symbol', 'SecType',
                                              'Exchange', 'Action', 'OrderType',
                                              'TotalQty', 'CashQty', 'LmtPrice',
                                              'AuxPrice', 'Status'])
        self.pos_df = pd.DataFrame(columns=['Account', 'Symbol', 'SecType',
                                            'Currency', 'Position', 'Avg cost'])
        self.acc_summary = pd.DataFrame(columns=['ReqId', 'Account', 'Tag', 'Value', 'Currency'])
        self.pnl_summary = pd.DataFrame(columns=['ReqId', 'DailyPnL', 'UnrealizedPnL', 'RealizedPnL'])

    def error(self, reqId, errorCode, errorString):
        print(
            f"Error with Request ID {reqId} with Error Code {errorCode}. {errorString}"
        )

    def contractDetails(self, reqId, contractDetails):
        print(f"Request ID: {reqId}, Contract: {contractDetails}")

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
        print(
            f"Request ID:{reqId}: Date {bar.date}, Open {bar.open}, High {bar.high}, Low {bar.low}, Close{bar.close}, Volume {bar.volume}"
        )

    def nextValidId(self, orderId):
        """get a new unique order id to avoid clashes across strategies and orders"""
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)

    def openOrder(self, orderId, contract, order, orderState):
        """retrieve open orders into a dataframe"""
        super().openOrder(orderId, contract, order, orderState)
        dictionary = {"PermId":order.permId, "ClientId": order.clientId, "OrderId": orderId, 
                      "Account": order.account, "Symbol": contract.symbol, "SecType": contract.secType,
                      "Exchange": contract.exchange, "Action": order.action, "OrderType": order.orderType,
                      "TotalQty": order.totalQuantity, "CashQty": order.cashQty, 
                      "LmtPrice": order.lmtPrice, "AuxPrice": order.auxPrice, "Status": orderState.status}
        self.order_df = self.order_df.append(dictionary, ignore_index=True)

    def position(self, account, contract, position, avgCost):
        """retrieve all current positions to a dataframe"""
        super().position(account, contract, position, avgCost)
        dictionary = {"Account":account, "Symbol": contract.symbol, "SecType": contract.secType,
                      "Currency": contract.currency, "Position": position, "Avg cost": avgCost}
        self.pos_df = self.pos_df.append(dictionary, ignore_index=True)

    def accountSummary(self, reqId, account, tag, value, currency):
        """retrieve an account summary to a dataframe"""
        super().accountSummary(reqId, account, tag, value, currency)
        dictionary = {"ReqId":reqId, "Account": account, "Tag": tag, "Value": value, "Currency": currency}
        self.acc_summary = self.acc_summary.append(dictionary, ignore_index=True)
        
    def pnl(self, reqId, dailyPnL, unrealizedPnL, realizedPnL):
        """retrieve a profit and loss summary to a dataframe"""
        super().pnl(reqId, dailyPnL, unrealizedPnL, realizedPnL)
        dictionary = {"ReqId":reqId, "DailyPnL": dailyPnL, "UnrealizedPnL": unrealizedPnL, "RealizedPnL": realizedPnL}
        self.pnl_summary = self.pnl_summary.append(dictionary, ignore_index=True)        


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
    for symbol in symbols:
        df_data[symbol] = pd.DataFrame(tradeapp_obj.data[symbols.index(symbol)])
        df_data[symbol].set_index("Date", inplace=True)
    return df_data


def runDataRetrieval():
    # retrieve historical data for a given data det of tickers
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
            # some latency to make sure that all historical data has been extracted
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
    return order


def marketOrder(direction, quantity):
    order = Order()
    order.action = direction
    order.orderType = "MKT"
    order.totalQuantity = quantity
    return order


def stopOrder(direction, quantity, st_price):
    order = Order()
    order.action = direction
    order.orderType = "STP"
    order.totalQuantity = quantity
    order.auxPrice = st_price
    return order


def trailStopOrder(direction, quantity, st_price, tr_step=1):
    order = Order()
    order.action = direction
    order.orderType = "TRAIL"
    order.totalQuantity = quantity
    order.auxPrice = tr_step
    order.trailStopPrice = st_price
    return order


def getOpenOrders():
    app.reqOpenOrders()
    time.sleep(1)
    order_df = app.order_df
    return order_df

def getCurrentPositions():
    app.reqPositions()
    time.sleep(1)
    pos_df = app.pos_df
    return pos_df

def getAccountSummary():
    app.reqAccountSummary(1, "All", "$LEDGER:ALL")
    time.sleep(1)
    acc_summ_df = app.acc_summary
    return acc_summ_df

def getPnlSummary():
    app.reqPnL(2, "DU3213143", "")
    time.sleep(1)
    pnl_summ_df = app.pnl_summary
    return pnl_summ_df

def MACD(DF,a=12,b=26,c=9):
    """function to calculate MACD
       typical values a(fast moving average) = 12; 
                      b(slow moving average) =26; 
                      c(signal line ma window) =9"""
    df = DF.copy()
    df["MA_Fast"]=df["Close"].ewm(span=a,min_periods=a).mean()
    df["MA_Slow"]=df["Close"].ewm(span=b,min_periods=b).mean()
    df["MACD"]=df["MA_Fast"]-df["MA_Slow"]
    df["Signal"]=df["MACD"].ewm(span=c,min_periods=c).mean()
    df.dropna(inplace=True)
    return df

def bollBnd(DF,n=20):
    "function to calculate Bollinger Band"
    df = DF.copy()
    #df["MA"] = df['close'].rolling(n).mean()
    df["MA"] = df['Close'].ewm(span=n,min_periods=n).mean()
    df["BB_up"] = df["MA"] + 2*df['Close'].rolling(n).std(ddof=0) #ddof=0 is required since we want to take the standard deviation of the population and not sample
    df["BB_dn"] = df["MA"] - 2*df['Close'].rolling(n).std(ddof=0) #ddof=0 is required since we want to take the standard deviation of the population and not sample
    df["BB_width"] = df["BB_up"] - df["BB_dn"]
    df.dropna(inplace=True)
    return df

def atr(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['High']-df['Low'])
    df['H-PC']=abs(df['High']-df['Close'].shift(1))
    df['L-PC']=abs(df['Low']-df['Close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    #df['ATR'] = df['TR'].rolling(n).mean()
    df['ATR'] = df['TR'].ewm(com=n,min_periods=n).mean()
    return df['ATR']

def rsi(DF,n=20):
    "function to calculate RSI"
    df = DF.copy()
    df['delta']=df['Close'] - df['Close'].shift(1)
    df['gain']=np.where(df['delta']>=0,df['delta'],0)
    df['loss']=np.where(df['delta']<0,abs(df['delta']),0)
    avg_gain = []
    avg_loss = []
    gain = df['gain'].tolist()
    loss = df['loss'].tolist()
    for i in range(len(df)):
        if i < n:
            avg_gain.append(np.NaN)
            avg_loss.append(np.NaN)
        elif i == n:
            avg_gain.append(df['gain'].rolling(n).mean()[n])
            avg_loss.append(df['loss'].rolling(n).mean()[n])
        elif i > n:
            avg_gain.append(((n-1)*avg_gain[i-1] + gain[i])/n)
            avg_loss.append(((n-1)*avg_loss[i-1] + loss[i])/n)
    df['avg_gain']=np.array(avg_gain)
    df['avg_loss']=np.array(avg_loss)
    df['RS'] = df['avg_gain']/df['avg_loss']
    df['RSI'] = 100 - (100/(1+df['RS']))
    return df['RSI']

def adx(DF,n=20):
    "function to calculate ADX"
    df2 = DF.copy()
    df2['H-L']=abs(df2['High']-df2['Low'])
    df2['H-PC']=abs(df2['High']-df2['Close'].shift(1))
    df2['L-PC']=abs(df2['Low']-df2['Close'].shift(1))
    df2['TR']=df2[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df2['+DM']=np.where((df2['High']-df2['High'].shift(1))>(df2['Low'].shift(1)-df2['Low']),df2['High']-df2['High'].shift(1),0)
    df2['+DM']=np.where(df2['+DM']<0,0,df2['+DM'])
    df2['-DM']=np.where((df2['Low'].shift(1)-df2['Low'])>(df2['High']-df2['High'].shift(1)),df2['Low'].shift(1)-df2['Low'],0)
    df2['-DM']=np.where(df2['-DM']<0,0,df2['-DM'])

    df2["+DMMA"]=df2['+DM'].ewm(span=n,min_periods=n).mean()
    df2["-DMMA"]=df2['-DM'].ewm(span=n,min_periods=n).mean()
    df2["TRMA"]=df2['TR'].ewm(span=n,min_periods=n).mean()

    df2["+DI"]=100*(df2["+DMMA"]/df2["TRMA"])
    df2["-DI"]=100*(df2["-DMMA"]/df2["TRMA"])
    df2["DX"]=100*(abs(df2["+DI"]-df2["-DI"])/(df2["+DI"]+df2["-DI"]))
    
    df2["ADX"]=df2["DX"].ewm(span=n,min_periods=n).mean()

    return df2['ADX']

def stochOscltr(DF,a=20,b=3):
    """function to calculate Stochastics
       a = lookback period
       b = moving average window for %D"""
    df = DF.copy()
    df['C-L'] = df['Close'] - df['Low'].rolling(a).min()
    df['H-L'] = df['High'].rolling(a).max() - df['Low'].rolling(a).min()
    df['%K'] = df['C-L']/df['H-L']*100
    df['%D'] = df['%K'].ewm(span=b,min_periods=b).mean()
    return df[['%K','%D']]

################################################################################
################################# main script ##################################
################################################################################

# create an event object for asynchronous execution
event = threading.Event()

# define app as connection to ibapi client through the wrapper
app = TradingApp()
app.connect("127.0.0.1", 7497, clientId=1)

# start the connection on a separate deamon thread
con_thread = threading.Thread(target=websocket_con)
con_thread.start()

# some latency to ensure that the connection was established as you move on
time.sleep(1)


#
# RETRIEVE HISTORICAL MARKET DATA
#

# runDataRetrieval()

#
# PLACE ORDERS
#

# create a contract object
#contract = getContract(symbol="AAPL", secType="STK", currency="USD", exchange="SMART")

# create an order object
# order = limitOrder(direction="BUY", quantity=1, lmt_price=200)
#order = marketOrder(direction="BUY", quantity=220)

# retrieve a valid order id
#order_id = app.nextValidOrderId

# EClient function to request contract details
#app.placeOrder(order_id, contract, order)


# get open orders
#order_df = getOpenOrders()

# get current positions
#pos_df = getCurrentPositions()

# get account summary
#acc_df = getAccountSummary()

# get profit and loss summary
#pnl_df = getPnlSummary()


#
# CLOSE
#


# close the connection upon event triger
event.set()
