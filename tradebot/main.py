"""
main script for the trade bot app
"""

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
import pandas as pd


class TradingApp(EWrapper, EClient):
    """Main class to establish connection retrieve ibapi functionality
    """

    def __init__(self):
        """Initiate TradingApp by inheriting the Eclient class
        """
        EClient.__init__(self, self)
        self.data = {}

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
    """retrieve contract data
    """
    contract = Contract()
    contract.symbol = sympbol
    contract.secType = secType
    contract.currency = currency
    contract.exchange = exchange
    return contract


def getHistData(reqNum, contract, duration="1 M", candle_size="5 mins"):
    """get historical data for a given contract
    """
    app.reqHistoricalData(
        reqId=reqNum,
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
    """store the requested tickers data in a pandas data frame
    """
    df_data = {}
    for symbol in symbols:
        df_data[symbol] = pd.DataFrame(tradeapp_obj.data[symbols.index(symbol)])
        df_data[symbol].set_index("Date", inplace=True)
    return df_data


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
    # make the process wait for the remainder of 30 seconds and then start again
    time.sleep(30 - ((time.time() - start_time) % 30))

# close the connection upon event triger
event.set()
