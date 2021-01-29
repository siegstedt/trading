"""
main script for the trade bot app
"""

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time

class TradingApp(EWrapper, EClient):
    """Main class to establish connection retrieve ibapi functionality
    """
    def __init__(self):
        """Initiate TradingApp by inheriting the Eclient class
        """
        EClient.__init__(self,self)
        
    def error(self, reqId, errorCode, errorString):
        print(f"Error with Request ID {reqId} with Error Code {errorCode}. {errorString}")

    def contractDetails(self, reqId, contractDetails):
        print(f"Request ID: {reqId}, Contract: {contractDetails}")

def websocket_con():
    """Run connection to the web socket.
    Note: We export the app.run() function here so that we can call it in a separate thread
    """
    # execute the app
    app.run()
    # close the app upon event trigger
    event.wait()
    if event.is_set():
        app.close()

# create an event object for asynchronous execution
event = threading.Event()

# define app as connection to ibapi client through the wrapper
app = TradingApp()
app.connect("127.0.0.1", 7497, clientId=1)

# start the connection on a separate deamon thread
con_thread = threading.Thread(target=websocket_con)
con_thread.start()
time.sleep(1) # some latency to ensure that the connection was established as you move on

# define contract parameters
contract = Contract()
contract.symbol = 'AAPL' 
contract.secType = 'STK'
contract.currency = 'USD'
contract.exchange = 'SMART'

# request contract details
app.reqContractDetails(1000, contract)
time.sleep(5) # some latency to make sure that contract information has been extracted

# close the connection upon event triger
event.set()